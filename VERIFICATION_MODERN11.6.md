# Consolidated modern11.6 local verification — 2026-10-26

- Regression suite: **196 passed in 34.12 seconds** on Linux Mint, Python 3.10/Qt5, offscreen GUI.
- Includes project lifecycle, project/source settings, internal build script, F8/compiler workflow, copybook creation, shipped demo executable/module builds and cross-reference listing checks.
- Shell syntax and git whitespace checks passed.
- Debian: `opencobolide_4.7.6+modern11.6_all.deb` built locally. Extracted documentation, internal builder and demonstration files verified against source.
- Debian SHA256: `7d5fb9a13501275b14884e460a4e155c5b7f9a7ba3e3be28ffb104a6af09be37`.
- Mageia 10 and Fedora 44 kits contain committed source and native build scripts. RPM builds, installation and GUI testing on those distributions remain pending.
- No GitHub push or release upload performed. Transfer kits record the exact source commit in SOURCE_REVISION.txt and include SHA256 checksums.
