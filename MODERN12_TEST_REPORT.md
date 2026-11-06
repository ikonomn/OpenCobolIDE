# modern12 local verification — 2026-11-01

Local development branch: `modern12`, based on `modern11.6`. Nothing pushed or published.

- Relevant full regression suite: **247 passed, 2 skipped**, 52.24 seconds.
- Final focused modern12/shortcut suite after UI and format refinements: **14 passed**, 6.86 seconds.
- The two skips require a separately supplied GnuCOBOL 3.2 compiler, unavailable in this session. These results use the installed GnuCOBOL 3.3-dev compiler; they do not claim fresh 3.2 verification.
- Real debug compilation succeeded in executable and module modes; failed compilation returned nonzero and removed the temporary workspace.
- Retained debug artifacts were only `.c` and `.h`, with listings in build and executable/module in bin.
- Incremental checks covered debug mode changes and removed retained headers.
- A real program successfully read a file through the accepted project's data search path.
- Real GixSQL preprocessing and debug compilation succeeded using the bundled database example and its copybooks. No database connection test was performed.
- GDB's source inventory referred to retained debug_data paths, with no deleted `.debug-*` compilation directory.
- Review dialog was rendered and visually inspected. Cancellation, acceptance and runtime configuration validation were tested.
- Existing single-file, project lifecycle, automatic mode, SQL detection, diagnostic severity and shortcut checks passed.

Package: `dist/opencobolide_4.7.6+modern12_all.deb`, architecture `all`, version `4.7.6+modern12`.

SHA256:

```text
0b8134ea29a313c431ecda82930cb650472359bbf6718997d3fc9849f29ba37b  opencobolide_4.7.6+modern12_all.deb
```

The package was extracted and all **241 shipped Python/shell files** compared with local source. The modern12 guide is included. The private release handoff is excluded. The package was not installed on the user's system. Windows and native Fedora/Mageia tests remain outside this local Mint verification. Our independent debugger is not integrated by this change.


## Preferences increment — 2026-11-04

- Fresh relevant regression run: **183 passed, 2 skipped**, 30.09 seconds, including the initial 10 new Preferences tests.
- Final dedicated Preferences run after two additional persistence checks: **12 passed**, 2.15 seconds. This overlaps the regression run; totals are not additive.
- Tested runtime/debug draft cancellation and acceptance, portable paths, explicit acceptance of suggestions, invalid-directory rejection, page-scoped Reset/Restore Defaults, duplicate-path prevention, independent-save preservation, existing GixSQL controller routing, no-project behavior, compiler-check Apply isolation, and disabling runtime overrides without losing folders/debug settings.
- Broader coverage included modern12, shortcuts, portable projects, settings/lifecycle, discovery, incremental builds, build script, compiler workflow/flag order/output, native/runtime diagnostics and source format.
- Tests used the repository virtual environment, offscreen Qt and isolated settings/cache directories under `/tmp`. An initial new-test fixture leak was corrected before the successful combined run.
- Projects and Debugger pages were rendered and visually inspected. `git diff --check` passed.
- Changes remain local and uncommitted on modern12; HEAD remains `a7bd7dc`. Existing untracked files were preserved. No package was rebuilt or installed, and nothing was pushed/published. The package and checksum above describe the November 1 baseline, not this increment.
- Native Python builder, profiles, system COPY tracking, and external debugger launch remain pending.


## Menu, GixSQL and executable-debugger update — 2026-11-04

- Relevant regression suite: **194 passed, 2 skipped**, 39.81 seconds.
- Final Preferences/debugger suite after tightening debugger preference persistence: **22 passed**, 4.23 seconds. These runs overlap; totals are not additive.
- Project/file compiler actions are absent from the COBOL menu. Preferences Compiler buttons use the existing editors; Ctrl+Alt+B / Ctrl+Alt+S route to that page.
- Separate GixSQL page tested for portable project paths, preservation of unrelated settings, Reset/defaults/cancel and failed validation without partial runtime saves.
- Debugger tests cover executable-only availability, module/copybook exclusion, shell-free launch arguments, runtime cwd/COB_FILE_PATH, missing binary/frontend errors, and the frontend's independent project-plan adapter.
- Real offscreen integration check used a read-only copy of the existing independent frontend and loaded the Easter executable and COBOL source through GDB. It did not run the target or change the debugger repository/engine.
- Final Compiler, GixSQL and Debugger pages rendered for visual inspection. `git diff --check` passed.
- Debugger installation is external. Configure its folder/Python in Preferences → Debugger; Python 3.10+, PyQt5 and GDB are required by that application.
- Updated local test package is `opencobolide_4.7.6+modern12+prefs2_all.deb`. The earlier package/checksum remains the historical November 1 baseline.


## Direct installed debugger launcher — 2026-11-04

- IDE calls cobgdb-python-gui directly, either without a target from Preferences or with executable/--source from Debug executable. The IDE-side adapter is removed. Legacy source-folder/interpreter values remain stored but unused.
- Independent debugger GUI adds optional executable and --source CLI arguments; no-argument startup is preserved. Engine/compiler are unchanged.
- Debugger regression suite: **37 passed**, 23.345 seconds. Relevant IDE suite: **53 passed**, 30.14 seconds. Final focused IDE suite after the no-target entry: **23 passed**, 4.61 seconds (overlapping coverage).
- Real extracted-package checks passed for no argument, executable only, and executable plus --source; binary loads were verified through GDB without running the target. Packaged --help and Python syntax were verified.
- Packages: cobgdb-python_0.1.0-2_all.deb and opencobolide_4.7.6+modern12+prefs3_all.deb. All 14 debugger and 241 IDE Python/shell files matched current source. Neither package was installed; both updates must be installed to replace the older no-CLI debugger behavior.
- Existing untracked files preserved. Nothing pushed or published. `git diff --check` passed.


## Preferences/menu icon update — 2026-11-04

- Existing Preferences/shortcut regressions: **22 passed**, 4.69 seconds. No new tests added for this visual-only change.
- Projects, Debugger and GixSQL tab icons and ten project/build/debug/listing/shortcut menu icons were checked for non-null icons and explicit menu visibility. Preferences and File menu were rendered offscreen and visually inspected.
- Icons use existing desktop themes with bundled Qt resource fallbacks; no configuration or debugger behavior change.
- Local IDE package updated to prefs4; debugger 0.1.0-2 remains compatible. Not installed or published.


## Project bin runtime default — 2026-11-04

- Both applications default project runtime cwd to bin when settings are absent/unaccepted or an accepted section omits working_directory. Explicit project overrides are preserved; standalone IDE files keep global fallback behavior.
- Runtime review/rescan and Restore Defaults select bin without removing discovery suggestions or moving any files.
- Relevant IDE regression suite: **121 passed**, 26.79 seconds. Independent debugger suite: **39 passed**, 24.681 seconds.
- Tests cover default/missing/unaccepted settings, accepted sections without cwd, explicit root override, standalone fallback, resolution before first build and discovery of data folders without overriding bin.
- Both runtime resolvers were checked against an isolated copy of gixsql-example with its runtime section removed. SQLite connection and SELECT succeeded from bin; the user's database was not used.
- Local packages: opencobolide 4.7.6+modern12+prefs5 and cobgdb-python 0.1.0-4. Not installed or published. Existing explicit configurations are not batch rewritten.

## 6 November 2026 follow-up

The focused IDE suite passed 121 tests covering Help, portable projects, project lifecycle, runtime review, Preferences, shortcuts and debugger launch. Qt reported backend-process teardown warnings after the suite. The independent debugger suite passed 39 tests. On the Linux desktop, a real GNOME Terminal received a menu choice typed into COBOL ACCEPT. GDB reported the value at the following breakpoint. The graphical COBOL score example opened its X11 window under GDB. A click reached the next COBOL breakpoint, and stepping changed score from 5 to 6 before normal exit.

The modern12 HTML manual was regenerated and checked for local links. Windows launcher worker dispatch was exercised as Python source. Windows 11 EXE/Inno Setup compilation and native Fedora 44/Mageia 10 RPM builds remain to be performed on the corresponding targets.
