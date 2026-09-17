# Pinned external inputs

The project does not contain font data. The builder uses these four original inputs.

Upstream release: **Ubuntu Sans Mono v1.100**, tag commit `c57353c1772eb8aaab9c539e3d42c971a03a5fcd`.

Release evidence: https://github.com/canonical/Ubuntu-Sans-Mono-fonts/releases/tag/v1.100

Bront reference: final master commit `aef23d9a11416655a8351230edb3c2377061c077`.

Cache directory by default: `.cache/vnm-font/`. These identifiers are **Git blob SHA-1s**, not ordinary file SHA-1s.

## upstream

Cache filename: `upstream-variable.ttf`

Repository path: `canonical/Ubuntu-Sans-Mono-fonts:fonts/variable/UbuntuSansMono[wght].ttf`

Git blob: `3d8d0e73d5507976bf749a409bce276c57c51274`

Pinned source: https://raw.githubusercontent.com/canonical/Ubuntu-Sans-Mono-fonts/c57353c1772eb8aaab9c539e3d42c971a03a5fcd/fonts/variable/UbuntuSansMono%5Bwght%5D.ttf

## original

Cache filename: `ubuntu-mono-original.ttf`

Repository path: `chrismwendt/bront:UbuntuMono.ttf`

Git blob: `fdd309d716629f4e5339d5e5508225ed857a3ede`

Pinned source: https://raw.githubusercontent.com/chrismwendt/bront/aef23d9a11416655a8351230edb3c2377061c077/UbuntuMono.ttf

## bront

Cache filename: `ubuntu-mono-bront.ttf`

Repository path: `chrismwendt/bront:UbuntuMono-Bront.ttf`

Git blob: `4731a05112ae85bd974e245c552bdf92c6ad2059`

Pinned source: https://raw.githubusercontent.com/chrismwendt/bront/aef23d9a11416655a8351230edb3c2377061c077/UbuntuMono-Bront.ttf

## licence

Cache filename: `Ubuntu-Font-Licence.txt`

Repository path: `chrismwendt/bront:UbuntuMono-LICENSE.txt`

Git blob: `ae78a8f94eae372cb1ca4e14b67244342fce604e`

Pinned source: https://raw.githubusercontent.com/chrismwendt/bront/aef23d9a11416655a8351230edb3c2377061c077/UbuntuMono-LICENSE.txt

## Manual/offline population

Place each exact original file in the cache using the filenames above. The
builder verifies the Git blob identity before parsing it. Do not rename a
different release to fit the expected filename, and do not use a language subset
in place of the full variable font. Keep bracketed variable-font names intact
when obtaining the upstream file; its local cache filename is intentionally
simpler.

The identity function is:

```python
hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
```

Each build report additionally records conventional SHA-256 digests of every
actual input used and the output. Identity checks prevent accidentally using a
changed file; they are not a substitute for reviewing this code or trusting its
original provenance.

The derivative name follows the user-selected spelling. The font output keeps
upstream notices and is accompanied by the Ubuntu Font Licence 1.0. The Python
code's MIT licence is separate and does not replace the font's licence.

Licence reference: https://ubuntu.com/legal/font-licence

Dependency versions are pinned to the versions used for the synthetic tests:
- https://pypi.org/project/fonttools/4.63.0/
- https://pypi.org/project/Pillow/12.3.0/
