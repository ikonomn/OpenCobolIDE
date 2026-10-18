import os

from open_cobol_ide import compilers


def test_find_build_script_requires_executable(tmp_path):
    source = tmp_path / 'program.cbl'
    source.write_text('IDENTIFICATION DIVISION.')
    script = tmp_path / 'build.sh'
    script.write_text('#!/bin/sh\n')

    assert compilers.find_build_script(str(source)) is None

    script.chmod(0o755)
    assert compilers.find_build_script(str(source)) == str(script)


def test_find_build_script_searches_up_to_project_root(tmp_path):
    project = tmp_path / 'project'
    source_dir = project / 'src' / 'batch'
    source_dir.mkdir(parents=True)
    source = source_dir / 'program.cbl'
    source.write_text('IDENTIFICATION DIVISION.')
    (project / 'Makefile').write_text('all:\n')
    script = project / 'build.sh'
    script.write_text('#!/bin/sh\n')
    script.chmod(0o755)

    assert compilers.find_build_script(str(source)) == str(script)
    assert compilers.get_build_script_output_directory(str(source)) == \
        str(project / 'bin')


def test_find_build_script_does_not_escape_project_root(tmp_path):
    project = tmp_path / 'project'
    source_dir = project / 'src'
    source_dir.mkdir(parents=True)
    source = source_dir / 'program.cbl'
    source.write_text('IDENTIFICATION DIVISION.')
    (project / '.git').mkdir()
    script = tmp_path / 'build.sh'
    script.write_text('#!/bin/sh\n')
    script.chmod(0o755)

    assert compilers.find_build_script(str(source)) is None
    assert compilers.get_build_script_output_directory(str(source)) is None


def test_compile_with_build_script_passes_absolute_source(monkeypatch,
                                                          tmp_path):
    source = tmp_path / 'program.cbl'
    source.write_text('IDENTIFICATION DIVISION.')
    script = tmp_path / 'build.sh'
    script.write_text('#!/bin/sh\n')
    script.chmod(0o755)
    called = {}
    emitted = []

    def fake_run_command(pgm, args, working_dir=''):
        called.update(pgm=pgm, args=args, working_dir=working_dir)
        return 0, 'Build completed'

    monkeypatch.setattr(compilers, 'run_command', fake_run_command)

    status, messages = compilers.compile_with_build_script(
        str(source), emitted.append)

    assert status == 0
    assert messages == []
    assert emitted == ['Build completed']
    assert called == {
        'pgm': str(script),
        'args': [str(source)],
        'working_dir': str(tmp_path),
    }


def test_compile_with_build_script_reports_unparsed_failure(monkeypatch,
                                                             tmp_path):
    source = tmp_path / 'program.cbl'
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
