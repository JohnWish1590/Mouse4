# Mouse4 public product page

This directory is the publishable website for Mouse4. It contains the sales page, public marketing images and demo video, support pages, payment QR images, and release-facing copy.

## Current public build

- [Mouse4 v1.1.22 Windows installer](https://github.com/JohnWish1590/Mouse4/releases/download/v1.1.22/Mouse4-Setup-1.1.22.exe)
- [Release notes](https://github.com/JohnWish1590/Mouse4/releases/tag/v1.1.22)
- [Live product page](https://johnwish1590.github.io/Mouse4/)
- English demo asset: `marketing/Mouse4-demo-English.mp4`

The page presents region capture, long-page stitching, annotation, desktop pinning, selected-text translation, local saving, and the $4.99 one-time license. Translation service credentials are entered by the user in the application and are never stored in this website.

## Publishing

The GitHub Pages site is deployed from the public repository root. Before publishing, copy the page files and public assets from this directory into that root, then check:

1. Every download link points to an existing release asset.
2. The demo video loads and has a poster image.
3. Payment links and QR images still match the displayed price.
4. The page works at desktop and narrow mobile widths.
5. No application source, private licensing code, API key, or local capture is included.
