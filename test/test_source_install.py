"""Regression checks for the modern source-installation path."""

from pathlib import Path
import warnings


ROOT = Path(__file__).resolve().parents[1]


def test_installed_runtime_sources_have_no_invalid_escape_warnings():
    """Compile every shipped runtime module with escape warnings as errors."""
    runtime_roots = [
        ROOT / 'open_cobol_ide',
    ]
    excluded = {
        ROOT / 'open_cobol_ide' / 'extlibs' / 'pygments',
        ROOT / 'open_cobol_ide' / 'extlibs' / 'future',
    }

    for runtime_root in runtime_roots:
        for path in runtime_root.rglob('*.py'):
            if any(parent == excluded_path for parent in path.parents
                   for excluded_path in excluded):
                continue
            source = path.read_text(encoding='utf-8')
            with warnings.catch_warnings():
                warnings.simplefilter('error', SyntaxWarning)
                warnings.simplefilter('error', DeprecationWarning)
                compile(source, str(path), 'exec')


def test_source_installers_use_pip_not_setup_py_install():
    linux_installer = (ROOT / 'scripts' / 'install_from_source.sh').read_text(
        encoding='utf-8')
    windows_installer = (
        ROOT / 'scripts' / 'install_from_source.ps1').read_text(
            encoding='utf-8')

    for installer in (linux_installer, windows_installer):
        assert '-m pip install' in installer
        assert 'setup.py install' not in installer


def test_obsolete_dependencies_are_excluded_from_source_distribution():
    manifest = (ROOT / 'MANIFEST.in').read_text(encoding='utf-8')
    assert 'recursive-exclude open_cobol_ide/extlibs/pygments *' in manifest
    assert 'recursive-exclude open_cobol_ide/extlibs/future *' in manifest


def test_setup_metadata_without_source_on_import_path(tmp_path):
    """PEP 517 may execute setup.py without the project on sys.path."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, '-I', str(ROOT / 'setup.py'), '--version'],
        cwd=str(tmp_path), text=True, capture_output=True, check=True)
    assert result.stdout.strip() == '4.7.6'
