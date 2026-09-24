Contributing
============

This branch is an unofficial compatibility polish for modern Python, PyQt5,
and Debian-family Linux. Original project ownership and maintainer attribution
remain unchanged.

The `original upstream project`_ remains the authoritative source for original
OpenCobolIDE authorship and project history. Compatibility work in this branch
was completed with assistance from OpenAI Codex and is not an official upstream
release.

Pull requests should target the ``modern-python`` branch. Keep changes focused,
add tests for behavior changes, and run ``python3 -m pytest`` when the test
dependencies are installed.

Windows and macOS packaging is outside the scope of this branch. Historical
cross-platform build files are preserved in the
``codex/legacy-cross-platform-backup`` branch.

.. _`original upstream project`: https://github.com/OpenCobolIDE/OpenCobolIDE
