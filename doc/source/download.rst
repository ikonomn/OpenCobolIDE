Download and install modern9.2
==============================

Scope
-----

The unofficial ``4.7.6+modern9.2`` package supports Debian, Ubuntu, Linux Mint,
and compatible Debian-family distributions. It preserves the original
OpenCobolIDE authorship and maintainer attribution.

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

Download ``opencobolide_4.7.6+modern9.2_all.deb`` from the `modern9.2 release`_.
Open a terminal in the download directory and install it with::

    sudo apt install ./opencobolide_4.7.6+modern9.2_all.deb

If GnuCOBOL must be installed separately, run::

    sudo apt update
    sudo apt install gnucobol

Confirm that the compiler is available with::

    cobc --version

Confirm the installed package version with::

    dpkg-query -W -f='${Package} ${Version}\n' opencobolide

The expected package version is ``4.7.6+modern9.2``.

Package checksum
----------------

Verify the downloaded package with::

    sha256sum opencobolide_4.7.6+modern9.2_all.deb

Compare the result with the checksum published alongside the GitHub release
asset. The checksum is kept outside this embedded manual so it can verify the
complete package that contains the manual itself.

Launch OpenCobolIDE from the desktop menu or run::

    opencobolide

Removal
-------

Remove the package with::

    sudo apt remove opencobolide

Windows, macOS, RPM, Arch Linux, and historical PPA builds are not supported by
this maintained branch. Their former assets are preserved only in the
``codex/legacy-cross-platform-backup`` branch.

.. _`modern9.2 release`: https://github.com/ikonomn/OpenCobolIDE/releases/tag/v4.7.6-modern9.2
