import os
import pytest

from open_cobol_ide import compilers


def test_internal_builder_ignores_project_script(tmp_path):
    from open_cobol_ide.settings import Settings
    source = tmp_path / 'program.cbl'
    source.write_text('IDENTIFICATION DIVISION.')
    script = tmp_path / 'build.sh'
    script.write_text('#!/bin/sh\nexit 99\n')
    script.chmod(0o755)
    assert compilers.find_build_script(str(source)) is None
    Settings().register_project(str(tmp_path))
    selected = compilers.find_build_script(str(source))
    assert selected != str(script)
    assert selected.endswith('/open_cobol_ide/build_tools/build.sh')


def test_internal_builder_handles_nested_sources_without_project_script(tmp_path):
    from open_cobol_ide.settings import Settings
    project = tmp_path / 'project'
    source_dir = project / 'src' / 'batch'
    source_dir.mkdir(parents=True)
    source = source_dir / 'program.cbl'
    source.write_text('IDENTIFICATION DIVISION.')
    Settings().register_project(str(project))
    assert compilers.find_build_script(str(source)).endswith('/build_tools/build.sh')
    assert compilers.get_build_script_output_directory(str(source)) == str(project / 'bin')


def test_internal_builder_does_not_capture_unrelated_or_sql_backend_sources(tmp_path):
    from open_cobol_ide.settings import Settings
    project = tmp_path / 'project'
    Settings().register_project(str(project))
    assert compilers.find_build_script(str(tmp_path / 'other/main.cbl')) is None
    assert compilers.find_build_script(str(project / 'db.scb')) is None
    assert compilers.find_build_script(str(project / 'db.sqb')) is None


def test_compile_with_build_script_passes_absolute_source(monkeypatch,
                                                          tmp_path):
    source = tmp_path / 'program.cbl'
    from open_cobol_ide.settings import Settings
    Settings().register_project(str(tmp_path))
    source.write_text('IDENTIFICATION DIVISION.')
    script = tmp_path / 'build.sh'
    script.write_text('#!/bin/sh\n')
    script.chmod(0o755)
    called = {}
    emitted = []

    def fake_run_command(pgm, args, working_dir='', process_environment=None):
        called_env = process_environment
        assert called_env.value('OCIDE_COMPILE_MODE') == '-x'
        assert called_env.value('OCIDE_PROJECT_DIR') == str(tmp_path)
        assert called_env.value('COBC')
        assert called_env.value('OCIDE_COMPILER_FLAGS')
        called.update(pgm=pgm, args=args, working_dir=working_dir)
        return 0, 'Build completed'

    monkeypatch.setattr(compilers, 'run_command', fake_run_command)

    status, messages = compilers.compile_with_build_script(
        str(source), emitted.append)

    assert status == 0
    assert messages == []
    assert emitted == ['Build completed']
    assert called == {
        'pgm': 'bash',
        'args': [compilers.find_build_script(str(source)), str(source)],
        'working_dir': str(tmp_path),
    }


def test_compile_with_build_script_reports_unparsed_failure(monkeypatch,
                                                             tmp_path):
    source = tmp_path / 'program.cbl'
    from open_cobol_ide.settings import Settings
    Settings().register_project(str(tmp_path))
    source.write_text('IDENTIFICATION DIVISION.')
    script = tmp_path / 'build.sh'
    script.write_text('#!/bin/sh\n')
    script.chmod(0o755)
    monkeypatch.setattr(
        compilers, 'run_command',
        lambda *args, **kwargs: (2, 'gixpp: preprocessing failed'))

    status, messages = compilers.compile_with_build_script(str(source))

    assert status == 2
    assert len(messages) == 1
    assert messages[0][0] == 'gixpp: preprocessing failed'
    assert messages[0][-1] == str(source)


def test_template_plain_build_needs_no_gixsql(tmp_path):
    import shutil
    import subprocess
    from pathlib import Path
    template = Path(__file__).resolve().parents[1] / 'examples' / 'gixsql'
    for name in ['build.sh', 'detect_sql.py']:
        shutil.copy2(template / name, tmp_path / name)
    source = tmp_path / 'plain.cbl'
    source.write_text('       identification division.\n'
                      '       program-id. plain.\n'
                      '       procedure division.\n'
                      '           goback.\n')
    env = dict(os.environ, GIXPP='nonexistent-gixpp-test-command')
    result = subprocess.run(['bash', str(tmp_path / 'build.sh'), str(source)],
                            env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / 'bin' / 'plain').exists()
    assert (tmp_path / 'build' / 'plain.lst').exists()
    assert not (tmp_path / 'build' / 'plain.cbsql').exists()


def test_detector_recurses_copy_and_ignores_comments(tmp_path):
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / 'examples/gixsql/detect_sql.py'
    spec = importlib.util.spec_from_file_location('sql_detector', path)
    detector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(detector)
    source = tmp_path / 'main.cbl'
    source.write_text('       DISPLAY "EXEC SQL".\n      * EXEC SQL\n')
    assert not detector.has_sql(source, [tmp_path])
    source.write_text('       COPY first.\n')
    (tmp_path / 'first.cpy').write_text('       COPY second.\n')
    (tmp_path / 'second.cpy').write_text('           EXEC SQL SELECT 1 END-EXEC.\n')
    assert detector.has_sql(source, [tmp_path])


@pytest.mark.parametrize('flags,listing', [
    ([], 'build/plain.lst'),
    (['-Wall'], 'build/plain.lst'),
    (['-T', 'listing with spaces.prn'], 'listing with spaces.prn'),
    (['-t', 'short listing.prn'], 'short listing.prn'),
])
def test_ide_flags_create_listing_and_show_compile_steps(tmp_path, flags, listing):
    import json
    import shutil
    import subprocess
    from pathlib import Path
    template = Path(__file__).resolve().parents[1] / 'examples/gixsql'
    for name in ('build.sh', 'detect_sql.py'):
        shutil.copy2(template / name, tmp_path / name)
    source = tmp_path / 'plain.cbl'
    source.write_text('       identification division.\n'
                      '       program-id. plain.\n'
                      '       procedure division.\n           goback.\n')
    env = dict(os.environ, OCIDE_COMPILER_FLAGS=json.dumps(flags))
    result = subprocess.run(['bash', str(tmp_path / 'build.sh'), str(source)],
                            cwd=tmp_path, env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / listing).stat().st_size > 0
    output = result.stdout + result.stderr
    assert 'SQL detection: plain' in output
    assert '$ cobc ' in output
    assert 'preprocessing:' in output
    assert 'parsing:' in output
    assert 'translating:' in output
    assert 'executing:' in output
    assert 'Listing:    ' in result.stdout
