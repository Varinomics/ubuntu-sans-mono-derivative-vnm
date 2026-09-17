# Validation status - 17 September 2026

## Completed here

The Python implementation was imported and compiled with fontTools 4.63.0 and
Pillow 12.3.0. The **32-test unittest suite** passed using **generated synthetic host fonts**.
See `validation-status.json` and `test-results.txt` for the recorded result.

The suite checks the 13-target set; stem measurement; variation-weight selection;
actual fontTools instancing of synthetic variable masters; output save/reload;
original glyph-ID and advance-width preservation; unchanged lowercase i outline
and instructions; composite and flattened accent handling; top-mark movement;
conversion of handled point-based mark anchors; symbol geometry; preservation of
existing keyboard glyphs; disabling extras; derivative names across platforms;
deterministic output; rejection of corrupt/missing cache inputs; and detection of
coverage and unrelated-outline regressions. The complete driver and all three
PNG proof outputs also run with synthetic inputs.

**Synthetic fixtures exercise mechanisms, not the actual target designs.** The
synthetic source weight, glyph counts and whole-font proof images are not
measurements or previews of a complete Ubuntu Sans Mono derivative vnm font.
No whole-font proof based on synthetic alphabet shapes is included.

The included `return-symbol-preview.png` is explicitly a **glyph-only proof**:
it renders the actual U+23CE procedural implementation at width 560, cap height
700 and stem 65 in a 1000-unit em, in a temporary in-memory host font. The PNG
was inspected at enlarged and native 16/20/24/32/48 pixel sizes on light and dark
backgrounds. It does not establish Windows/Qt or actual Ubuntu font rendering.

Ten U+23CE regression tests were added. They cover its distinct mapping, complete
keyboard set, two oppositely wound contours, transparent head/arms/elbow,
positive rim ink, metrics at four representative width/height/stem combinations,
invalid metrics, preservation of an upstream U+23CE, `--no-keyboard`, rejection
of a missing mapping, save/reload, direct FreeType raster checks, single-cell
advances and inclusion in the main proof sheet. BASIC layout grid-fits advances;
the small-size tests compare against H rather than assuming fractional advances.

## Not completed here

The real complete font inputs could not be retrieved into the implementation
environment. Therefore all of the following remain **NOT RUN**:

- Build against the actual pinned Ubuntu Sans Mono and Bront font binaries.
- Real-font selection of an optical/source weight.
- Visual comparison of the three actual fonts, at normal reading sizes.
- Inspection and resolution of actual-font accent/alternate warnings.
- DirectWrite, CoreText, Qt and terminal-cell rendering acceptance.
- Fresh production hinting, comprehensive shaping QA and font-sanitizer testing.
- Genuine bold, italic and variable-family implementations.

A passing synthetic suite must not be treated as evidence that those steps pass.

## Checks performed on every local candidate

After constructing a real candidate on your computer, the driver saves and
reloads the candidate and baseline. It checks:

1. No upstream best-Unicode-cmap entries were lost or remapped.
2. All pre-existing glyph IDs and advance widths remain stable.
3. Outlines outside the explicitly modified/dependent set remain unchanged.
4. Lowercase i remains unchanged; the requested derivative family name is set.
5. The output is static, without fvar/gvar variation tables.
6. Box drawing, block elements and Braille retain their full expected coverage.
7. Enabled keyboard/Powerline extras exist and are not empty.
8. Native GSUB compilation and the checked line-metric fields remain unchanged.

These are **structural assertions**. `Validation: PASS` does not mean the font is
visually approved, fully shaped correctly, or production-hinted. In particular,
GSUB equality does not prove equality of GPOS behavior. The procedure changes
some GPOS mark-to-base anchors intentionally, and other relationships still need
real-font review. Cmap coverage also does not prove every upstream mapping has
an appropriate or visually legible outline.

The recipe is guarded: a source identity mismatch or failed assertion ends the
build rather than publishing that candidate. Do not suppress these errors just
to get an output font. Diagnose the actual source assumption instead.

## First actual-font acceptance pass

Run the wrapper with its default settings and keep its console output and
`build-report.json`. A network-capable machine with Python is sufficient; nothing
is installed into the system fonts automatically.

Open `proof-characters.png`, `proof-reading.png` and `proof-symbols.png`. Compare
the default auto-weight result against a separate `--weight 473 --output build-473`
build rather than assuming either is optically final. Pay particular attention
to the imported shapes' stroke weight, the distinguishing `0/O` and `i/l/1`
sequences, adjacent underscores, and the vertical arithmetic-operator band.

Check accents on G, l and t, both precomposed and typed as a base plus combining
mark. Resolve every warning in the actual report individually. The builder is
permitted to preserve an unsafe-to-reconstruct related upstream design with a
warning, so accepting warnings is a design decision, not a silent success.

Pillow's RAQM support is recorded in `proof-report.json`. Without RAQM, the image
is not a useful test of OpenType combining-mark positioning. Even with RAQM,
platform-specific font rendering and small-size hinting remain untested.

Then test only the candidate (not `reference-upstream-instance.ttf`) in the
intended application. Compare normal DPI and the actual UI scale settings;
check 12-24 pixel text, selection/caret placement, line clipping, box joins,
fractional blocks, Braille, keyboard keys and Powerline transitions. Test real
cell placement: proof-sheet text layout alone cannot establish terminal seams.

This project contains only Regular. The application may synthesize bold or
italic; that is not a completed VNM bold or italic design.
