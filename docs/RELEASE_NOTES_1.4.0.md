## Mouse4 v1.4.0

Mouse4 v1.4.0 adds a second lightweight path into the daily ChatGPT workflow: select text on a webpage and send it to AI without taking another screenshot.

### Browser text handoff

- Select text on any webpage in Chrome and choose **Send to AI** from the context menu.
- Chinese Chrome displays **发送到AI**.
- The selected text joins the same daily ChatGPT conversation and queue used by screenshot handoff.
- Chat mode is checked before sending; the workflow does not route new work into ChatGPT Work.
- Unrelated drafts are protected, and selected text is treated as analysis material rather than as Mouse4 control instructions.
- Mouse4 does not monitor `Ctrl+C`, read the clipboard, or register a Windows system-wide context menu.

### Reliability updates included in the release

- Individual failed screenshots remain in manual review instead of stopping later screenshots.
- Uncertain browser delivery is not silently resent.
- The queue keeps receipt verification, daily conversation naming, newest-first history, and blank-chat `Instant` selection.
- The Chrome extension remains bilingual while the product name stays in English.

### Distribution

- Windows installer: `Mouse4-Setup-1.4.0.exe`
- Chrome extension: `1.2.0`
- Trial: 14 days
- Lifetime license: $4.99 one-time payment

The existing English demo video and page animation are unchanged in this release. The public repository contains the product page, public marketing material, and release assets; it does not contain application source code, private licensing infrastructure, or API credentials.
