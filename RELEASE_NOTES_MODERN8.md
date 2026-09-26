# OpenCobolIDE 4.7.6 – Modern Linux Compatibility Build 8

This is an unofficial compatibility-maintained build of the original
OpenCobolIDE 4.7.6 for modern Python, PyQt5, and Debian-based Linux
distributions.

It is not a new upstream OpenCobolIDE release and does not change the original
project ownership or maintainer attribution. The compatibility fixes, Debian
packaging, and testing were completed with assistance from OpenAI Codex.

## Fixed in modern8

- Fixed GnuCOBOL standard selection on Python 3.11 and newer.
- OpenCobolIDE now passes stable standard names such as `-std=default` and
  `-std=mf` instead of numeric enum values such as `-std=0` and `-std=6`.
- Applied the correction to both compilation and live syntax checking.
- Selecting `none` now omits the automatic `-std` option consistently from
  both commands.
- Retained the Python 3.12 Pygments fixes from modern6 and the file-opening fix
  from modern7.

The defect was caused by a Python 3.11 change to `IntEnum` string conversion.
It could make GnuCOBOL search for nonexistent files such as `0.conf` or
`6.conf`, even though `default.conf` and `mf.conf` were installed correctly.

## Dependencies

- Python 3.8 or newer
- PyQt5 5.15 or newer
- GnuCOBOL

The GnuCOBOL compiler is not bundled. A system installation is required.

## Installation or upgrade

```bash
sudo apt install ./opencobolide_4.7.6+modern8_all.deb
```

Confirm the installed version:

```bash
dpkg-query -W -f='${Package} ${Version}\n' opencobolide
```

Expected result:

```text
opencobolide 4.7.6+modern8
```

## Validation

- Complete test suite: 54 passed
- Python 3.12 enum-name regression check
- Compiler and live-linter checks for every standard exposed by the IDE
- Debian Lintian
- Simulated APT installation or upgrade
- Package metadata and dependency checks
- Verification that generated Python bytecode is not included

## SHA-256 checksum

```text
6ce4aeead2ac27b918789e2cf45c360854c03bc31d5c66fd79372e92b0f973ac
```

Verify the downloaded package with:

```bash
sha256sum opencobolide_4.7.6+modern8_all.deb
```

## Attribution and disclaimer

The original OpenCobolIDE authors and maintainer retain full credit and
ownership of the project. OpenAI Codex assisted only with modern Python and
Linux compatibility fixes, Debian packaging, and testing.

This is an unofficial community compatibility build supplied as is, without
warranty. Back up important source code, configuration, and project files
before installation or use.
