# OpenCobolIDE 4.7.6 modern11.6

An unofficial maintained modern build of OpenCobolIDE, preserving its original authorship and GPL licensing while adding current Python/PyQt5 compatibility and a portable COBOL project workflow.

This consolidated modern11.6 includes the project1–project8 development packages and the subsequent copybook-creation work. The public-facing version is **4.7.6+modern11.6**, without a `+projectN` suffix. It is not a new upstream OpenCobolIDE release or a transfer of the original project's ownership.

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
| Compile Project / F8 | Batch compilation plus current-source compilation with existing dependency detection. |
| Automatic mode | Detects `-x` / `-m` for each source; PROCEDURE DIVISION USING selects a module. |
| Copybooks | New File offers .cpy/.CPY, blank templates and project copybooks-folder defaults; copybooks are not standalone build targets. |
| GixSQL | Detects SQL in sources/COPY dependencies and preprocesses only sources that need it. |
| Listings | Separate source listings with `--Xref -ftsymbols`, custom filenames and source-level overrides. |
| Diagnostics | Full compile/link output, runtime information, optional trace logging and retained shutdown fixes. |

Existing runtime-argument entry, source format directives, per-source compiler selection and offline Help are retained.

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

## Linux targets and RPM work

The Debian build is prepared and verified on Linux Mint. Mageia 10 and Fedora 44 RPMs must be built and tested on their respective persistent USB installations.

The tested Mageia build-script logic is retained with modern11.6 references. Fedora has a separate RPM setup. Build kits, logs, native RPMs and source RPMs are collected before returning to Mint for the planned GitHub push and release uploads. Neither RPM is represented as built/tested merely because a spec or kit exists.

See [the RPM plan](packaging/RPM_MODERN11.6.md). Other Fedora-based or RPM distributions require separate compatibility checks. Native Windows support for this new Bash-based project workflow has not been validated.

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
