> Compile Project now means changed files (Ctrl+F8); Rebuild Project means all
> files (Ctrl+Shift+F8). See [build and shortcut verification](INCREMENTAL_BUILD_MODERN11.6.md).

> Native fix update: RPM release 11.6.3 includes SQL-only GixSQL paths,
> GnuCOBOL 3.2 diagnostic severity fixes and RPM payload cleanup.
> It also keeps the explicitly opened project root authoritative when a nested
> src/config/project.json exists. See [the project-root fix](PROJECT_ROOT_FIX_MODERN11.6.md).
> See [the verification and remaining native checks](NATIVE_FIX_MODERN11.6.md).

# modern11.6 — Mageia 10 and Fedora 44 USB build/collection plan

The existing persistent USB installations are the native build/test environments. Create the transfer kits on Mint from the committed modern11.6 source. Boot Mageia 10 to build its RPM, boot Fedora 44 to build its RPM, then return to Mint with the results. GitHub push/release uploads wait until both native results are collected and reviewed.

The Mageia script retains the previously tested build logic, updated for modern11.6 source/spec/package names and build-log capture. Fedora 44 has a separate spec and build script. The final 11.6 RPMs are **pending native builds/tests**; preparing a kit does not constitute a tested RPM release.

## Take the kit to the target USB

Extract the corresponding `opencobolide-modern11.6-<target>-kit.tar.gz` into a writable home folder. It contains the source archive, spec, build script, source commit identifier and checksums. Verify with `sha256sum -c SHA256SUMS` from the extracted kit directory.

Both kits contain the same source revision. Do not mix a newer working tree into one kit.

## Mageia 10

Record the environment:

```bash
cat /etc/mageia-release
uname -m
python3 --version
```

Ensure the Mageia Core Release/Core Updates media are enabled. Install packaging and runtime/build prerequisites using the same package setup as the tested Mageia procedure:

```bash
sudo urpmi task-packager python3-devel python3-pip python3-setuptools python3-wheel python3-rpm-macros python3-qt5-gui python3-pygments desktop-file-utils gnucobol
```

If task-packager is unavailable, the existing procedure uses rpm-build, rpmdevtools, rpmlint and spec-helper. Verify the actual packages available on the persistent installation.

From the extracted Mageia kit:

```bash
./build-mageia10-rpm.sh
```

The script refuses a non-Mageia-10 environment, builds binary and source RPMs and collects them in `mageia10-rpm-output/`. Inspect `rpmbuild.log`, `rpmlint.log` and `SHA256SUMS`.

## Fedora 44

Record `/etc/os-release`, architecture and Python version. Install native prerequisites:

```bash
sudo dnf install rpm-build rpmdevtools rpmlint python3-devel python3-setuptools python3-wheel pyproject-rpm-macros python3-qt5-base python3-pygments desktop-file-utils gnucobol
```

Fedora's PyQt5 base package provides QtCore, QtGui, QtWidgets and QtNetwork. The Fedora spec uses pyproject RPM macros instead of the Mageia legacy setuptools macros. Confirm the target's actual Python/Qt behavior: Fedora 44 packaging uses Python 3.14, which needs native application tests in addition to a successful RPM build.

From the extracted Fedora kit:

```bash
./build-fedora44-rpm.sh
```

The script refuses a non-Fedora-44 environment and collects binary/source RPMs, logs and checksums in `fedora44-rpm-output/`.

## Inspect, install and test on each USB

For the package you just built:

```bash
rpm -qpR /path/to/opencobolide-package.rpm
rpm -qpl /path/to/opencobolide-package.rpm
```

Install with the target package manager so dependencies are resolved (`urpmi` on Mageia, `dnf install` on Fedora). Do not use the Debian package on these targets. Run the IDE from a terminal and test:

1. Launch/About/runtime diagnostics and shutdown/restart.
2. New Project, Open Project and portable config/project.json.
3. The included project-demo main program, worker module and shared copybook.
4. Automatic -x/-m modes and Compile Project/F8.
5. New .cpy/.CPY creation, syntax editing and exclusion from standalone compile/run.
6. Cross-reference listings and symbol tables (`--Xref -ftsymbols`).
7. Project defaults, source overrides, validation and a moved/copied project.
8. Close Project and switching projects, including Save/Discard/Cancel.
9. Fixed/free source directives and runtime arguments.
10. GixSQL where installed; record separately if GixSQL is not installed and therefore not tested.
11. Scrolling, Page Down, toolbar tooltip timing and the actual desktop session. These were historically reported areas and are not certified by a headless build.

## Bring back to Mint

Keep separate `mageia10/` and `fedora44/` result folders containing:

- Binary `.noarch.rpm` and source `.src.rpm`.
- Exact spec and SOURCE_REVISION.txt.
- Build and rpmlint logs; complete failure logs if applicable.
- SHA256SUMS with filenames relative to the results folder.
- OS/architecture, Python, Qt, GnuCOBOL versions and a short test-results note.
- Any diagnostic trace if the application crashes.

Review results on Mint before the planned GitHub push and release uploads. Do not relabel one target's binary as another target or claim every Fedora-based distribution is supported from a single Fedora 44 run.

## References

- [Fedora 44 PyQt5 base files and dependencies](https://packages.fedoraproject.org/pkgs/python-qt5/python3-qt5-base/fedora-44.html).
- [Fedora pyproject RPM macros](https://packages.fedoraproject.org/pkgs/pyproject-rpm-macros/pyproject-rpm-macros/).
- Existing Mageia procedure: packaging/mageia/README.md in the source tree.
