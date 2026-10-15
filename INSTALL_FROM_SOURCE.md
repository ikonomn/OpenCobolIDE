# Installing OpenCobolIDE from source

These instructions use Python's standard virtual-environment and `pip`
workflow. They do not use the deprecated `setup.py install` command.

OpenCobolIDE still requires a separate GnuCOBOL installation. Before starting,
confirm that this command works:

```text
cobc --version
```

## Linux

Install Python 3.8 or newer, Python virtual-environment support, and GnuCOBOL
with your distribution's package manager. Install Git, then clone the
modern-python branch of the repository and run:

```bash
git clone --branch modern-python https://github.com/ikonomn/OpenCobolIDE.git
cd OpenCobolIDE
./scripts/install_from_source.sh
```

Start the installed copy with:

```bash
./.venv/bin/opencobolide
```

The script installs PyQt5 from PyPI. If your distribution cannot use the PyPI
PyQt5 wheel, install PyQt5 with the distribution package manager and create the
environment with access to system packages:

```bash
rm -rf .venv
python3 -m venv --system-site-packages .venv
./.venv/bin/python -m pip install --upgrade pip setuptools wheel
./.venv/bin/python -m pip install .
```

## Windows

Install 64-bit Python 3.8 or newer and select **Add Python to PATH** in the
Python installer. Install a Windows build of GnuCOBOL separately and add the
directory containing `cobc.exe` to `PATH`.

Install Git, then open PowerShell and clone the repository before running
the installer:

```powershell
git clone --branch modern-python https://github.com/ikonomn/OpenCobolIDE.git
cd OpenCobolIDE
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_from_source.ps1
```

Start the installed copy with:

```powershell
.\.venv\Scripts\opencobolide.exe
```

Alternatively, on either operating system the equivalent manual commands are:

```text
python -m venv .venv
<venv-python> -m pip install --upgrade pip setuptools wheel
<venv-python> -m pip install .
```

You can also start the application using the environment's Python interpreter:

```text
<venv-python> -m open_cobol_ide
```

## Build a wheel

For redistribution within your own environment, install `build` and create a
wheel with:

```text
python -m pip install build
python -m build
```

The resulting wheel is written to `dist/`. GnuCOBOL is not included in it.

## Notes

- The Debian `.deb` remains the tested and supported binary package.
- Source installation is intended to help other Linux distributions and
  Windows users, but Windows packaging and every Linux distribution have not
  yet been fully tested.
- The historical bundled copies of Pygments and Future are not installed.
  A maintained Pygments release is resolved as an ordinary Python dependency,
  while the obsolete Python 2 compatibility dependency is no longer needed.
  This avoids Python 3.12 `invalid escape sequence` warnings from those copies.
