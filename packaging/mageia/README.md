# Building the OpenCobolIDE modern11.6 RPM on Mageia 10

The tested script logic is retained with modern11.6 references. The consolidated RPM still requires a native build/test run on the Mageia 10 persistent USB. Use the source-matched transfer kit and [current collection plan](../RPM_MODERN11.6.md).

These instructions are for anyone who would like to help create and test a
native Mageia 10 RPM of OpenCobolIDE 4.7.6 modern11.6.

The build must be performed on Mageia 10. The resulting binary package will be
identified as a Mageia 10 package. Compatibility with Fedora, openSUSE, or
other RPM-based distributions is not assumed.

## 1. Prepare Mageia

Make sure that the Mageia **Core Release** and **Core Updates** online media
are enabled. Then update the package lists and the system:

```bash
sudo urpmi.update -a
sudo urpmi --auto-update
```

Record the system version and architecture:

```bash
cat /etc/mageia-release
uname -m
```

## 2. Install the packaging tools

The simplest option is Mageia's packaging task:

```bash
sudo urpmi task-packager
```

If `task-packager` is unavailable, install the required tools directly:

```bash
sudo urpmi rpm-build rpmdevtools rpmlint spec-helper git
```

Install the Python and OpenCobolIDE runtime/build dependencies:

```bash
sudo urpmi \
    python3 \
    python3-devel \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-qt5-gui \
    python3-pygments \
    desktop-file-utils \
    gnucobol
```

Verify that the required PyQt5 modules are available:

```bash
python3 -c 'from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork; print("PyQt5 OK")'
```

If Mageia reports a missing PyQt5 module, locate the package that provides it:

```bash
urpmf 'PyQt5/QtNetwork'
urpmf 'PyQt5/QtWidgets'
```

Install the package reported by `urpmf`, and repeat the Python check.

Record the installed versions:

```bash
python3 --version
rpm --version
cobc --version
rpm -q python3-qt5-gui python3-pygments gnucobol
```

## 3. Create the RPM build tree

Run this as the normal user, without `sudo`:

```bash
rpmdev-setuptree
```

It should create:

```text
~/rpmbuild/BUILD
~/rpmbuild/BUILDROOT
~/rpmbuild/RPMS
~/rpmbuild/SOURCES
~/rpmbuild/SPECS
~/rpmbuild/SRPMS
```

## 4. Copy the supplied build files

The build attachment will contain:

```text
opencobolide-4.7.6-modern11.6.tar.gz
opencobolide-modern11.6.spec
build-mageia10-rpm.sh
```

Place the files as follows:

```bash
chmod +x build-mageia10-rpm.sh
```

Do not unpack or modify the source archive before building it.

## 5. Build the RPM

Keep all three supplied files in the same directory and run the script as the
normal user:

```bash
./build-mageia10-rpm.sh 2>&1 | tee ~/opencobolide-modern11.6-rpmbuild.log
```

Do not use `sudo` for `rpmbuild`.

The script runs the equivalent of:

```bash
rpmbuild -ba ~/rpmbuild/SPECS/opencobolide-modern11.6.spec
```

## 6. Locate and inspect the packages

```bash
find ~/rpmbuild/RPMS ~/rpmbuild/SRPMS \
    -type f -iname '*opencobolide*.rpm' -print
```

There should be a Mageia 10 `noarch.rpm` and a source RPM. Check them with:

```bash
rpmlint \
    ~/rpmbuild/RPMS/noarch/opencobolide-*.rpm \
    ~/rpmbuild/SRPMS/opencobolide-*.src.rpm \
    2>&1 | tee ~/opencobolide-modern11.6-rpmlint.log
```

Inspect the dependencies and installed files:

```bash
rpm -qpR ~/rpmbuild/RPMS/noarch/opencobolide-*.rpm
rpm -qpl ~/rpmbuild/RPMS/noarch/opencobolide-*.rpm
```

## 7. Install and test

If an earlier RPM installation exists, remove that package first:

```bash
rpm -q opencobolide && sudo rpm -e opencobolide
```

Install the newly built package with Mageia's package manager so dependencies
are resolved:

```bash
sudo urpmi ~/rpmbuild/RPMS/noarch/opencobolide-*.rpm
```

Confirm the installation:

```bash
command -v opencobolide
rpm -q opencobolide
opencobolide --version
```

Start the IDE:

```bash
opencobolide
```

Please test:

1. Opening, compiling, and running a normal COBOL executable.
2. A source containing `>>SOURCE FREE`.
3. A source containing `>>SOURCE FORMAT IS FREE`.
4. Automatic free-format margins, highlighting, and navigation.
5. A callable source with `PROCEDURE DIVISION USING`, including linkage declared through COPY.
6. Per-source compiler flags and listing filenames.
7. Per-source `COB_COPY_DIR` using a copybook outside the source directory.
8. A GixSQL project through the IDE-owned internal preprocessing workflow.
9. Normal IDE shutdown and restart.

## 8. Return the build results

Please attach:

- The Mageia 10 `noarch.rpm`.
- The `.src.rpm`.
- The `.spec` file used for the build.
- `opencobolide-modern11.6-rpmbuild.log`.
- `opencobolide-modern11.6-rpmlint.log`.
- Any OpenCobolIDE trace JSONL produced if the application crashes.

Create checksums for the packages:

```bash
sha256sum \
    ~/rpmbuild/RPMS/noarch/opencobolide-*.rpm \
    ~/rpmbuild/SRPMS/opencobolide-*.src.rpm \
    | tee ~/opencobolide-modern11.6-sha256.txt
```

Please attach `opencobolide-modern11.6-sha256.txt` as well.

If the build fails, attach the complete build log. The complete log is more
useful than only the final error lines.

## Compatibility statement

The binary RPM produced by this procedure is built and tested for Mageia 10.
Fedora and openSUSE use RPM too, but package names, Python and Qt packaging,
filesystem paths, RPM macros, and dependency versions can differ. Separate
builds and tests are required before claiming support for those distributions.
