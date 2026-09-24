# OpenCobolIDE 4.7.6 for Modern Python on Debian-Based Linux

This package is the original OpenCobolIDE 4.7.6 release, polished with assistance from OpenAI Codex so it can run with modern Python, PyQt5, and current Debian-based Linux distributions.

It is not a new upstream OpenCobolIDE release, does not change the original project ownership or maintainership, and does not add major new IDE features. It is an unofficial compatibility polish intended only for Debian-family systems, including Debian, Ubuntu, Linux Mint, and compatible derivatives.

The original OpenCobolIDE authors and maintainer retain full credit for the project. OpenAI Codex assisted only with the modern Python, PyQt5, Linux compatibility, packaging, and testing work described below.

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

## Attribution and Development Assistance

The modernization, Python and PyQt5 compatibility fixes, Debian packaging, and testing were completed with assistance from OpenAI Codex.

This project remains based on the original OpenCobolIDE 4.7.6 source code and retains its original authorship and maintainer attribution. This compatibility package is not an official continuation, a transfer of ownership, or a new upstream release.
