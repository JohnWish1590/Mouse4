# Mouse4

**Capture what matters. Translate what you need. Keep moving.**

Mouse4 is a lightweight Windows utility for clean region capture, long-page screenshots, selected-text translation, local saving, desktop pinning, and one-click AI handoff. It keeps useful information close without opening a heavy editor.

## Latest release

Mouse4 **1.4.15** is the current Windows build. Chromium long captures use smaller scroll steps to preserve overlap when the selection is short. At the bottom of a scrollable page, continued wheel input extends the capture frame and image in small steps. Setup keeps the per-user install mode and, only when necessary, requests UAC permission to stop the elevated Chrome native host without closing Chrome.

<p align="center">
  <img src="https://img.shields.io/badge/version-1.4.15-2ea44f.svg" alt="Version 1.4.15">
  <img src="https://img.shields.io/badge/platform-Windows-blue.svg" alt="Platform Windows">
  <img src="https://img.shields.io/badge/Python-3.12-orange.svg" alt="Python 3.12">
</p>

## Download

- [Download the latest published Mouse4 release](https://github.com/JohnWish1590/Mouse4/releases/latest)
- [Read the release notes](RELEASE_NOTE.md)
- [Visit the product page](https://johnwish1590.github.io/Mouse4/)
- [Watch the English product demo](https://johnwish1590.github.io/Mouse4/marketing/Mouse4-demo-English.mp4)

The installer includes a 14-day trial. A lifetime license costs **$4.99** as a one-time payment. No subscription and no account are required.

## What it does

- Capture a screen region with a global hotkey.
- Copy each capture to the clipboard and save a timestamped PNG locally.
- Capture long, scrollable pages and stitch them into one complete image.
- Annotate captures with rectangles, arrows, text, drawing, and mosaic redaction.
- Pin a finished capture above the desktop, then drag, zoom, copy, save, or close it.
- Support multiple monitors and mixed display scaling with physical-pixel capture.
- Send a finished screenshot to the Mouse4 for ChatGPT extension with one click.
- Select text on a webpage and choose **Send to AI** (or **鍙戦€佸埌AI** in Chinese Chrome) to send the text without making a screenshot.
- Double-click empty space in File Explorer to return to the previous folder.
- Run quietly from the Windows system tray.

## 1.4.4 reliability update

- **Long screenshots:** a short initial selection no longer leaves the visible capture frame above the page bottom. When the page reaches the bottom, continue scrolling down to include the remaining content and extend the blue frame to the content viewport edge, before Save. No manual resizing is needed. Entering Long Capture does not resize the frame, and stopping the wheel still cancels buffered scrolling.
- **Initial snapshot:** capture exclusion is registered before the selection mask is shown, avoiding a dark first snapshot from the overlay itself.

## 1.4.13 installer reliability update

- **Upgrades:** Setup tries to stop only `Mouse4-ChatGPT-Bridge.exe`. If it is elevated, Setup requests permission to stop that process without closing Chrome; the rest of Setup remains per-user. If the request is declined or the host remains active, Setup aborts before copying files.

## 1.4.12 withdrawn installer test

- The per-user Setup could not replace bridge files held by an elevated native host. Use 1.4.13 instead.

## 1.4.9 reliability update

- **Chrome long screenshots:** controlled wheel steps use Windows' normal input routing instead of posting to transient Chrome child-window handles. Synthesized input is let through the low-level hook exactly once.
- **Stop behavior:** pending scroll intent is cleared when capture closes. Real Chrome desktop checks cover page-bottom capture and verify the page stays still after scrolling stops.
- Windows Setup: `Mouse4-Setup-1.4.9.exe`.

## 1.4.8 reliability update

- **Long screenshots:** when the page reaches its bottom, the missing tail is appended to the stitched image while the visible selection frame, toolbar, and alignment reference stay in place. This prevents the frame from suddenly stretching toward the taskbar.
- Includes regression coverage for a short selection reaching the page bottom, including a real desktop pixel comparison.
- Windows Setup: `Mouse4-Setup-1.4.8.exe`.

## 1.4.7 reliability update

- **Long screenshots:** stops before exceeding a 30,000 px stitched-image limit, or earlier if available memory is low. Mouse4 automatically saves the already aligned portion at either safety limit.
- **Idle safety:** after 60 seconds without input, Mouse4 saves the captured portion and closes only if saving succeeds. If saving fails, the capture stays open so Finish can retry.
- **Clipboard safety:** selected-text translation aborts before copying if the current clipboard formats cannot all be preserved.
- Windows Setup: `Mouse4-Setup-1.4.7.exe`.

## 1.4.6 reliability update

- **Long screenshots:** appends only new aligned strips, then renders once at finish; memory headroom is checked before scrolling. If headroom is low, the session pauses and keeps the captured portion available for manual finish/save. Long Capture does not auto-close while idle.
- **Queue and clipboard:** malformed screenshot tasks no longer block later items, unchanged records are not reparsed on every poll, and selected-text translation will not overwrite clipboard content it cannot preserve.
- **Diagnostics and browser handoff:** text annotations use their actual font bounds, settings-save failures are logged, and the Chrome bridge allows safe headroom for the supported 5 MiB image payload.

## 1.4.5 annotation update

- **Text annotations:** press Enter to commit and leave text mode, then drag the text directly to reposition it. Turning off the text tool commits the text and returns to the pointer state as well.

## 1.4.3 reliability update

- **Long screenshots:** clicking Long Capture keeps the original selection and toolbar position. On finish at a confirmed scroll bottom, missing rows below the selection are appended from the actual content viewport after checking the overlapping pixels. Unsupported or changed pages keep the existing capture.

## 1.4.1 reliability update

- **Long screenshots:** refreshes the controlled scroll target from the latest wheel position, accepts the same webpage's scrollbar just outside the selected pixels, retries a stalled viewport once while the wheel is active, and stops without draining stale input after the wheel becomes idle.

## 1.4.0 feature and reliability updates

- **Browser text handoff:** adds a selection-only browser context-menu action, localized to the Chrome UI language. Selected text is placed in the same daily ChatGPT queue as screenshots; Ctrl+C is not monitored and no system-wide context-menu registration is added.
- **Shared delivery safeguards:** browser text uses the existing Chat-only routing, blank-chat Instant preference, draft protection, queue isolation, receipt verification, and newest-first history.

## 1.3.x feature and reliability updates

- **ChatGPT reasoning:** on a truly blank new ChatGPT chat, the extension attempts to select `Instant` before uploading. If the live page does not expose a confirmable `Instant` option, it preserves the current setting and continues rather than pausing the queue. Existing daily chats are not changed.

- **Capture:** region capture, native-pixel long-page stitching, mixed-monitor scaling support, local PNG saving, annotation, clipboard copy, pinning, and desktop file-drop integration.
- **Long screenshots:** waits for the page to stop moving before alignment, handles fast-scroll transient frames, keeps the original PNG dimensions and lossless saving path, and discards buffered wheel intent when the user stops scrolling.
- **Translation:** selected-text translation in a compact floating panel with frosted treatment, four transparency levels, three remembered font sizes, read-aloud, copy, pin/unpin, close-on-switch behavior, consistent hover help, and trigger-position recovery when Chrome's first UIA bounds query is empty.
- **AI handoff:** the toolbar gives immediate feedback, routes screenshots to an ordinary Chat conversation rather than Work, preserves user drafts, avoids duplicate sends after an uncertain browser response, and keeps the extension bilingual while the product name remains English.
- **Chat history:** sends are shown newest first, daily conversations are named with the current date, and successful screenshot receipts are retained when a later naming step needs repair.
- **Recovery:** sleep/resume handling, first-capture warmup, queue recovery, channel-loss receipt checks, and fast-scroll regression coverage were added without silently resending a screenshot.

The detailed version-by-version record, including known limitations and resolved bugs, is in [CHANGELOG.md](CHANGELOG.md).

## 1.3.0 queue recovery

- Isolates a failed screenshot in manual review instead of pausing later screenshots.
- Never automatically resends an uncertain delivery; the history provides a conversation link and a clear action.
- Keeps system-level Chrome or extension failures separately pausable and exposes a clear Resume sending action.
- Limits bulk cleanup to sent records so manual-review evidence is not removed accidentally.

## 1.3.1 long screenshot wheel pacing

- Keeps the existing controlled scroll and viewport-stability checks needed for reliable stitching.
- Detects a short idle gap after the last real wheel event and clears queued scroll intent instead of continuing to scroll in the background.
- Finishing a long capture saves the current viewport and never drains stale wheel input.

## Selected-text translation

Select text in a supported Windows application and press `Alt+1` (or your configured shortcut). Mouse4 places the result in a light floating panel near the selection so the source page stays visible.

The panel includes:

- copy, read aloud, pin, translation settings, and close actions;
- large, standard, and small text sizes;
- four readable transparency levels with a frosted panel treatment;
- compact hover help and remembered display preferences;
- error messages that stay at the original translation position;
- automatic foreign-language to Simplified Chinese and Chinese to English modes.

The default service is Alibaba Cloud Model Studio `qwen-mt-flash`. The provider, service URL, model, and API key can be entered manually in the translation-only settings page. Keys are stored locally using Windows user encryption and are never included in this repository or installer source.

Unpinned translation panels close when you switch away from the source application or perform another ordinary desktop action. Pinned panels remain available and can be dragged.

## AI handoff

The capture toolbar includes an `AI` action for sending a finished screenshot to the Mouse4 for ChatGPT Chrome extension. Clicking it immediately shows `Sent to AI` in the toolbar while delivery continues through the extension. In Chrome, select webpage text and choose **Send to AI** to use the same daily conversation and queue. The extension keeps its interface bilingual with the product name in English.

The public repository does not include application source, private licensing infrastructure, or API credentials.

## Installation

Download the Windows Setup installer and run it. Mouse4 installs for the current Windows user and does not require administrator rights. The installer includes the optional Mouse4 for ChatGPT Chrome extension files and English installation instructions.

## License delivery

After a Stripe or PayPal payment is confirmed, the license key is sent manually to the email address used at checkout. One license key can activate up to three computers. The old `SNIPNOW-` license prefix is retired; current keys begin with `MOUSE4-`.

## Support

For support, email [johnwish1590@hotmail.com](mailto:johnwish1590@hotmail.com).

## Repository policy

This repository is for the public product page, release notes, marketing assets, and downloadable installers. Mouse4 is commercial closed-source software; application source code and private licensing services are not included.

