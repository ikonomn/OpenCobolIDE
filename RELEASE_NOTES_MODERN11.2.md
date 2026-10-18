# OpenCobolIDE 4.7.6+modern11.2

- Optional automatic listing names based on each source basename.
- Explicit listing names are preserved; bare -T and {stem} are supported.
- Per-source extra compiler flags with a return-to-global-defaults option.
- Syntax checks use the selected flags without writing listing files.
- Optional user-level launcher during Linux source installation.
- Rebuild on Compile so changed compiler flags take effect.
- Existing SQL preferences and storage remain shared.

See doc/modern11.2-workflow.md for usage and limitations.
Mageia crash investigation remains separate. This is a local candidate;
no GitHub release or tag has been published for modern11.2 yet.

The GixSQL build template includes `detect_sql.py`; copy it alongside `build.sh`.
Plain COBOL is compiled directly without requiring gixpp or linking libgixsql.
Embedded SQL, including SQL in COPY files, selects GixSQL preprocessing.
The detector handles standard fixed/free source and simple COPY names; it stops
on unresolved copybooks rather than silently choosing a plain build.
