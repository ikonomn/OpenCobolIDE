# OpenCobolIDE + GixSQL minimal project

If you want to see GixSQL working in OpenCobolIDE, start here. The project has
one small COBOL program: it reads a database profile, connects, runs `SELECT 1`
and exits. SQLite works out of the box; a MariaDB profile is included for you
to fill in.

```text
src/database-test.cbl
        |  gixpp (embedded SQL preprocessing)
        v
build/database-test.cbsql
        |  cobc (COBOL compile and GixSQL link)
        v
bin/database-test
```

The same COBOL source can connect to SQLite or MariaDB. Only the runtime
profile changes.

## Quick start

From this directory, run:

```sh
./build.sh src/database-test.cbl
cd bin
./database-test
```

You should see `DATABASE CONNECTION OK` followed by `SELECT RESULT: 000000001`.
The rest of this README explains what happened and how to adapt the example.

## 1. Requirements

Install OpenCobolIDE `4.7.6+modern9.3` or newer, GnuCOBOL, GixSQL, and the
SQLite or MariaDB client libraries required by the selected GixSQL driver.

Verify the commands:

```sh
cobc --version
gixpp --version
```

The OpenCobolIDE Debian package does not install GixSQL automatically.

## 2. Project structure

```text
gixsql/
├── build.sh
├── README.md
├── gitignore.example
├── src/
│   └── database-test.cbl
├── copybooks/
│   └── db-config-procedure.cpy
├── config/
│   ├── application-sqlite.conf
│   └── application-mariadb.conf.example
├── build/                       generated during preprocessing
└── bin/                         generated during compilation
```

`build/` and `bin/` should normally be ignored by version control.
If this will be a standalone project, enable the supplied ignore rules:

```sh
cp gitignore.example .gitignore
```

## 3. Copy the installed example

The Debian package installs the project under:

```text
/usr/share/doc/opencobolide/examples/gixsql
```

Copy it to a writable location:

```sh
cp -a /usr/share/doc/opencobolide/examples/gixsql my-gixsql-project
cd my-gixsql-project
chmod +x build.sh
```

To add only the build script to an existing project:

```sh
cp /usr/share/doc/opencobolide/examples/gixsql/build.sh ./build.sh
chmod +x ./build.sh
```

Place `build.sh` in the project root, above `src/`.

## 4. How OpenCobolIDE finds the script

When **Compile** or **Run** is selected, OpenCobolIDE starts at the directory
of the open `.cbl` or `.cob` source and searches upward for an executable
`build.sh`. The search stops at the nearest directory containing `.git` or a
`Makefile`.

When found, the IDE runs:

```sh
/absolute/project/build.sh /absolute/project/src/program.cbl
```

The working directory is the directory containing `build.sh`. Standard output
and standard error appear in the compiler log. A nonzero script exit status
marks the build as failed.

Without an executable `build.sh`, OpenCobolIDE uses its normal `cobc`, DBPRE,
or esqlOC flow.

## 5. Preprocessing with `gixpp`

`build.sh` validates the source and creates `build/` and `bin/`. For the
minimal test, the preprocessing command is equivalent to:

```sh
gixpp \
  -e \
  -S \
  -z a \
  -P varchar \
  -I /usr/share/gixsql/copy \
  -I ./copybooks \
  -i ./src/database-test.cbl \
  -o ./build/database-test.cbsql
```

Options:

- `-e` enables embedded SQL preprocessing.
- `-S` emits static GixSQL calls.
- `-z a` uses anonymous SQL parameters.
- `-P varchar` maps suitable `PIC X` host variables as varying text.
- `-I` adds GixSQL and project copybook search paths.
- `-i` selects the original COBOL source.
- `-o` selects the generated COBOL source.

`gixpp` converts `EXEC SQL ... END-EXEC` statements into COBOL calls to the
GixSQL runtime. It never overwrites the original `.cbl`. If preprocessing
fails, the script stops and does not run `cobc`.

Use `build/database-test.cbsql` to inspect generated code when troubleshooting.

## 6. Compiling and linking with `cobc`

After successful preprocessing, the compile command is equivalent to:

```sh
cobc \
  -x \
  -v \
  -debug \
  --Xref \
  -ftsymbols \
  -T ./build/database-test.lst \
  -I /usr/share/gixsql/copy \
  -I ./copybooks \
  -L /usr/lib \
  -lgixsql \
  -o ./bin/database-test \
  ./build/database-test.cbsql
```

Options:

- `-x` builds an executable.
- `-v` prints compiler and linker commands.
- `-debug` enables runtime checks.
- `--Xref` generates cross-reference information.
- `-ftsymbols` retains symbol information.
- `-T` writes the compiler listing.
- `-L` adds the GixSQL library directory.
- `-lgixsql` links the GixSQL runtime.
- `-o` selects the executable path.

A successful build produces:

```text
build/database-test.cbsql   preprocessed COBOL
build/database-test.lst     compiler listing
bin/database-test           executable
```

OpenCobolIDE expects a custom-build executable under the project-root `bin/`.
**Run** executes it with `bin/` as the working directory. **Clean** removes the
matching executable from `bin/`; intermediate files remain under `build/` for
inspection.

## 7. Check the result

`build.sh` also accepts an absolute source path:

```sh
./build.sh /absolute/project/src/database-test.cbl
```

Expected SQLite output:

```text
USING CONFIG: ../config/application-sqlite.conf
USING DATASOURCE: sqlite://../build/application.db
DATABASE CONNECTION OK
SELECT RESULT: 000000001
```

## 8. SQLite profile

The supplied `config/application-sqlite.conf` contains:

```ini
DATASRC=sqlite://../build/application.db
DATASRC_USR=
DATASRC_PWD=
```

Because the program runs from `bin/`, `../build/application.db` points to the
project database. SQLite creates it if needed. The source selects SQLite with:

```cobol
           MOVE "00" TO DB-FLAG
```

For deployment, an absolute Unix path uses three slashes:

```ini
DATASRC=sqlite:///absolute/path/to/application.db
```

## 9. MariaDB profile

Create and protect the active profile:

```sh
cp config/application-mariadb.conf.example \
   config/application-mariadb.conf
chmod 600 config/application-mariadb.conf
```

Edit the database and dedicated application credentials:

```ini
DATASRC=mysql://localhost:3306/application
DATASRC_USR=application_user
DATASRC_PWD=change-me
```

Select MariaDB before `LOAD-DB-CONFIG`:

```cobol
           MOVE "01" TO DB-FLAG
```

Rebuild after changing that COBOL statement. Do not commit a profile containing
a real password. Add it to `.gitignore` and commit only `.conf.example`.

## 10. Change profiles without recompiling

`DB_CONFIG_FILE` overrides `DB-FLAG`, allowing the same executable to use
development, test, or production settings:

```sh
cd bin
DB_CONFIG_FILE=/absolute/path/application-sqlite.conf ./database-test
```

```sh
cd bin
DB_CONFIG_FILE=/absolute/path/application-mariadb.conf ./database-test
```

Configuration files are runtime inputs. Changing a datasource, username, or
password does not require preprocessing or compilation.

## 11. Nonstandard GixSQL installation

Defaults used by `build.sh`:

```text
GIXPP=gixpp
COBC=cobc
GIXSQL_COPY_DIR=/usr/share/gixsql/copy
GIXSQL_LIBRARY_DIR=/usr/lib
PROJECT_COPY_DIR=<project>/copybooks
```

Override them without editing COBOL:

```sh
GIXSQL_COPY_DIR=/opt/gixsql/share/gixsql/copy \
GIXSQL_LIBRARY_DIR=/opt/gixsql/lib \
./build.sh src/database-test.cbl
```

`GIXPP`, `COBC`, and `PROJECT_COPY_DIR` can be overridden similarly.

## 12. Troubleshooting

### OpenCobolIDE does not call `build.sh`

Ensure the file is named exactly `build.sh`, is above the source, and is
executable:

```sh
chmod +x build.sh
```

Check that an unrelated parent `.git` directory or `Makefile` does not stop
the upward search before the script is found.

### `gixpp: command not found`

Install GixSQL or set `GIXPP` to its absolute executable path.

### `Cannot resolve copy file`

Put application copybooks in `copybooks/`, or set `PROJECT_COPY_DIR`. GixSQL's
`SQLCA` copybook must exist under `GIXSQL_COPY_DIR`.

### Linker cannot find `libgixsql`

Set `GIXSQL_LIBRARY_DIR` to the directory containing `libgixsql.so`. At
runtime, the system linker must also locate GixSQL and the selected database
driver library.

### Configuration file status `35`

Status `35` means the configuration file was not found. Run from `bin/`, use
an absolute profile path, or set `DB_CONFIG_FILE`.

### Output contains `Built ... 23:32:34`

This is compiler version information, not an error. Current OpenCobolIDE only
treats output explicitly marked as error, warning, or note as a diagnostic.
