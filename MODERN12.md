# OpenCobolIDE modern12 — local test build

This local development version builds on modern11.6. It has not been pushed or published.

## Project runtime folders

When you create or open a project through Open Project, the IDE opens **Review Project Folders** if no runtime settings have been accepted. You can also choose **File → Rescan Project Folders** (**Ctrl+Alt+D**) or **Configure Project → Runtime folders / debug**.

The scan reads COBOL sources and copybooks inside the project tree. It looks for SELECT/ASSIGN declarations, matches literal file names against existing project files and suggests descriptive folders such as data, files, input, output, datasets, records and reports. Generated, hidden and symbolic-link folders are excluded. The table identifies exact matches, ambiguous matches, missing/output files and dynamic assignments. Folder names alone are suggestions, not proof of a file's purpose.

Review the table, choose a working directory and enter data search directories, one per line. **Save** accepts the settings for this project. **Cancel** leaves the configuration untouched. Rescanning replaces the displayed suggestions only; it does not save them automatically. Runtime files are never moved or created by the scan.

Accepted settings are stored in `config/project.json`, separately from compiler settings:

```json
"runtime": {
  "accepted": true,
  "working_directory": ".",
  "data_directories": ["data", "input"]
},
"debug": {"enabled": true}
```

Paths within the project are relative to its root so they survive moving the project. When running, the accepted working directory overrides the global working directory for this project only. Data directories set the program's GnuCOBOL `COB_FILE_PATH` environment variable. Embedded and external terminals use the same settings. Existing runtime variables are preserved except an explicitly accepted data search path replaces `COB_FILE_PATH`. A missing accepted folder is reported before launching; use Rescan to correct it.

For `ASSIGN TO "customers.dat"`, a matching `data/customers.dat` suggests data as the working directory/search folder. For `ASSIGN TO "data/customers.dat"`, the project root is suggested as the working directory. Multiple candidates are displayed for review. Explicit paths, runtime configuration and assignments computed by the application can affect GnuCOBOL file resolution; the scanner cannot infer arbitrary program logic. It inventories declarations in copybooks, including those not currently used by a source; it is not a complete COBOL parser and does not expand COPY REPLACING or external copybooks. Check the proposals against your program.

## Debug compilation

In the same review window, enable **Debug compilation** and Save. This applies to project sources built by the internal builder, including F8. It adds:

```text
-g -fsource-location -ftraceall -O0 -save-temps
```

Automatic `-x`/`-m`, effective compiler settings, listing options, COPY search paths and SQL-only GixSQL preprocessing remain in use. Debug compilation is off for existing projects until explicitly enabled.

Outputs are separated:

- `bin/`: executable programs and modules.
- `build/`: listings, preprocessed SQL COBOL, build history and temporary compilation workspace.
- `debug_data/<source-relative-path-without-extension>/`: generated **`.c` and `.h` files only**. For `src/main.cbl`, this is `debug_data/src/main/`.

The temporary workspace is removed on success or failure. Debug information maps its temporary C compilation directory to the retained C/header directory through the GCC/Clang debug prefix map option. The source-specific retained C/header set is replaced only after successful compilation. On failure older files may remain, but the build is marked unsuccessful; do not debug a failed build. Keep the executable, original COBOL source and retained files from the same successful build together.

**Compile Project (Ctrl+F8) still means compile changed files**, including COPY dependencies. Changing debug compilation mode or deleting a retained debug header/source triggers recompilation. **Rebuild Project (Ctrl+Shift+F8)** compiles everything. F8 still compiles the current source with its detected mode.

This version prepares artifacts for our independent Python debugger. The Preferences/menu update below adds external launch through COBOL → Debug executable; the debugger remains a separate application. Standalone sources outside projects retain their previous compilation behavior.

## Install the local Debian test package

```bash
sudo apt install ./opencobolide_4.7.6+modern12_all.deb
```

Restart OpenCobolIDE after installation. Confirm modern12 in the title/About window. This replaces the installed IDE package; project data and user preferences remain in their existing locations.

## Verification

Focused tests cover matching/ambiguous/missing/dynamic assignments, comment and literal handling, source format directives, portable accepted paths, missing runtime directories, invalid configuration, review cancellation/acceptance, real executable and module debug builds, compiler failure propagation, generated artifact cleanup and incremental rebuilds after debug mode/header changes. Existing project, compiler, SQL detection, diagnostic severity, shortcut and lifecycle suites are also run for regression coverage. See the local build report for actual results; Windows and native Fedora/Mageia execution are not validated by this Mint package.


## Preferences consolidation — first increment (4 November 2026)

Preferences now includes **Projects** and **Debugger**, and the existing SQL tab is named **SQL / GixSQL**. Existing saved tab indices remain valid. Open a project to enable project controls.

Projects embeds the existing runtime discovery table, working directory, data search folders and rescan action. Check **Use these runtime folders for this project** to accept the reviewed directories. Unchecking it restores the global runtime fallback while preserving the configured folders. Opening Preferences and clicking OK does not accept unreviewed suggestions. Debugger contains the existing debug-compilation toggle with the same flags and retained `debug_data/` artifacts.

Runtime/debug edits are drafts until Preferences **OK**; **Cancel** discards them. Invalid accepted directories keep Preferences open with an error. **Reset** reloads the current page; **Restore Defaults** disables project runtime overrides or debug compilation on the corresponding page without writing until OK. Runtime and debug settings retain their existing separate JSON sections.

The SQL / GixSQL page opens the existing project compiler/GixSQL defaults dialog. Projects provides access to project defaults, source overrides and validation through Configure Project. These child dialogs keep their own save behavior: their OK/Save writes independently of Preferences Cancel. This first increment embeds runtime/debug controls; it does not yet migrate every compiler/source editor into a single transaction.

The standalone Review Project Folders action remains available and shares its runtime controls with Preferences. Repeated Compiler Reset no longer duplicates COPY or library search paths. No configuration schema migration is required. The builder and debugger launch integration are unchanged.


## Compiler, GixSQL and debugger entry points — 4 November 2026

**Project compiler settings** and **Compiler options for this file** are removed from the COBOL menu. Use **Preferences → Compiler → Project compiler settings… / File compiler settings…**. The file button edits the saved file selected when Preferences opened; it is disabled when no saved file is selected. Project settings require an open project. Existing project/source inheritance, validation and configuration are preserved. These child dialogs save with their own OK. Their accepted changes are independent of Preferences Cancel. The existing Ctrl+Alt+B / Ctrl+Alt+S shortcuts now open Preferences on Compiler.

**Preferences → GixSQL** is a separate tab from legacy **SQL COBOL** (dbpre/esqlOC). It edits the project's preprocessor, copybook and library directories. Blank fields inherit defaults. File overrides remain available through the file compiler dialog. GixSQL edits are validated and saved with Preferences OK; Cancel discards them. Reset reloads saved paths; Restore Defaults stages clearing the project overrides. Relative project paths remain portable, and unrelated compiler/source configuration is preserved. Project defaults must be enabled for their paths to apply.

**COBOL → Debug executable…** opens our independent Python frontend externally on the current executable and COBOL source. It is enabled for an executable source whose binary exists, and disabled for modules, copybooks and during compilation. Build first; enable debug compilation and rebuild to obtain matching executable/source/debug_data artifacts. Launching does not compile or run the target program automatically.

In **Preferences → Debugger**, configure the folder containing `cobgdb_python` (default `~/cobgdb-python`) and its Python interpreter (default the IDE interpreter). The frontend requires Python 3.10+, PyQt5 and GDB. The IDE adapter uses the existing frontend launch interface because the frontend currently has no executable CLI option. The debugger repository and its independent compiler/engine are unchanged. Accepted project runtime directories, data search paths and compiler/runtime environment are passed to the external process. Missing binaries, frontend folders, interpreters or accepted runtime directories are reported without launching.

Use the new local test package `opencobolide_4.7.6+modern12+prefs2_all.deb` for these menu/GixSQL/debugger changes; the earlier prefs1 package contains only the first Preferences increment.


## Installed debugger launcher — 4 November 2026

The IDE now calls the installed **cobgdb-python-gui** command directly. Configure its executable path/name under Preferences → Debugger; the default is `cobgdb-python-gui` on PATH. A source checkout and a separate Python setting are no longer needed. Older debugger-folder/interpreter preference values are retained in storage but are not used by this launcher.

- **Open installed debugger…** in Preferences → Debugger calls it without arguments for manual selection, including when no project is open.
- **COBOL → Debug executable…** calls `cobgdb-python-gui /path/to/binary --source /path/to/source.cbl`, preserving accepted project runtime cwd/environment.
- The debugger itself also accepts `cobgdb-python-gui /path/to/binary` without a source argument and resolves the source/project using its independent reader. Loading never runs the target automatically.

Install the updated **cobgdb-python 0.1.0-2** package together with **opencobolide 4.7.6+modern12+prefs3**. The older debugger package does not implement the optional executable argument. The IDE-side Python adapter from prefs2 is no longer used or shipped. The independent debugger engine/compiler remain unchanged.


## Preferences and menu icons — 4 November 2026

Projects, Debugger and GixSQL Preferences tabs now show icons before their names. New project workflow, compile/rebuild, debugger, automatic listing and keyboard-shortcut menu entries use matching icons. Related Preferences buttons and import/export preferences actions also have icons. Theme icons have bundled resource fallbacks, and menu icons are explicitly enabled for these actions. This visual update does not change configuration or launch behavior. The updated IDE package is `opencobolide_4.7.6+modern12+prefs4_all.deb`; the debugger package remains `cobgdb-python_0.1.0-2_all.deb`.


## Project runtime default — bin (4 November 2026)

For all projects, the default runtime working directory is the project’s **bin/** folder, in both the IDE and independent debugger. This applies when runtime settings are absent/unaccepted or an accepted runtime section omits working_directory. An explicitly saved project working directory still overrides the default. Standalone IDE files retain their global working-directory behavior.

Review Project Folders and Preferences now begin with bin as the working-directory selection, even when discovery finds data/config folders. Discovery still inventories files and suggests data search paths; it does not change the bin default automatically. Restore Defaults returns to bin. Nothing moves existing runtime files or databases.

The default can be resolved before the first build; compilation creates its output folder. For programs using ../config or ../build, those paths now resolve from bin. A project with a deliberately different runtime layout can retain or set an explicit override.

Updated packages: opencobolide_4.7.6+modern12+prefs5_all.deb and cobgdb-python_0.1.0-4_all.deb. Install both for the system-installed applications to use this default.
