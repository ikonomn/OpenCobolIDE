import ast
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock
import pytest

ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('flags,optimization', [([], '-O0'), (['-O2'], '-O2'), (['-g','-g','-fsource-location','-fsource-location','-ftraceall','-ftraceall','-save-temps','-save-temps'], '-O0'), (['-Os'], '-Os'), (['-g','-ftraceall','-fsource-location','-save-temps','-O3'], '-O3')])
@pytest.mark.parametrize('status', [0, 9])
def test_debug_flags_and_exit_status(tmp_path, flags, optimization, status):
    source = tmp_path/'plain.cob'
    source.write_text('       identification division.\n       program-id. plain.\n')
    compiler = tmp_path/'compiler'
    compiler.write_text('#!/usr/bin/env python3\nimport os,sys,json\nopen(os.environ["ARGS"],"w").write(json.dumps(sys.argv[1:]))\nsys.exit(int(os.environ["STATUS"]))\n')
    compiler.chmod(0o755)
    env = dict(os.environ, OCIDE_PROJECT_DIR=str(tmp_path), COBC=str(compiler),
               OCIDE_DEBUG_BUILD='1', OCIDE_COMPILER_FLAGS=json.dumps(flags),
               ARGS=str(tmp_path/'args'), STATUS=str(status))
    result = subprocess.run(['bash', str(ROOT/'open_cobol_ide/build_tools/build.sh'), str(source)], env=env, capture_output=True, text=True)
    assert result.returncode == status, result.stderr
    args = json.loads((tmp_path/'args').read_text())
    assert [a for a in args if a.startswith('-O')] == [optimization]
    for flag in ('-g','-fsource-location','-ftraceall','-save-temps'):
        assert args.count(flag) == 1


def test_project_summary_counts_failures_and_exceptions(monkeypatch):
    # Execute the production thread method with fake compiler services, without
    # launching a GUI. Covers success, nonzero exit, parsed error, and exception.
    import sys
    tree = ast.parse((ROOT/'open_cobol_ide/controllers/cobol.py').read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'CompilationThread')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
    fake = SimpleNamespace(started=Mock(), output_available=Mock())
    def compile_source(path, callback):
        if path == 'exception': raise RuntimeError('test')
        return {'ok': (0, []), 'exit': (9, []), 'diagnostic': (0, [('bad', 2)])}[path]
    monkeypatch.setitem(sys.modules, 'open_cobol_ide.project_build', SimpleNamespace(BuildState=Mock(), snapshot=Mock()))
    scope = dict(GnuCobolCompiler=lambda: fake, DbpreCompiler=lambda: fake,
                 EsqlOCCompiler=lambda: fake, Settings=lambda: SimpleNamespace(project_root_for_source=lambda f: None),
                 trace_log=Mock(), _logger=lambda: Mock(), CheckerMessages=SimpleNamespace(ERROR=2),
                 find_build_script=lambda f: 'builder', compile_with_build_script=compile_source)
    exec(compile(ast.Module(body=[method], type_ignores=[]), '<thread>', 'exec'), scope)
    thread = SimpleNamespace(file_path='ok', file_paths=['ok','exit','diagnostic','exception'],
                             incremental=True, force_project=False, command_started=Mock(),
                             output_available=Mock(), errored=Mock(), file_compiled=Mock(), finished=Mock())
    scope['run'](thread)
    thread.output_available.emit.assert_called_with('Project build: 1 compiled, 3 failed, 0 up to date.\n')
    assert thread.file_compiled.emit.call_count == 3
    thread.errored.emit.assert_called_once()



def test_windows_project_paths_at_bash_boundary(tmp_path):
    project = tmp_path / 'Project with spaces'
    project.mkdir()
    source = project / 'caller.cob'
    source.write_text('       identification division.\n       program-id. caller.\n')
    helper = project / 'helper file.c'
    helper.write_text('int helper(void) { return 0; }\n')
    cygpath = tmp_path / 'cygpath'
    cygpath.write_text(
        '#!/usr/bin/env python3\n'
        'import os, sys\n'
        'path = sys.argv[-1].replace(chr(92), "/")\n'
        'assert path.startswith("C:/")\n'
        'print(os.path.join(os.environ["TEST_DRIVE"], path[3:]))\n'
    )
    cygpath.chmod(0o755)
    compiler = project / 'compiler tool'
    compiler.write_text(
        '#!/usr/bin/env python3\n'
        'import json, os, sys\n'
        'with open(os.environ["TEST_ARGS"], "w") as stream:\n'
        '    json.dump(sys.argv[1:], stream)\n'
    )
    compiler.chmod(0o755)
    drive = r'C:\Project with spaces'
    args_file = tmp_path / 'args.json'
    environment = dict(os.environ, PATH=str(tmp_path) + os.pathsep + os.environ['PATH'],
                       TEST_DRIVE=str(tmp_path), TEST_ARGS=str(args_file),
                       OCIDE_PROJECT_DIR=drive, COBC=drive + r'\compiler tool',
                       OCIDE_OUTPUT_DIR=drive + r'\custom output',
                       OCIDE_OUTPUT_EXTENSION='.exe', OCIDE_DEBUG_BUILD='1',
                       OCIDE_C_SOURCES=json.dumps([drive + r'\helper file.c']),
                       OCIDE_COMPILER_FLAGS=json.dumps(['-T', drive + r'\listing file.prn',
                                                         '-I' + drive + r'\copy books']))
    result = subprocess.run(['bash', str(ROOT/'open_cobol_ide/build_tools/build.sh'),
                             drive + r'\caller.cob'], cwd=tmp_path, env=environment,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    args = json.loads(args_file.read_text())
    assert args[args.index('-o') + 1] == str(project/'custom output'/'caller.exe')
    assert args[args.index('-T') + 1] == str(project/'listing file.prn')
    assert '-I' + str(project/'copy books') in args
    assert args[-2:] == [str(source), str(helper)]
    assert (project/'debug_data'/'caller').is_dir()
