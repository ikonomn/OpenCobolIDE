# Local bug-report fixes and investigation status

Updated: 2026-10-23. Base commit: `8459c9d` (modern11.5).

This records the pending working-tree changes. It is not a released-fix list
and does not establish what is included in Vincent's Mageia 10 RPM.
No report identifiers or original runtime-diagnostics report text were available
in this review; the behavior below is established from the local diff.

## Pending fix: runtime diagnostics in About

Status: local changes on hold, not committed at the time of this review.

Previously, `GnuCobolCompiler.get_cobcrun_infos()` invoked
`cobcrun --runtime-env`, and the About report displayed that same command.
The pending change uses `cobcrun --runtime-config` by default and accepts an
option argument. The About report now includes separate `cobcrun --info` and
`cobcrun --runtime-config` sections, alongside `cobc --info`. Failure messages
name the actual requested option.

Files:
- `open_cobol_ide/compilers.py`
- `open_cobol_ide/view/dialogs/about.py`
- `test/test_runtime_diagnostics.py` (pending new test file)

The tests cover success/failure for both options, a missing cobcrun executable,
and the report headings and contents. Verification on 2026-10-23:

- `test/test_runtime_diagnostics.py`
- `test/test_compiler_flag_order.py`
- `test/test_compiler_output.py`
- `test/test_compiler_workflow.py`
- `test/test_build_script.py`

Result: **32 passed** (0.72 seconds). Tests ran with Qt's offscreen platform,
a temporary cache-directory override in the test process, and a separate Qt
user-settings path under `work/`. No production logger changes were needed.
The initial logging-path restriction was bypassed only for this test run.
These tests do not establish actual GnuCOBOL/Mageia compatibility or resolve
the scrolling/tooltip reports; those still need runtime verification.

## Vincent: scrolling with Compiler / Issues / Output open

Status: investigated; no corresponding fix in the pending diff.

Report: Down Arrow stops advancing at the bottom of the editor; Page Down
appears to omit approximately six lines while Logs is open. Closing Logs
changes the behavior.

The supplied 33-second modern11.5 recording shows scrolling with Logs open,
but does not display key presses or compare with Logs closed. It therefore
does not confirm or conclusively disprove the specific report. The nearly
blank view around 00:28 shows line 388 and is consistent with reaching EOF;
it does not establish lost source text.

Initial source review:
- CodeEdit.keyPressEvent delegates unconsumed navigation to Qt. Editor modes
  can consume events before that delegation.
- CodeEdit.resizeEvent calls the Qt implementation and resizes editor panels.
- Logs is a main-window QDockWidget, separate from editor margin panels.
- Compilation shows Logs and changes tabs without an explicit editor focus
  restoration at those sites. Focus routing is a hypothesis to test, not an
  established cause; showing the dock alone does not prove focus is stolen.

Next verification: record focused widget, cursor line, visible line range and
viewport height while repeating Down Arrow/Page Down before and after opening
and closing Logs. Use the exact sources and dependencies of Vincent's RPM.

## Vincent: delayed toolbar tooltips

Status: unconfirmed; no corresponding fix in the pending diff.

The recording does not provide a clear stationary toolbar hover followed by
a tooltip appearance, so no delay can be measured. No custom toolbar-tooltip
delay was found in the files inspected. Check hover timing and UI responsiveness
on the affected Mageia system before assigning a cause.

## Broader verification

See [2026-10-23 verification](broader-verification-2026-10-23.md): full suite
112 passed; two additional exploratory checks passed. Mageia and tooltip
verification remain pending.
