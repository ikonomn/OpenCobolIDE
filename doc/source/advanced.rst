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
part of the modern10 compatibility test matrix. Back up source files and verify
the generated COBOL independently before relying on it.

A typical DBPRE setup requires:

* the ``dbpre`` executable;
* the ``cobmysqlapi.o`` object file;
* the ``PGCTBBAT``, ``PGCTBBATWS``, and ``SQLCA`` copybooks;
* the appropriate database development headers and client library.

Configure their paths under ``Edit -> Preferences -> SQL COBOL``. Add required
include, copybook, library-search, and library options under the compiler
settings, then open and compile the ``.scb`` source.

Project compilation with the internal build script
--------------------------------------------------

Choose **Open Project** and select the source directory. OpenCobolIDE uses its
own installed ``open_cobol_ide/build_tools/build.sh`` for project compilation,
F8 and Run. It never executes a ``build.sh`` from the project directory. No
project-local build script or SQL detector needs to be copied or maintained.
Projects previously configured in the IDE also use this internal builder.

The IDE supplies the project directory and absolute source path. The bundled
SQL detector inspects sources and copybooks. SQL sources use GixSQL's ``gixpp``
before compilation; plain COBOL sources go directly to ``cobc``. GixSQL must be
installed separately when SQL preprocessing is required. Existing DBPRE and
esqlOC source extensions retain their dedicated compiler paths.

The IDE detects ``-x`` or ``-m`` per source and passes the compiler options and
environment resolved from IDE defaults, project defaults and source overrides.
Artifacts remain inside the project: ``bin/`` for executable/module output and
``build/`` for intermediate SQL output and default ``<source>.lst`` listings.
Explicit ``-T``/``-t`` filenames are preserved. Listings include cross references
(``--Xref``) and symbol tables (``-ftsymbols``). The compiler log shows the exact
commands and verbose preprocessing, translation, compilation and linking steps.

**File → New Project…** asks for a name and parent directory and creates ``src/``,
``copybooks/``, ``bin/``, ``build/``, ``data/`` and ``config/`` without replacing
existing files. A New Project button is also available on the opening screen.
New source files default to the project's ``src/`` directory and offer source
compiler settings after creation.

**Open Project** opens the sources and displays **Configure Project**, which is
also available from the File menu. It lists the sources, whether they inherit
project defaults or have overrides, and validation results. Use **Project
defaults…** or **Selected source settings…** to configure them.

Project settings are saved atomically in ``config/project.json``. Source keys and
project-local paths are relative to the project root, so settings survive moving
or copying the project. Existing project and source preferences are imported
once when an older project without this file is opened. Existing project.json
files are loaded as-is; invalid configuration is reported without replacing it.

**COBOL → Project compiler settings…** edits shared defaults. **Compiler options
for this file…** edits a source override. Both support extra compiler flags,
compiler and tools paths, copybook and library paths, libraries, source format,
listing generation and filenames, and GixSQL preprocessor/copy/library paths.
Blank environment fields and Inherit selections fall back to the level above.
Priority is source overrides, project defaults, then IDE defaults. Executable
and module modes remain automatically detected; do not enter ``-x`` or ``-m``
in the flags. Source listing filenames can use ``{stem}`` for the source basename.

A minimal portable configuration looks like this::

    {
      "schema_version": 1,
      "name": "MyProject",
      "defaults": {
        "enabled": true,
        "flags": ["-Wall", "-debug"],
        "environment": {},
        "copybook_paths": ["copybooks"],
        "listing": {"enabled": true, "filename": "build/{stem}.lst"}
      },
      "sources": {
        "src/helper.cbl": {"flags": ["-Wall"]}
      }
    }

Validation runs when reviewing settings, before saving changed settings, and
before compiling. Errors introduced by an edit are rejected; existing errors
can be repaired incrementally. Compilation is blocked until errors are fixed.
Warnings require acknowledgment. Checks include compiler/tool availability,
missing directories and COPY dependencies, fixed/free format conflicts,
manual mode/output flags, and overlapping binary/listing/intermediate names.
The project source files and configuration may not be used as listing targets.

GixSQL's copy and library directories may be selected with ``GIXSQL_COPY_DIR``
and ``GIXSQL_LIBRARY_DIR`` in the IDE's environment. The example directory
contains SQLite and MariaDB runtime profiles. The optional example ``build.sh``
is retained for command-line use; the IDE does not select it.

Sources opened outside a project retain ordinary single-file compilation.

Developer mode
--------------

OpenCobolIDE normally loads the legacy pure-Python libraries bundled under
``open_cobol_ide/extlibs``. Setting ``OCIDE_DEV_MODE=1`` disables that bundled
path modification and requires compatible dependencies to be supplied by the
development environment.

The maintained Debian package deliberately uses the distribution PyQt5 package
so its native Qt dependencies match the host system. Developer mode is intended
for source work and is not required for normal use.
