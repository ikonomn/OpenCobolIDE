# OpenCobolIDE 4.7.6+modern11.6 — consolidated modern build

Prepared 26 October 2026. This consolidates the project development iterations under the plain modern11.6 version; original upstream authorship and licence are retained.

## Projects

- New Project wizard and standard src/copybooks/bin/build/data/config folders.
- Open Project on the opening screen; recursive source discovery and rooted tree.
- Configure Project with shared defaults, per-source overrides and diagnostics.
- Portable config/project.json; relative paths, one-time migration and atomic writes.
- Close Project and safe switching with Save/Discard/Cancel, failed-save protection and split/detached view cleanup.

## Builds and source files

- Internal IDE-owned project builder, independent of project-local build.sh.
- Compile Project (Ctrl+F8) builds changed sources and changed-copybook dependents; Rebuild Project (Ctrl+Shift+F8) forces all sources. F8 remains current-source compilation.
- Keyboard shortcuts for modern project/settings/support actions, with an in-app shortcut list.
- Automatic executable/module detection from PROCEDURE DIVISION USING.
- Plain/GixSQL routing through source and COPY dependency inspection.
- Default/custom source listings, `--Xref -ftsymbols` and full compile/link output.
- New File .cpy/.CPY choices, empty copybooks, project folder defaults and COBOL editing; copybooks are not standalone compile/run targets.
- Compiler/path/format/artifact conflict checks and cross-reference-safe syntax checking.

The earlier modern runtime arguments, source directives, environment settings, optional trace, shutdown corrections and runtime diagnostics remain included.

## Documentation and example

The package includes an updated README, HOWTO_MODERN11.6.md, REVIEW_MODERN11.6.md, offline HTML manual and a portable main/module/shared-copybook demonstration derived from the reviewed user project. Generated demo binaries/listings are excluded.

## Installing over test builds

```bash
sudo apt install --reinstall --allow-downgrades ./opencobolide_4.7.6+modern11.6_all.deb
```

The plain version sorts earlier than +projectN. Reinstall also ensures a previous package with the same plain version is replaced. Check the accompanying SHA-256 checksum.

## Platform and publication state

The Debian package is prepared/verified on Mint. Mageia 10 and Fedora 44 RPM kits use the same committed source; their native builds and desktop tests are pending on the persistent USB installations. GitHub push and release uploads are deferred until both RPM results are collected and reviewed back on Mint. Windows and other RPM distributions are not newly certified by this build.

See README.md, HOWTO_MODERN11.6.md, REVIEW_MODERN11.6.md and packaging/RPM_MODERN11.6.md for details.
