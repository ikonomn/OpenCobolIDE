Contributing
============

This repository contains the unofficial ``4.7.6+modern10`` compatibility polish
of the original OpenCobolIDE 4.7.6 release for modern Python, PyQt5, GnuCOBOL,
and Debian-family Linux. It does not change the original project ownership or
maintainer attribution.

The original upstream project is:

https://github.com/OpenCobolIDE/OpenCobolIDE

When submitting a change:

1. Create a focused branch from ``modern-python``.
2. Keep changes compatible with Python 3.8 or newer and PyQt5 5.15.
3. Add or update tests when changing behavior.
4. Run ``python3 -m pytest -q`` when the test dependencies are installed.
5. Submit the pull request against ``modern-python``.

The Debian package remains the primary tested binary distribution. Portable
source-installation improvements for other Linux distributions and Windows are
welcome when they preserve the Debian build. The
``codex/legacy-cross-platform-backup`` branch preserves former platform-specific
build files for reference.

The compatibility and packaging work on this branch was completed with
assistance from OpenAI Codex. It is not represented as an official upstream
release or a transfer of maintainership.
