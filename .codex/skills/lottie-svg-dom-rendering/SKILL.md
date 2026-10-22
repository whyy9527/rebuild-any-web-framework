---
name: lottie-svg-dom-rendering
description: Diagnose serialized Lottie SVG frames that render black, repeat sprites, or lose clipping when embedded as an image during app-rebuild asset capture.
---

# Lottie SVG DOM Rendering

Use this when a captured serialized SVG differs from the original browser frame, especially when image-element output shows black content, repeated sprites, or broken clipping despite the source DOM rendering correctly.

Compare the same SVG two ways in an isolated browser context, with identical viewport, CSS dimensions, and device scale:

1. Embed it as an image with a data URL.
2. Insert the SVG markup inline in the page.

Capture both outputs with transparency and compare against the observed frame. Preserve the failed render as evidence. If inline rendering matches, keep an explicit per-asset inline mode only when the current asset loader supports it; do not replace every image renderer.

The Duolingo capture that demonstrated this behavior is historical evidence, not a current source or runtime dependency: old resolver at source commit（历史证据未随公开发行） and failed image render（历史证据未随公开发行）. Do not copy its app assets into a framework release.

Correct still rendering and observed movement do not prove animation phase or trigger equality. Do not redraw source geometry to compensate for an embedding failure, remove image comparisons, mask the broken region, or use a static screenshot as proof of dynamic fidelity.
