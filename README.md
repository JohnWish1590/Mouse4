# Mouse4

**Capture what matters. Translate what you need. Keep moving.**

Mouse4 is a focused Windows utility for clean region screenshots, long-page capture, selected-text translation, local saving, and desktop pinning. It keeps the useful part of the workflow close without opening a large editor.

Mouse4 **v1.4.7** is the latest Windows release. It adds safety limits for long screenshots, saves captured content before automatically ending an idle or memory-limited capture, and protects the existing clipboard during selected-text translation. See the changelog for the full version history.

## Download

- [Download Mouse4 for Windows](https://github.com/JohnWish1590/Mouse4/releases/download/v1.4.7/Mouse4-Setup-1.4.7.exe)
- [Read the v1.4.7 release notes](https://github.com/JohnWish1590/Mouse4/releases/tag/v1.4.7)
- [Visit the product page](https://johnwish1590.github.io/Mouse4/)
- [Watch the product demo](https://johnwish1590.github.io/Mouse4/#demo)
- [Watch the English demo video](https://johnwish1590.github.io/Mouse4/marketing/Mouse4-demo-English.mp4)

The installer includes a 14-day trial. A lifetime license costs $4.99 as a one-time payment. No subscription and no account are required.

## What it does

- Capture a screen region with a global hotkey.
- Copy each capture to the clipboard and save a timestamped PNG locally.
- Capture long, scrollable pages and stitch them into one complete image.
- Annotate a capture with rectangles, arrows, and other lightweight markup; commit text with Enter, then drag it to reposition.
- Pin a capture above the desktop, drag it, zoom it, and close it when finished.
- Support multiple monitors, including mixed-resolution displays.
- Send a finished screenshot to the Mouse4 for ChatGPT extension with one click.
- Select webpage text and choose **Send to AI** in Chrome (or **发送到AI** in Chinese Chrome) without making a screenshot.
- Double-click empty space in File Explorer to return to the previous folder.
- Run quietly from the Windows system tray.

## Selected-text translation

Select text in a supported Windows application and press `Alt+1` (or your configured shortcut). Mouse4 places the translation in a light floating panel near the selection, so the source page stays visible.

The panel includes:

- copy, read aloud, pin, translation settings, and close actions;
- large, standard, and small text sizes;
- four readable transparency levels with a frosted panel treatment;
- short hover help and remembered display preferences;
- automatic foreign-language to Simplified Chinese and Chinese to English mode;
- error messages that stay at the original translation position.

The default service is Alibaba Cloud Model Studio `qwen-mt-flash`. Enter the provider, service URL, model, and API key in the translation-only settings page. Keys are stored locally using Windows user encryption and are never included in this repository or installer source.

Unpinned translation panels close when you switch away from the source application or perform another ordinary desktop action. Pinned panels remain available and can be dragged.

## AI handoff

Click `AI` after finishing a capture to send it through the Mouse4 for ChatGPT Chrome extension. The app immediately shows `Sent to AI` while delivery continues through the extension. In Chrome, select webpage text and choose **Send to AI** to place the text in the same daily Chat conversation and queue. The extension checks Chat mode before sending, keeps user drafts protected, and does not monitor `Ctrl+C` or read the clipboard.

## Installation

Download the Windows Setup installer and run it. Mouse4 installs for the current Windows user and does not require administrator rights.

To enable the optional Chrome extension, open Mouse4's ChatGPT analysis rules and click **Install Chrome extension**. In Chrome, open `chrome://extensions/`, enable Developer mode, choose **Load unpacked**, and select the `chrome-extension` folder inside the Mouse4 installation folder. Return to Mouse4 and click **Connect Chrome**.

## License delivery

After a Stripe or PayPal payment is confirmed, the license key is sent manually to the email address used at checkout. One license key can activate up to three computers. The old `SNIPNOW-` license prefix is retired; current keys begin with `MOUSE4-`.

## About this repository

This is the public product and release repository for Mouse4. It contains the product page, public marketing assets, release notes, and downloadable installers. Mouse4 is commercial closed-source software; application source code and private licensing infrastructure are not included.

## Support

For support, email [johnwish1590@hotmail.com](mailto:johnwish1590@hotmail.com).
