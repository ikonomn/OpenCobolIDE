# modern12 native RPM build kits — Fedora 44 and Mageia 10

Use this guide for the **current modern12 release**. Each target kit builds **OpenCobolIDE and COBOL Debugger together** from recorded source revisions. Run the single `build-rpms.sh` entry point on the matching distribution. It produces two binary RPMs and two source RPMs.

The archived modern11.6 workflow builds only the IDE with its own source archive and target-specific scripts. Fedora and Mageia use the same native build hosts across both releases, so some prerequisite commands overlap. See the [archived modern11.6 guide](RPM_MODERN11.6.md).

Native RPM builds and desktop tests are pending.

| Application | Application version | Fedora RPM | Mageia RPM |
| --- | --- | --- | --- |
| OpenCobolIDE | 4.7.6 modern12 | 4.7.6-12.9.fc44 | 4.7.6-12.9.mga10 |
| COBOL Debugger | 0.1.0 | 0.1.0-9.fc44 | 0.1.0-9.mga10 |

Debian test suffixes such as prefs5 and Debian revision -4 are not application versions and are not copied into RPM release numbers. Both target kits contain archives of the exact same committed IDE/debugger source revisions. Private .local-guidance files, environments, packages and generated outputs are excluded by git archive.

## Prepare matching kits on the development host

Commit intended changes in both local repositories; leave their Git status clean. From the IDE repository:

```bash
python3 packaging/make-modern12-transfer-kits.py \
  --debugger-repo /home/ikonomn/cobgdb-python \
  --output /path/to/transfer-kits
```

Take modern12-fedora44-rpm-kit.tar.gz and modern12-mageia10-rpm-kit.tar.gz to their respective native installations. Each contains both source archives, both specs, build-rpms.sh, TARGET, SOURCE_REVISIONS.json, instructions and SHA256SUMS. Verify the outer .sha256 sidecar before extraction and run `sha256sum -c SHA256SUMS` inside the kit.

## Fedora 44 prerequisites

```bash
sudo dnf install rpm-build rpmdevtools rpmlint python3-devel \
  python3-setuptools python3-wheel pyproject-rpm-macros \
  python3-qt5-base python3-pygments desktop-file-utils gdb gnucobol
```

The IDE spec uses Fedora pyproject macros. Runtime Qt dependencies are explicit. Verify actual repository availability and Python/Qt behavior on the native installation.

## Mageia 10 prerequisites

Enable Core Release/Core Updates media, then install:

```bash
sudo urpmi rpm-build rpmdevtools rpmlint spec-helper python3-devel \
  python3-setuptools python3-wheel python3-rpm-macros \
  python3-qt5-gui python3-pygments desktop-file-utils gdb gnucobol
```

The IDE retains the established Mageia setuptools macro build. The debugger is a pure Python application installed with explicit distro Python/Qt/GDB dependencies. GixSQL must be installed separately if its native SQL workflow is to be tested.

## Build on each native target

Extract its kit in a writable folder and run:

```bash
bash build-rpms.sh
```

TARGET selects Fedora 44 or Mageia 10. The script refuses other operating systems, verifies kit checksums, builds both packages with rpmbuild -ba, and collects two binary noarch RPMs plus two source RPMs. It creates fresh build/output directories to avoid collecting stale packages. Do not relabel packages built for one target as packages for the other.

The results include per-application build logs, rpmlint output/status, source revisions, OS/architecture/Python/Qt information, specs and RPM checksums. Failed builds leave their diagnostic directories intact. No package is installed automatically.

The debugger's supplied project metadata currently has no declared redistribution license. Its existing Debian notice and these private local-test RPMs do not invent one: LicenseRef-Local-Test-Only identifies that condition. Resolve the project license before public redistribution; native rpmlint may flag this metadata. This is not an approved distribution-repository submission.

## Inspect, install and verify natively

Inspect `rpm -qpR package.rpm` and `rpm -qpl package.rpm`. Install the binary packages together with the target package manager (`dnf install` on Fedora, `urpmi` on Mageia), after reviewing build/rpmlint results. Do not install source RPMs as applications.

Verify both applications on the real desktop:

1. About/version, launch, shutdown and restart.
2. New/Open/Close/Switch Project, unsaved-file protection, defaults and source overrides.
3. Preferences Compiler/Projects/Debugger/GixSQL entries and icons.
4. Executable/module modes, COPY dependencies, incremental compile and full rebuild.
5. Listings and retained debug_data C/headers from the same successful build.
6. Default runtime cwd bin, explicit project overrides and a moved project.
7. Single-folder data lookup and the documented multi-directory COB_FILE_PATH limitation.
8. `cobol-debugger` with no arguments, executable only, and executable plus --source.
9. IDE direct debugger launch, breakpoints, stepping, variables, input and flowchart/PDF.
10. GixSQL separately if available; keep configuration/database paths relative to their intended cwd. Use disposable test data.

Return binary/source RPMs, all logs, source revisions, environment details and actual test results to the development host. Publication waits for review. Use the installed COBOL Debugger to run the graphical example from its documentation. Check Program output and Send input alongside the program window; COBOL Debugger uses its embedded console. Native Windows results are independent of these RPM results.

## Release archives

Keep the exact build source in the dedicated OpenCobolIDE and COBOL Debugger source archives. The Fedora and Mageia transfer kits are internal build inputs. For the separate Windows build, use the [Windows build guide](windows/README.md) in the IDE source archive and the corresponding guide in the COBOL Debugger source archive.

## Packaging references

- Fedora Python packaging: https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/
- Fedora Qt5 base package: https://packages.fedoraproject.org/pkgs/python-qt5/python3-qt5-base/
- Historical Mageia procedure: packaging/mageia/README.md.
