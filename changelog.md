# Mouse4 Changelog

Newer versions are listed first. This is the public release history; private licensing and service credentials are not included.

## [1.1.22] - 2026-10-04

### Translation panel polish

- Centers the copy action on the final translated line across all supported reading sizes.
- Keeps wrapping, panel width, and action placement stable as translated text changes length.
- Refreshes the public product page, demo video, release notes, and launch copy.

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
