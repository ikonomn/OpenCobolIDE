# modern11.6 consolidation review

Date: 26 October 2026. Status: local preparation; remote push and release uploads are deferred until Mageia 10 and Fedora 44 RPMs have been collected and reviewed back on Mint.

## Scope and evidence

This review covers the modern11.6 baseline, development iterations project1–project8 and the subsequent copybook work (internally called project9; no project9 Debian was built). It also checks carried-forward modern11.1–modern11.5 behavior against their release notes. The source, tests, historical verification reports, package resources and user demonstration project were reviewed.

The consolidated Debian/app label is `4.7.6+modern11.6`; development suffixes are removed from the current display version. Historical packages and records remain identifiable by their original names.

## Earlier modern line retained

| Version | Retained work |
| --- | --- |
| modern11.1 | Runtime argument popup, quoting, remembered arguments and source-install/shutdown corrections. |
| modern11.2 | Automatic listings, ordered operands, per-source extra flags and plain/SQL routing. |
| modern11.3 | Optional durable diagnostic trace for native-crash investigation. |
| modern11.4 | Deferred, idempotent application teardown after the Qt event loop. |
| modern11.5 | Source compiler/environment controls, path cleanup and source-format directives. |
| Initial modern11.6 | About runtime diagnostics using cobcrun --info / --runtime-config. |

These historical notes describe their own release state. Old instructions requiring a project-local build.sh or storing all project settings only in IDE preferences are superseded by the current internal-builder/portable-config workflow.

## modern11.6 development iterations

| Iteration | Main additions / corrections | Consolidated state |
| --- | --- | --- |
| project1 | Directory projects, project tree, batch compile, source mode/options forwarded to scripts. | Retained, with internal builder replacing local script selection. |
| project2 | Open Project on the opening screen and open discovered source files. | Retained. |
| project3 | PROCEDURE DIVISION USING selects module mode without requiring inline LINKAGE SECTION. | Retained; comments/literals and source format are considered. |
| project4 | Project defaults below source overrides. | Retained; persistence moved from preference-only records to project.json. |
| project5 | Restore listings and full build steps when IDE flags are supplied. | Retained, with accurate listing paths and explicit source overrides. |
| project6 | IDE-owned build.sh/SQL detector; ignore project scripts. | Retained. |
| project7 | New Project, folder scaffold, portable config, migration, Configure Project and validation. | Retained. |
| project8 | Close Project, safe switching, Save/Discard/Cancel, split/detached view cleanup. | Retained; prevents old source tabs mixing into the next project. |
| Subsequent copybook work | .cpy/.CPY in New File, empty template, default copybooks folder and COBOL editing. | Included in the consolidated build; copybooks remain excluded from standalone compilation. |

## Review findings resolved in this preparation

1. README incorrectly said the modern build added no major IDE features. It now describes the implemented project workflow and current platform scope.
2. Old Mageia instructions/spec were for modern11.5. The tested script logic is retained with modern11.6 references; Fedora 44 has a separate spec/build setup.
3. The reviewed user project contained old `src/bin` binaries and generated listings. The distributed demonstration includes source/configuration only, preserves the three original COBOL files, fixes source format explicitly and demonstrates a real worker flag override.
4. Final plain Debian version ordering differs from +projectN packages. Reinstall/downgrade commands are documented so the consolidated package actually replaces both test builds and earlier same-version packages.
5. The consolidated README, how-to and review are installed with the offline manual and source examples.
6. Source transfer kits carry a common committed source archive, source revision, target-specific spec/script and checksums. No RPM result is claimed before native builds/tests.

## Current behavior to keep

- Source → project → IDE precedence; relative source keys and local paths.
- Automatic -x/-m; no manual mode field in project.json.
- IDE internal script for project builds; F8 remains current-source compilation.
- Plain sources bypass GixSQL; SQL/COPY detection uses the configured include environment.
- `--Xref -ftsymbols`, verbose compile output and separate listings by default.
- Known-conflict validation before build; warnings acknowledged and existing errors repairable incrementally.
- Safe project close/switch, no disk deletion, unrelated standalone tabs preserved.
- Copybooks edited as COBOL, empty on creation, not separate program targets.

## Verification

The current full regression set passed 193 tests before consolidation. The final local verification record adds the shipped demonstration and RPM wrong-host guards and records the final count, extracted-package checks, archive/source matching and Debian metadata/checksum.

The user demonstration was independently validated, rebuilt and run from a fresh copy: test01 uses -x, worker uses -m, both listings include cross references, and the program prints HELLO from OpenCobolIDE modern11.6. Original project files were not modified.

## Limits and release gates

- Compile Project is deterministic batch compilation, not a new dependency-graph/multi-target linker system.
- Native Windows support for the new Bash project workflow is unverified.
- Mageia 10 and Fedora 44 must be tested on their respective persistent USB installations. A successful spec/source preparation is not a native RPM test.
- Actual desktop scrolling, tooltip timing and target shutdown behavior must be checked on the target desktop. Historical reports are not all certified fixed by headless tests.
- GixSQL runtime/database tests require a suitable installed GixSQL/database environment and are recorded separately from compile checks.
- Wider Fedora-derived/RPM compatibility is not inferred from one Fedora 44 package.
- The final package uses a previously used plain version string. Its checksum and consolidation date identify the new content; preserve the earlier artifact.

Return to Mint with both binary/source RPMs, exact specs, source revision, logs, checksums and desktop test notes before remote push and release uploads.
