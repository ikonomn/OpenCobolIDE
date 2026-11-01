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

This version prepares artifacts for our independent Python debugger. It does not yet add a debugger launch action or integrate that backend into the IDE. The debugger may need explicit search paths to the retained files. Standalone sources outside projects retain their previous compilation behavior.

## Install the local Debian test package

```bash
sudo apt install ./opencobolide_4.7.6+modern12_all.deb
```

Restart OpenCobolIDE after installation. Confirm modern12 in the title/About window. This replaces the installed IDE package; project data and user preferences remain in their existing locations.

## Verification

Focused tests cover matching/ambiguous/missing/dynamic assignments, comment and literal handling, source format directives, portable accepted paths, missing runtime directories, invalid configuration, review cancellation/acceptance, real executable and module debug builds, compiler failure propagation, generated artifact cleanup and incremental rebuilds after debug mode/header changes. Existing project, compiler, SQL detection, diagnostic severity, shortcut and lifecycle suites are also run for regression coverage. See the local build report for actual results; Windows and native Fedora/Mageia execution are not validated by this Mint package.
