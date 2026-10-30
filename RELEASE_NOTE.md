# Mouse4 Release Notes

## 1.4.15 - More reliable fast scrolling

- Chromium capture scrolls in smaller controlled steps, making it less likely that a short selection skips the overlap needed for stitching. Other applications retain the existing wheel behavior.
- Recovery waits for wheel input before moving the page. If the last frame cannot be aligned, the confirmed portion can be saved and is not automatically sent to AI.
- Tested against fast scrolling and page-bottom cases in a real Chrome test page; dynamic pages may behave differently.
- Windows Setup: `Mouse4-Setup-1.4.15.exe`.

## 1.4.14 - Controlled page-bottom capture

- Additional downward wheel input at the confirmed page bottom extends the selection and captured image together, one small step at a time.
- Stopping or finishing does not automatically append the rest of the viewport.
- On Windows, an administrator-elevated Chrome cannot expose its scrolling area to non-elevated Mouse4. Use a normally launched Chrome window for this feature.

## 1.4.13 - Upgrade while Chrome remains open

- Setup remains a per-user installation. It first tries to stop only `Mouse4-ChatGPT-Bridge.exe`; if Windows blocks that because the host is elevated, it requests UAC permission just for that process.
- Chrome stays open. If permission is declined or the bridge remains active, Setup stops before copying files.
- Windows Setup: `Mouse4-Setup-1.4.13.exe`.

## 1.4.12 - Withdrawn local installer test

- The installer could not replace bridge files held by an elevated Chrome native host. Use 1.4.13 instead.

## 1.4.11 - Withdrawn local installer test

- This test build stopped the native host only before replacing its EXE, after bridge runtime DLLs were already copied. It could fail when Chrome relaunched the host during setup; use 1.4.12 instead.

## 1.4.10 - Fix upgrades with the Chrome bridge running

- Setup now closes `Mouse4-ChatGPT-Bridge.exe` before replacing installed files, preventing Windows error 5 when the native messaging host is still running.
- Windows Setup: `Mouse4-Setup-1.4.10.exe`.

## 1.4.9 - Reliable Chrome long-capture scrolling

- Routes controlled wheel steps through Windows' normal input path so Chrome receives them without relying on transient child-window handles.
- Lets synthesized wheel events pass through Mouse4's hook once, and clears buffered scroll intent when capture closes.
- Real Chrome desktop regression checks passed for scrolling, page-bottom capture, pixel-accurate stitching, and stopping after wheel input ends.
- Windows Setup: `Mouse4-Setup-1.4.9.exe`.

## 1.4.8 - Keep the long-capture selection frame stable

- Appends the final verified page tail to the long screenshot without stretching or moving the visible selection frame toward the taskbar.
- Keeps the toolbar and scroll-alignment reference tied to the original selection throughout bottom capture.
- Regression-tested short and full-height selections with real desktop pixel comparisons.
- Windows Setup: `Mouse4-Setup-1.4.8.exe`.

## 1.4.7 - Safe long-capture limits

- Stops long scrolling before the stitched image exceeds 30,000 px, or earlier if the current memory budget is insufficient.
- Saves the already captured, aligned portion automatically when a safety limit is reached.
- After 60 seconds without input, saves and closes Long Capture. If saving fails, it remains open with a Finish retry available.
- Selected-text translation refuses to overwrite clipboard formats it cannot preserve.
- Regression-tested height limits, idle finishing, save retry, and unsupported clipboard formats.
- Windows Setup: `Mouse4-Setup-1.4.7.exe`.

## 1.4.6 - Safer, faster long screenshots

- Long screenshots now append aligned strips without redrawing all earlier pixels after every scroll.
- Available-memory checks pause scrolling before the process risks exhausting memory; captured content stays available for manual finish/save.
- Long Capture remains open until you finish or cancel it, even when you pause to read for more than 60 seconds.
- A malformed queue record no longer blocks later screenshots, and unchanged records are not reparsed on every status poll.
- Selected-text translation stops before altering the clipboard when its existing formats cannot be preserved.
- Text annotation redraw bounds now follow the actual font metrics, and settings-save errors are logged for diagnosis.
- Chrome extension version: `1.2.1`. Windows Setup: `Mouse4-Setup-1.4.6.exe`.

## 1.4.5 - Move text annotations after typing

- Press Enter to finish text entry and return to the normal pointer state.
- Drag a committed text annotation to place it where you want on the capture canvas.
- Turning off the text tool also commits the text and leaves it movable.
- Windows Setup: `Mouse4-Setup-1.4.5.exe`.

## 1.4.4 - Wheel through the final content from a short selection

- At the actual page bottom, continuing to wheel down includes the remaining content below the original selection and extends the blue frame before Save.
- Keeps the selected top and width; no manual dragging is required.
- Does not resize the selection merely because Long Capture was clicked.
- Verifies the tail before appending and prevents duplicate rows on subsequent bottom wheels.
- Preserves stop-on-idle behavior and the on-finish tail fallback.
- Registers the selection overlay's capture exclusion before its first visible frame to avoid a dark initial snapshot.
- Windows Setup: `Mouse4-Setup-1.4.4.exe`.

## 1.4.3 - Stable long-capture selection and final page tail

- Clicking Long Capture preserves the selected region, including when no wheel input follows.
- Finishing at a confirmed page bottom adds missing rows below the selection using the actual content viewport, not the monitor bottom.
- The tail is verified against the last captured pixels before it is appended. If accessibility is unavailable or the page changes, the existing capture is kept.
- Handles first-use Chrome accessibility initialization before checking the page bottom.
- Windows Setup: `Mouse4-Setup-1.4.3.exe`.

## 1.4.2 - Include the last visible page content in long captures

- Long captures keep the selected top and width, and automatically extend the bottom edge to the current monitor work-area bottom.
- The final visible page content is included when the webpage scrollbar reaches the bottom.
- Controlled scrolling, alignment checks, and stop-when-idle behavior are unchanged.
- Windows Setup: `Mouse4-Setup-1.4.2.exe`.

## 1.4.1 - Keep long captures moving to the actual page bottom

- Refreshes the controlled scroll target from the latest wheel position before each step.
- Recognizes the same webpage's scrollbar even when it sits just outside the selected capture rectangle.
- Does not treat an unchanged viewport as successful progress; retries once only while the real wheel is still active.
- Stops immediately after the wheel becomes idle and discards stale buffered scroll intent.
- Windows Setup: `Mouse4-Setup-1.4.1.exe`.

## 1.4.0 - Send selected browser text

- Select text on any webpage and choose **Send to AI** from the browser context menu; Chinese Chrome shows **鍙戦€佸埌AI**.
- Sends the selected text directly to the same daily ChatGPT conversation used for screenshots.
- Uses the existing Chat-only routing, blank-chat Instant preference, draft protection, queue recovery, and receipt verification.
- Does not monitor `Ctrl+C`, read the clipboard, or add a Windows system-wide context-menu item.
- Chrome extension version: `1.2.0`. Windows Setup: `Mouse4-Setup-1.4.0.exe`.

## 1.3.2 - Prefer Instant for blank ChatGPT chats

- Detects the visible ChatGPT model/reasoning control before a screenshot is uploaded to a genuinely blank chat.
- Selects `Instant` when the current page exposes and confirms that option, even if the previous chat used a higher or lower effort.
- Leaves existing daily conversations unchanged.
- If `Instant` is unavailable or cannot be confirmed, keeps the current page setting and continues sending.
- Chrome extension version: `1.1.1`. Windows Setup: `Mouse4-Setup-1.3.2.exe`.

## 1.3.1 - Stop long capture when the wheel stops

- Keeps one controlled scroll step followed by viewport-stability sampling so long-page stitching remains reliable.
- Clears buffered wheel intent after a short idle gap instead of continuing to scroll after the user stops.
- Finishing a long capture no longer drains stale scroll input.
- Windows Setup: `Mouse4-Setup-1.3.1.exe`.

## 1.3.0 - Per-screenshot ChatGPT queue recovery

- A failed screenshot moves to manual review instead of pausing later screenshots.
- An uncertain delivery is never resent automatically and keeps its conversation link for inspection.
- Chrome or extension-wide failures remain separately pausable with a visible **Resume sending** action.
- The extension history adds **Manual review**, per-task **Clear record**, and sent-only bulk cleanup.
- Chrome extension version: `1.1.0`. Windows Setup: `Mouse4-Setup-1.3.0.exe`.

## 1.2.13 - Keep first translations beside the selection

- Uses the shortcut trigger position when Chrome UIA returns selected text before selection rectangles.
- Prevents a maximized browser window from sending the first translation to the desktop's lower-left corner.
- Keeps clipboard fallback placement unchanged.
- Windows Setup: `Mouse4-Setup-1.2.13.exe`.
- Full `unittest` suite: 171 tests passed; 5 opt-in native desktop checks were skipped.

## 1.2.12 - Restore daily date naming

- Locates the current conversation after opening a collapsed sidebar.
- Ignores same-page skip links and unrelated open menus.
- Keeps screenshot sending and Chat mode selection unchanged.
- Includes extension 1.0.8. Windows Setup: `Mouse4-Setup-1.2.12.exe`.
- Verified the live title `2026-10-12` and cleared naming warnings without resending. 51 Node and 6 Python regression tests passed.

## 1.2.11 - Chat-first sending

- Waits for the actual editor before classifying an existing daily conversation as Chat or Work.
- Selects Chat before upload and switches back automatically if the mode changes before submission.
- Checks the current text and submit button after switching, without silently submitting an unrelated draft.
- Includes extension 1.0.7. Windows Setup: `Mouse4-Setup-1.2.11.exe`.
- Explicitly cleared daily entries start fresh rather than recovering an old same-date Work conversation.
- 49 Node regression tests and 6 Python queue-recovery tests passed. Live clean-start delivery confirmed the screenshot, message ID, ordinary Chat composer, server URL, and expected answer.

## 1.2.10 - Chat routing based on the actual page

- Recognizes separately wrapped Chat/Work controls and prioritizes the actual rich-text editor over the textarea mirror.
- Uses an ordinary Chat target for new screenshots instead of reusing a legacy Work thread or temporary local URL.
- Clears only recognized failed Mouse4 drafts; never requeues failed screenshots.
- Verifies a receipt after message-channel interruption without repeating the send click.
- Includes extension 1.0.6. Reload the extension after installing `Mouse4-Setup-1.2.10.exe`.
- 45 Node and 6 Python recovery tests passed. Live Work-to-Chat switching was observed; complete screenshot submission remains pending verification.

## 1.2.9 - Recover the paused screenshot queue

- Repairs the exact old pre-submit Chat guard error at connection startup in both the extension and local bridge.
- Lets new queued screenshots proceed without requeuing the old unsent screenshot. Other failed and uncertain deliveries retain review protection.
- Includes extension 1.0.5. Reload Mouse4 for ChatGPT in `chrome://extensions/` after installing `Mouse4-Setup-1.2.9.exe`.
- Regression tests cover the Chrome connection entry point and a real local-host subprocess. Live ChatGPT submission remains unverified.

## 1.2.8 - Chat switching and newest-first history

- Actively selects Chat when mode controls are available and reads the editor's persistent accessible name after instructions are inserted.
- Reports confirmed pre-submit failures as unsent instead of uncertain delivery; repairs the exact old Chat guard failure without resending it.
- Displays newest send records first while preserving send-queue order.
- Includes extension 1.0.4. Reload Mouse4 for ChatGPT in `chrome://extensions/` after installation.
- Windows Setup: `Mouse4-Setup-1.2.8.exe`
- Regression checks cover switching, filled editors, receipt classification, and history order. Live end-to-end submission remains unverified.

## 1.2.7 - Chat-only screenshot sending

- Mouse4 checks and selects Chat before uploading each screenshot instead of inheriting Work from the previous browser session.
- Rechecks the mode immediately before submitting. If Chat cannot be confirmed, sending pauses for manual review.
- Preserves drafts and the existing daily conversation/receipt workflow.
- Includes Mouse4 for ChatGPT extension 1.0.3. Reload the extension in `chrome://extensions` after installing this update.
- Windows Setup: `Mouse4-Setup-1.2.7.exe`
- Automated mode-switch regression coverage is included; signed-in live-page verification remains pending.

## 1.2.6 - Scrolling screenshot stability

- Waits for the viewport to stop moving before stitching scrolling screenshots, instead of relying only on a fixed delay.
- Pauses further wheel steps while checking stability and preserves pending completion/recovery requests.
- Retains strict matching and bounded recovery; does not silently save a known misaligned result.
- Preserves native image dimensions and lossless PNG saving. Translation behavior is unchanged.
- Windows Setup: `Mouse4-Setup-1.2.6.exe`
- Regression tests cover fast scrolling and transient frames. Reproduction on the original live webpage remains to be verified.

## 1.2.5 - Translation position diagnostics

- Adds local control/rectangle diagnostics to distinguish empty bounds, query errors, and changing accessibility geometry on the first translation.
- Repeated samples are read-only, stay on the owning COM thread, and never replace the original positioning result.
- No selected text, control names, or API credentials are included in these new diagnostics.
- Existing positioning and retry rules are unchanged. Install, cold-start Mouse4, then translate the same Chrome selection twice and note the times.
- Windows Setup: `Mouse4-Setup-1.2.5.exe`

## 1.2.4 - Sleep/resume recovery

- Prevents restart helpers from restoring stale settings and process identifiers when they exit.
- Confirms the previous instance has exited before replacement. A timed-out shutdown is enforced only for a verified executable and process creation time.
- Confirms GUI and native shortcut readiness after recovery instead of checking process survival alone.
- Records local thread stacks in `hang-traces.log` and logs shutdown stages to investigate the original hang. These diagnostics are not uploaded automatically.
- Windows Setup: `Mouse4-Setup-1.2.4.exe`
- Actual Modern Standby sleep/resume validation remains pending; this update addresses the confirmed recovery defects, not a proven root cause of the original native hang.

## 1.2.3 - Daily ChatGPT naming fix

- Opens conversation options with pointer events and confirms that the menu has expanded before looking for Rename.
- Reports menu-opening failures separately from a missing Rename action.
- Includes Mouse4 for ChatGPT extension 1.0.2, with updated sender injection so existing tabs can load the corrected listener.
- Keeps confirmed screenshot deliveries and their conversation links when naming fails; naming retries do not resend screenshots.
- Windows Setup: `Mouse4-Setup-1.2.3.exe`

## 1.2.2 - First-capture responsiveness

Mouse4 1.2.2 reduces the delay before the first screenshot after startup.

### Highlights

- The persistent desktop-capture worker warms up after startup, before the first user request.
- The native overlay and toolbar are primed without activating a window, taking focus, or accepting input.
- Every user screenshot is still a fresh capture. The warmup frame is never reused.
- A capture already waiting in the queue takes priority over the optional warmup job.
- Capture duration is recorded in the log to make performance changes measurable.
- The existing AI handoff, translation panel, long-page capture, pinning, and mixed-DPI workflows remain available.

### Public materials

- The README, changelog, and sales page are written for English-speaking customers.
- The existing English product demo and page animation are unchanged in this release.

### Distribution

- Windows Setup: `Mouse4-Setup-1.2.2.exe`
- Trial: 14 days
- Lifetime license: $4.99 one-time payment
- Source code and private licensing infrastructure are not included in the public release.

