Contributing
============

This repository maintains OpenCobolIDE 4.7.6 for modern Python, PyQt5, and
Debian-family Linux distributions. It is not a new upstream release.

Report problems at:

https://github.com/ikonomn/OpenCobolIDE/issues

When submitting a change:

1. Create a focused branch from ``modern-python``.
2. Keep changes compatible with Python 3.8 or newer and PyQt5 5.15.
3. Add or update tests when changing behavior.
4. Run ``python3 -m pytest`` when the test dependencies are installed.
5. Submit the pull request against ``modern-python``.

Changes specific to Windows or macOS are outside the scope of this maintained
branch. The ``codex/legacy-cross-platform-backup`` branch preserves the former
cross-platform build files.
