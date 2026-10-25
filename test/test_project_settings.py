"""Project defaults must be isolated, persistent, and below source overrides."""
import json

from open_cobol_ide.compilers import GnuCobolCompiler, compile_with_build_script
from open_cobol_ide.enums import FileType
from open_cobol_ide.linter import make_linter_command
from open_cobol_ide.settings import Settings


def test_project_inheritance_isolation_disable_and_reset(tmp_path):
    settings = Settings()
    root = tmp_path / 'project'
    source = str(root / 'src/main.cbl')
    other = str(tmp_path / 'project-other/main.cbl')
    global_flags = settings.compiler_flags
    settings.set_project_options(str(root), {'flags': ['-Wall', '-T', '{stem}.prn'],
        'environment': {'compiler_path': '/opt/project/cobc', 'path_mode': 'prepend',
                        'path': '/opt/project/bin', 'cob_copy_dir': '/opt/project/copy'}})
    assert Settings().effective_flags(source) == ['-Wall', '-T', str(root / '{stem}.prn')]
    assert settings.effective_flags(other) == global_flags
    assert settings.effective_environment(source)['compiler_path'] == '/opt/project/cobc'
    settings.set_source_flags(source, [])
    settings.set_source_environment(source, {'compiler_path': '/opt/source/cobc'})
    assert settings.effective_flags(source) == []
    environment = settings.effective_environment(source)
    assert environment['compiler_path'] == '/opt/source/cobc'
    assert environment['path'] == '/opt/project/bin'
    assert environment['cob_copy_dir'] == '/opt/project/copy'
    settings.set_source_flags(source, None)
    options = settings.project_options(str(root))
    options['enabled'] = False
    settings.set_project_options(str(root), options)
    assert settings.effective_flags(source) == global_flags
    assert settings.effective_environment(source)['compiler_path'] == '/opt/source/cobc'
    settings.set_project_options(str(root), None)
    assert settings.project_options(str(root)) == {}
    assert settings.compiler_flags == global_flags


def test_nearest_project_and_empty_flags(tmp_path):
    settings = Settings()
    settings.set_project_options(str(tmp_path), {'flags': ['-Wall']})
    nested = tmp_path / 'nested'
    settings.set_project_options(str(nested), {'flags': []})
    assert settings.effective_flags(str(nested / 'source.cbl')) == []
    assert settings.effective_flags(str(tmp_path / 'source.cbl')) == ['-Wall']


def test_project_settings_reach_compiler_linter_and_script(tmp_path, monkeypatch):
    from open_cobol_ide import compilers
    root = tmp_path / 'project'
    root.mkdir()
    source = root / 'module.cbl'
    source.write_text('       procedure division using argument.\n')
    script = root / 'build.sh'
    script.write_text('#!/bin/sh\n')
    script.chmod(0o755)
    settings = Settings()
    settings.set_project_options(str(root), {
        'flags': ['-Wall', '-I', '/opt/copy with spaces', '-T', '{stem}.prn'],
        'environment': {'compiler_path': '/opt/project/cobc', 'path_mode': 'prepend',
                        'path': '/opt/project/bin', 'cob_copy_dir': '/opt/project/copy'}})
    pgm, args = GnuCobolCompiler().make_command(
        [source.name], FileType.MODULE, 'bin', source_path=str(source))
    assert pgm == '/opt/project/cobc'
    assert args[0] == '-m'
    assert args[args.index('-T')+1] == str(root / 'module.prn')
    pgm, lint_args = make_linter_command('temp.cbl', str(source))
    assert pgm == '/opt/project/cobc'
    assert '/opt/copy with spaces' in lint_args
    assert '-T' not in lint_args
    env = GnuCobolCompiler.setup_process_environment(str(source))
    assert env.value('COB_COPY_DIR') == '/opt/project/copy'
    captured = []
    def run(pgm, args, working_dir='', process_environment=None):
        captured.append(process_environment)
        return 0, ''
    monkeypatch.setattr(compilers, 'run_command', run)
    compile_with_build_script(str(source))
    assert captured[0].value('COBC') == '/opt/project/cobc'
    assert captured[0].value('OCIDE_COMPILE_MODE') == '-m'
    assert str(root / 'module.prn') in json.loads(captured[0].value('OCIDE_COMPILER_FLAGS'))
    settings.set_source_flags(str(source), ['-w'])
    assert settings.effective_flags(str(source)) == ['-w']


def test_project_settings_menu_saves_defaults(app, tmp_path, monkeypatch):
    from open_cobol_ide.view.dialogs.source_compiler_options import SourceCompilerOptionsDialog
    from pyqode.qt import QtWidgets
    app.file.open_project(str(tmp_path))
    def accept(dialog):
        assert dialog.windowTitle() == 'Project compiler settings'
        dialog.use_global_flags.setChecked(False)
        dialog.flags.setText('-Wall -T {stem}.prn')
        return QtWidgets.QDialog.Accepted
    monkeypatch.setattr(SourceCompilerOptionsDialog, 'exec_', accept)
    app.cobol.project_settings_action.trigger()
    options = Settings().project_options(str(tmp_path))
    assert options['enabled'] is True
    assert options['flags'] == ['-Wall', '-T', '{stem}.prn']
