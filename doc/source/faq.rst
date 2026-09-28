Frequently asked questions
==========================

Where are generated binaries stored?
------------------------------------

By default, executable programs and modules are written to a ``bin`` directory
beside the source file. The output directory can be changed under
``Edit -> Preferences -> Compiler``.

Where is the documentation?
---------------------------

Choose ``Help -> Help`` or press the Help button to open the complete manual
installed with the Debian package. It is a self-contained local HTML page and
does not require an internet connection.

The maintained RST source is also available at:

https://github.com/ikonomn/OpenCobolIDE/tree/modern-python/doc/source

How do I verify which GnuCOBOL installation is active?
------------------------------------------------------

Run::

    command -v cobc
    readlink -f "$(command -v cobc)"
    cobc --version
    cobc --info

``cobc --info`` reports configuration, copybook, include, and library paths.
Use the path from ``command -v cobc`` as the OpenCobolIDE compiler path.

Why did GnuCOBOL look for ``0.conf`` or ``6.conf``?
---------------------------------------------------

Older compatibility builds converted the selected standard to a numeric
``IntEnum`` value on Python 3.11 and newer. This could produce ``-std=0`` for
``default`` or ``-std=6`` for ``mf``.

Modern8 and newer fix this in both compiler and live-linter commands. Upgrade
to ``4.7.6+modern9.1`` and select the desired standard from
``Edit -> Preferences -> Compiler``. Selecting ``mf`` now produces
``-std=mf``.

How do I diagnose a missing configuration file?
-----------------------------------------------

Find the configured directory with::

    cobc --info | grep COB_CONFIG_DIR

Then list its available dialect files, for example::

    ls -1 /usr/local/share/gnucobol/config/*.conf

Use the actual path reported by your compiler. If ``mf.conf`` exists and a
direct ``cobc -std=mf`` test works, the GnuCOBOL installation is correctly
configured.

Why are Python ``SyntaxWarning`` messages printed?
-------------------------------------------------

Some bundled legacy modules contain old regular-expression string literals.
Modern Python reports these as warnings. The modern6 compatibility work fixed
the expressions that prevented operation on Python 3.12, but harmless warnings
may still appear. They are not the same as a compilation failure.

Why are Wayland ``requestActivate`` messages printed?
-----------------------------------------------------

Qt may print messages stating that Wayland does not support
``QWindow::requestActivate()``. They describe a window-activation limitation
and normally do not prevent editing or compiling. Include the complete terminal
log when reporting a problem so these messages can be distinguished from the
actual failure.

How do I compile SQL COBOL source?
---------------------------------

GnuCOBOL does not process ``EXEC SQL`` statements directly. A COBOL SQL
precompiler is required. See :ref:`sql-guide` for the retained DBPRE integration
notes.

What if a file cannot be decoded?
---------------------------------

OpenCobolIDE first tries the configured preferred encodings. If decoding fails,
the editor displays an encoding panel. Choose **Add or remove**, add the likely
encoding, select it, and choose **Retry**. Back up the file before saving it in a
different encoding.

Where is the OpenCobolIDE log?
-----------------------------

On Debian-family Linux, logs are stored under::

    ~/.cache/.OpenCobolIDE/

Starting OpenCobolIDE from a terminal also captures warnings and compiler
activity::

    opencobolide 2>&1 | tee opencobolide.log

How should paths with spaces be entered?
----------------------------------------

Quote a path containing spaces in additional compiler flags, for example::

    -I "/home/user/my copybooks"

How do I report a useful test result?
------------------------------------

Include the package version, Python version, compiler information, session
type, and terminal log::

    dpkg-query -W -f='${Package} ${Version}\n' opencobolide
    python3 --version
    cobc --version
    cobc --info
    echo "$XDG_SESSION_TYPE"
    opencobolide 2>&1 | tee opencobolide.log
