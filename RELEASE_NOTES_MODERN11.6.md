# OpenCobolIDE 4.7.6+modern11.6 — local test build

The About diagnostic report now requests `cobcrun --info` for runtime build
information and `cobcrun --runtime-config` for runtime configuration, replacing
`cobcrun --runtime-env`. Errors identify the command that failed.

The compiler workflow and settings remain compatible with modern11.5.
The offline Help manual and Debian package identify this build as modern11.6.

## Verification and limits

The functional change previously passed the complete 112-test suite and two
exploratory checks. See `doc/broader-verification-2026-10-23.md` for scope and
environment. Verification of this release preparation is recorded separately
in `doc/modern11.6-validation.md`.

Vincent's scrolling and toolbar-tooltip reports are not claimed as fixed.
Mageia 10 compatibility and desktop tooltip timing remain unverified.
This build is prepared for local installation and user testing, not published.

## Debian package

`opencobolide_4.7.6+modern11.6_all.deb`

Install the package locally with apt, then confirm modern11.6 in the title/About
and check the compiler and runtime information. Test compiling and running,
per-source options, source format directives, and Down Arrow/Page Down with
Logs both open and closed. Check toolbar tooltip timing on the actual desktop.
