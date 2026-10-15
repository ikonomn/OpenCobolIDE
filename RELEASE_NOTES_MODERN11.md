# OpenCobolIDE 4.7.6+modern11

Modern11 adds a program-arguments popup when Run is selected.

- Enter runtime arguments, including quoted values containing spaces.
- Remember the last arguments separately for each source file.
- Leave the field empty to run without arguments, or Cancel to stop.
- Report unmatched quotes before compiling or launching.
- Forward arguments to executables and modules in the embedded console
  and external terminal; quote Linux terminal commands safely.

For `bio2.cbl`, enter `18090212 18650415` in the popup. This corresponds
to running `bio2 18090212 18650415` in a terminal.

## Installation

Download the Debian package and install it with:

```sh
sudo apt install ./opencobolide_4.7.6+modern11_all.deb
```

Restart the IDE after installation. Supports Debian, Ubuntu, Linux Mint, and
compatible systems. Retains modern10 source-installation and compatibility
changes. This is an unofficial compatibility release; original authorship
and maintainer attribution remain unchanged.

## Verification

The arguments popup and COBOL argument handling were tested locally, and
the user confirmed successful operation with `bio2.cbl` on Linux Mint.

- Automated test suite: **73 passed**.
- Debian installer rebuilt from the updated repository and version verified.

## SHA-256

`dfe2e1bf76e0d15e0da20274701293c22468663a7149c2be907f747f09e850f7`

A `SHA256SUMS` file is included with the release assets.
