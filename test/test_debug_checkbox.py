import pytest
from open_cobol_ide import project_config as config
from open_cobol_ide.view.dialogs.source_compiler_options import SourceCompilerOptionsDialog
from pyqode.qt import QtWidgets


def test_debug_preview_and_reset(app, tmp_path):
    dialog = SourceCompilerOptionsDialog(str(tmp_path), ['-O2'], None, {}, project=True, debug_enabled=True)
    assert '-O2' in dialog.debug_note.text()
    assert 'less predictable' in dialog.debug_note.text()
    assert '-O0' not in dialog.debug_note.text()
    dialog.use_global_flags.setChecked(False)
    dialog.flags.setText('-g -ftraceall')
    assert '-O0' in dialog.debug_note.text()
    assert '_FORTIFY_SOURCE' in dialog.debug_note.text()
    dialog.flags.setText("'unfinished")
    assert 'quoting' in dialog.debug_note.text()
    dialog.reset()
    assert not dialog.debug.isChecked()
    dialog.close()


@pytest.mark.parametrize('accepted', [False, True])
def test_project_debug_saved_only_on_accept(app, tmp_path, monkeypatch, accepted):
    app.file.open_project(str(tmp_path))
    data = config.load(tmp_path)
    data['debug'] = {'enabled': False, 'future_option': 'preserve'}
    config.save(tmp_path, data)
    def execute(dialog):
        assert not dialog.debug.isChecked()
        dialog.debug.setChecked(True)
        dialog.use_global_flags.setChecked(False)
        dialog.flags.setText('-O2 -g')
        return QtWidgets.QDialog.Accepted if accepted else QtWidgets.QDialog.Rejected
    monkeypatch.setattr(SourceCompilerOptionsDialog, 'exec_', execute)
    app.cobol.edit_project_compiler_options()
    result = config.load(tmp_path)
    assert result['debug'] == {'enabled': accepted, 'future_option': 'preserve'}
    if accepted:
        assert result['defaults']['flags'] == ['-O2', '-g']



@pytest.mark.parametrize('project', [False, True])
def test_file_debug_checkbox_controls_compile_command(app, tmp_path, project):
    from open_cobol_ide.compilers import GnuCobolCompiler, get_file_type
    from open_cobol_ide.settings import Settings

    source = tmp_path / 'debug-file.cob'
    source.write_text('       identification division.\n       program-id. debug-file.\n')
    if project:
        config.save(tmp_path, config.default_config(tmp_path))
    settings = Settings()
    dialog = SourceCompilerOptionsDialog(str(source), [], [], {})
    dialog.file_debug.setChecked(True)
    settings.set_source_compiler_options(str(source), ['-g', '-g'], {}, dialog.extra_values())
    assert settings.debug_build_enabled(str(source))
    _, arguments = GnuCobolCompiler().make_command(
        [source.name], get_file_type(str(source)), str(tmp_path), source_path=str(source))
    for flag in ('-g', '-fsource-location', '-ftraceall', '-O0', '-save-temps'):
        assert arguments.count(flag) == 1
    if project:
        from open_cobol_ide.project_build import snapshot
        assert any('debug_data' in path for path in snapshot(str(source))['outputs'])
    dialog.file_debug.setChecked(False)
    settings.set_source_compiler_options(str(source), [], {}, dialog.extra_values())
    assert not settings.debug_build_enabled(str(source))
    dialog.close()
