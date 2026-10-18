import ast
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('compiler_options',ROOT/'open_cobol_ide/compiler_options.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

@pytest.mark.parametrize('flags,auto,syntax,expected',[
 ([],False,False,[]),([],True,False,['-T','payapply1.prn']),
 (['-T'],False,False,['-T','payapply1.prn']),
 (['-T','-Wall'],False,False,['-T','payapply1.prn','-Wall']),
 (['-T','custom listing.prn'],True,False,['-T','custom listing.prn']),
 (['-T','{stem}.prn'],False,False,['-T','payapply1.prn']),
 (['-t','custom.prn','-Wall'],True,True,['-Wall']),
 ([],True,True,[]),
])
def test_listing(flags,auto,syntax,expected):
 assert mod.listing_options(flags,'/project/payapply1.cbl',auto,syntax)==expected

def settings_class():
 tree=ast.parse((ROOT/'open_cobol_ide/settings.py').read_text())
 cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Settings')
 cls.body=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ('source_flags','set_source_flags')]
 scope={'os':os,'json':json}
 exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),'settings','exec'),scope)
 return scope['Settings']

def test_per_file_override_and_reset(tmp_path):
 data={'SQL/password':'unchanged'}
 store=SimpleNamespace(value=lambda k,d=None:data.get(k,d),setValue=lambda k,v:data.__setitem__(k,v),remove=lambda k:data.pop(k,None))
 settings=settings_class()(); settings._settings=store
 a=str(tmp_path/'one.cbl');b=str(tmp_path/'two.cbl')
 assert settings.source_flags(a) is None
 settings.set_source_flags(a,['-Wall','-T','one.prn'])
 assert settings.source_flags(a)==['-Wall','-T','one.prn']
 assert settings.source_flags(b) is None
 settings.set_source_flags(a,[])
 assert settings.source_flags(a)==[]
 settings.set_source_flags(a,None)
 assert settings.source_flags(a) is None
 assert data=={'SQL/password':'unchanged'}

def test_changed_sources_compile():
 for name in ['compiler_options.py','settings.py','compilers.py','linter.py','controllers/cobol.py']:
  p=ROOT/'open_cobol_ide'/name
  compile(p.read_text(),str(p),'exec')

def test_optional_launcher_and_existing_command(tmp_path):
 import subprocess
 venv=tmp_path/'venv with spaces'
 (venv/'bin').mkdir(parents=True)
 python=venv/'bin/python'
 python.write_text('#!/bin/sh\nif [ "$1" = "-m" ]; then exit 0; fi\nexec /usr/bin/python3 "$@"\n')
 python.chmod(0o755)
 executable=venv/'bin/opencobolide'
 executable.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
 executable.chmod(0o755)
 launcher=tmp_path/'user bin'/'opencobolide'
 env=dict(os.environ,PYTHON=str(python),OCIDE_VENV_DIR=str(venv),
          OCIDE_INSTALL_LAUNCHER='1',OCIDE_LAUNCHER_DIR=str(launcher.parent))
 script=ROOT/'scripts/install_from_source.sh'
 result=subprocess.run(['bash',str(script)],env=env,capture_output=True,text=True)
 assert result.returncode==0,result.stderr
 result=subprocess.run([str(launcher),'argument with spaces'],capture_output=True,text=True)
 assert result.stdout.strip()=='argument with spaces'
 launcher.write_text('#!/bin/sh\necho unrelated\n')
 result=subprocess.run(['bash',str(script)],env=env,capture_output=True,text=True)
 assert result.returncode!=0
 assert launcher.read_text()=='#!/bin/sh\necho unrelated\n'


def test_command_uses_source_override_and_automatic_listing(tmp_path):
    from open_cobol_ide.settings import Settings
    from open_cobol_ide.compilers import GnuCobolCompiler
    from open_cobol_ide.enums import FileType
    settings = Settings()
    original_flags = settings.compiler_flags
    original_auto = settings.automatic_listing
    source = str(tmp_path / 'first.cbl')
    try:
        settings.compiler_flags = ['-Wall']
        settings.automatic_listing = True
        settings.set_source_flags(source, ['-debug'])
        _, command = GnuCobolCompiler().make_command(
            ['first.cbl'], FileType.EXECUTABLE, 'bin', source_path=source)
        assert '-debug' in command and '-Wall' not in command
        assert command[command.index('-T') + 1] == 'first.prn'
        settings.set_source_flags(source, None)
        _, command = GnuCobolCompiler().make_command(
            ['first.cbl'], FileType.EXECUTABLE, 'bin', source_path=source)
        assert '-Wall' in command and '-debug' not in command
    finally:
        settings.set_source_flags(source, None)
        settings.compiler_flags = original_flags
        settings.automatic_listing = original_auto
