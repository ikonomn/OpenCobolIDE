# OpenCobolIDE 4.7.6 modern12

An unofficial maintained modern build of OpenCobolIDE, preserving its original authorship and GPL licensing while adding current Python/PyQt5 compatibility and a portable COBOL project workflow.

This is the local **4.7.6+modern12** test build. See [modern12 changes and testing instructions](MODERN12.md). The following modern11.6 documentation describes the inherited features.

The consolidated modern11.6 included the project1–project8 development packages and the subsequent copybook-creation work. Its published version was **4.7.6+modern11.6**, without a `+projectN` suffix. It is not a new upstream OpenCobolIDE release or a transfer of the original project's ownership.

## Information and guides

- [How to use modern11.6](HOWTO_MODERN11.6.md): installation, projects, copybooks, settings, compilation, listings, runtime and troubleshooting.
- [Development review](REVIEW_MODERN11.6.md): changes from the earlier modern line and each modern11.6 project iteration, verification and remaining platform work.
- [Release notes](RELEASE_NOTES_MODERN11.6.md).
- [RPM build and USB collection plan](packaging/RPM_MODERN11.6.md).
- [Source installation](INSTALL_FROM_SOURCE.md).

## What is included

| Area | Behavior |
| --- | --- |
| New Project | Creates src, copybooks, bin, build, data and config folders without replacing existing contents. |
| Open / Configure Project | Opens recognized sources and reviews shared/default and per-source settings. |
| Close / Switch Project | Closes previous project documents safely; Save/Discard/Cancel protects unsaved edits. |
| Portable settings | `config/project.json` stores project defaults and relative per-source overrides. |
| Validation | Checks known flag, source-format, directory, compiler and output/listing conflicts before compilation. |
| Internal builder | Uses the IDE-owned builder; project-local build.sh files are ignored. |
| Compile Project / Rebuild Project | Ctrl+F8 compiles changed sources, including changed copybook dependents; Ctrl+Shift+F8 compiles everything. F8 keeps its current-file behavior. |
| Automatic mode | Detects `-x` / `-m` for each source; PROCEDURE DIVISION USING selects a module. |
| Copybooks | New File offers .cpy/.CPY, blank templates and project copybooks-folder defaults; copybooks are not standalone build targets. |
| GixSQL | Detects SQL in sources/COPY dependencies and preprocesses only sources that need it. |
| Listings | Separate source listings with `--Xref -ftsymbols`, custom filenames and source-level overrides. |
| Diagnostics | Full compile/link output, runtime information, optional trace logging and retained shutdown fixes. |

Existing runtime-argument entry, source format directives, per-source compiler selection and offline Help are retained.

## Runtime working directory and data search folders

The original default working directory for project executables is **`bin/`**, in both OpenCobolIDE and the independent debugger. An explicitly saved project working directory overrides it. Changing data search folders does not change the working directory or move any files.

The IDE field **Data search folders (one per line)** supplies directories for GnuCOBOL runtime data-file access. For example:

```text
MyProject/
├── bin/customers
├── data/customers.dat
├── config/
└── src/
```

For a COBOL declaration containing a bare filename:

```cobol
SELECT CUSTOMER-FILE ASSIGN TO "customers.dat".
```

entering this directory in the field:

```text
data
```

sets the launched program's environment to the equivalent of:

```text
COB_FILE_PATH=/absolute/path/MyProject/data
```

The program still runs from `MyProject/bin/`. Relative entries in this field are resolved against the **project root**, so `data` means `MyProject/data`, not `MyProject/bin/data`. Project-relative settings remain portable when the project is moved.

### Current limitation: use one directory

Although the field accepts one directory per line, the current implementation joins multiple entries with the platform path separator (`:` on Linux) into `COB_FILE_PATH`. **Do not currently use multiple entries with the tested GnuCOBOL 3.3-dev runtime.** A real file-open check succeeded with either single directory, but failed with status 35 when the two directories were joined with `:`. The current label therefore implies a multiple-directory search capability that is not working on this runtime.

Use a single existing directory, such as `data`, or leave the field empty. Multiple-directory handling still needs correction; accepting multiple lines in the interface is not proof that the runtime searches them. See the [GnuCOBOL runtime documentation](https://gnucobol.sourceforge.io/doc/gnucobol.html) for `COB_FILE_PATH`.

### Entry and save rules

- Enter directories, not individual filenames. Absolute paths are also accepted.
- Do not add shell quotes around a path containing spaces. Use literal paths, not shell variables or `~` shortcuts.
- Blank lines are ignored; accepted directories must already exist.
- Review the suggestions before accepting them. The scanner does not create or relocate runtime files.
- In Preferences, enable **Use these runtime folders for this project**, then choose **OK**. The standalone Review Project Folders dialog saves with **Save**. Cancel discards that dialog's unaccepted edits.
- An empty directory list does not set or clear `COB_FILE_PATH`; an inherited value may remain active.

Settings are stored in the project's `config/project.json`, for example:

```json
"runtime": {
  "accepted": true,
  "working_directory": "bin",
  "data_directories": ["data"]
}
```

OpenCobolIDE and the independent debugger read this same portable configuration. The debugger does not automatically scan or accept folder suggestions. Reopen the executable in an existing debugger session after changing its runtime settings.

### Different paths have different purposes

| Setting | Purpose |
| --- | --- |
| Working directory (`bin`) | Starting directory for relative runtime paths. |
| Data directory (`data`) | Supplies `COB_FILE_PATH` for COBOL runtime data-file access. |
| Compiler COPY paths | Locate copybooks during compilation; unrelated to this runtime field. |
| GixSQL paths | Locate the SQL preprocessor, SQL copybooks and libraries. |
| SQLite datasource URL | Selects the database file through the database driver; not controlled by `COB_FILE_PATH`. |

Keep explicit relative filenames consistent with the working directory; do not rely on this field to rewrite paths already containing directories. Absolute filenames identify their own location.

### GixSQL example

For the supplied `gixsql-example`, use working directory **`bin`** and leave data search folders empty unless the application needs additional COBOL data files. Its COBOL loader opens:

```text
../config/application-sqlite.conf
```

and that profile contains:

```text
sqlite://../build/application.db
```

Both paths are intended to resolve from `bin/`. Running from the project root instead can make the configuration-file open fail with status 35. Adding `config` or `build` to the data-search field is not the fix: restore the intended working directory. An inherited `DB_CONFIG_FILE` can separately override the profile chosen by the example program.

## Debian / Ubuntu-family installation

The package is:

```text
opencobolide_4.7.6+modern11.6_all.deb
```

For a first installation, close the IDE and run from the package directory:

```bash
sudo apt install ./opencobolide_4.7.6+modern11.6_all.deb
```

To replace an earlier modern11.6 package or a `+projectN` test package:

```bash
sudo apt install --reinstall --allow-downgrades ./opencobolide_4.7.6+modern11.6_all.deb
```

The plain version sorts before `+projectN` in Debian's version comparison. The flags above allow the intentional version-label consolidation and ensure an older package with the same plain version is replaced. Use the accompanying SHA-256 file to identify this consolidated build.

Python 3.8+, distribution PyQt5 and Pygments are package dependencies. GnuCOBOL is recommended by the package and is required to compile/run COBOL; it is not bundled. If using an existing source-built compiler, `--no-install-recommends` can avoid installing another compiler package.

Start with `opencobolide`. Open an existing project or create one. The updated Markdown files and offline HTML manual are installed under `/usr/share/doc/opencobolide/`.

## Included demonstration project

A clean main-program/module/shared-copybook example is supplied at:

```text
/usr/share/doc/opencobolide/examples/project-demo
```

Copy it to a fresh writable folder, then choose **Open Project**:

```bash
cp -a /usr/share/doc/opencobolide/examples/project-demo "$HOME/OpenCobolIDE-demo"
```

The example compiles `test01` and `worker.so`, uses `copybooks/copybook.cpy`, demonstrates a source-specific flag override, and produces separate cross-reference listings. It includes no precompiled binaries or old listings.

See [the modern12 IDE and Help review](MODERN12.md) and [release notes](RELEASE_NOTES_MODERN12.md).

## Linux targets and Windows release packages

Current modern12 RPM definitions and matched two-application transfer kits target **Mageia 10** and **Fedora 44**. The original modern11.6 files remain historical. The native RPM builds/install/desktop tests are pending; a kit is not a tested RPM release. See [modern12 packaging instructions](packaging/RPM_MODERN12.md).

Planned application versions are **OpenCobolIDE 4.7.6 modern12** and **independent debugger 0.1.0**. Windows deliverables will include a standalone `.exe` and an **Inno Setup `.exe` installer** for each application, built and tested on Windows separately. Publication is not authorized by preparing packaging files.

## Source installation and verification

Use the supplied consolidated source archive or the local `modern11.6` checkout:

```bash
./scripts/install_from_source.sh
./.venv/bin/opencobolide
```

The GitHub publication is a later step; an older published branch should not be assumed to contain these local changes.

The current regression set covers project creation/migration/relocation, safe closing/switching, copybooks, executable/module compilation, GixSQL routing, listings, syntax checking, F8/run behavior, arguments, help and source installation. Exact release test results and package checks are recorded alongside the release assets.

## Attribution and licence

OpenCobolIDE retains its original authors, Colin Duquesnoy's original project attribution, bundled component notices and GPL licence. See [AUTHORS.rst](AUTHORS.rst) and [LICENSE](LICENSE).

Modern compatibility, project-workflow, packaging and verification work was developed with assistance from OpenAI Codex. This is an unofficial community-maintained modern build, provided under the existing licence without a warranty of suitability for every platform.

Project compilation and the complete keyboard shortcut table are explained in [the How-to guide](HOWTO_MODERN11.6.md#18-keyboard-shortcuts).
