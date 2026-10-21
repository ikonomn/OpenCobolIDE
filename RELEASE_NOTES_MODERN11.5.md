# OpenCobolIDE 4.7.6+modern11.5

modern11.5 adds a clearer per-source compiler configuration dialog. Each saved
source can inherit or replace the global extra compiler flags and can override
the compiler executable and `COB_COPY_DIR`. An optional **Additional tools
directory** can be searched before the inherited `PATH` when a compiler needs a
particular `gcc`, `clang`, or preprocessor. The compiler path is the direct way
to select `cobc`; the system `PATH` is never replaced. These overrides are used
by compilation and live syntax checking without modifying the desktop
environment or another open source file.

Directory settings are checked for accidental leading or trailing whitespace,
including whitespace immediately beside `/` or `\\`. The IDE shows the
original and corrected values before saving them. Valid spaces inside directory
names, such as `My Projects`, are preserved. This validation covers the global
compiler and run paths, copybook and library paths, and the per-source fields.

Existing modern11.4 settings remain compatible. Per-source settings continue
to be keyed by the canonical full source path; moving a file does not transfer
its overrides.

GixSQL projects continue to use their project `build.sh`. The script detects
embedded SQL, preprocesses SQL sources with `gixpp`, and then compiles the
generated COBOL with `cobc`. Sources without SQL continue through the script's
flat COBOL compilation path. The new per-source dialog does not bypass or
replace this preprocessing workflow.

OpenCobolIDE also detects callable COBOL sources that contain both a `LINKAGE
SECTION` and `PROCEDURE DIVISION USING`. These sources are compiled explicitly
with `cobc -m` as loadable modules instead of `cobc -x` executables.

The editor now recognizes `>>SOURCE FREE`, `>>SOURCE FORMAT IS FREE`, and the
corresponding `FIXED` directives. It automatically changes the visible source
layout, margins, syntax highlighting, navigation parser, and live syntax
checking. The global **Free format** option remains the fallback for sources
without a directive. When a directive is present, the status-bar option shows
the detected format and is locked to avoid a conflicting manual setting.

The first format directive controls the editor layout. GnuCOBOL still receives
the source unchanged, so it can process later format switches in the same file.

## Compiler options for one source file

![Compiler options for this file](https://raw.githubusercontent.com/ikonomn/OpenCobolIDE/v4.7.6-modern11.5/doc/images/modern11.5-compiler-options-for-this-file.png)

## Release assets

The Debian-family package is provided as
`opencobolide_4.7.6+modern11.5_all.deb`. GnuCOBOL is recommended rather than
required, so systems using a separately built GnuCOBOL installation can install
the IDE without replacing their compiler.

`opencobolide-modern11.5-mageia10-build-kit.tar.gz` is a source build kit for
creating and testing a native Mageia 10 RPM. It contains the committed source,
Mageia RPM specification, automated build script, dependency list, validation
commands, and test instructions. It is not a prebuilt RPM.

The resulting RPM should initially be described as built and tested for Mageia
10. Compatibility with Fedora, openSUSE, and other RPM-based distributions is
not claimed without separate builds and testing.

SHA-256 checksums are published in `SHA256SUMS`.
