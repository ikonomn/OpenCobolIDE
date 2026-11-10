# OpenCobolIDE 4.7.6 modern12

Modern12 is the continuation of the archived 4.7.6 IDE. The version shown in About identifies the modern release. The application retains the Qt editor and the original COBOL editing workflow. It adds portable projects, a project compiler and a connection to the independent COBOL Debugger debugger.

## Workspace and Help

The home page opens files and projects. The editor contains COBOL highlighting, completion, outline, fixed/free source format detection, per-file settings and syntax diagnostics. The file tree follows the active project. Issues, compiler output and program output appear in the lower panes. The View menu controls the panes and editor layout. The Help menu opens the offline modern12 manual with the original editing topics and the cumulative changes since 4.7.6. Use Help → About to check versions and runtime diagnostics. The offline layout-recovery guide describes resetting window preferences if docks become unusable.

The modern branch updates compatibility with Python 3 and PyQt5, uses maintained Pygments and avoids the obsolete bundled future/Pygments dependencies. It includes virtual-environment source installation, Linux launcher support, optional diagnostic trace logging and safer console/editor shutdown. The diagnostic tools report the actual GnuCOBOL runtime and build output. Native RPM packaging retains distribution-specific Python and Qt dependencies.

## Improvements since archived 4.7.6

- Early modern releases moved the IDE and packages to modern Python and Qt while retaining the original project attribution. They fixed syntax highlighter compatibility, file opening and GnuCOBOL standard selection.
- The modern9 through modern11 updates added offline Help, layout recovery, optional project build scripts, the GixSQL example, source installation and the per-file program arguments dialog.
- Modern11.1 through modern11.5 added lifecycle and crash tracing fixes, ordered compiler flags, SQL-only preprocessing, executable/module mode detection, per-source build settings, fixed/free format directives and improved runtime and compiler diagnostics.
- Modern11.6 added portable projects, safe project switching, copybook creation and editing, internal project builds, COPY dependency tracking, incremental compilation, rebuild shortcuts and target-specific RPM recipes.
- Modern12 added runtime discovery and review, retained C/header files, distinct Preferences pages, menu icons, direct COBOL Debugger launch, a consistent bin runtime default and the current debug folder prerequisite. The debugger can use the system terminal while the program's graphical windows stay interactive.

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

Existing projects do not require `bin/`. When opening a project without it, the IDE looks for COBOL executables and libraries in the existing tree, saves their output folders in `config/project.json`, and asks you to choose if several locations match. With no outputs yet, the project root is used. Builds, incremental checks and executable launching use the selected folders. An older accepted runtime default of `bin` falls back to the detected executable folder if `bin/` is missing; other explicit runtime folders remain unchanged. Opening creates only a missing `debug_data/` folder (plus portable configuration if needed), and displays a message explaining that C/header files appear after a successful debug build. Compilation may also create its intermediate `build/` directory.

New Project creates these folders. Open Project creates a missing `debug_data/` and opens recognized sources. Copybooks can be created and edited as COBOL files. They participate in builds through COPY dependencies. Generated output and hidden directories are excluded from source discovery. Close Project and switching projects protect unsaved edits with Save, Discard and Cancel.

## Settings and builds

Open **Preferences → Compiler** for IDE defaults and project or source compiler options. The IDE resolves global defaults, project defaults and per-source overrides in that order. Configure Project provides a source overview and validates settings. Relative project paths travel with the project. Legacy options are migrated when opening a project without portable settings. The independent debugger reads the saved project JSON for its own builds.

**F8** compiles the current source. **Ctrl+F8** compiles changed project sources and affected COPY dependents. **Ctrl+Shift+F8** rebuilds the project. The IDE-owned builder selects executable or module mode from the COBOL source and saves listings in `build/` by default. Cross-references and symbol tables are available using the listing settings. Build diagnostics identify compiler and linker failures. Plain COBOL takes the direct compiler path. Sources using embedded SQL use GixSQL preprocessing and linking. Configure the preprocessor, SQL copybooks and libraries in **Preferences → GixSQL**. The IDE project builder currently uses Bash and Python.

Run prompts for program arguments and remembers them per file. The IDE supports embedded and external program terminals.

## Runtime files

Use **Preferences → Projects** or **File → Rescan Project Folders** (Ctrl+Alt+D) to review suggestions from SELECT and ASSIGN declarations. Review missing, ambiguous and dynamic assignments yourself. Accept settings to save them. Project launches default to `bin/`. An explicit project working directory takes precedence. For the GixSQL example, `../config/application-sqlite.conf` and `sqlite://../build/application.db` resolve from `bin/`.

The data search field accepts one directory per line, with project-relative paths resolved from the project root. Use a single directory with the tested GnuCOBOL runtime. A colon-separated multi-directory value in `COB_FILE_PATH` failed with status 35 on that runtime. The field affects COBOL runtime file lookup. SQL datasource paths, COPY search and library search are separate settings. Folder discovery leaves runtime files in place.

## Debugging a project

Enable **Compile with debug** in **Preferences → Compiler → Project compiler settings**. The checkbox shares the existing project debug setting with Preferences → Debugger and Review Project Folders. OK saves it; Cancel leaves the project unchanged. The next project build recompiles affected sources when this setting changes; Rebuild Project forces a complete rebuild. The compiler adds `-g -fsource-location -ftraceall -O0 -save-temps` by default. Matching debug switches are used once. Explicit optimization such as `-O2` is preserved instead of adding `-O0`; optimized debugging can make stepping and variable inspection less predictable. The dialog previews the debug options without rewriting extra compiler flags. With `-O0`, hardened toolchains such as Mageia may warn that `_FORTIFY_SOURCE` requires optimization. Compiler warnings remain visible; the IDE does not disable hardening or silently change optimization. Explicit extra debug flags remain active even when the checkbox is off. The builder retains generated C and headers in `debug_data/<source-relative-path-without-extension>/`. For `src/main.cbl`, look in `debug_data/src/main/`. These are compiler-generated companions to your COBOL program. COBOL Debugger uses them to map stops to COBOL statements and interpret variables. Keep the executable, COBOL source and C/headers from the same successful build together. Rebuild if any generated files are missing or the executable was built separately.

Choose **COBOL → Debug executable** to open the installed COBOL Debugger on the built executable and original source. A project executable requires Debug compilation and its retained C and header files. The IDE reports the expected directory when these are missing. **Preferences → Debugger → Open installed debugger** opens COBOL Debugger for manual selection. With COBOL Debugger, set a breakpoint, click Run, then read program output in COBOL Debugger’s Program output pane. On Linux, enter values in the debugger input box and click Send input. Graphical programs use their own windows.

## Verification and release files

The offline Help is generated from the bundled documentation and this review. See the [release notes](RELEASE_NOTES_MODERN12.md) for changes, local verification and native test status. The [RPM guide](packaging/RPM_MODERN12.md) covers the matched Mageia 10 and Fedora 44 kits. The [Windows build guide](packaging/windows/README.md) covers the Windows 11 standalone executable and Inno Setup installer.


## COBOL callers with C helpers

Project builds detect literal `CALL "function"` and `CALL STATIC "function"` statements and look for a matching C function definition in the project. Matched C files are linked into that caller's output automatically. Generated build/debug folders, hidden folders and virtual environments are excluded. If several C files define a function, select the helper explicitly instead of letting the IDE guess. Dynamic calls, macro-generated C definitions, calls inside COPY books and arbitrary external-library dependencies need explicit settings.

The **caller COBOL filename** determines the output: `score.cob` produces `score` on Linux or `score.exe` on Windows, even when its PROGRAM-ID is `gui-score` and the helper is `score_window.c`. Existing project output-folder settings are respected. In **Preferences → Compiler → File compiler settings**, **Executable name (optional)** overrides the output filename for that caller. Build, successful-output messages, Run, Debug and incremental checks all use that saved name; folders and drive names are not allowed in this field.

The default helper detection is enabled for every project. Uncheck **Detect C helpers from literal COBOL CALLs** to enter **Manual C helper sources**, with one project-relative C filename per line. An empty manual list disables helpers for the caller. Use the existing **Libraries** and **Extra compiler flags** fields for other dependencies. **Preview proposed C build command** shows the current caller, output name, helpers and libraries before saving. The actual builder also adds listing/diagnostic and retained-debug-source options and logs its complete command. These controls save with OK; Cancel leaves settings unchanged.

Supported automatic library mappings are deliberately limited: helpers including `X11/...` headers add `-lX11` on Linux; helpers using `MessageBox`, `MessageBoxA` or `MessageBoxW` add `-luser32` on Windows. Already supplied libraries are not added again. X11 development headers/libraries or the matching Windows toolchain must already be installed. No dependencies are installed automatically. The compiler remains authoritative for conditional C code, unsupported libraries and missing symbols.

For the bundled [C GUI example](examples/common/gui/README.md), open the folder as a project. The source declares Free format. The essential Linux command is:

```bash
cobc -free -x -o score score.cob score_window.c -lX11
```

With an executable-name override of `gui-score`, the command uses `-o gui-score`. On Windows it uses the `.exe` suffix and `-luser32`. Enable **Compile with debug** to retain the generated COBOL C/header companions under `debug_data/`. C helper and locally quoted header changes participate in incremental rebuild checks. The same caller-to-helper association is recomputed for each build; manual choices and name overrides are portable in `config/project.json`:

```json
"sources": {
  "score.cob": {
    "output_name": "gui-score",
    "c_sources": ["score_window.c"],
    "libraries": []
  }
}
```

Omit `c_sources` or set it to null for automatic matching. These are IDE project-build features; independent COBOL Debugger rebuild support for these additional settings has not been added in this change. Debug an IDE-built executable with its matching retained sources.

## Building GTK3 and GTK4 programs

For a COBOL source that calls GTK directly, OpenCobolIDE looks for literal calls specific to one GTK version. For example, `gtk_main` and `gtk_widget_show_all` select GTK3. Calls such as `gtk_window_set_child` and `gtk_box_append` select GTK4. The IDE queries the selected package with `pkg-config --libs` and adds GnuCOBOL's `--static` to the compile command. The proposed command preview shows the resolved flags.

If the source only uses calls shared by both versions, uses dynamic call names, or contains conflicting version clues, specify the library under **Preferences → Compiler → File compiler settings → Extra compiler flags**. Explicit GTK library settings take precedence over detection. Use the expression for the version you want:

| GTK version | Extra compiler flags |
| --- | --- |
| GTK3 | `$(pkg-config --libs gtk+-3.0)` |
| GTK4 | `$(pkg-config --libs gtk4)` |

The IDE also accepts backticks, for example `` `pkg-config --libs gtk4` ``. It resolves these queries at build time using the configured tools environment. Install `pkg-config` and the development files for the selected package in that environment. For C headers as well as libraries, use `$(pkg-config --cflags --libs gtk4)`. Queries can include multiple packages, version requirements, and options such as `--static` or `--libs-only-l`. GnuCOBOL's `--static` controls call generation, while `pkg-config --static` asks for additional link dependencies.

If the program calls `gtk_builder_new_from_file` with a relative `.ui` filename, the file must be available in the application's working directory when it runs. To embed it, compile and link a GLib GResource and load it with `gtk_builder_new_from_resource`.

## Common examples

Open **Help → Open examples folder** to find the same five projects shipped with
COBOL Debugger. The [examples index](examples/common/README.md) links to each
build and debugging guide. Open an example folder as a project to use its
saved compiler and runtime settings.

The IDE ships the source snapshot in `examples/common/`. When updating the
snapshot, copy the files listed in COBOL Debugger's `scripts/example-files.txt`
from its `examples/` directory into `examples/common/`. Keep generated output
out of the templates. The older IDE examples remain available in the source tree.
