"""Native RPM compiler output must not turn successful builds into errors."""
import json
import os
from pathlib import Path
import subprocess

import pytest
from open_cobol_ide.compilers import GnuCobolCompiler, compile_with_build_script, run_command
from open_cobol_ide.settings import Settings
from pyqode.core.modes import CheckerMessages

ROOT = Path(__file__).resolve().parents[1]


def test_diagnostic_severity_and_verbose_chatter(tmp_path):
    output = '''cobc: executing: gcc -o main main.c
cobc: elapsed time: 0 seconds
cobc: warning: ignoring nonexistent directory "/usr/share/gixsql/copy"
cobc: note: compiler information
src/main.cbl:12: note: context
src/main.cbl:13: warning: unused item
src/main.cbl:14: error: invalid statement
/path with spaces/copybooks/data.cpy:15:7: error: invalid item
cobc: error: missing input
'''
    messages = GnuCobolCompiler.parse_output(output, str(tmp_path))
    assert [m[1] for m in messages] == [
        CheckerMessages.WARNING, CheckerMessages.INFO, CheckerMessages.INFO,
        CheckerMessages.WARNING, CheckerMessages.ERROR, CheckerMessages.ERROR,
        CheckerMessages.ERROR]
    assert messages[-2][-1] == '/path with spaces/copybooks/data.cpy'


@pytest.mark.parametrize('status', [0, 7])
def test_warning_only_output_preserves_status(monkeypatch, tmp_path, status):
    source = tmp_path / 'main.cbl'
    source.write_text('       identification division.\n')
    Settings().register_project(str(tmp_path))
    monkeypatch.setattr('open_cobol_ide.compilers.run_command',
                        lambda *a, **kw: (status, 'cobc: warning: test warning'))
    actual, messages = compile_with_build_script(str(source))
    assert actual == status
    assert sum(m[1] == CheckerMessages.ERROR for m in messages) == (status != 0)


@pytest.mark.parametrize('sql_location', ['none', 'source', 'copybook'])
@pytest.mark.parametrize('mode', ['-x', '-m'])
@pytest.mark.parametrize('exit_status', [0, 9])
def test_internal_builder_sql_options_and_status(tmp_path, sql_location, mode, exit_status):
    source = tmp_path / 'main.cbl'
    (tmp_path / 'copybooks').mkdir()
    source.write_text('       identification division.\n' + {
        'none': '       procedure division.\n           goback.\n',
        'source': '           EXEC SQL SELECT 1 END-EXEC.\n',
        'copybook': '       COPY sqlbook.\n'}[sql_location])
    (tmp_path / 'copybooks/sqlbook.cpy').write_text('           EXEC SQL SELECT 1 END-EXEC.\n')
    compiler = tmp_path / 'fake-cobc'
    compiler.write_text('#!/usr/bin/env python3\nimport json,os,sys\n'
                        'open(os.environ["ARGS"],"w").write(json.dumps(sys.argv[1:]))\n'
                        'sys.exit(int(os.environ["EXIT_STATUS"]))\n')
    compiler.chmod(0o755)
    preprocessor = tmp_path / 'fake-gixpp'
    preprocessor.write_text('#!/bin/sh\nexit "${GIX_STATUS:-0}"\n')
    preprocessor.chmod(0o755)
    env = dict(os.environ, OCIDE_PROJECT_DIR=str(tmp_path), OCIDE_COMPILE_MODE=mode,
               COBC=str(compiler), GIXPP=str(preprocessor), ARGS=str(tmp_path/'args.json'),
               EXIT_STATUS=str(exit_status), GIXSQL_COPY_DIR='/missing/gixsql/copy',
               GIXSQL_LIBRARY_DIR='/missing/gixsql/lib', OCIDE_COMPILER_FLAGS='[]')
    result = subprocess.run(['bash', str(ROOT/'open_cobol_ide/build_tools/build.sh'), str(source)],
                            env=env, capture_output=True, text=True)
    assert result.returncode == exit_status, result.stderr
    args = json.loads((tmp_path/'args.json').read_text())
    assert args[0] == mode
    assert ('/missing/gixsql/copy' in args) == (sql_location != 'none')
    assert ('-lgixsql' in args) == (sql_location != 'none')
    assert str(tmp_path/'copybooks') in args
    if sql_location != 'none':
        (tmp_path/'args.json').unlink()
        env['GIX_STATUS'] = '6'
        result = subprocess.run(['bash',str(ROOT/'open_cobol_ide/build_tools/build.sh'),str(source)],
                                env=env,capture_output=True,text=True)
        assert result.returncode == 6
        assert not (tmp_path/'args.json').exists()


def test_process_start_failure_is_nonzero():
    status, output = run_command('/nonexistent/ocide-test-compiler', [])
    assert status == 127
    assert 'Could not start' in output


def test_gnucobol32_unlabelled_include_messages_are_warnings(tmp_path):
    messages = GnuCobolCompiler.parse_output(
        'cobc: invalid parameter: -I\n'
        'cobc: ignoring nonexistent directory "/usr/share/gixsql/copy"\n', str(tmp_path))
    assert len(messages) == 2
    assert all(m[1] == CheckerMessages.WARNING for m in messages)


def test_gnucobol32_real_project_build_and_error(monkeypatch, tmp_path):
    import shutil
    from open_cobol_ide.enums import FileType
    from open_cobol_ide.compilers import get_file_type
    compiler = os.environ.get('OCIDE_TEST_COBC32')
    if not compiler:
        pytest.skip('Set OCIDE_TEST_COBC32 to the GnuCOBOL 3.2.0 compiler')
    assert '3.2.0' in subprocess.check_output([compiler, '-V'], text=True)
    project = tmp_path / 'project with spaces'
    shutil.copytree(ROOT/'examples/project-demo', project)
    settings = Settings()
    monkeypatch.setattr(Settings, 'compiler_path', property(lambda self: compiler))
    settings.register_project(str(project))
    for name, mode in [('test01', FileType.EXECUTABLE), ('worker', FileType.MODULE)]:
        source = project/'src'/(name+'.cbl')
        assert get_file_type(str(source)) == mode
        status, messages = compile_with_build_script(str(source))
        assert status == 0, messages
        assert not [m for m in messages if m[1] == CheckerMessages.ERROR]
        listing = (project/'build'/(name+'.lst')).read_text()
        assert 'REFERENCES' in listing
    result = subprocess.run([str(project/'bin/test01')], cwd=project/'bin',
                            capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert 'HELLO from OpenCobolIDE' in result.stdout
    bad = project/'src/broken.cbl'
    bad.write_text('       identification division.\n       program-id. broken.\n'
                   '       procedure division.\n           MOVE TO.\n')
    status, messages = compile_with_build_script(str(bad))
    assert status != 0
    assert any(m[1] == CheckerMessages.ERROR for m in messages)


def test_fedora_rpm_payload_cleanup(tmp_path):
    import shutil
    stage = tmp_path
    docs = stage/'usr/share/doc/opencobolide'
    site = stage/'usr/lib/python3/site-packages'
    docs.mkdir(parents=True)
    site.mkdir(parents=True)
    shutil.copytree(ROOT/'examples/project-demo', docs/'examples/project-demo')
    for rel in ['open_cobol_ide/backend.py', 'open_cobol_ide/build_tools/detect_sql.py',
                'open_cobol_ide/build_tools/build.sh',
                'opencobolide-4.7.6.dist-info/licenses/LICENSE']:
        p = site/rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('#!/usr/bin/env python\npass\n' if rel.endswith('.py') else
                     ('#!/usr/bin/env bash\ntrue\n' if rel.endswith('.sh') else 'license'))
    (docs/'LICENSE').write_text('license')
    license_dir = stage/'usr/share/licenses/opencobolide'
    license_dir.mkdir(parents=True)
    (license_dir/'LICENSE').write_text('license')
    spec = (ROOT/'packaging/fedora/opencobolide-modern11.6.spec').read_text()
    block = spec[spec.index('find %{buildroot}%{_docdir}'):spec.index('desktop-file-validate')]
    for old, new in [('%{buildroot}',str(stage)),('%{_docdir}','/usr/share/doc'),
                     ('%{python3_sitelib}','/usr/lib/python3/site-packages'),
                     ('%{_licensedir}','/usr/share/licenses'),('%{name}','opencobolide')]:
        block = block.replace(old,new)
    subprocess.run(['bash','-eu','-c',block],check=True)
    assert not list(docs.rglob('.gitkeep'))
    assert not list(docs.rglob('.gitignore'))
    assert not (site/'open_cobol_ide/backend.py').read_text().startswith('#!')
    assert (site/'open_cobol_ide/build_tools/build.sh').stat().st_mode & 0o111
    assert (docs/'LICENSE').resolve() == license_dir/'LICENSE'
    assert (site/'opencobolide-4.7.6.dist-info/licenses/LICENSE').is_symlink()
