# Mouse4 v1.4.7 Release Notes

Mouse4 1.4.7 makes long screenshots safer on very large pages and preserves captured work when a safety limit is reached.

- **Long Capture limits:** stops before the stitched image exceeds 30,000 px, or earlier if available memory is low.
- **Save before stopping:** saves the aligned portion already captured at a safety limit. If saving fails, the capture remains open so you can retry Finish.
- **Idle safety:** after 60 seconds without input, saves the captured portion and closes Long Capture only after a successful save.
- **Clipboard protection:** selected-text translation does not overwrite clipboard formats it cannot preserve; it stops before copying and leaves the original clipboard intact.

The release includes the Windows installer `Mouse4-Setup-1.4.7.exe`. Mouse4 remains closed-source; this public repository contains product materials and release downloads, not the application source code.
