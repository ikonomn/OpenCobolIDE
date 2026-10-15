# OpenCobolIDE 4.7.6+modern11.1

Modern11.1 replaces modern11, retaining the program-arguments popup and fixing source installation and shutdown.

- Read package metadata without importing the application during isolated builds.
- Stop the Run console helper when the IDE closes, preventing the QProcess warning.

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
sudo apt install ./opencobolide_4.7.6+modern11.1_all.deb
```

Restart the IDE after installation. Supports Debian, Ubuntu, Linux Mint, and
compatible systems. Retains modern10 source-installation and compatibility
changes. This is an unofficial compatibility release; original authorship
and maintainer attribution remain unchanged.

## Verification

The arguments popup and COBOL argument handling were tested locally, and
the user confirmed successful operation with `bio2.cbl` on Linux Mint.

- Automated test suite: **75 passed**.
- Debian installer rebuilt from the updated repository and version verified.

A `SHA256SUMS` file is included with the release assets.
