# Changelog

## 0.1.2 - 17 September 2026

- Add ordinary directional arrows U+2190/U+2191/U+2192/U+2193 as native procedural glyphs.
- Keep U+23CE RETURN SYMBOL and the earlier keyboard-symbol additions unchanged.
- Preserve any upstream mappings for the added directional arrows.
- Add four regression tests, bringing the synthetic-host test suite to 36.
- Add the directional arrows to the main symbol proof.
- Bump the output font revision to 1.103 and builder version to 0.1.2.
- Regenerate the package checksums; exclude Python/pytest caches and font files.

## 0.1.1 - 17 September 2026

- Add U+23CE RETURN SYMBOL as a real hollow bent arrow with its own mapping.
- Keep the existing ten keyboard glyphs and the core Bront port unchanged.
- Preserve any upstream U+23CE; support the existing `--no-keyboard` switch.
- Add ten regression tests, bringing the synthetic-host test suite to 32.
- Add U+23CE to the main symbol proof and provide a standalone glyph-only preview.
- Bump the output font revision to 1.102 and builder version to 0.1.1.
- Regenerate the package checksums; exclude Python/pytest caches and font files.

The full pinned Ubuntu/Bront build is still not verified in this environment.
The new glyphs' own geometry and direct FreeType rendering are verified using
synthetic host fonts; Windows/Qt, full-font visual acceptance and production
hinting remain outside this validation.
