# Mouse4 Changelog

Newer versions are listed first. This public history excludes private licensing details, service credentials, and application source code.

## [1.4.15] - 2026-10-30

### Improve fast scrolling with short selections

- Chromium windows use smaller controlled scroll steps, helping consecutive frames retain overlap when the selection is short; other application windows keep the previous wheel step.
- Alignment recovery does not move the page after wheel input stops. If alignment cannot be confirmed, the already verified portion can be saved without automatically sending an incomplete image to AI.
- Real Chrome test pages were checked for fast wheel input, pixel continuity and the page-bottom scenarios. This does not guarantee alignment on every dynamic page.
- Windows Setup: `Mouse4-Setup-1.4.15.exe`.

## [1.4.14] - 2026-10-30

### Fix long-capture bottom selection

- At a confirmed page bottom, each additional downward wheel step extends the visible frame and captured image together, instead of appending the entire remaining viewport at once.
- Finishing a capture no longer silently adds uncaptured bottom content. Stopping the wheel leaves the captured range unchanged.
- Chrome started with administrator privileges cannot be inspected by a non-elevated Mouse4 process; run Chrome normally for long-capture bottom detection.

## [1.4.13] - 2026-10-30

### Fix upgrades when the Chrome bridge runs elevated

- Keeps the installer in per-user mode and first tries to stop only `Mouse4-ChatGPT-Bridge.exe` without elevation.
- If that bridge is still running with elevated privileges, Setup requests UAC only to stop the bridge; Chrome stays open.
- If permission is declined or the bridge cannot be stopped, Setup aborts before copying files instead of offering to skip locked files.
- Windows Setup: `Mouse4-Setup-1.4.13.exe`.

## [1.4.12] - 2026-10-30

### Withdrawn installer test build

- The per-file stop hook could not terminate an elevated Chrome native host from the per-user installer, so Windows still refused to replace locked bridge files. Use 1.4.13 instead.

## [1.4.11] - 2026-10-30

### Withdrawn installer test build

- This local test build stopped the native host only before replacing its EXE, after the bridge runtime DLLs had already been copied. It could fail when Chrome relaunched the host during setup; use 1.4.12 instead.

## [1.4.10] - 2026-10-30

### Fix upgrades when the Chrome bridge is still running

- The installer now closes `Mouse4-ChatGPT-Bridge.exe` before replacing installed files, preventing Windows error 5 when Chrome still holds the native messaging host open.
- Windows Setup: `Mouse4-Setup-1.4.10.exe`.

## [1.4.9] - 2026-10-30

### Restore reliable Chrome long-capture scrolling

- Replays each controlled wheel step through Windows' normal input routing instead of posting to transient Chrome child-window handles.
- Passes synthesized wheel events through Mouse4's low-level hook so they reach the foreground page once without being recaptured.
- Clears pending scroll intent when a long-capture window closes.
- Regression-tested the real Chrome desktop flow: scrolling, bottom capture, pixel-accurate stitching, and no continued scrolling after input stops.
- Windows Setup: `Mouse4-Setup-1.4.9.exe`.

## [1.4.8] - 2026-10-22

### Keep the selection frame fixed when appending the final page tail

- When the page reaches its bottom, append the verified remaining content to the stitched image without changing the visible selection frame or its alignment reference.
- Prevents the sudden jump/stretch toward the taskbar that could occur when a short selection reached the page bottom.
- Adds regression coverage for unchanged frame geometry and a real desktop pixel comparison across bottom-scroll scenarios.
- Windows Setup: `Mouse4-Setup-1.4.8.exe`.

## [1.4.7] - 2026-10-21

### Safe long-capture limits and idle finish

- Stops before another wheel step would push the stitched image past 30,000 pixels; also stops earlier when the available-memory guard says finishing would be unsafe.
- Automatically saves the already aligned portion at either safety limit. If disk saving fails, the capture remains open and Finish can retry instead of discarding the image.
- After 60 seconds without input, Long Capture stops, saves the captured portion, and closes only after a successful save.
- Selected-text translation still aborts before sending Ctrl+C if any native clipboard format cannot be preserved; the existing clipboard remains untouched.
- Adds regression coverage for both height-limit paths, idle finishing, save retry, and unsupported native clipboard formats.
- Windows Setup: `Mouse4-Setup-1.4.7.exe`.

## [1.4.6] - 2026-10-21

### Long-capture, queue, and clipboard reliability

- Appends each aligned scroll strip once and renders the completed long screenshot once, avoiding repeated full-image copies as the page grows.
- Checks available Windows memory before accepting another long-capture step. If memory headroom is low, scrolling pauses while the already captured portion remains available to finish and save.
- Long Capture no longer closes itself after 60 seconds without input; the user ends or cancels the session manually.
- Skips an unreadable or malformed queue record without terminating the Chrome sender, and avoids reparsing unchanged queue files on every monitor poll.
- Protects the existing clipboard during selected-text translation: if all clipboard formats cannot be preserved, translation stops before copying over them.
- Uses the rendered font metrics for text annotation redraw bounds, logs ordinary settings-save failures, and leaves extra headroom for the maximum supported screenshot payload in the Chrome bridge.
- Bumps the Chrome extension to 1.2.1.

## [1.4.5] - 2026-10-20

### Move text annotations after typing

- Pressing Enter commits the text and returns to the normal pointer state.
- Drag a committed text annotation directly to reposition it within the capture canvas.
- Turning off the text tool also commits the current text and keeps it editable by dragging.
- Shows a move cursor when the pointer is over a committed text annotation.

## [1.4.4] - 2026-10-16

### Reach the page bottom with the wheel, even from a short selection

- After the page reaches its actual scroll limit, another downward wheel input captures the missing content below the original selection and extends the visible blue frame to the content viewport bottom before Save.
- Preserves the selected top and width. No dragging or manual frame adjustment is needed.
- Clicking Long Capture without scrolling still leaves the original frame unchanged; no automatic jump to the screen bottom is introduced.
- Verifies the overlapping pixels before appending the tail and updates the alignment reference, preventing repeated bottom wheels from duplicating content.
- Keeps idle-wheel cancellation and the verified on-finish tail fallback.
- Sets capture exclusion before the selection overlay is first shown, preventing the overlay mask from entering an initial DXGI snapshot.

## [1.4.3] - 2026-10-16

### Preserve the selected region and capture the final page tail

- Fixes the 1.4.2 regression that expanded the selection to the screen bottom as soon as Long Capture was clicked, even without wheel input.
- Keeps the selection and toolbar in place throughout scrolling.
- On finish, checks the actual scroll container through Windows accessibility on the capture worker. At a confirmed bottom, captures the missing rows below the selection up to the content viewport edge.
- Appends the tail only when its overlapping pixels match the last captured viewport; unsupported or changed pages retain the existing capture.
- Handles Chrome's first accessibility query with a bounded background wait for the scroll pattern to become available.
- Keeps controlled scrolling and idle-input cancellation.

## [1.4.2] - 2026-10-15

### Include the last visible page content in long captures

- Extends a long-capture selection down to the current monitor work-area bottom while keeping the user's selected top and width.
- Prevents the page from reaching the scrollbar bottom while the final visible content remains below the fixed capture rectangle.
- Keeps the existing controlled scrolling, viewport-stability checks, and idle-wheel behavior unchanged.
- Adds regression coverage for bottom anchoring and cross-monitor selections.

## [1.4.1] - 2026-10-15

### Keep long captures moving to the actual page bottom

- Refreshes the scroll target from the latest real wheel position before each controlled step, so a stale child window cannot silently stop the page.
- Allows a scrollbar just outside the selected pixels to continue the same capture when it belongs to the already identified source window.
- Treats a settled frame with no viewport movement as a stalled scroll instead of accepting it as progress; retries once only while real wheel input is still active.
- Keeps the idle rule: once the wheel stops, buffered intent is discarded and the capture does not continue scrolling in the background.
- Adds regression coverage for the no-motion retry, idle cancellation, and native wheel target routing.

## [1.4.0] - 2026-10-15

### Send selected browser text to the daily ChatGPT chat

- Adds a Chrome selection-only context-menu action: **Send to AI** in English Chrome and **鍙戦€佸埌AI** in Chinese Chrome.
- Sends the selected webpage text directly through the existing daily ChatGPT queue without creating a screenshot or reading the clipboard.
- Reuses Chat-only routing, blank-chat `Instant` selection, draft protection, receipt checks, manual-review isolation, and newest-first history.
- Treats selected text as delimited analysis material so instructions inside the webpage selection are not treated as Mouse4 commands.
- Keeps the existing screenshot path unchanged and does not add a system-wide Windows context-menu entry or a global `Ctrl+C` listener.
- Includes Mouse4 for ChatGPT Chrome extension `1.2.0`.

## Current 1.3.x鈥?.4.0 scope

The current line covers the complete workflow: region and long-page capture, native-dimension lossless PNG output, annotation and clipboard actions, mixed-monitor scaling, selected-text translation, frosted translation controls, and one-click AI handoff. Reliability work covers first-capture startup, sleep/resume, fast scrolling, Chat/Work mode selection, browser-channel loss, duplicate-send protection, newest-first history, automatic daily conversation naming, and per-screenshot queue recovery.

The entries below record the implementation and the bug each iteration addressed. A successful screenshot receipt is never treated as unsent merely because a later naming or browser-channel step needs repair.

## [1.3.2] - 2026-10-15

### Start blank ChatGPT chats in Instant mode when available

- Checks the model and reasoning control before a screenshot is uploaded to a genuinely blank ChatGPT chat.
- Selects `Instant` when the visible ChatGPT control exposes that option, regardless of the previous chat's reasoning level.
- Leaves existing daily conversations unchanged so their current model and reasoning settings are not overwritten.
- If the current ChatGPT layout does not expose or confirm `Instant`, keeps the existing setting and continues sending instead of blocking the queue.
- Includes Mouse4 for ChatGPT Chrome extension `1.1.1`.

## [1.3.1] - 2026-10-15

### Stop long capture when the wheel stops

- Keeps the controlled one-step scroll and viewport-stability sampling that protects stitched-image alignment.
- Detects a short idle gap after the last real wheel event and clears buffered scroll intent.
- Saves the current viewport when finishing instead of draining stale wheel input.

## [1.3.0] - 2026-10-15

### Keep individual screenshot failures from stopping the queue

- A failed screenshot is retained for manual review and does not pause later screenshots.
- A delivery whose result cannot be confirmed is never automatically resent; the history exposes the conversation for inspection.
- Only system-level Chrome or extension failures pause the queue, with a separate **Resume sending** action.
- The manual-review filter, per-task clear action, and sent-only bulk cleanup prevent accidental removal of diagnostic evidence.
- Includes Mouse4 for ChatGPT extension `1.1.0`.

## Chrome extension [1.1.0] - 2026-10-15

- Adds per-task manual-review actions and keeps later screenshots moving after an individual failure.
- Separates system-level queue pauses from failed or uncertain screenshot records.
- Keeps bulk cleanup limited to sent records.

## Chrome extension [1.0.9] - 2026-10-15

- Moves **Resume queue** to the top connection panel, before **Reconnect**, so it stays easy to find above long histories.
- Keeps queue behavior unchanged: resume processes pending tasks and does not resend failed or uncertain screenshots.

## [1.2.13] - 2026-10-13

### Keep first translations beside the selected text

- Uses the shortcut trigger position when Chrome UIA returns the selected text before it exposes selection rectangles.
- Prevents the source browser's full-window bounds from placing the first translation at the desktop's lower-left corner.
- Keeps the existing source-window placement for the clipboard fallback, where no native selection geometry is available.
- Adds a regression test for the reproduced first-translation placement failure.

## [1.2.12] - 2026-10-12

### Restore daily conversation naming

- Opens a collapsed sidebar before locating the current conversation's rename action.
- Excludes same-page skip links from conversation lookup.
- Checks the selected conversation menu's expanded state instead of treating an unrelated open menu as success.
- Keeps Chat routing and screenshot submission unchanged. Includes extension 1.0.8.

## [1.2.11] - 2026-10-12

### Chat-first screenshot delivery

- Waits for the daily conversation's editor to load before deciding whether a legacy thread is Work.
- Selects Chat before uploading, and checks again immediately before submission. A late change to Work triggers a switch back to Chat rather than an immediate failure.
- Rechecks the current editor and send button after switching; unrelated drafts and uncertain receipts remain protected.
- Distinguishes a ChatGPT page-load failure from a missing sign-in.
- Starts a cleared daily entry fresh instead of recovering the old same-date Work conversation.
- Includes Mouse4 for ChatGPT extension 1.0.7.

## [1.2.10] - 2026-10-12

### Live-page Chat routing and editor fixes

- Recognizes Chat and Work buttons inside separate wrappers, matching the current website structure.
- Uses the rich-text composer instead of the stale textarea mirror for mode and draft checks and prompt insertion.
- Routes new screenshots away from legacy Work threads and temporary local conversation mappings into an ordinary Chat conversation.
- Resets only a draft matching a failed Mouse4 prompt before starting a new Chat. Unrelated user drafts remain protected.
- Checks for a server receipt once after a response-channel loss without repeating submission. Temporary local URLs are not accepted as confirmed receipts.

## [1.2.9] - 2026-10-12

### Native queue recovery

- Repairs the exact legacy pre-submit mode error during Chrome connection, before paused-queue checks can skip recovery.
- Applies the same verified-unsent correction to the local screenshot queue, allowing new queued screenshots to proceed without resending the old failed screenshot.
- Keeps other failed tasks and genuinely uncertain delivery paused for review.

## [1.2.8] - 2026-10-12

### Chat switching and send history

- Uses the editor's persistent accessible name as well as selected controls, so Chat confirmation survives inserting instructions.
- Actively selects Chat when a visible switch exists but only stale placeholder evidence claims Chat, then waits for rendering.
- Distinguishes errors before the submit click from unknown delivery after submission. Repairs the exact pre-submit mode-guard error from 1.2.7 without resending it or unblocking other uncertain messages.
- Shows newest send-history entries first without changing queue order.
- Includes Mouse4 for ChatGPT extension 1.0.4.

## [1.2.7] - 2026-10-12

### Send screenshots in Chat mode

- Checks Chat/Work before each screenshot upload, switches to Chat when available, and reacquires the editor after switching.
- Checks Chat again immediately before submission. Unknown modes or unsuccessful switching stop the job instead of sending into Work.
- Preserves user drafts, existing daily conversation links, and duplicate-delivery safeguards.
- Includes extension 1.0.3 and refreshes previously injected sender listeners.

## [1.2.6] - 2026-10-11

### Scrolling screenshot stability

- Samples the viewport until two consecutive comparisons confirm that scrolling has stopped before attempting alignment.
- Keeps queued wheel steps paused during sampling; transient rendering no longer immediately consumes alignment retries or starts reverse recovery.
- Bounds each stability wait to 1.5 seconds and retains the existing strict alignment and recovery limits.
- Waits for pending samples before saving. PNG dimensions and lossless saving remain unchanged.
- Adds regression coverage for transient rendering, continuing motion, timeouts, rapid wheel input, and pending completion.

## [1.2.5] - 2026-10-11

### Translation position diagnostics

- Records selected-control identity, cursor/focus origin, visibility, initial rectangle values, and safe exception codes without logging selected text.
- Takes two immediate read-only samples of the first incomplete text range on its owning COM thread. Samples are diagnostic only and do not replace the original anchor.
- Keeps existing translation retry counts, positioning, fallback, and error behavior unchanged. This diagnostic release does not claim to fix first-translation positioning.

## [1.2.4] - 2026-10-09

### Sleep/resume recovery

- Prevents helper processes and rejected instances from overwriting live settings with stale instance information on exit.
- Verifies the old process executable and creation time before enforcing a timed-out shutdown from the independent restart helper.
- Waits for confirmed process exit before replacement, and checks GUI/native shortcut readiness instead of treating a surviving process as a successful recovery.
- Adds local thread-stack diagnostics and shutdown-stage logging. The original native hang remains under investigation; real sleep/resume validation is still required.

## [1.2.3] - 2026-10-07

### Daily chat naming

- Opens ChatGPT conversation menus with pointer events and verifies that the menu opens before looking for Rename.
- Distinguishes a menu that did not open from a missing Rename action.
- Updates the extension to 1.0.2 and replaces previously injected sender listeners when the updated script is loaded.
- Preserves successful screenshot receipts and retries naming without resending screenshots.

## [1.2.2] - 2026-10-06

### First-capture responsiveness

- Warms the persistent capture worker after startup so the first user screenshot does not pay the full DXGI/MSS initialization cost.
- Primes the native overlay and toolbar without activating them, taking focus, or accepting mouse input.
- Keeps shortcut readiness independent of warmup and skips queued warmup when a user capture is already waiting.
- Captures a fresh desktop frame for every user request; the warmup frame is never reused as a screenshot.
- Records desktop capture duration in milliseconds for performance diagnostics.

## [1.2.1] - 2026-10-06

### Multi-monitor toolbar and feedback

- Adapts capture toolbar controls to each monitor's DPI and reduces button spacing on high-scale displays.
- Uses compact yellow feedback with readable 22px semibold text for capture and AI actions.
- Shows `Sent to AI` immediately when the AI action is clicked, without waiting for delivery confirmation.

## [1.2.0] - 2026-10-06

### AI handoff

- Replaces the screenshot toolbar's paper-plane action with a compact `AI` mark.
- Keeps the existing Mouse4 for ChatGPT bridge and bilingual Chrome extension workflow.
- Preserves the one-shot graphite toast behavior and capture-location placement.

## [1.1.24] - 2026-10-06

### ChatGPT bridge and public materials

- Matches capture completion feedback to the graphite UI with white text and a brief fade-out.
- Uses a single `Sent to ChatGPT` delivery message.
- Recovers daily chat links from successful receipts and existing ChatGPT history before creating a new chat.
- Keeps chat naming warnings separate from screenshot delivery.
- Adds Chinese and English Chrome extension UI with English fallback and the fixed name `Mouse4 for ChatGPT`.
- Makes Chrome extension installation instructions in the installer English-only.

## [1.1.22] - 2026-10-04

### Translation panel polish

- Centers the copy action on the final translated line across all supported reading sizes.
- Keeps wrapping, panel width, and action placement stable as translated text changes length.
- Refreshes the public product page, English demo, release notes, and launch copy.

## [1.1.21] - 2026-10-04

### Pinned references

- Fixes a crash while drawing the pin control on a captured reference.
- Keeps pinned screenshots fully visible, draggable, zoomable, and above other windows.

## [1.1.20] - 2026-10-04

### Reading controls

- Adds large, standard, and small translation text sizes with remembered preferences.
- Adds four readable frosted transparency levels.
- Adds concise hover help for the translation panel controls.

## [1.1.19] - 2026-10-03

### Translation panel behavior

- Unpinned translation panels close on an outside click, scroll, or source-application switch.
- Pinned panels stay available and can be moved independently of the next translation.
- The translation-only service page returns to the active result after saving or closing.

## [1.1.18] - 2026-10-03

### Translation display

- Adds the light frosted translation panel and four readable transparency levels.
- Keeps translated text and controls clear while the source application remains visible.

## [1.1.17] - 2026-10-03

### Reliability

- Improves first-use selection handling, cancellation, streaming response handling, and clipboard fallback behavior.
- Preserves the original panel position when a translation request reports an error.
- Adds diagnostics for selection, foreground-window, and panel lifecycle issues.

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

- Adds selected-text translation with the `Alt+1` shortcut by default.
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

