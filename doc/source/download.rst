Download & Install
==================

Scope
-----

This compatibility-maintained OpenCobolIDE 4.7.6 package supports Debian,
Ubuntu, Linux Mint, and compatible Debian-family distributions.

Requirements
------------

* Python 3.8 or newer
* PyQt5 5.15 or newer
* GnuCOBOL
* Standard Debian package-management tools

The Debian package declares these dependencies so ``apt`` can obtain missing
packages from the configured distribution repositories.

Installation
------------

Install the downloaded package with::

    sudo apt install ./opencobolide_4.7.6+modern4_all.deb

If GnuCOBOL must be installed separately, run::

    sudo apt update
    sudo apt install gnucobol

Confirm that the compiler is available with::

    cobc --version

Launch OpenCobolIDE from the desktop menu or run::

    opencobolide

Removal
-------

Remove the package with::

    sudo apt remove opencobolide

Windows, macOS, RPM, Arch Linux, and historical PPA build instructions are not
supported by this maintained branch.
