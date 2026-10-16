import ast
from pathlib import Path
from types import SimpleNamespace
import subprocess
import shutil
import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'open_cobol_ide' / 'settings.py'

@pytest.mark.parametrize('flags', [
    ['-Wall', '-debug', '-T', 'payapply3.prn'],
    ['-I', 'first', '-I', 'second', '-T', 'listing with spaces.prn'],
])
def test_settings_preserves_option_operands(flags):
    tree = ast.parse(SOURCE.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Settings')
    getter = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'compiler_flags')
    getter.decorator_list = []
    module = ast.Module(body=[getter], type_ignores=[])
    scope = {}
    exec(compile(ast.fix_missing_locations(module), str(SOURCE), 'exec'), scope)
    fake = SimpleNamespace(_settings=SimpleNamespace(value=lambda *args: repr(flags)))
    assert scope['compiler_flags'](fake) == flags

@pytest.mark.skipif(shutil.which('cobc') is None, reason='GnuCOBOL is not installed')
def test_cobc_listing_operand(tmp_path):
    source = tmp_path / 'hello.cbl'
    source.write_text('       identification division.\n       program-id. hello.\n       procedure division.\n           goback.\n')
    listing = tmp_path / 'listing with spaces.prn'
    result = subprocess.run([shutil.which('cobc'), '-m', '-o', str(tmp_path/'hello.so'),
                             '-Wall', '-debug', '-T', str(listing), str(source)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert listing.exists()
