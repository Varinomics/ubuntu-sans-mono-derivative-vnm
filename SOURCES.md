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

## Source archive checksums

`SHA256SUMS.txt` contains ordinary SHA-256 digests of the tracked file bytes in
Git, excluding the checksum manifest itself. These are also the bytes written by
`git archive`: `.gitattributes` keeps text files at LF line endings in new
checkouts and archives regardless of `core.autocrlf`, and binary files are unchanged.
The manifest describes the source archive, not a font binary or the inputs used
for an earlier local font build.

In an extracted source archive, verify the files with:

```sh
sha256sum --check SHA256SUMS.txt
```

A checkout made before this line-ending convention may retain CRLF files and
therefore have different file digests. Verify an archive of the same revision
instead:

```sh
git archive --format=zip --output=../font-source.zip HEAD
```

### Historical 0.1.5 font build

The locally distributed Regular font with SHA-256
`86f23c1188625152b280df59a63d870b20d4dcd53295c34eac60c070480ce361`
was built with fontTools 4.56.0 and CRLF bytes of `vnm_font.py` from revision
`242dfad431b1ebb27cfc3e6cc751432d91258035`. Its recorded builder SHA-256 is
`5725ffcef86d84b2b432757b0f56ada5463e482df8b9d7453282a67c6ee4c7c6`.
That provenance remains distinct from the LF source checksums and the dependency
versions in `requirements.txt`; it does not claim a build with those dependencies.

The [recorded builder source](https://github.com/Varinomics/ubuntu-sans-mono-derivative-vnm/blob/242dfad431b1ebb27cfc3e6cc751432d91258035/vnm_font.py)
has LF-byte SHA-256
`0e14e7321460ea6b17dcde1f84519f2503044e7d5ffcba28d8f2dc31f4fa0c0f`.
To recover the exact historical builder bytes from a clone, read that Git blob
as bytes and convert LF to CRLF without changing its encoding or other content:

```python
import hashlib
import subprocess

source = subprocess.check_output([
    "git", "show", "242dfad431b1ebb27cfc3e6cc751432d91258035:vnm_font.py"
])
historical_source = source.replace(b"\n", b"\r\n")
print(hashlib.sha256(historical_source).hexdigest())
```

This recovers the recorded source identity; it is not a claim that a new build
under a different fontTools version produces identical font bytes.
