# OpenCobolIDE 4.7.6 for Modern Python on Debian-Based Linux

This package is the original OpenCobolIDE 4.7.6 release, updated to run with modern Python, PyQt5, and current Debian-based Linux distributions.

It is not a new upstream OpenCobolIDE release and does not add major new IDE features. It is a compatibility-maintained version intended only for Debian-family systems, including Debian, Ubuntu, Linux Mint, and compatible derivatives.

## Compatibility Updates

- Updated for Python 3.8 and newer.
- Updated for PyQt5 5.15 and newer.
- Fixed APIs removed from modern Python.
- Fixed bundled legacy modules that conflicted with the Python standard library.
- Fixed PyQt5 drawing, sizing, color, margin, and editor-panel errors.
- Updated GnuCOBOL detection and compilation support.
- Updated Debian and Python packaging metadata.
- Updated the Linux desktop launcher.
- Added a Debian installation package.

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
opencobolide_4.7.6+modern4_all.deb
```

Open a terminal in the directory containing the downloaded file and install it with:

```bash
sudo apt install ./opencobolide_4.7.6+modern4_all.deb
```

Using `apt` is recommended because it resolves missing dependencies automatically.

Launch the application from the desktop menu or run:

```bash
opencobolide
```

## Removal

To remove OpenCobolIDE:

```bash
sudo apt remove opencobolide
```

## Package Checksum

SHA-256:

```text
d7cf7a9143020b7f4e7216884321c6f9b38cd4e7eb2543301689b180fb89e71d
```

## Testing

This package was built and tested on a Debian-based Linux system with:

- Python 3.10
- PyQt5 5.15
- GnuCOBOL 3.1.2

The package was also checked with Debian Lintian and tested through a simulated `apt` installation.

## Development Assistance

The modernization, Python and PyQt5 compatibility fixes, Debian packaging, and testing were completed with assistance from OpenAI Codex.

This project remains based on the original OpenCobolIDE 4.7.6 source code. It is not an official continuation or a new upstream release.

### Disclaimer

This is an unofficial, community-maintained compatibility build provided for testing and convenience. It is supplied **as is**, without any warranty or guarantee that it will work correctly on every system.

Use this software and the provided Debian package at your own risk. The original developers, contributors, package maintainer, and development-assistance providers accept no responsibility or liability for data loss, system damage, compilation errors, security issues, interrupted work, or any other consequences resulting from installing or using this software.

Always back up important source code, configuration, and project files before installation or use. This disclaimer does not replace or modify the terms of the GNU General Public License under which OpenCobolIDE is distributed.
