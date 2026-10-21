# Mouse4 Changelog

Newer versions are listed first. This is the public release history; private licensing and service credentials are not included.

## [1.4.7] - 2026-10-21

### Safer long screenshots and clipboard handling

- Stops Long Capture before the stitched image exceeds 30,000 px, or earlier when available memory is low.
- Saves the aligned content already captured when a safety limit is reached. If saving fails, the capture stays open so Finish can be retried.
- After 60 seconds without input, saves the captured portion and closes Long Capture only after a successful save.
- Selected-text translation does not overwrite clipboard formats it cannot preserve; it stops first and leaves the clipboard intact.
- Windows Setup: `Mouse4-Setup-1.4.7.exe`.

## [1.4.5] - 2026-10-20

### Move text annotations after typing

- Pressing Enter commits the text and returns to the normal pointer state.
- Drag a committed text annotation directly to reposition it within the capture canvas.
- Turning off the text tool also commits the current text and keeps it movable.
- Shows a move cursor when the pointer is over a committed text annotation.

## [1.4.4] - 2026-10-16

### Reach the page bottom with the wheel, even from a short selection

- After the page reaches its actual scroll limit, another downward wheel input captures the missing content below the original selection and extends the visible blue frame to the content viewport bottom before Save.
- Preserves the selected top and width. No dragging or manual frame adjustment is needed.
- Clicking Long Capture without scrolling leaves the original frame unchanged; it does not jump to the screen bottom.
- Verifies overlapping pixels before appending the tail and updates the alignment reference to prevent duplicate content on repeated bottom wheels.
- Keeps idle-wheel cancellation and the verified on-finish tail fallback.
- Registers capture exclusion before the selection overlay first appears, preventing the overlay mask from entering an initial snapshot.

## [1.4.3] - 2026-10-16

### Preserve the selection and capture the final page tail

- Fixes the 1.4.2 regression that expanded the selection to the screen bottom as soon as Long Capture was clicked, even without wheel input.
- Keeps the selection and toolbar in place throughout scrolling.
- On finish at a confirmed page bottom, checks the actual scroll container and captures missing rows below the selection up to the content viewport edge.
- Appends the tail only when its pixels overlap the last captured viewport; if accessibility is unavailable or the page changes, it keeps the existing capture.
- Handles Chrome's first accessibility query with a bounded wait for the scroll pattern to become available.
- Keeps controlled scrolling and idle-input cancellation.

## [1.4.2] - 2026-10-15

### Include the last visible page content in long captures

- Extends a long-capture selection to the current monitor work-area bottom while keeping the selected top and width.
- Prevents the page from reaching the scrollbar bottom while the final visible content remains below a fixed capture rectangle.
- Keeps controlled scrolling, viewport-stability checks, and idle-wheel behavior unchanged.
- Adds regression coverage for bottom anchoring and cross-monitor selections. The automatic frame extension was revised in 1.4.3.

## [1.4.1] - 2026-10-15

### Keep long captures moving to the actual page bottom

- Refreshes the scroll target from the latest real wheel position before each controlled step.
- Allows a scrollbar just outside the selected pixels to continue the same capture when it belongs to the identified source window.
- Treats a settled frame with no viewport movement as a stalled scroll and retries once only while wheel input is active.
- Discards buffered scroll intent after the wheel becomes idle so capture does not continue in the background.

## [1.4.0] - 2026-10-15

### Send selected webpage text to AI

- Adds a Chrome selection-only context-menu action: **Send to AI** in English Chrome and **发送到AI** in Chinese Chrome.
- Sends selected webpage text to the same daily ChatGPT conversation and queue used by screenshot handoff.
- Keeps the workflow Chat-only, protects unrelated drafts, and does not monitor `Ctrl+C`, read the clipboard, or add a Windows system-wide context-menu entry.
- Keeps the extension interface bilingual while the product name remains English.

### Reliability and release maintenance

- Keeps individual screenshot failures in manual review so later screenshots can continue.
- Preserves receipt checks, duplicate-send protection, newest-first history, daily conversation naming, and the blank-chat `Instant` preference.
- Updates the public English README, sales page, installation guide, release notes, and launch copy.
- Leaves the existing English demo video and page animation unchanged in this release.
- Application source code, private licensing services, and API credentials remain outside the public repository.

## [1.2.2] - 2026-10-06

### First-capture responsiveness

- Warms the persistent capture worker after startup so the first user screenshot is ready faster.
- Primes the native overlay and toolbar without taking focus or accepting mouse input.
- Keeps shortcut readiness independent of warmup and captures a fresh frame for every user request.
- Records desktop capture duration in milliseconds for performance diagnostics.

### Public materials

- Updates the public English README and sales page to 1.2.2.
- Adds one-click AI handoff to the current product description and documents the immediate `Sent to AI` feedback shown after the AI action is clicked.
- Leaves the existing English demo video and page animation unchanged.

## [1.1.22] - 2026-10-04

### Translation panel polish

- Centers the copy action on the final translated line across all supported reading sizes.
- Keeps wrapping, panel width, and action placement stable as translated text changes length.
- Refreshes the public product page, demo video, release notes, and launch copy.

### Public materials

- Adds an English customer demo with English captions, an English translation result, and the complete capture workflow.
- Adds the direct English demo link to the public README.
- Publishes three English feature articles covering context-preserving capture, Long Capture, and selected-text translation.
- Keeps application source code, private licensing services, and API credentials out of the public repository.

## [1.1.21] - 2026-10-04

### Pinned references

- Fixes a crash while drawing the pin control on a captured reference.
- Keeps pinned screenshots fully visible, draggable, zoomable, and above other windows.

## [1.1.20] - 2026-10-04

### Reading controls

- Adds large, standard, and small translation text sizes with remembered preferences.
- Adds a four-step frosted transparency control with a readable light panel at every level.
- Adds concise hover help for the translation panel controls.

## [1.1.19] - 2026-10-03

### Translation panel behavior

- Unpinned translation panels close on an outside click, scroll, or source-application switch.
- Pinned panels stay available and can be dragged independently of the next translation.
- The translation-only settings page returns to the active result after saving or closing.

## [1.1.18] - 2026-10-03

### Translation display

- Adds the light frosted translation panel and four readable transparency levels.
- Keeps translated text and controls clear while the source application remains visible.

## [1.1.17] - 2026-10-03

### Reliability

- Improves first-use selection handling, cancellation, streaming response handling, and clipboard fallback behavior.
- Preserves the original panel position when a translation request reports an error.
- Adds practical diagnostics for selection, foreground-window, and panel lifecycle issues.

## [1.1.16] - 2026-10-03

### Panel controls

- Changes the transparency control to a circular icon with four visual states.
- Keeps transparency independent from the text and icon opacity.

## [1.1.12] - 2026-10-03

### Translation service settings

- Allows the provider, base URL, model, and API key to be entered manually.
- Adds immediate background transparency preview and local preference storage.

## [1.1.10] - 2026-10-03

### Startup and positioning

- Improves direct shortcut activation after a cold start.
- Keeps selection-read errors in the original translation position instead of moving them to a screen corner.
- Keeps the current source-window context separate from an older pinned panel.

## [1.1.9] - 2026-10-03

### Selected-text translation

- Adds the selected-text translation workflow using the `Alt+1` shortcut by default.
- Adds copy, read aloud, pin, settings, and close actions to the floating result panel.
- Uses a separate translation service settings page and returns to the active result after closing it.

## [1.0.34] - 2026-09-30

### Capture reliability

- Adds an automatic capture fallback for display-driver reset and monitor sleep/wake cases.

## [1.0.33] - 2026-09-30

### Capture backend

- Uses the Windows Desktop Duplication capture path when available and falls back automatically when necessary.

## [1.0.30] - 2026-09-28

### Long Capture

- Warms up alignment components while the capture area is selected.
- Checks scrolling viewport changes more frequently for faster continuous scrolling.
- Warns when a scroll jump does not leave enough overlap for a reliable stitch.

## [1.0.19] - 2026-09-21

### Pinned screenshots

- Keeps the pinned window, image, and frame synchronized through repeated zooming.
- Retains the draggable pinned reference workflow.

## [1.0.11] - 2026-09-20

### Product rename

- Renamed the product from SnipNow to Mouse4 across the public product materials.
- Retired the old `SNIPNOW-` license prefix; current keys begin with `MOUSE4-`.
