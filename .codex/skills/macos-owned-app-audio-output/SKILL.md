---
name: macos-owned-app-audio-output
description: Verify macOS application sound and mute with an owned-app ScreenCaptureKit collector or an explicit CoreAudio process tap. Use when generated WAV files or playback logs do not establish output, or an owned Chromium root PID is silent while a child process plays audio.
---
# Verify owned application audio output

## Failure mechanism

AVAudioPlayer construction, generated WAV bytes, and advancing playback time prove separate stages, not system output. A ScreenCaptureKit recording can also be all zeros when browser audio is emitted by an owned child process rather than the supplied root PID. Active WebAudio does not prove sampled application output.

## ScreenCaptureKit route

When the target application can be selected as a shareable process, use an application or window filter and add only audio output. Keep microphone capture disabled and do not save screen frames. The maintained S16 implementation is in the independent [S16 repository](https://github.com/xinxiayiyan/s16): [capture_audio.py](https://github.com/xinxiayiyan/s16/blob/main/tools/capture_audio.py) and [capture-owned-audio.swift](https://github.com/xinxiayiyan/s16/blob/main/tools/capture-owned-audio.swift).

From the S16 checkout root:

```sh
mkdir -p private
swiftc -parse-as-library tools/capture-owned-audio.swift -o private/capture-owned-audio
python3 -m tools.capture_audio --pid OWNED_SAFARI_PID --seconds 30 --out private/new-capture
```

The wrapper accepts an explicitly owned Safari PID, a fresh output path under private/, and a 5–30 second window. It records collector and binary hashes, verifies capture readiness, and leaves UI actions to CUA after ready.json appears. Begin capture before triggering playback. The Swift binary also accepts an optional JSON list of AX identifiers for a directly driven capture, but the S16 wrapper intentionally does not use that path.

The collector selects the exact `SCRunningApplication.processID` and uses `SCContentFilter(display:including:exceptingWindows:)`; it sets `capturesAudio=true` and `captureMicrophone=false`, attaches only audio output, saves no screen frames, and flushes the sample queue after stopping before closing the file. Preserve its failure receipt; no samples is unavailable, not proof of silence.

## CoreAudio process-tree fallback

Use this when the supplied browser process is silent but audio may come from its owned audio-service child. First launch one isolated browser/app instance and record its root PID. Do not capture an existing browser with unrelated user tabs.

The maintained [VALORANT audio inspection tool](https://github.com/xinxiayiyan/valorant-predictor/blob/main/scripts/inspect_owned_audio.swift) lists output-producing CoreAudio objects only for supplied PIDs. It does not record audio.

Compile the maintained [owned-process collector](https://github.com/xinxiayiyan/valorant-predictor/blob/main/scripts/capture_owned_process_audio.swift) from the root of the independent VALORANT predictor checkout. Embed the usage description from its accompanying plist:

```sh
mkdir -p artifacts
swiftc -parse-as-library scripts/capture_owned_process_audio.swift \
  -Xlinker -sectcreate -Xlinker __TEXT -Xlinker __info_plist \
  -Xlinker scripts/audio_capture_info.plist \
  -o artifacts/capture-owned-process-audio
artifacts/capture-owned-process-audio OWNED_APP_ROOT_PID artifacts/output.wav 5
```

Initialize the app's audio service before capture so its output objects exist. Wait for READY owned process audio capture, then trigger the real UI action in the isolated app. The collector takes one owned root PID, output WAV path, and duration up to 60 seconds. It selects that PID and descendants' explicit CoreAudio process objects, not a global tap or microphone. Inspect the sidecar's captured PIDs, frames, peak/RMS, sample rate, and callback errors.

## Verification and limits

For audible scenarios, require actual frames and nonzero signal. For mute, trigger real playback while muted, require sampled silence, then restore playback and require output. Preserve the WAV and source provenance. afconvert -f WAVE -d LEI16 input.wav replay.wav converts a float WAV for playback; it is not new evidence.

Both collectors have been verified with real UI actions, sampled mute, restored output, and product cues. Digital output presence does not prove physical speaker volume, complete sound identity, or subjective quality. Screen Recording, Accessibility, CoreAudio, SDK, and process-object failures remain unavailable; do not turn them into silent passes.

## High-risk actions

Never record another app or microphone as a substitute. Do not use an unrelated tone generator to prove product UI behavior, accept silence without in-window triggers, or weaken assertions to make capture succeed. Run UI suites sequentially to avoid focus competition; preserve user progress and failed receipts.
