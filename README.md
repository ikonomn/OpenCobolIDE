# OpenCobolIDE 4.7.6 for Modern Python on Debian-Based Linux

This package is the original OpenCobolIDE 4.7.6 release, polished with assistance from OpenAI Codex so it can run with modern Python, PyQt5, and current Debian-based Linux distributions.

It is not a new upstream OpenCobolIDE release, does not change the original project ownership or maintainership, and does not add major new IDE features. The binary package remains an unofficial compatibility polish for Debian-family systems, including Debian, Ubuntu, Linux Mint, and compatible derivatives. A modern source-installation workflow is also provided for testing on other Linux distributions and Windows.

The original OpenCobolIDE authors and maintainer retain full credit for the project. OpenAI Codex assisted only with the modern Python, PyQt5, Linux compatibility, packaging, and testing work described below.

## Compatibility Updates

- Updated for Python 3.8 and newer.
- Updated for PyQt5 5.15 and newer.
- Fixed APIs removed from modern Python.
- Replaced the obsolete bundled Pygments/Future runtime copies with a maintained
  Pygments dependency and native Python 3 built-ins, eliminating their Python
  3.12 invalid-escape warnings from installed builds.
- Fixed file opening after Python removed the legacy universal-newline mode.
- Fixed GnuCOBOL standard selection on Python 3.11 and newer so options such
  as `mf` are passed as `-std=mf` instead of their numeric enum value.
- Fixed bundled legacy modules that conflicted with the Python standard library.
- Fixed PyQt5 drawing, sizing, color, margin, and editor-panel errors.
- Updated GnuCOBOL detection and compilation support.
- Updated Debian and Python packaging metadata.
- Updated the Linux desktop launcher.
- Added a Debian installation package.
- Added modern virtual-environment and ``pip`` source installers for Linux and
  Windows without the deprecated ``setup.py install`` workflow.
- Added a self-contained offline manual generated from all maintained RST
  documentation pages; the Help action opens it locally.

## Dependencies

The following dependencies are required:

- Python 3.8 or newer
- PyQt5 5.15 or newer
- GnuCOBOL
- Standard Debian package-management tools

The Debian package declares these dependencies, allowing `apt` to install missing packages from the configured Debian or Ubuntu repositories.

## GnuCOBOL Compiler

The GnuCOBOL compiler is not bundled with this package.

OpenCobolIDE requires a system installation of GnuCOBOL. The package has been tested with GnuCOBOL 3.1.2.

Other recent GnuCOBOL versions may work but have not yet been fully tested.

If necessary, install the compiler manually:

```bash
sudo apt update
sudo apt install gnucobol
```

Confirm that it is available:

```bash
cobc --version
```

## Installation

Download:

```text
opencobolide_4.7.6+modern11.3_all.deb
```

Open a terminal in the directory containing the downloaded file and install it with:

```bash
sudo apt install ./opencobolide_4.7.6+modern11.3_all.deb
```

Using `apt` is recommended because it resolves missing dependencies automatically.

If GnuCOBOL was installed from source and `cobc` is already available, avoid
installing the distribution compiler package with:

```bash
sudo apt install --no-install-recommends ./opencobolide_4.7.6+modern11.3_all.deb
```

Launch the application from the desktop menu or run:

```bash
opencobolide
```

## Installation from source

The source tree now uses the standard Python virtual-environment and `pip`
workflow on Linux and Windows. It no longer requires the deprecated
`setup.py install` command.

Install Git first, then clone the repository and enter its directory.

Linux:

```bash
git clone --branch modern-python https://github.com/ikonomn/OpenCobolIDE.git
cd OpenCobolIDE
./scripts/install_from_source.sh
./.venv/bin/opencobolide
```

Windows PowerShell:

```powershell
git clone --branch modern-python https://github.com/ikonomn/OpenCobolIDE.git
cd OpenCobolIDE
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_from_source.ps1
.\.venv\Scripts\opencobolide.exe
```

GnuCOBOL must be installed separately and `cobc` (or `cobc.exe`) must be
available through `PATH`. See [INSTALL_FROM_SOURCE.md](INSTALL_FROM_SOURCE.md)
for prerequisites, manual commands, wheel-building instructions, and current
cross-platform limitations.

## Removal

To remove OpenCobolIDE:

```bash
sudo apt remove opencobolide
```

## Package Checksum

After downloading, calculate the SHA-256 checksum with:

```bash
sha256sum opencobolide_4.7.6+modern11.3_all.deb
```

Compare it with the checksum published alongside the GitHub release asset.

## Testing

This package was built and tested on a Debian-based Linux system with:

- Python 3.10.12 (package build and full application checks)
- Python 3.12.14 (bundled Pygments compatibility checks)
- PyQt5 5.15
- GnuCOBOL 3.1.2

The package was also checked with Debian Lintian, verified through a simulated `apt` installation, checked for correct runtime dependency declarations and package permissions, and passed the complete test suite, including regression checks for opening files without Python's removed `U` mode and for stable GnuCOBOL standard names on Python 3.11 and newer. The source-installation work additionally passed 66 tests, a Python 3.12 warning-as-error compilation check, a wheel-content audit, an isolated virtual-environment import test, and a Debian-package regression build.

## Attribution and Development Assistance

The modernization, Python and PyQt5 compatibility fixes, Debian packaging, and testing were completed with assistance from OpenAI Codex.

This project remains based on the original OpenCobolIDE 4.7.6 source code and retains its original authorship and maintainer attribution. This compatibility package is not an official continuation, a transfer of ownership, or a new upstream release.

### Disclaimer

This is an unofficial, community-maintained compatibility build provided for testing and convenience. It is supplied **as is**, without any warranty or guarantee that it will work correctly on every system.

Use this software and the provided Debian package at your own risk. The original developers, contributors, package maintainer, and development-assistance providers accept no responsibility or liability for data loss, system damage, compilation errors, security issues, interrupted work, or any other consequences resulting from installing or using this software.

Always back up important source code, configuration, and project files before installation or use. This disclaimer does not replace or modify the terms of the GNU General Public License under which OpenCobolIDE is distributed.

## Program arguments (modern11.3)

Press **Run** to enter optional arguments for the COBOL program. For example,
for `bio2.cbl`, enter `18090212 18650415`. Enter only the arguments; the IDE
supplies the program name. The last entry is remembered separately for each
source file. An empty entry runs without arguments; Cancel stops the launch.

Use double quotes for an argument containing spaces, for example
`123 "customer name"`. Unmatched quotes are reported before compilation.
Arguments are passed to the program in both the embedded console and external
terminal. These are runtime arguments, separate from compiler options.

## Compiler workflow in modern11.3

Automatic listing names, optional source-install launcher and per-file compiler
flags are described in [the workflow guide](doc/modern11.3-workflow.md).

## Native-crash trace log

For an intermittent native crash, start the source installation with tracing
enabled:

```bash
cd /path/to/OpenCobolIDE
OCIDE_TRACE_LOG="$HOME/opencobolide-trace.jsonl" .venv/bin/opencobolide
```

Repeat the action that triggers the problem and close the IDE normally if it
does not crash. The JSONL file records startup, compilation, program launch,
process completion, window shutdown, and Qt cleanup in order. Every event is
flushed to disk immediately, and Python's native fault handler writes thread
stacks to the same file when the runtime receives a supported fatal signal.
Program argument values and the full environment are not recorded; only the
argument count and a small set of display/runtime conditions are included.

`OCIDE_TRACE_LOG=1` uses an automatically named file below
`~/.cache/OpenCobolIDE/`. Leave the variable unset for normal operation.
