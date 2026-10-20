import Foundation
import AppKit
import ScreenCaptureKit
import AVFoundation
import CoreMedia
import ApplicationServices

// System-output loopback filtered to one explicitly supplied, owned application.
// No microphone input and no screen frames are recorded.
final class AudioSink: NSObject, SCStreamOutput, @unchecked Sendable {
    let destination: URL
    var file: AVAudioFile?
    var frames: Int64 = 0
    var peak: Float = 0
    var energy: Double = 0
    var samples: Int64 = 0
    var failure: String?
    init(_ destination: URL) { self.destination = destination }
    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .audio, CMSampleBufferDataIsReady(sampleBuffer), let description = sampleBuffer.formatDescription else { return }
        let format = AVAudioFormat(cmAudioFormatDescription: description)
        let count = CMSampleBufferGetNumSamples(sampleBuffer)
        guard count > 0, let pcm = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: AVAudioFrameCount(count)) else { return }
        pcm.frameLength = AVAudioFrameCount(count)
        let status = CMSampleBufferCopyPCMDataIntoAudioBufferList(sampleBuffer, at: 0, frameCount: Int32(count), into: pcm.mutableAudioBufferList)
        guard status == noErr else { failure = "Audio buffer extraction failed: \(status)"; return }
        do {
            if file == nil {
                var settings = format.settings
                settings[AVLinearPCMIsNonInterleaved] = false
                file = try AVAudioFile(forWriting: destination, settings: settings, commonFormat: .pcmFormatFloat32, interleaved: false)
            }
            try file?.write(from: pcm)
            frames += Int64(count)
            for buffer in UnsafeMutableAudioBufferListPointer(pcm.mutableAudioBufferList) {
                guard let data = buffer.mData, format.commonFormat == .pcmFormatFloat32 else { continue }
                let values = data.assumingMemoryBound(to: Float.self)
                let length = Int(buffer.mDataByteSize) / MemoryLayout<Float>.size
                for i in 0..<length { peak = max(peak, abs(values[i])); energy += Double(values[i]) * Double(values[i]) }
                samples += Int64(length)
            }
        } catch { failure = "Audio file write failed" }
    }
}
@main struct CaptureOwnedAudio {
    @MainActor static func main() async throws {
        let filterMode = CommandLine.arguments.contains("--filter=window") ? "window" : "application"
        let excludeSelf = !CommandLine.arguments.contains("--include-self-audio")
        let args = CommandLine.arguments.filter { $0 != "--filter=window" && $0 != "--include-self-audio" }
        let pid = pid_t(args[1])!
        let destination = URL(fileURLWithPath: args[2])
        let duration = Double(args[3])!
        let content = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: true)
        guard let app = content.applications.first(where: { $0.processID == pid }), let display = content.displays.first else { throw NSError(domain: "OwnedAudio", code: 1, userInfo: [NSLocalizedDescriptionKey: "The supplied child application is not shareable"]) }
        let filter: SCContentFilter
        var ownedWindow: UInt32?
        if filterMode == "window" {
            _ = NSApplication.shared
            guard let window = content.windows.first(where:{ $0.owningApplication?.processID == pid && $0.frame.width > 100 && $0.frame.height > 100 }) else {
                throw NSError(domain:"OwnedAudio",code:3,userInfo:[NSLocalizedDescriptionKey:"No supplied owned application window"])
            }
            ownedWindow = window.windowID
            filter = SCContentFilter(desktopIndependentWindow:window)
        } else { filter = SCContentFilter(display: display, including: [app], exceptingWindows: []) }
        let config = SCStreamConfiguration()
        config.width = 2; config.height = 2; config.capturesAudio = true
        config.sampleRate = 48000; config.channelCount = 2
        config.excludesCurrentProcessAudio = excludeSelf
        config.captureMicrophone = false
        let sink = AudioSink(destination)
        let queue = DispatchQueue(label: "owned-audio")
        let stream = SCStream(filter: filter, configuration: config, delegate: nil)
        try stream.addStreamOutput(sink, type: .audio, sampleHandlerQueue: queue)
        try await stream.startCapture()
        print("READY owned application audio capture"); fflush(stdout)
        let started = Date()
        var actions: [[String: Any]] = []
        if args.count > 4 {
            let ids = try JSONDecoder().decode([String].self, from: Data(contentsOf: URL(fileURLWithPath: args[4])))
            let axApp = AXUIElementCreateApplication(pid)
            func attribute(_ element: AXUIElement, _ name: String) -> AnyObject? {
                var value: CFTypeRef?
                guard AXUIElementCopyAttributeValue(element, name as CFString, &value) == .success else { return nil }
                return value
            }
            func nodes(_ root: AXUIElement, _ depth: Int = 0) -> [AXUIElement] {
                guard depth < 24 else { return [] }
                return [root] + ((attribute(root, kAXChildrenAttribute) as? [AXUIElement]) ?? []).flatMap { nodes($0, depth + 1) }
            }
            for id in ids {
                var target: AXUIElement?
                while Date().timeIntervalSince(started) < duration - 1 {
                    let windows = attribute(axApp, kAXWindowsAttribute) as? [AXUIElement] ?? []
                    target = windows.flatMap { nodes($0) }.first { attribute($0, kAXIdentifierAttribute) as? String == id && (attribute($0, kAXEnabledAttribute) as? NSNumber)?.boolValue == true }
                    if target != nil { break }
                    try await Task.sleep(for: .milliseconds(70))
                }
                guard let target, AXUIElementPerformAction(target, kAXPressAction as CFString) == .success else {
                    try await stream.stopCapture()
                    throw NSError(domain: "OwnedAudio", code: 2, userInfo: [NSLocalizedDescriptionKey: "Cannot press owned audio scenario control: " + id])
                }
                actions.append(["id": id, "elapsed_seconds": Date().timeIntervalSince(started)])
                let gap = args.count > 5 ? Double(args[5])! : 0.16
                try await Task.sleep(for: .seconds(gap))
            }
        }
        let remaining = duration - Date().timeIntervalSince(started)
        if remaining > 0 { try await Task.sleep(for: .seconds(remaining)) }
        try await stream.stopCapture()
        queue.sync {}
        var result: [String: Any] = ["kind": "owned_application_audio_loopback", "frames": sink.frames, "peak": sink.peak, "rms": sink.samples > 0 ? sqrt(sink.energy / Double(sink.samples)) : 0, "samples": sink.samples, "microphone": false, "filter": "Only explicitly selected owned application/window", "filter_mode":filterMode, "excludes_current_process_audio":excludeSelf, "owned_pid":pid, "duration_seconds": duration, "ui_actions": actions]
        if let ownedWindow { result["owned_window_id"] = ownedWindow }
        if let failure = sink.failure { result["failure"] = failure }
        sink.file = nil
        try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]).write(to: destination.appendingPathExtension("json"))
        print(String(data: try JSONSerialization.data(withJSONObject: result, options: .sortedKeys), encoding: .utf8)!)
    }
}
