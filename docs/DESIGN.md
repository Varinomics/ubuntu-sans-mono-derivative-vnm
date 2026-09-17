# Design and implementation decisions

## Objective

Preserve the readability choices of final Ubuntu Mono - Bront while retaining
Ubuntu Sans Mono v1.100's modern character repertoire. This first implementation
is a static upright Regular proof candidate. It is not a new all-style family.

## Targeted designs

| Character | Final Bront decision |
|---|---|
| `0` | Slashed, rather than dotted, zero. |
| `$` | Continuous central vertical stroke. |
| `*` | Six spokes and placement in the arithmetic-operator band. |
| `_` | Shorter drawn width, allowing adjacent underscores to remain distinct. |
| `-` | Same drawn width as the underscore. |
| `=` | Vertical alignment with the hyphen. |
| `~` | A more pronounced wave. |
| `%` | Circular counters, with adjusted stroke thickness. |
| `G` | A horizontal bar. |
| `j`, `l`, `J` | Removal of serifs; longer tail on `J`. |
| `t` | Ascender raised to the height of `l`. |

Lowercase `i` is not a target: Bront's author reverted its experiment before the
final font snapshot. The port therefore keeps the **modern upstream** `i`, rather
than copying a legacy `i`. This distinction is intentional.

Evidence:
- Bront's pinned README: https://github.com/chrismwendt/bront/blob/aef23d9a11416655a8351230edb3c2377061c077/README.md
- Equal-sign alignment: https://github.com/chrismwendt/bront/commit/96af984b2ac9b08d79f2b1ca5bc969c1c7d59d6e
- Reversion of `i`: https://github.com/chrismwendt/bront/commit/e54624cfc134dc7aa6e78ec28a02e3e6984b33e2

## What the implementation actually does

This is a procedural overlay on an instantiated TrueType font. It does **not**
redraw these characters in Canonical's UFO masters. It obtains Bront's final
outlines, fully decomposes any donor components, transforms the shapes, and puts
them into the corresponding modern glyph slots without reordering old glyph IDs.

The horizontal transformation uses the modern/legacy H advance-width ratio. The
vertical transformation uses the modern/legacy H outline-height ratio. The
baseline follows H's outline bottom. Thus horizontal and vertical scale may be
different. This adaptation retains the donor designs' proportions relative to
cell width and cap height; it is not proof of a perfect optical match.

With automatic weight selection, H's two stems are measured at 80% of its cap
height. A binary search finds an upstream weight with a stem width matching the
horizontally scaled legacy reference. This does not independently match horizontal
strokes or curves, so visual comparison is still needed. Explicit `--weight 473`
is also supported: Canonical documents it as an approximate original-weight
starting point, not an exact recreation.

Canonical reference: https://github.com/canonical/Ubuntu-Sans-Mono-fonts/blob/c57353c1772eb8aaab9c539e3d42c971a03a5fcd/README.md

The imported `*`, `-` and `=` are shifted as one group onto the existing `+` band.
The underscore preserves its upstream vertical center below the baseline, while
using Bront's width/shape. This avoids moving the rest of the family's operators
or underline metrics merely to match old font coordinates.

## Related glyphs and shaping

Composite glyphs that reference modified bases naturally receive the new bases.
Their instruction programs are cleared because point numbering may have changed.
Point-attached composites in the initial dependency set are rejected rather than
used with potentially invalid donor point references.

For Unicode characters with a canonical decomposition beginning with G, j, l, J
or t, the builder also examines simple, already-flattened outlines. It replaces
only base contours that are exactly translated versions of the old base. It
allows a different contour start point, but not reversed direction, fuzzy
similarity or an unrelated redraw. A failed match retains the upstream form and
records a warning for manual review.

A detached top accent can move upwards with a raised t ascender. Below-body and
side accents are not indiscriminately translated. Corresponding mark-to-base top
anchors are adjusted; Format 2 point anchors in those handled base records are
converted to coordinate anchors because imported points have different numbers.

These rules deliberately have limits. Nested transformed composites, noncanonical
letter variants and other positioning lookup types have not had full real-font
shaping acceptance. Alternate zero designs, including oldstyle numerals, remain
upstream and are explicitly reported. This prototype must not be described as a
complete stylistic-alternate or all-language redesign.

## Coverage additions

The builder requires complete upstream box drawing (128 mappings), block elements
(32) and Braille (256) in its full-font output. It preserves every pre-existing
best-Unicode-cmap mapping, not only these blocks.

Fifteen missing keyboard/arrow symbols receive original procedural single-cell outlines:
U+232B, U+2326, U+21B5, U+21E5, U+21E4, U+21B9, U+21E7, U+21E9, U+21EA, U+2386, U+23CE,
U+2190, U+2191, U+2192 and U+2193. Seven missing Powerline symbols are taken from
Bront: U+E0A0-E0A2 and U+E0B0-E0B3. Native existing glyphs at these positions are
not overwritten. These additions can be disabled independently.

Powerline symbols use the text's body scale in this prototype. Their junctions
with colored terminal cells need a separate visual pass at actual line spacing.
No Nerd Fonts icon set or programming-ligature set is added.

## Rendering and future work

Modified glyphs have no new TrueType hinting. Existing upstream instructions are
kept only where the associated outlines remain safe to retain. This can affect
small-size rendering and is a substantial acceptance item, not cosmetic cleanup.

A production family would need real-font visual approval, any warning-specific
accent repairs, a hinting decision, and independently designed bold/italic
variants. An interpolating variable family should ultimately express the design
changes in compatible source masters. This first binary-outline overlay is a
bounded prototype and reference implementation for that work, not a claim that
those later stages are already finished.

## U+23CE hollow Return symbol and ordinary arrows

Unicode names U+23CE RETURN SYMBOL and permits a hollow or filled drawing:
https://www.unicode.org/charts/nameslist/n_2300.html#23CE
This derivative deliberately uses the hollow form requested by the user.
U+2386 ENTER SYMBOL and U+21B5 are not substitutes or aliases for this mapping.

The new drawing has a clockwise outer bent-arrow contour and a
counter-clockwise inner contour. The latter is a continuous hole through the
arrowhead, horizontal arm, elbow and vertical arm, with a closed rim at the top.
Both sloping arrowhead edges are offset by the same perpendicular wall thickness
as the straight edges. No enclosing keycap rectangle is drawn. Its advance is
the existing H advance, as for the other added keyboard symbols. Existing line
metrics and glyph IDs are preserved. Added glyphs receive no TrueType hinting.

This revision adds ordinary arrows U+2190/U+2191/U+2192/U+2193 as separate filled single-cell symbols. The existing white-arrow keyboard symbols remain distinct.
The small source-version increment is 0.1.2; the output font revision is 1.103.
