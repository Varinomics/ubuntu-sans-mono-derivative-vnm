# Ubuntu Sans Mono derivative vnm

**Upright Regular prototype build project, version 0.1.2.**

This project implements Bront's final targeted character designs on a static
instance of Canonical's Ubuntu Sans Mono v1.100. The installed family name is
exactly **Ubuntu Sans Mono derivative vnm**. Lowercase `vnm` is intentional.

## U+23CE correction in this revision

`⏎` **U+23CE RETURN SYMBOL** now has its own hollow bent-arrow outline. It is
not an alias for `↵` U+21B5 or `⎆` U+2386; both existing symbols are unchanged.
The new glyph is single-cell and is included in normal builds and
`proof-symbols.png`. `--no-keyboard` disables it with the other keyboard extras.
Any pre-existing upstream U+23CE mapping is preserved, not overwritten.

The **36-test suite** includes tests of the actual procedural U+23CE drawing and the added ordinary directional arrows:
opposite contour winding, open interior, save/reload, direct FreeType rendering,
and preservation of existing mappings. The complete host fonts in these tests
are synthetic. The new glyph alone is previewed in
[`docs/return-symbol-preview.png`](docs/return-symbol-preview.png), using explicit
representative metrics rather than claiming a complete Ubuntu/Bront build.
Regenerate that standalone preview after installing requirements with
`python proof_return.py`. This command needs no upstream font downloads.

## Verification status - read before using

The implementation and complete driver were exercised with generated synthetic
fonts, including variable-font instancing, save/reload validation and PNG proof
generation. The synthetic test suite passes.

**The complete real Ubuntu/Bront inputs could not be downloaded into the
implementation environment. A real-font build, visual comparison and
Windows/Qt rendering acceptance have NOT been completed.** In particular, an
assertion or a geometric matching assumption may still need adjustment when
first applied to the actual pinned inputs. This is a working prototype builder,
not a claim of a production-ready or visually approved font.

This archive contains code and documentation, not font files. On your computer,
the builder downloads its pinned inputs, checks their identities, builds the
candidate, validates the saved font, and optionally renders comparison sheets.
It never installs or replaces system fonts and does not modify its cached inputs.

## Build

Python **3.10 or newer** is required. On Windows, install Python with the `py`
launcher or make `python` available on PATH. Extract the complete archive first.
The first build needs access to PyPI and raw.githubusercontent.com.

From PowerShell or Command Prompt in the extracted directory:

```powershell
.\build.cmd
```

On Linux or macOS:

```sh
sh build.sh
```

The wrappers create `.venv`, install the pinned dependencies, and run the builder
with `--proof`. A Linux installation may need its distribution's Python venv
package installed. No FontForge installation is required.

Manual invocation, using your preferred Python environment:

```sh
python -m pip install -r requirements.txt
python vnm_font.py --proof
python -m unittest discover -s tests -v
```

The build defaults to `--weight auto`: it measures the legacy font's H stems,
scales that reference to the new character-cell width, and finds a native
variable-font weight with a matching stem thickness. This is a geometric
heuristic, not visual certification. For a comparison with Canonical's documented
approximate legacy-weight starting point:

```powershell
.\build.cmd --weight 473 --output build-473
```

or:

```sh
sh build.sh --weight 473 --output build-473
```

The source weight is recorded in `build-report.json`. The output is labeled as
this derivative family's Regular style with weight class 400, even when its
source instance used a different weight value. This keeps source interpolation
coordinates separate from the named derivative style.

## Local output

A successful default build writes the following into `build/`:

| File | Purpose |
|---|---|
| `UbuntuSansMonoDerivativeVnm-Regular.ttf` | Candidate static upright Regular font. |
| `build-report.json` | Source identities, chosen weight, transforms, changes, warnings and structural validation. |
| `proof-characters.png` | Bront/upstream/derivative comparison of targeted characters and accents. |
| `proof-reading.png` | Three-font source-code comparison. |
| `proof-symbols.png` | Derivative keyboard symbols, terminal graphics, Braille and accent samples. |
| `proof-report.json` | Proof renderer and shaping information. |
| `reference-upstream-instance.ttf` | Unmodified upstream instance used in comparisons; **do not install it**. |
| `Ubuntu-Font-Licence.txt`, `NOTICE.txt` | Licence and attribution accompanying local output. |

The candidate is not copied to its final filename unless structural validation
passes. A later proof-rendering error can leave the successfully validated font
and its report in place; the command will still report failure. An older output
from an earlier run is not deleted when a new run fails. Check the command's exit
status and report, not merely the presence of a file in `build/`.

## Implemented scope

The 13 ASCII targets are `$ 0 * _ - = ~ % G j l J t`. The final Bront outlines are
transferred with explicit scale/alignment adaptation, rather than approximated
from screenshots. `i` is intentionally untouched. All unrelated modern outlines,
existing glyph IDs, existing advances and line metrics are required to survive.
No programming ligatures are added; upstream substitution features are retained.

The port propagates composite references and attempts exact base-contour
replacement in canonically decomposable accented forms. It adjusts detached top
marks and relevant mark-to-base anchors where the ascender grows. Related forms
that cannot safely be reconstructed are retained and reported as warnings.
**Read those warnings:** accent consistency is not guaranteed by a PASS result.
Alternate zeros such as oldstyle figures also remain upstream designs and are
reported separately.

Missing `⌫` U+232B, `⌦` U+2326, `↵` U+21B5, `⇥` U+21E5, `⇤` U+21E4, `↹` U+21B9,
`⇧` U+21E7, `⇩` U+21E9, `⇪` U+21EA, `⎆` U+2386, `⏎` U+23CE, and ordinary arrows
`←` U+2190, `↑` U+2191, `→` U+2192, `↓` U+2193 receive original procedural outlines. Seven missing Bront Powerline private-use symbols are added.
Existing mappings are never replaced for these extras. Disable these additions
with `--no-keyboard` and/or `--no-powerline` when testing the core port alone.

## Important limits

This is a **post-build TrueType outline overlay**, not a patch to Canonical's UFO
master files. The recipe is reproducible and pinned, but the current implementation
does not produce an interpolating variable family. Bold and italic have not been
ported. A request for either style may lead an application to synthesize it.

Bront's donor hint programs are not imported into the unrelated target font.
Instructions on changed outlines and dependent composites are removed; surviving
upstream instructions are retained elsewhere. **No fresh production TrueType
hinting is provided.** Small-size rendering needs particular attention.

The renderer uses direct FreeType/Pillow font loading, not system font fallback.
Its proof images do not establish behavior in DirectWrite, CoreText, Qt or your
terminal. Powerline seams depend on actual cell geometry and need separate tests.
Some GPOS positioning relationships outside the handled mark-to-base adjustments
also require shaping review. See `docs/VALIDATION.md`.

## Offline use and upstream updates

After all four inputs are cached, invoke the installed environment directly:

```sh
python vnm_font.py --offline --proof
```

In a wrapper-created environment, use `.venv\Scripts\python.exe` on Windows or
`.venv/bin/python` on Linux/macOS in place of `python`. See `SOURCES.md` for the
exact cache names, paths and Git blob hashes. Incorrect or partial files are
rejected rather than silently used. Offline mode does not install dependencies.

Future upstream versions require a deliberate revision/hash update followed by
real-font tests. This project does not silently follow `main` or a moving release.

## Attribution and licences

Canonical supplies Ubuntu Sans Mono. Chris Wendt supplies the Bront design
changes. The derivative does not imply their endorsement. Builder/test code is
MIT-licensed under `LICENSE-CODE.txt`; external font inputs and font output remain
subject to the Ubuntu Font Licence and their original notices.

Design rationale and upstream evidence: `docs/DESIGN.md` and `SOURCES.md`.
