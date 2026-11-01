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
