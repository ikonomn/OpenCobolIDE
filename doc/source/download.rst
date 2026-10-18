Download and install modern11.2
=============================

Scope
-----

The unofficial ``4.7.6+modern11.2`` package supports Debian, Ubuntu, Linux Mint,
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

Download ``opencobolide_4.7.6+modern11.2_all.deb`` from the `modern11.2 release`_.
Open a terminal in the download directory and install it with::

    sudo apt install ./opencobolide_4.7.6+modern11.2_all.deb

GnuCOBOL is recommended rather than required. A normal ``apt`` installation
installs the distribution compiler package. If ``cobc`` was already installed
from source, keep that version and skip recommended packages with::

    sudo apt install --no-install-recommends \
        ./opencobolide_4.7.6+modern11.2_all.deb

After installation, confirm that the intended compiler is first on ``PATH``::

    command -v cobc
    cobc --version

If GnuCOBOL must be installed separately, run::

    sudo apt update
    sudo apt install gnucobol

Confirm that the compiler is available with::

    cobc --version

Confirm the installed package version with::

    dpkg-query -W -f='${Package} ${Version}\n' opencobolide

The expected package version is ``4.7.6+modern11.2``.

Package checksum
----------------

Verify the downloaded package with::

    sha256sum opencobolide_4.7.6+modern11.2_all.deb

Compare the result with the checksum published alongside the GitHub release
asset. The checksum is kept outside this embedded manual so it can verify the
complete package that contains the manual itself.

Launch OpenCobolIDE from the desktop menu or run::

    opencobolide

Removal
-------

Remove the package with::

    sudo apt remove opencobolide

Installation from source
------------------------

The source tree supports the standard Python virtual-environment and ``pip``
workflow. It does not require the deprecated ``setup.py install`` command.

First install Git. Clone the modern-python branch of the repository and
change into its directory before running the installer.

On Linux::

    git clone --branch modern-python https://github.com/ikonomn/OpenCobolIDE.git
    cd OpenCobolIDE
    ./scripts/install_from_source.sh
    ./.venv/bin/opencobolide

On Windows, install Python 3.8 or newer and a Windows build of GnuCOBOL. Make
sure ``cobc.exe`` is available through ``PATH``. Then run in PowerShell::

    git clone --branch modern-python https://github.com/ikonomn/OpenCobolIDE.git
    cd OpenCobolIDE
    Set-ExecutionPolicy -Scope Process Bypass
    .\scripts\install_from_source.ps1
    .\.venv\Scripts\opencobolide.exe

The Debian package remains the tested binary distribution. Source installation
is provided to help users of other Linux distributions and Windows, but those
platform combinations have not all been fully tested. See
``INSTALL_FROM_SOURCE.md`` in the repository for detailed prerequisites,
manual commands, and wheel-building instructions.

Historical RPM, Arch Linux, macOS, and Windows package-building assets remain
preserved in the ``codex/legacy-cross-platform-backup`` branch. They are not
used by the modern source-installation workflow.

.. _`modern11.2 release`: https://github.com/ikonomn/OpenCobolIDE/releases/tag/v4.7.6-modern11.2
