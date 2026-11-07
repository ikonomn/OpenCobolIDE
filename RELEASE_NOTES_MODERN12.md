# OpenCobolIDE 4.7.6 modern12 release notes

## Changes since the archived 4.7.6 release

- Updated Python and Qt compatibility, maintained Pygments, source installation, and Linux launchers.
- Added portable projects with settings migration, per-source overrides, validation, COPY-aware incremental builds, GixSQL preprocessing and listings.
- Added project switching with unsaved-edit protection, copybook editing, fixed/free format detection, persistent program arguments and improved diagnostics.
- Consolidated Compiler, Projects, Debugger and GixSQL preferences. Added project runtime review and preserved bin as the default runtime working directory.
- Made debug_data a project folder and made the IDE explain the generated C/header prerequisites when starting COBGDB. Debug builds retain those files by source under debug_data.
- Added direct COBGDB launch with or without a selected program. The independent debugger uses its Program output pane and embedded Linux input controls.
- Rebuilt offline Help from the bundled manual and the full modern12 structure and workflow review.

## Target builds

| Target | Planned deliverables | Status |
| --- | --- | --- |
| Fedora 44 | 4.7.6-12.2.fc44 binary and source RPMs | Native build and desktop verification pending |
| Mageia 10 | 4.7.6-12.2.mga10 binary and source RPMs | Native build and desktop verification pending |
| Windows 11 x64 | opencobolide.exe and Inno Setup installer | Native build and installer verification pending |

See [the IDE review](MODERN12.md), [RPM guide](packaging/RPM_MODERN12.md) and [Windows build instructions](packaging/windows/README.md). On the tested GnuCOBOL runtime, use one data search directory. The current multi-directory COB_FILE_PATH handling remains limited.


## Release files

Keep the exact committed build source in the dedicated `opencobolide-4.7.6-modern12.tar.gz` archive, following the modern11.6 release layout. Record its commit ID and checksum alongside the release files.

Build and verify Windows 11 separately. Its release downloads are the standalone executable and Inno Setup installer. Use the source archive for the Windows build instructions and recipes. Keep the Fedora and Mageia transfer kits and native build logs with the internal build records.
