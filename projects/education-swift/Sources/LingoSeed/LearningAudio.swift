import AppKit
import AVFoundation

/// Bundled reference speech where observed; synthesized cues remain a known fidelity gap.
@MainActor final class LearningAudio {
    enum Cue: String, CaseIterable { case tap, correct, incorrect, complete }
    private var player: AVAudioPlayer?
    private let speech = AVSpeechSynthesizer()
    private var referenceSpeech: AVAudioPlayer?
    private var referenceEffects: [AVAudioPlayer] = []
    private let resourceURL: (String) -> URL?
    init(resourceURL: @escaping (String) -> URL? = { _ in nil }) { self.resourceURL = resourceURL }
    var referenceSpeechPlaying: Bool { referenceSpeech?.isPlaying ?? false }
    var referencePlaybackTime: TimeInterval { referenceSpeech?.currentTime ?? 0 }
    var muted = false { didSet { if muted { player?.stop(); referenceSpeech?.stop(); referenceEffects.forEach { $0.stop() }; speech.stopSpeaking(at: .immediate) } } }
    var effectsEnabled = true { didSet { if !effectsEnabled { player?.stop(); referenceEffects.forEach { $0.stop() } } } }
    @discardableResult func playReferenceEffect(_ resource: String?, volume: Double? = nil) -> Bool {
        guard !muted, effectsEnabled, let resource, let url = resourceURL(resource) else { return false }
        do {
            referenceEffects.removeAll { !$0.isPlaying }
            let effect = try AVAudioPlayer(contentsOf: url)
            if let volume,volume.isFinite,(0...1).contains(volume) {effect.volume=Float(volume)}
            effect.prepareToPlay(); referenceEffects.append(effect)
            return effect.play()
        } catch { NSLog("Reference effect playback failed: %@", error.localizedDescription); return false }
    }
    var isPlaying: Bool { player?.isPlaying ?? false }
    var playbackTime: TimeInterval { player?.currentTime ?? 0 }
    @discardableResult func play(_ cue: Cue) -> Bool {
        guard !muted && effectsEnabled else { return false }
        player?.stop()
        speech.stopSpeaking(at: .immediate)
        do {
            player = try AVAudioPlayer(data: Self.wave(cue))
            player?.prepareToPlay()
            return player?.play() ?? false
        } catch { NSLog("Audio playback failed: %@", error.localizedDescription); return false }
    }
    func speak(_ text: String, language: String = "en-US", resource: String? = nil) {
        if let resource {
            guard !muted else { return }
            player?.stop(); referenceSpeech?.stop(); speech.stopSpeaking(at: .immediate)
            guard let url = resourceURL(resource) else {
                NSLog("Reference speech resource missing: %@", resource); return
            }
            do {
                referenceSpeech = try AVAudioPlayer(contentsOf: url)
                referenceSpeech?.prepareToPlay(); referenceSpeech?.play()
            } catch { NSLog("Reference speech playback failed: %@", error.localizedDescription) }
            return
        }
        guard !muted else { return }
        player?.stop(); referenceSpeech?.stop(); speech.stopSpeaking(at: .immediate)
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: language)
        utterance.rate = 0.45
        speech.speak(utterance)
    }
    static func wave(_ cue: Cue) -> Data {
        let notes: [Double] = switch cue {
        case .tap: [640]
        case .correct: [660, 880]
        case .incorrect: [330, 220]
        case .complete: [523.25, 659.25, 783.99, 1046.5]
        }
        let rate = 22050
        let duration = cue == .tap ? 0.045 : 0.15
        let count = Int(Double(rate) * duration)
        var samples = Data()
        for frequency in notes {
            for i in 0..<count {
                let t = Double(i) / Double(rate)
                let envelope = min(1, t / 0.008) * pow(max(0, 1 - Double(i) / Double(count)), 1.5)
                let value = Int16(sin(2 * .pi * frequency * t) * envelope * 7000)
                var little = value.littleEndian
                withUnsafeBytes(of: &little) { samples.append(contentsOf: $0) }
            }
        }
        var data = Data()
        func ascii(_ value: String) { data.append(contentsOf: value.utf8) }
        func number<T: FixedWidthInteger>(_ value: T) { var little = value.littleEndian; withUnsafeBytes(of: &little) { data.append(contentsOf: $0) } }
        ascii("RIFF"); number(UInt32(36 + samples.count)); ascii("WAVEfmt "); number(UInt32(16)); number(UInt16(1)); number(UInt16(1)); number(UInt32(rate)); number(UInt32(rate * 2)); number(UInt16(2)); number(UInt16(16)); ascii("data"); number(UInt32(samples.count)); data.append(samples)
        return data
    }
}
