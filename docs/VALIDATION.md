# Validation procedure and limits

Build provenance for the distributed Regular font is recorded in
[SOURCES.md](../SOURCES.md#historical-015-font-build). That identifies the actual
font and its inputs; it does not establish visual approval or platform rendering
acceptance for another build.

## Synthetic checks

Run the suite from the project root with the installed dependencies:

```sh
python -m unittest discover -s tests -v
```

The tests exercise the builder with generated host and donor fonts, including
variation instancing, source preservation, added symbols, Braille geometry,
save/reload and proof generation. Consult the tests for their exact cases.

**Synthetic fixtures exercise mechanisms, not the actual target designs.** The
synthetic source weight, glyph counts and whole-font proof images are not
measurements or previews of a complete Ubuntu Sans Mono derivative vnm font.
No whole-font proof based on synthetic alphabet shapes is included.

The included [Return-symbol preview](return-symbol-preview.png) is a
**glyph-only proof**:
it renders the actual U+23CE procedural implementation at width 560, cap height
700 and stem 65 in a 1000-unit em, in a temporary in-memory host font. It was
inspected at enlarged and native 16/20/24/32/48 pixel sizes on light and dark
backgrounds. It does not establish Windows/Qt or actual Ubuntu font rendering.
BASIC layout grid-fits advances; the small-size tests compare against H rather
than assuming fractional advances.

## Checks performed on every local candidate

After constructing a real candidate on your computer, the driver saves and
reloads the candidate and baseline. It checks:

1. No upstream best-Unicode-cmap entries were lost or remapped.
2. All pre-existing glyph IDs remain stable. Advances remain unchanged except
   that blank Braille U+2800 is normalized to the other Braille cells.
3. Outlines outside the explicitly modified/dependent set remain unchanged.
4. Lowercase i remains unchanged; the requested derivative family name is set.
5. The output is static, without fvar/gvar variation tables.
6. Box drawing, block elements and Braille retain their full expected coverage.
7. Enabled keyboard/Powerline extras and the always-included activity symbols
   exist and are not empty. Activity symbols fit their monospace cell.
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

## Actual-font and application acceptance

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
proof images do not establish platform-specific rendering or small-size hinting.

Then test only the candidate (not `reference-upstream-instance.ttf`) in the
intended application. Compare normal DPI and the actual UI scale settings;
check 12-24 pixel text, selection/caret placement, line clipping, box joins,
fractional blocks, Braille, keyboard keys and Powerline transitions. Test real
cell placement: proof-sheet text layout alone cannot establish terminal seams.

Visual comparison, warning-specific accent/alternate review, DirectWrite,
CoreText, Qt and terminal-cell acceptance, comprehensive shaping QA and
font-sanitizer testing require evidence for the candidate being assessed. A
passing synthetic suite or a successful real-font build does not close them.

This project contains only static Regular and supplies no fresh production
hinting. The application may synthesize bold or italic; those are not designed
VNM styles or an interpolating variable family.
