"""Copybook creation types must not become standalone build targets."""
import mimetypes
from pathlib import Path
import pytest
from pyqode.qt import QtWidgets
from open_cobol_ide import project_config as config
from open_cobol_ide.project import project_sources
from open_cobol_ide.settings import Settings
from open_cobol_ide.view.dialogs.new_file import DlgNewFile
from open_cobol_ide.view.editors.cobol import CobolCodeEdit


def choose(dialog, extension):
    index = dialog.comboBoxExtension.findText(extension)
    assert index >= 0
    dialog.comboBoxExtension.setCurrentIndex(index)


def test_copybook_extensions_available_without_compiler_registration(app, tmp_path):
    before = list(Settings().all_extensions)
    dialog = DlgNewFile(app.win, str(tmp_path))
    extensions = [dialog.comboBoxExtension.itemText(i) for i in range(dialog.comboBoxExtension.count())]
    assert extensions.count('.cpy') == 1
    assert extensions.count('.CPY') == 1
    assert Settings().all_extensions == before
    assert mimetypes.guess_type('record.cpy')[0] == 'text/x-cobol'
    assert mimetypes.guess_type('record.CPY')[0] == 'text/x-cobol'
    dialog.close()


@pytest.mark.parametrize('free_format', [False, True])
@pytest.mark.parametrize('extension', ['.cpy', '.CPY'])
def test_copybook_uses_empty_template_and_restores_source_template(app, tmp_path, extension, free_format):
    settings = Settings()
    previous = settings.free_format
    settings.free_format = free_format
    try:
        dialog = DlgNewFile(app.win, str(tmp_path))
        dialog.comboBoxType.setCurrentIndex(1)
        choose(dialog, extension)
        assert dialog.template() == ''
        assert dialog.comboBoxType.currentIndex() == 2
        assert not dialog.comboBoxType.isEnabled()
        choose(dialog, '.cbl')
        assert dialog.comboBoxType.isEnabled()
        assert dialog.comboBoxType.currentIndex() == 1
        assert 'PROCEDURE DIVISION USING' in dialog.template()
        dialog.close()
    finally:
        settings.free_format = previous


def test_copybook_defaults_to_project_copybooks_and_preserves_custom_paths(app, tmp_path):
    root = Path(config.create_project(tmp_path, 'Project'))
    dialog = DlgNewFile(app.win, str(root / 'src'))
    choose(dialog, '.cpy')
    assert dialog.lineEditPath.text() == str(root / 'copybooks')
    choose(dialog, '.cbl')
    assert dialog.lineEditPath.text() == str(root / 'src')
    custom = root / 'custom'
    custom.mkdir()
    dialog.lineEditPath.setText(str(custom))
    dialog.lineEditPath.textEdited.emit(str(custom))
    choose(dialog, '.cpy')
    assert dialog.lineEditPath.text() == str(custom)
    dialog.close()


@pytest.mark.parametrize('extension', ['.cpy', '.CPY'])
def test_create_and_edit_copybook_without_compiler_prompt(app, tmp_path, monkeypatch, extension):
    root = Path(config.create_project(tmp_path, 'Project'))
    source = root / 'src/example.cbl'
    source.write_text('       identification division.\n       program-id. example.\n'
                      '       procedure division.\n           goback.\n')
    assert app.file.open_project(str(root))
    def accept(dialog):
        dialog.lineEditName.setText('record')
        choose(dialog, extension)
        return QtWidgets.QDialog.Accepted
    monkeypatch.setattr(DlgNewFile, 'exec_', accept)
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question',
                        lambda *args: pytest.fail('Copybook creation asked for compile overrides'))
    app.file.request_new()
    path = root / 'copybooks' / ('record' + extension)
    assert path.exists() and path.read_text().strip() == ''
    assert isinstance(app.edit.current_editor, CobolCodeEdit)
    assert app.edit.current_editor.file.path == str(path)
    assert not app.win.ui.actionCompile.isEnabled()
    assert not app.win.ui.actionRun.isEnabled()
    assert not app.win.ui.menuProgramType.isEnabled()
    assert app.cobol.project_compile_action.isEnabled()
    calls = []
    monkeypatch.setattr(app.cobol, '_start_compilation', calls.append)
    app.cobol.compile_project()
    assert calls == [[str(source)]]
    assert str(path) not in project_sources(str(root), Settings().all_extensions + ['.cpy'])
    assert app.file.close_project()


def test_copybook_direct_compile_and_run_do_nothing(app, tmp_path, monkeypatch):
    root = Path(config.create_project(tmp_path, 'Project'))
    copybook = root / 'copybooks/record.cpy'
    copybook.write_text('       01 record-name pic x(20).\n')
    app.file.open_project(str(root))
    app.file.open_file(str(copybook))
    monkeypatch.setattr(app.cobol, '_start_compilation', lambda *args: pytest.fail('Copybook compiled as a program'))
    monkeypatch.setattr(QtWidgets.QInputDialog, 'getText', lambda *args: pytest.fail('Copybook run asked for arguments'))
    app.cobol.compile()
    app.cobol.run()
    app.cobol.enable_compile(True)
    app.cobol.enable_run(True)
    assert not app.win.ui.actionCompile.isEnabled()
    assert not app.win.ui.actionRun.isEnabled()
    assert not app.cobol._run_requested
    app.file.close_project()
