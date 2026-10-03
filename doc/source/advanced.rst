Advanced topics
===============

This maintained branch targets Debian-family Linux. The Windows and macOS
instructions from the original 4.7.6 documentation are intentionally omitted.

Using a custom GnuCOBOL installation
-------------------------------------

The Debian package depends on GnuCOBOL, but OpenCobolIDE can also use a compiler
installed in a custom location such as ``/usr/local/bin/cobc``.

First identify the active compiler and its configuration directories::

    command -v cobc
    readlink -f "$(command -v cobc)"
    cobc --version
    cobc --info

Open ``Edit -> Preferences -> Compiler`` and set **Compiler path** to the value
reported by ``command -v cobc``. Use **Check compiler** to confirm that the IDE
can compile a small program.

The important GnuCOBOL directories reported by ``cobc --info`` include:

``COB_CONFIG_DIR``
    Contains dialect files such as ``default.conf``, ``cobol85.conf``, and
    ``mf.conf``.

``COB_COPY_DIR``
    Contains the default GnuCOBOL copybooks.

``COB_LIBS``
    Shows the library search and link options used by the compiler.

Do not override these paths in OpenCobolIDE unless the compiler genuinely uses
non-default directories. A compiler installed under ``/usr/local`` normally
reports the matching ``/usr/local/share/gnucobol`` paths itself.

Compiler standards on modern Python
-----------------------------------

Modern8 and newer pass compiler standards by their GnuCOBOL names on every supported
Python version. The available selections are:

* ``default``
* ``cobol2002``
* ``cobol85``
* ``ibm``
* ``mvs``
* ``bs2000``
* ``mf``
* ``cobol2014``
* ``acu``
* ``none``

For example, selecting ``mf`` produces ``-std=mf`` for compilation and live
syntax checking. Selecting ``none`` omits the automatic ``-std`` option. Do not
add a duplicate ``-std`` option under additional compiler flags.

To verify a dialect outside the IDE, run a direct compiler test such as::

    cobc -x -std=mf -o hello hello.cob
    ./hello

.. _sql-guide:

SQL COBOL with DBPRE
--------------------

GnuCOBOL does not support ``EXEC SQL`` statements natively. A precompiler must
convert them to COBOL before compilation. The legacy OpenCobolIDE integration
supports DBPRE on Linux for files with the ``.scb`` extension.

This integration is retained from the original 4.7.6 release and has not been
part of the modern9.3 compatibility test matrix. Back up source files and verify
the generated COBOL independently before relying on it.

A typical DBPRE setup requires:

* the ``dbpre`` executable;
* the ``cobmysqlapi.o`` object file;
* the ``PGCTBBAT``, ``PGCTBBATWS``, and ``SQLCA`` copybooks;
* the appropriate database development headers and client library.

Configure their paths under ``Edit -> Preferences -> SQL COBOL``. Add required
include, copybook, library-search, and library options under the compiler
settings, then open and compile the ``.scb`` source.

SQL COBOL with a project build script
-------------------------------------

Projects that use another SQL precompiler, such as GixSQL's ``gixpp``, can
provide an executable ``build.sh`` in the same directory as their COBOL source
files or in the project root above them. OpenCobolIDE searches upward as far as
the nearest ``.git`` directory or ``Makefile``. When **Compile** or **Run** is
selected, it invokes the script with the absolute source-file path as its only
argument instead of calling ``cobc`` directly::

    ./build.sh /absolute/path/to/program.cbl

The script is responsible for preprocessing the source, compiling the generated
COBOL, and placing the resulting executable in the project-root ``bin``
directory. OpenCobolIDE uses that directory for **Run** and **Clean** as well.
The script's standard output and standard error are shown in the compiler log.
A nonzero exit status marks the compilation as failed.

The script must be executable::

    chmod +x build.sh

A generic GixSQL template is included in the source tree at
``examples/gixsql/build.sh``. The Debian package installs the same template at
``/usr/share/doc/opencobolide/examples/gixsql/build.sh``. Start a new project
by copying it to the project root::

    cp /usr/share/doc/opencobolide/examples/gixsql/build.sh ./build.sh
    chmod +x ./build.sh

The template uses ``gixpp`` followed by ``cobc``, writes intermediate files to
``build/``, and writes executables to ``bin/``. Install GixSQL separately and,
when it is installed outside the distribution defaults, set
``GIXSQL_COPY_DIR`` and ``GIXSQL_LIBRARY_DIR`` in the project script or its
environment. The example directory also contains ``README.md`` and sample
SQLite and MariaDB ``.conf.example`` profiles. They document runtime profile
selection with ``DB-FLAG`` and ``DB_CONFIG_FILE`` without hard-coding database
paths or credentials in COBOL sources.

If no executable ``build.sh`` is found in that project scope, OpenCobolIDE
keeps the normal compiler flow, including the existing DBPRE and esqlOC
integrations. Do not modify the original source file in the build script; write
preprocessed and listing files to a separate build directory.

Developer mode
--------------

OpenCobolIDE normally loads the legacy pure-Python libraries bundled under
``open_cobol_ide/extlibs``. Setting ``OCIDE_DEV_MODE=1`` disables that bundled
path modification and requires compatible dependencies to be supplied by the
development environment.

The maintained Debian package deliberately uses the distribution PyQt5 package
so its native Qt dependencies match the host system. Developer mode is intended
for source work and is not required for normal use.
