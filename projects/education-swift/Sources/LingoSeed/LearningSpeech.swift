@preconcurrency import AVFoundation
@preconcurrency import Speech
import Observation
import Foundation

/// Capture is started only by an explicit learner action. Verification can inject denial without opening audio input.
@MainActor @Observable final class LearningSpeech {
    enum State { case idle, requesting, recording, recognizing, denied, failed }
    var state: State = .idle
    var transcript = ""
    var failure: String?
    private var engine: AVAudioEngine?
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?
    private var generation = UUID()
    var onFinal: ((String) -> Void)?
    var active: Bool { state == .requesting || state == .recording || state == .recognizing }

    func start() async {
        guard !active else { finish(); return }
        cancel()
        transcript = ""; failure = nil; state = .requesting
        let attempt = generation
        if CommandLine.arguments.contains("--verify-speech-denied") { state = .denied; NSLog("Verification microphone refusal injected before capture"); return }
        guard Bundle.main.object(forInfoDictionaryKey: "NSMicrophoneUsageDescription") != nil,
              Bundle.main.object(forInfoDictionaryKey: "NSSpeechRecognitionUsageDescription") != nil else {
            state = .failed; failure = "无法开始录音。"; return
        }
        let microphone = await AVCaptureDevice.requestAccess(for: .audio)
        guard generation == attempt else { return }
        guard microphone else { state = .denied; return }
        let authorization = await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { continuation.resume(returning: $0) }
        }
        guard generation == attempt else { return }
        guard authorization == .authorized else { state = .failed; failure = "无法使用语音识别。"; return }
        guard let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US")), recognizer.isAvailable else {
            state = .failed; failure = "无法开始录音。"; return
        }
        let engine = AVAudioEngine()
        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        self.engine = engine; self.request = request
        task = recognizer.recognitionTask(with: request) { [weak self] result, error in
            let text = result?.bestTranscription.formattedString
            let final = result?.isFinal == true
            let message = error?.localizedDescription
            Task { @MainActor [weak self] in
                guard let self, self.generation == attempt else { return }
                if let text { self.transcript = text }
                if final {
                    let completed = self.onFinal; self.cancel()
                    if let text { self.transcript = text; completed?(text) }
                } else if let message {
                    self.cancel(); self.state = .failed; self.failure = message
                }
            }
        }
        let input = engine.inputNode
        let format = input.outputFormat(forBus: 0)
        guard format.sampleRate > 0, format.channelCount > 0 else { cancel(); state = .failed; failure = "无法开始录音。"; return }
        input.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
            request.append(buffer)
        }
        do { engine.prepare(); try engine.start(); state = .recording }
        catch { cancel(); state = .failed; failure = "无法开始录音。" }
    }
    func finish() {
        guard state == .recording else { return }
        releaseInput(); request?.endAudio(); state = .recognizing
    }
    private func releaseInput() {
        if let engine { engine.stop(); engine.inputNode.removeTap(onBus: 0) }
        engine = nil
    }
    func cancel() {
        generation = UUID(); releaseInput(); request?.endAudio(); task?.cancel()
        request = nil; task = nil; state = .idle
    }
    func dismissDenial() { if state == .denied { state = .idle } }
}
