# OpenCobolIDE 4.7.6+modern10

Modern10 improves Python 3.12 compatibility and makes installation from source
practical on modern Linux distributions and Windows. It remains an unofficial
compatibility polish of the original OpenCobolIDE 4.7.6 release.

## Changes

- Removed obsolete bundled Pygments and Future copies from wheels, source
  distributions, and Debian packages.
- Uses the maintained Pygments package and native Python 3 built-ins.
- Fixed remaining invalid escape warnings in OpenCobolIDE and bundled PyQode
  runtime modules on Python 3.12 and newer.
- Updated legacy PyQode imports for current Pygments releases.
- Added virtual-environment and `pip` installation from source.
- Added Linux shell and Windows PowerShell installation helpers.
- Added support for `python -m open_cobol_ide`.
- Replaced the Debian builder's deprecated `setup.py install` step with a
  modern `pip` build-and-stage workflow.
- Added `python3-pygments` as a Debian runtime dependency.
- Updated the self-contained offline manual and source documentation.

Modern10 retains the file-opening, GnuCOBOL standard-selection, local Help,
custom project build-script, and source-built GnuCOBOL support from earlier
modern releases.

## Debian installation

```sh
sudo apt install ./opencobolide_4.7.6+modern10_all.deb
```

The package supports Debian, Ubuntu, Linux Mint, and compatible Debian-family
distributions. GnuCOBOL is recommended. If `cobc` was built from source, use:

```sh
sudo apt install --no-install-recommends \
  ./opencobolide_4.7.6+modern10_all.deb
```

## Installation from source

Linux:

```sh
./scripts/install_from_source.sh
./.venv/bin/opencobolide
```

Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_from_source.ps1
.\.venv\Scripts\opencobolide.exe
```

Windows source installation is provided for community testing. It has not yet
been tested by this compatibility maintainer on a Windows machine.

## Verification

- Complete automated test suite: 66 tests passed.
- Warning-free compilation of shipped runtime sources with Python 3.12.
- Wheel and source-distribution audits for excluded legacy dependencies.
- Isolated virtual-environment installation and import checks.
- Debian package contents, metadata, and installed-runtime compilation checks.

## Package checksum

`be6e979932e9e98f47fbd89add93ecb4ccd17f92d96b334dec68d9a79f5a5f6a`

The original OpenCobolIDE ownership and maintainer attribution are unchanged.
The modernization work was completed with assistance from OpenAI Codex and is
not an official new upstream release.
