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
