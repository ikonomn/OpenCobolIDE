Contributing
============

This repository contains an unofficial compatibility polish of the original
OpenCobolIDE 4.7.6 release for modern Python, PyQt5, and Debian-family Linux.
It does not change the original project ownership or maintainer attribution.

The original upstream project is:

https://github.com/OpenCobolIDE/OpenCobolIDE

When submitting a change:

1. Create a focused branch from ``modern-python``.
2. Keep changes compatible with Python 3.8 or newer and PyQt5 5.15.
3. Add or update tests when changing behavior.
4. Run ``python3 -m pytest`` when the test dependencies are installed.
5. Submit the pull request against ``modern-python``.

Changes specific to Windows or macOS are outside the scope of this compatibility
branch. The ``codex/legacy-cross-platform-backup`` branch preserves the former
cross-platform build files.

The compatibility and packaging work on this branch was completed with
assistance from OpenAI Codex. It is not represented as an official upstream
release or a transfer of maintainership.
