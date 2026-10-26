# OpenCobolIDE project demonstration

A small portable project showing a main program, a callable module and a shared copybook. The three COBOL files are copied from the user's reviewed `mynewproject` example; generated binaries and listings are intentionally omitted.

## Open a writable copy

For a Debian installation, copy the example from the installed documentation:

```bash
cp -a /usr/share/doc/opencobolide/examples/project-demo "$HOME/OpenCobolIDE-demo"
```

Choose a different destination name if that folder already exists. Then start the IDE and choose **Open Project**, selecting the copied folder. When working from a source checkout, copy `examples/project-demo` to a writable location instead.

## Files and settings

| File | Role |
| --- | --- |
| `src/test01.cbl` | Main executable; calls `worker` and passes `LK-VALUE`. |
| `src/worker.cbl` | Module; accepts `LK-VALUE` with PROCEDURE DIVISION USING and displays it. |
| `copybooks/copybook.cpy` | Shared `PIC X(40)` field definition. |
| `config/project.json` | Relative project/source settings, fixed source format and separate listing names. |

Project defaults use `-Wall -debug`. The worker has a source-specific extra-flag override of `-Wall`, demonstrating replacement of the inherited extra-flag list. The IDE still adds its automatically detected mode and managed listing/diagnostic options. Neither source supplies `-x` or `-m` manually.

## Demonstration steps

1. Open the project and inspect **Configure Project**.
2. Use **Project defaults…**, then select the worker and inspect **Selected source settings…**.
3. Validate settings.
4. Choose **Compile Project**.
5. Verify `bin/test01`, `bin/worker.so`, `build/test01.lst` and `build/worker.lst` on Linux.
6. Select `test01.cbl` and choose **Run**, leaving the arguments empty.
7. The program should display `HELLO from OpenCobolIDE modern11.6` followed by padding spaces.
8. Inspect the listings for cross references and symbol tables (`--Xref -ftsymbols`).
9. Open the shared copybook through the project tree. It is edited as COBOL and is not a standalone compile/run target.
10. Optionally use **New File** and select `.cpy` to create another empty copybook. The default project destination is `copybooks/`.
11. Close the project, or open a second copy to demonstrate switching. Unsaved project edits offer Save/Discard/Cancel.

The normal IDE runtime directory is the project `bin/` folder. If you have changed the global runtime working directory or module-search environment, restore an appropriate setting so the `worker` module can be found.

The `data/` folder is included as part of the standard project layout; this example does not require application data or a database.
