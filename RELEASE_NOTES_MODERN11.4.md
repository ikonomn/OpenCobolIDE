# OpenCobolIDE 4.7.6+modern11.4

modern11.4 is a Linux service release that corrects the application shutdown
lifecycle across distributions and desktop environments.

Diagnostic traces from Mageia 10 showed that compilation, console shutdown and
the pyQode backend completed successfully before a native
`malloc_consolidate()` abort occurred during final Qt/Python teardown.

This release:

- keeps application references alive until the Qt event loop returns;
- performs Python-side cleanup once, after `app.exec_()`;
- makes cleanup idempotent to prevent repeated teardown;
- retains the optional durable trace log for further diagnostics.

The correction is applicable to all Linux installations, including Debian,
Ubuntu, Linux Mint, Mageia and other distributions using the source installer.
The Debian package is provided for Debian-family distributions; other Linux
distributions should install from source.

modern11.4 also retains automatic listing names, per-source compiler flags,
runtime program arguments, the optional user launcher, and automatic plain
COBOL/GixSQL build routing.
