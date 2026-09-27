# OpenCobolIDE 4.7.6 – Modern Linux Compatibility Build 9

This is an unofficial compatibility-maintained build of the original
OpenCobolIDE 4.7.6 for modern Python, PyQt5, GnuCOBOL, and Debian-family Linux.
It preserves the original project ownership and maintainer attribution.

## Added in modern9

- Added a self-contained offline HTML manual generated from all ten maintained
  RST documentation pages.
- Embedded the documentation screenshots directly in the manual so it works
  without internet access or separate image files.
- Changed **Help → Help** to open the installed local manual in the user's
  default browser.
- Retained the GitHub documentation directory as a fallback if the local file
  is unavailable.
- Added automated checks for local Help resolution and complete RST coverage.

Modern9 retains the Python 3.12 compatibility fixes from modern6, the modern
file-opening fix from modern7, and the stable GnuCOBOL standard-name fix from
modern8.

## Dependencies

- Python 3.8 or newer
- PyQt5 5.15 or newer
- GnuCOBOL

The GnuCOBOL compiler is not bundled. A system installation is required.

## Installation or upgrade

```bash
sudo apt install ./opencobolide_4.7.6+modern9_all.deb
```

Confirm the installed version:

```bash
dpkg-query -W -f='${Package} ${Version}\n' opencobolide
```

Expected result:

```text
opencobolide 4.7.6+modern9
```

## Validation

- Complete automated suite: 57 passed
- Offline manual contains all ten maintained RST pages
- Embedded screenshots and internal page links checked
- Debian package contents and metadata checked
- Debian Lintian check
- Simulated APT installation or upgrade
- Verification that generated Python bytecode is not included

## SHA-256 checksum

```text
04fd5324d4b84dcef79975530946157c3a67e351e4250f3aebd4b09b3514e6fa
```

Verify the downloaded package with:

```bash
sha256sum opencobolide_4.7.6+modern9_all.deb
```

## Attribution and disclaimer

The original OpenCobolIDE authors and maintainer retain full credit and
ownership of the project. OpenAI Codex assisted only with modern Python and
Linux compatibility fixes, Debian packaging, documentation, and testing.

This is an unofficial community compatibility build supplied as is, without
warranty. Back up important source code, configuration, and project files
before installation or use.
