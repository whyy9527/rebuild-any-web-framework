---
name: macos-owned-app-audio-output
description: Verify macOS application sound and mute through PID-filtered ScreenCaptureKit or CoreAudio process taps with timed UI actions. Use when player logs or generated WAV files are insufficient, or a Chromium root-PID recording is silent despite active WebAudio.
---
# Verify owned application audio output

## Failure mechanism

AVAudioPlayer construction, generated WAV bytes and advancing playback time prove separate stages, not application system output. A silent recording is also weak evidence if the clicks happened before capture began. Preserve those transport checks, then record real triggers inside a PID-filtered capture.

## Procedure

Use an isolated app instance and progress file. Record its PID; inspect or terminate only that owned instance. Screen Recording and Accessibility permissions must already be available or obtained through the normal authorized flow.

The repository's tested collector is [capture-owned-audio.swift](../../../projects/duolingo-web/capture-owned-audio.swift). Its optional fourth argument is a JSON array of AX identifiers. Compile and invoke from the repository root:

```sh
swiftc -parse-as-library projects/duolingo-web/capture-owned-audio.swift -o artifacts/capture-owned-audio
artifacts/capture-owned-audio OWNED_PID artifacts/output.wav 7 artifacts/actions.json
```

Adapt the real app's AX identifiers and duration; do not copy the education fixture's answers into a different product. The [product audio suite](../../../projects/duolingo-web/product-audio-checks.py) demonstrates isolated launch, failure reporting and cleanup.

Essential mechanics:

- Find the exact `SCRunningApplication.processID`, use `SCContentFilter(display:including:[app],exceptingWindows:[])`, set `capturesAudio = true` and `captureMicrophone = false`. Add only `.audio` stream output; no screen frames are saved.
- Begin capture before any UI trigger. Drive the owned PID's enabled AX controls and record elapsed action timestamps inside the recording interval. Reject missing controls or incomplete action counts.
- Copy samples with `CMSampleBufferCopyPCMDataIntoAudioBufferList` into an allocated `AVAudioPCMBuffer`; write through `AVAudioFile`. Flush the serial sample queue after `stopCapture` before reading totals/closing the file.
- Require sampled frames and nonzero signal for audible scenarios. For mute, trigger actual sounds while muted and require sampled silence, then unmute and require output again. Do not treat no samples as silence.
- Keep the original WAV and source provenance. For convenient playback, `afconvert -f WAVE -d LEI16 input.wav replay.wav` converts a float WAV to PCM16; it does not create additional audio evidence.

## Verification and limits

Verified on an actual SwiftUI client: choice and instruction speech, correct/incorrect/completion cues, automatic matching feedback, mute during real matching clicks, and restored output. The collector records digital application output; it does not prove physical speaker volume or subjective sound quality. Use a host SDK supporting the collector's ScreenCaptureKit properties; permission/API failure remains unavailable, not pass.

## Chromium audio-child fallback

A Chromium root-PID ScreenCaptureKit recording can contain only zeros while an
owned audio-service child emits sound. This was observed with both application
and window filters; an active WebAudio context alone did not prove system output.
Keep those failed receipts and inspect the isolated browser's owned PID tree.

[inspect_owned_audio.swift](https://github.com/xinxiayiyan/valorant-predictor/blob/main/scripts/inspect_owned_audio.swift)
queries `kAudioProcessPropertyIsRunningOutput` only for explicitly supplied PIDs.
Use the root and known descendants from the task's isolated browser, not an
existing browser containing unrelated user tabs.

The tested fallback is
[capture_owned_process_audio.swift](https://github.com/xinxiayiyan/valorant-predictor/blob/main/scripts/capture_owned_process_audio.swift).
The files are maintained in the independent
[`xinxiayiyan/valorant-predictor` checkout](https://github.com/xinxiayiyan/valorant-predictor).
From that checkout's root, compile with its audio-usage description embedded,
using a host SDK exposing the CoreAudio process-tap APIs:

```sh
swiftc -parse-as-library scripts/capture_owned_process_audio.swift \
  -Xlinker -sectcreate -Xlinker __TEXT -Xlinker __info_plist \
  -Xlinker scripts/audio_capture_info.plist \
  -o artifacts/capture-owned-process-audio
artifacts/capture-owned-process-audio OWNED_BROWSER_ROOT_PID artifacts/output.wav 5
```

The collector maps the owned PID tree to explicit CoreAudio process objects,
uses `CATapDescription(stereoMixdownOfProcesses:)` with `.unmuted`, and reads a
private aggregate device. It copies float PCM into `AVAudioPCMBuffer` and flushes
the serial writer queue after stopping. The sidecar reports captured PIDs,
frames, peak/RMS and callback failures; it does not open a microphone or global tap.

Initialize the product's audio service first if no owned audio object exists,
reset the scenario, then wait for `READY` before the measured UI triggers. The
retired `qa_audio.py` handshake helper is preserved only as [historical evidence
at source commit `8dd71eb`](https://github.com/whyy9527/rebuild-any-web/blob/8dd71eb7cb3815ebee93ca40950e8bfced518086/projects/valorant-predictor/scripts/qa_audio.py);
it is not an entrypoint in the independent checkout. Adapt the actual product controls.
The fallback was verified with real clicks, sampled mute, restored output,
autofill and save cues. Nonzero output establishes audibility, not complete sound
identity; retain waveform differences and any transport anomalies.

## Avoid false evidence

Never record another app or microphone as a substitute. Do not bypass permission failures, use an unrelated tone generator to prove the product UI, accept silence without in-window triggers, or weaken behavior assertions to make capture succeed. Run UI suites sequentially to avoid focus competition; preserve user progress and failed receipts.
Do not replace an explicit owned-process tap with a global tap to obtain a nonzero recording.
