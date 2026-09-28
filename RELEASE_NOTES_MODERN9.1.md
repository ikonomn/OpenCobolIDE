# OpenCobolIDE 4.7.6+modern9.1

This update adds project-level build scripts to OpenCobolIDE.

When a COBOL project contains an executable `build.sh`, **Compile** and
**Run** use that script instead of calling `cobc` directly. This allows a
project to run tools such as the GixSQL preprocessor before compilation.

## What changed

- OpenCobolIDE finds `build.sh` from the source directory up to the project
  root.
- Compiler output from the script appears in the normal compiler log.
- Executables are read from the project's `bin/` directory.
- **Run**, **Clean**, and **Rebuild** work with project-built executables.
- Compiler version timestamps are no longer reported as source errors.
- The offline manual explains the project build flow.
- A small GixSQL project is included under `examples/gixsql/`.

The example contains a reusable `build.sh`, one minimal COBOL database test,
SQLite and MariaDB profiles, and a practical README covering preprocessing and
compilation.

GixSQL is not bundled with OpenCobolIDE and must be installed separately.

## Install

```sh
sudo apt install ./opencobolide_4.7.6+modern9.1_all.deb
```

## Try the GixSQL example

```sh
cp -a /usr/share/doc/opencobolide/examples/gixsql my-gixsql-project
cd my-gixsql-project
./build.sh src/database-test.cbl
cd bin
./database-test
```

SQLite is selected by default. MariaDB setup is described in the example
README.

## Package checksum

```text
SHA-256: 3c0ca60a6819e99d49b8682e9cba648945f9d87a428a728d7dc21b2cdfa235b2
```

Verify it with:

```sh
sha256sum opencobolide_4.7.6+modern9.1_all.deb
```

This is an unofficial maintenance build of OpenCobolIDE 4.7.6.
