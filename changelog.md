# Mouse4 Changelog

This document records the main product, implementation, release, website, licensing, and testing changes made during the Mouse4 development process. Newer versions are listed first.

## [1.0.19] - 2026-09-21

### Pinned screenshot alignment fix

- Changed the pinned screenshot thumbtack to an upright, straight-down orientation instead of the previous slanted angle.
- Removed the pinned-image layout manager and position the image label directly so every zoom step updates the window and image to identical dimensions.
- Kept the two-line frame, colours, pin location, and all pin interactions unchanged.
- Rebuilt the Setup installer.

## [1.0.18] - 2026-09-21

### Pinned screenshot presentation

- Added the requested two-line white-and-grey frame directly over the pinned screenshot, without an outer grey panel or shadow.
- Added a small yellow, black-outlined thumbtack with a subtle contact shadow at the pinned image's top-left corner.
- Synchronized the image label size with every zoomed pixmap so shrinking no longer leaves a blank band inside the pinned window.
- Kept dragging, zooming, copying, saving, and closing behavior unchanged.

## [1.0.17] - 2026-09-21

### Annotation toolbar rendering fix

- Fixed the filled action-button stylesheet so undo, pin, confirm, and cancel render their backgrounds and icons correctly instead of appearing invisible until hover.
- Kept the A-plan colours and all existing button actions unchanged.
- Rebuilt the Setup installer.

## [1.0.16] - 2026-09-21

### Annotation toolbar visual refresh

- Kept the annotation behavior unchanged while separating the toolbar into drawing tools, undo, and result actions.
- Added filled action colours: muted red for undo, warm gold for pin, green for confirm/save, and blue-grey for cancel.
- Matched the rectangle and ellipse icon sizes and moved only the cancel glyph upward inside its button.
- Rebuilt the Setup installer with the refreshed interface.

## [1.0.15] - 2026-09-21

### Reliable in-place upgrades

- Improved the installer shutdown path to signal the running Mouse4 process through its existing named exit event before replacing files.
- This handles a Mouse4 process started with higher Windows integrity than the per-user installer, where `taskkill` alone returns access denied.
- Kept the forced process-stop fallback for older or unresponsive builds.
- Rebuilt the Setup installer with the corrected upgrade behavior.

## [1.0.14] - 2026-09-21

### Reliable in-place upgrades

- Fixed Setup upgrades so a running Mouse4 process is closed before the installed executable and Qt DLLs are replaced.
- Added an explicit installation-stage process stop as a fallback for tray-only processes that Windows Restart Manager may not detect.
- Disabled restarting the old process after installation; Setup starts the newly installed version instead.
- Rebuilt the Setup installer with the corrected upgrade behavior.

## [1.0.13] - 2026-09-21

### Annotation arrow color

- Fixed arrow annotations so the line, outline, and arrowhead all use the selected color.
- Removed the inverted-color halo that made one arrow appear to contain multiple unrelated colors.
- Rebuilt the Setup installer with the corrected annotation rendering.

## [1.0.12] - 2026-09-20

### License generator reliability

- Rotated the private Worker administrator token after clearing the development license records.
- The private generator now reads the current user's Windows environment value directly, so it works when launched by double-clicking the EXE instead of requiring a special PowerShell session.
- Rebuilt the Setup installer and private generator with the new version.

## [1.0.11] - 2026-09-20

### Product rename and license reset

- Renamed the customer-facing product from SnipNow to Mouse4 across the application, installer, license generator, website copy, and release documentation.
- Changed the license prefix from `SNIPNOW-` to `MOUSE4-`; old SnipNow keys are intentionally invalid and are not migrated.
- Changed local application storage, mutexes, events, capture filenames, and registry paths to Mouse4-specific identifiers so the renamed app does not collide with the old product.
- Bumped the application and Setup installer version to `1.0.11`.
- The deployed Worker hostname is temporarily retained as an internal service endpoint until the renamed deployment is published; it is not a customer-facing product name.

## [1.0.10] - 2026-09-20

### Annotation text size

- Restored `12` as the smallest selectable annotation size for users who need compact labels.
- Kept the default annotation size at `24` so the normal annotation workflow remains readable.
- Retained the expanded larger sizes through `96`.
- Built the Setup installer successfully: `dist/SnipNow-Setup-1.0.10.exe`.
- Installer SHA-256: `9AB447EFF225B4129DD70C53085473B6DA68939FE7911B61618BCDB617BD4979`.
- Re-ran Python compilation and the full test suite: 22 tests passed.

## [1.0.9] - 2026-09-20

### Annotation text size

- Expanded the text annotation sizes from `12–48` to `16, 20, 24, 32, 40, 48, 64, 80, 96`.
- Changed the default annotation size from `18` to `24` so normal screenshot labels are easier to read.
- Normalized saved legacy or unsupported font sizes to the new default instead of silently keeping an unusably small value.
- Unified the text-entry preview and the final rendered annotation around point-size units so the size shown while typing is consistent with the saved screenshot.
- Bumped the application and Setup installer version to `1.0.9`.
- Built the Setup installer successfully: `dist/SnipNow-Setup-1.0.9.exe`.
- Installer SHA-256: `3F3D7794A595FA82B5BFB5025AE8B80659D281BFB5EE03DE10FAA85B7F22EE8D`.
- Re-ran Python compilation and the full test suite: 22 tests passed.

## [1.0.8] - 2026-09-20

### Performance

- Added a transparent, input-transparent startup warm-up surface to prime overlay rendering before the first user capture.
- Kept the warm-up surface non-focusable and automatically removed it after startup; it does not remain visible as an application window.
- Removed unnecessary image copies from the capture path when creating the pinned screenshot window.
- Reused the image prepared for saving instead of making another deep copy for the last-rendered capture state.
- Used exact-size pixmap drawing where scaling was not required.
- Limited antialiasing to annotation drawing instead of enabling it for every overlay paint operation.
- Kept per-monitor capture and physical-pixel stitching for mixed-resolution multi-monitor layouts.
- Added timing logs for capture, image save, clipboard copy, and overlay display so future performance regressions can be diagnosed from `debug.log`.
- Verified that the optimized PNG path remains lossless by comparing decoded pixel data, not only file bytes.

### Release and packaging

- Bumped the application and installer version to `1.0.8`.
- Kept `version.py` as the application version source of truth.
- Built the Windows Setup installer with PyInstaller and Inno Setup.
- Kept the release output in `dist` and removed the need for historical `build1`, `build2`, and `build3` output folders.
- Current installer: `dist/SnipNow-Setup-1.0.8.exe`.
- Confirmed that only one Setup installer is present in `dist`.
- Installer SHA-256: `3A07439D2D98146A1D4EBF82B53DF385444F39DD6318C8317AA1DC0073629936`.

### Verification

- `python -m py_compile main.pyw version.py navigation.py` passed.
- `python -m unittest discover -s tests -p "test_*.py"` passed: 22 tests.
- `git diff --check` passed apart from normal line-ending warnings.
- Lossless PNG pixel-identity verification passed.
- QPixmap lifetime verification passed after source-buffer deletion and memory pressure.
- Static import review found no unused-import candidates in the key application, licensing, internationalization, and navigation modules.
- Multi-monitor, settings-window capture, About-window capture, Escape cancellation, clipboard copy, and local PNG saving were exercised during release checks.
- The current build was checked against the runtime version shown by the application logging/version path.

### Known measurement notes

- First-capture latency is dominated by Windows desktop composition and the size of the virtual desktop. On the test machine, full multi-monitor first capture was approximately 0.5 seconds, while the selected-image save operation was approximately 10–11 ms and clipboard copy was approximately 32–56 ms.
- These timings are hardware- and desktop-dependent and are not a guaranteed limit for every customer's computer.
- HDR was not tested.

### Engineering experiment later reverted

- An additional off-screen opaque pre-warm experiment was tested under a temporary source version `1.0.9`.
- It did not improve first-capture latency consistently and was reverted.
- This performance experiment was reverted before the annotation-size change recorded in the released `1.0.9` version.

## [1.0.7] - 2026-09-19

### Performance and rendering

- Improved the overlay paint path for exact 1:1 rendering.
- Delayed antialiasing until annotation drawing so normal capture display work uses a lighter rendering path.
- Continued reducing redundant image conversions and copies in capture and pin-to-desktop handling.
- Fixed the source of the version text used in runtime logs so it follows the application version instead of a stale hardcoded value.

### Stability

- Continued stabilizing screenshots started while Settings or About was open.
- Preserved safe Escape cancellation and overlay cleanup after capture attempts.
- Rebuilt and installed the Setup package for the versioned release workflow.

## [1.0.6] - 2026-09-19

### First performance pass

- Removed an unconditional startup delay that was no longer appropriate for the onedir Setup application.
- Reduced unnecessary image copies in the capture-to-save and capture-to-pinned-window path.
- Added the first capture warm-up and timing instrumentation.
- Optimized PNG saving while retaining lossless decoded image data.
- Added automatic-save and clipboard timing records to the debug log.
- Started the structured performance review requested for first-capture lag, application size, and unused code.

### Release workflow

- Established the versioned Setup release process.
- Kept the installer as a Setup package rather than a portable single executable.
- Began keeping one current installer in `dist` instead of accumulating numbered build folders.

## [1.0.5] - Baseline release iteration

- Served as the previous installed/tested baseline before the performance-focused 1.0.6–1.0.8 work.
- Included the core screenshot workflow, licensing UI, settings, About dialog, multi-monitor support, and the initial public sales-page integration.
- Subsequent releases preserved the existing user-facing feature set while improving rendering, startup behavior, diagnostics, and release consistency.

## Project history before 1.0.5

### Core screenshot workflow

- Added the global `Ctrl+1` capture hotkey.
- Added region selection across the virtual desktop.
- Added confirm/cancel behavior and capture toolbar actions for annotations.
- Added automatic clipboard copy.
- Added timestamped local PNG saving.
- Added the ability to pin a captured screenshot above other windows so it can remain visible while the user works.
- Added multi-monitor capture, including mixed monitor resolutions and virtual-desktop coordinates.
- Added quiet system-tray operation and settings access.
- Added the File Explorer empty-space double-click action that returns to the previous folder. This was treated as a Plus feature and added to both feature checks and sales copy.

### Settings and About dialog fixes

- Made Settings and About non-modal/modeless where necessary so the global screenshot workflow remains usable while those windows are open.
- Fixed the regression where starting a capture from Settings or About could leave the screen dark, block input, or fail to show the selection overlay.
- Stabilized the capture toolbar so confirm, cancel, annotation, and Escape actions continue to work across repeated captures.
- Added the application icon to Settings and About.
- Synchronized the About version display with the current application version.
- Added screenshot-folder selection behavior and retained access to folders that already contain captured images.
- Added license-state display so an activated installation shows its activated status rather than presenting registration as if it were still incomplete.
- Addressed the unsupported `QMimeData.hasPixmap` diagnostic crash by using supported clipboard checks.

### Licensing and activation

- Moved the licensing direction away from Paddle.
- Designed and implemented the Cloudflare Worker + D1 licensing direction.
- Added the local license generator application.
- Added signed license-key handling and device activation tracking.
- Enforced the product rule that one license can activate up to three computers.
- Added duplicate-registration and concurrency-oriented tests for the license flow.
- Kept private signing material and Worker secrets out of public documentation and client-facing files.
- Added licensing UI and activation status to the application settings.

### Payment and fulfillment decision

- Prepared Stripe and PayPal payment links/QR codes for the sales page.
- Kept the initial fulfillment process intentionally manual: the owner confirms that the payment has arrived, generates or registers the license using the local generator, and sends the license key to the customer's email.
- Discussed, but deliberately deferred, a fully automatic Stripe/PayPal webhook → Cloudflare Worker → email-license-delivery workflow.
- Payment notifications may be delivered by the payment provider, but a payment notification alone does not automatically deliver a license in the current release.

### Internationalization direction

- Kept the current product interface in English for the initial Western-market release.
- Separated interface text from program logic so future Simplified Chinese, Traditional Chinese, Japanese, and other language packs can be added without rewriting core behavior.

### Website and sales page

- Reviewed the original GitHub Pages sales page and redesigned the presentation around a small, focused Windows utility.
- Reworked the copy around the product's main value: capture a region, pin it to the desktop, and keep working with minimal clutter.
- Added clearer trial and purchase calls to action, including the 14-day trial, Windows Setup wording, no-subscription messaging, and the `$4.99` one-time price.
- Added the product icon and product screenshots to the sales presentation.
- Added the three main screenshot features:
  1. Capture instantly
  2. Pin to desktop
  3. Save and copy automatically
- Added the separate Plus feature: double-click empty space in File Explorer to go back.
- Final feature layout direction: three screenshot-feature cards plus a full-width, visually distinct Plus row, responsive for desktop and mobile.
- Kept Stripe and PayPal QR codes visible in the payment section, along with checkout links.
- Removed the duplicate lower download section from the revised page concept and kept the direct trial download action near the top of the page.
- Positioned the current release/version and release-notes information near the download action.
- Published and iterated the GitHub Pages sales-page design during the project. Updating the page's direct download target to each newly released installer remains part of the normal release checklist.

### Review and quality process

- Performed read-only architecture and code reviews with the requested Astra/Luna review workflow and double-checks.
- Reviewed critical, high, medium, and low risk findings across screenshot behavior, licensing, installer packaging, website claims, and localization structure.
- Added or expanded tests for licensing, activation, concurrency, navigation, and key application behavior.
- Investigated first-capture lag, unused code, package size, multi-monitor behavior, Settings/About capture, and clipboard/save reliability.
- Confirmed that the application is intended to be distributed as an installer and not as an uninstalled portable executable.

## Deferred or not included in the current release

- Automatic Stripe/PayPal fulfillment and automatic license email delivery are not enabled; payment-to-license fulfillment remains manual.
- HDR-specific capture validation has not been completed.
- Windows code signing has not been added. The installer may therefore show `Unknown publisher` on systems that do not otherwise trust the package.
- A custom independent sales domain is not required for the current GitHub Pages approach and has not been added.
- Full end-to-end payment testing with a real customer transaction and production fulfillment should be performed before public sales.

## Release checklist for the next public upload

- Increment the application/installer version according to the project's semantic versioning practice.
- Build the Setup installer and confirm the output is in `dist`.
- Confirm that `dist` contains only the intended current installer.
- Run the Python compile check and the complete test suite.
- Exercise one normal capture, repeated captures, Settings/About capture, clipboard copy, local save, pin-to-desktop, Escape cancellation, and multi-monitor capture.
- Update the sales page's direct download link to the new GitHub release asset.
- Publish the GitHub release notes and verify that the download link works in a clean Windows environment.
- Confirm the manual payment notification and license-delivery procedure before accepting customer orders.
