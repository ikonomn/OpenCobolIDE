# OpenCobolIDE 4.7.6 modern12

Modern12 is the continuation of the archived 4.7.6 IDE. The version shown in About identifies the modern release. The application retains the Qt editor and the original COBOL editing workflow. It adds portable projects, a project compiler and a connection to the independent COBGDB debugger.

## Workspace and Help

The home page opens files and projects. The editor contains COBOL highlighting, completion, outline, fixed/free source format detection, per-file settings and syntax diagnostics. The file tree follows the active project. Issues, compiler output and program output appear in the lower panes. The View menu controls the panes and editor layout. The Help menu opens the offline modern12 manual with the original editing topics and the cumulative changes since 4.7.6. Use Help → About to check versions and runtime diagnostics. The offline layout-recovery guide describes resetting window preferences if docks become unusable.

The modern branch updates compatibility with Python 3 and PyQt5, uses maintained Pygments and avoids the obsolete bundled future/Pygments dependencies. It includes virtual-environment source installation, Linux launcher support, optional diagnostic trace logging and safer console/editor shutdown. The diagnostic tools report the actual GnuCOBOL runtime and build output. Native RPM packaging retains distribution-specific Python and Qt dependencies.

## Improvements since archived 4.7.6

- Early modern releases moved the IDE and packages to modern Python and Qt while retaining the original project attribution. They fixed syntax highlighter compatibility, file opening and GnuCOBOL standard selection.
- The modern9 through modern11 updates added offline Help, layout recovery, optional project build scripts, the GixSQL example, source installation and the per-file program arguments dialog.
- Modern11.1 through modern11.5 added lifecycle and crash tracing fixes, ordered compiler flags, SQL-only preprocessing, executable/module mode detection, per-source build settings, fixed/free format directives and improved runtime and compiler diagnostics.
- Modern11.6 added portable projects, safe project switching, copybook creation and editing, internal project builds, COPY dependency tracking, incremental compilation, rebuild shortcuts and target-specific RPM recipes.
- Modern12 added runtime discovery and review, retained C/header files, distinct Preferences pages, menu icons, direct COBGDB launch, a consistent bin runtime default and the current debug folder prerequisite. The debugger can use the system terminal while the program's graphical windows stay interactive.

## Project layout

| Folder | Contents |
| --- | --- |
| `src/` | COBOL main programs and callable modules |
| `copybooks/` | Shared COBOL copybooks |
| `config/project.json` | Portable project defaults, overrides, runtime settings and debug mode |
| `data/` | Application inputs and databases you manage |
| `bin/` | Executables and modules. Default runtime working directory |
| `build/` | Listings, SQL-preprocessed sources and incremental build state |
| `debug_data/` | Generated C and headers needed for project debugging |

New Project creates these folders. Open Project creates a missing `debug_data/` and opens recognized sources. Copybooks can be created and edited as COBOL files. They participate in builds through COPY dependencies. Generated output and hidden directories are excluded from source discovery. Close Project and switching projects protect unsaved edits with Save, Discard and Cancel.

## Settings and builds

Open **Preferences → Compiler** for IDE defaults and project or source compiler options. The IDE resolves global defaults, project defaults and per-source overrides in that order. Configure Project provides a source overview and validates settings. Relative project paths travel with the project. Legacy options are migrated when opening a project without portable settings. The independent debugger reads the saved project JSON for its own builds.

**F8** compiles the current source. **Ctrl+F8** compiles changed project sources and affected COPY dependents. **Ctrl+Shift+F8** rebuilds the project. The IDE-owned builder selects executable or module mode from the COBOL source and saves listings in `build/` by default. Cross-references and symbol tables are available using the listing settings. Build diagnostics identify compiler and linker failures. Plain COBOL takes the direct compiler path. Sources using embedded SQL use GixSQL preprocessing and linking. Configure the preprocessor, SQL copybooks and libraries in **Preferences → GixSQL**. The IDE project builder currently uses Bash and Python.

Run prompts for program arguments and remembers them per file. The IDE supports embedded and external program terminals.

## Runtime files

Use **Preferences → Projects** or **File → Rescan Project Folders** (Ctrl+Alt+D) to review suggestions from SELECT and ASSIGN declarations. Review missing, ambiguous and dynamic assignments yourself. Accept settings to save them. Project launches default to `bin/`. An explicit project working directory takes precedence. For the GixSQL example, `../config/application-sqlite.conf` and `sqlite://../build/application.db` resolve from `bin/`.

The data search field accepts one directory per line, with project-relative paths resolved from the project root. Use a single directory with the tested GnuCOBOL runtime. A colon-separated multi-directory value in `COB_FILE_PATH` failed with status 35 on that runtime. The field affects COBOL runtime file lookup. SQL datasource paths, COPY search and library search are separate settings. Folder discovery leaves runtime files in place.

## Debugging a project

Enable **Debug compilation** in **Preferences → Debugger** and rebuild. The compiler uses `-g -fsource-location -ftraceall -O0 -save-temps`. The builder retains generated C and headers in `debug_data/<source-relative-path-without-extension>/`. For `src/main.cbl`, look in `debug_data/src/main/`. These are compiler-generated companions to your COBOL program. COBGDB uses them to map stops to COBOL statements and interpret variables. Keep the executable, COBOL source and C/headers from the same successful build together. Rebuild if any generated files are missing or the executable was built separately.

Choose **COBOL → Debug executable** to open the installed COBGDB on the built executable and original source. A project executable requires Debug compilation and its retained C and header files. The IDE reports the expected directory when these are missing. **Preferences → Debugger → Open installed debugger** opens COBGDB for manual selection. With COBGDB, set a breakpoint, click Run, then enter program data in the native terminal. Graphical programs continue to use their own windows. Linux falls back to the debugger input and output panes if a desktop terminal is unavailable.

## Verification and release files

The offline Help is generated from the bundled documentation and this review. See the [release notes](RELEASE_NOTES_MODERN12.md) for changes, local verification and native test status. The [RPM guide](packaging/RPM_MODERN12.md) covers the matched Mageia 10 and Fedora 44 kits. The [Windows build guide](packaging/windows/README.md) covers the Windows 11 standalone executable and Inno Setup installer.
