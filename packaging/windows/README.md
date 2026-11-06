# OpenCobolIDE modern12 for Windows 11 x64

Extract the dedicated `opencobolide-4.7.6-modern12.tar.gz` source archive and work from its root. Build Windows separately on Windows 11 x64. The Windows release downloads are the standalone executable and Inno Setup installer.

On Windows 11, use 64-bit Python in a build environment with PyQt5, Pygments and PyInstaller 6.9 or newer. Use your installed Inno Setup 7 command-line compiler, ISCC.exe.

```powershell
python -m pip install "PyQt5>=5.15,<6" "Pygments>=2.11,<3" "PyInstaller>=6.9,<7"
.\packaging\windows\build.ps1 -InnoCompiler 'C:\Program Files\Inno Setup 7\ISCC.exe'
```

Adjust the compiler path to match your Inno Setup 7 installation.

The script produces opencobolide.exe, OpenCobolIDE-modern12-win11-x64-setup.exe and SHA256SUMS in dist/windows by default. The executable bundles Python, Qt, the offline manual and editor backend workers. The build uses a console-capable executable so the bundled console worker can use standard input and output. GnuCOBOL remains a separate toolchain. The current IDE project builder also requires compatible Bash, Python 3 and Unix tools on PATH, such as a matching MSYS2 environment. GixSQL is needed for SQL builds. Configure the compiler and runtime tools before testing.

Test the standalone executable on Windows without a development Python on PATH. Verify launch, editing, completion, F1 Help, standalone and project compilation, native Run output and shutdown. Build a project in a path with spaces and confirm C and headers are retained under debug_data. Install COBGDB and verify the IDE finds its launcher, opens the executable and source, and hits a COBOL breakpoint. Then test installer install, Start menu launch and uninstall in a separate test profile. Check GixSQL separately if available. The scripts were prepared on Linux. Windows builds and these native checks are pending.

[PyInstaller command options](https://pyinstaller.org/en/stable/usage.html) · [Inno Setup compiler options](https://jrsoftware.org/ishelp/topic_compilercmdline.htm)
