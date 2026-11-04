"""Preferences must stage runtime edits without changing project inheritance."""
from types import SimpleNamespace

import pytest

from open_cobol_ide import project_config as config
from open_cobol_ide.settings import Settings
from open_cobol_ide.view.dialogs.preferences import DlgPreferences


@pytest.fixture
def preferences(tmp_path, app):
    original = Settings().export_to_dict()
    root = config.create_project(tmp_path, 'preferences')
    controller = SimpleNamespace(app=SimpleNamespace(file=SimpleNamespace(project_root=root)))
    dialog = DlgPreferences(None, project_controller=controller)
    yield dialog, root, controller
    dialog.stop_backend()
    dialog.close()
    Settings().clear()
    Settings().import_from_dict(original)


def test_cancel_discards_runtime_and_debug(preferences):
    dialog, root, _ = preferences
    before = config.load(root)
    dialog.project_controls.use_runtime.setChecked(True)
    dialog.project_controls.debug.setChecked(True)
    dialog.reject()
    assert config.load(root) == before


def test_accept_saves_portable_runtime_and_debug_preserving_defaults(preferences):
    dialog, root, _ = preferences
    before = config.load(root)
    controls = dialog.project_controls
    controls.use_runtime.setChecked(True)
    controls.cwd.setCurrentText(root)
    controls.paths.setPlainText(root + '/data')
    controls.debug.setChecked(True)
    dialog.accept()
    saved = config.load(root)
    assert saved['runtime'] == {'accepted': True, 'working_directory': '.', 'data_directories': ['data']}
    assert saved['debug']['enabled'] is True
    assert saved['defaults'] == before['defaults']
    assert saved['sources'] == before['sources']


def test_open_and_accept_does_not_accept_suggestions(preferences):
    dialog, root, _ = preferences
    before = config.load(root)
    dialog.accept()
    assert config.load(root) == before


def test_debug_only_does_not_accept_runtime(preferences):
    dialog, root, _ = preferences
    dialog.project_controls.debug.setChecked(True)
    dialog.accept()
    saved = config.load(root)
    assert saved['debug']['enabled']
    assert not saved.get('runtime', {}).get('accepted')


def test_invalid_runtime_keeps_preferences_open(preferences, monkeypatch):
    from pyqode.qt import QtWidgets
    dialog, root, _ = preferences
    before = config.load(root)
    warnings = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', lambda *args: warnings.append(args))
    dialog.project_controls.use_runtime.setChecked(True)
    dialog.project_controls.cwd.setCurrentText('missing-folder')
    dialog.accept()
    assert warnings
    assert dialog.result() != dialog.Accepted
    assert config.load(root) == before


def test_reset_and_defaults_are_scoped_and_do_not_write(preferences):
    dialog, root, _ = preferences
    before = config.load(root)
    controls = dialog.project_controls
    controls.debug.setChecked(True)
    dialog.tabWidget.setCurrentWidget(dialog.tabProjects)
    controls.use_runtime.setChecked(True)
    dialog.reset()
    assert not controls.use_runtime.isChecked()
    assert controls.debug.isChecked()
    dialog.restore_defaults()
    assert controls.cwd.currentText() == 'bin'
    assert not controls.paths.toPlainText()
    dialog.tabWidget.setCurrentWidget(dialog.tabDebugger)
    dialog.restore_defaults()
    assert not controls.debug.isChecked()
    assert config.load(root) == before


def test_compiler_reset_does_not_duplicate_paths(preferences):
    dialog, _, _ = preferences
    Settings().copybook_paths = '/tmp/copy-one;/tmp/copy-two'
    Settings().library_search_path = '/tmp/library-one'
    dialog.tabWidget.setCurrentWidget(dialog.tabCompiler)
    dialog.reset()
    dialog.reset()
    assert [dialog.listWidgetCopyPaths.item(i).text() for i in range(dialog.listWidgetCopyPaths.count())] == ['/tmp/copy-one', '/tmp/copy-two']
    assert dialog.listWidgetLibPaths.count() == 1


def test_external_project_save_is_preserved_if_draft_unchanged(preferences):
    dialog, root, _ = preferences
    data = config.load(root)
    data['debug'] = {'enabled': True}
    data['runtime'] = {'accepted': True, 'working_directory': '.', 'data_directories': ['data']}
    config.save(root, data)
    dialog.accept()
    assert config.load(root) == data


def test_sql_entry_uses_existing_project_controller(preferences):
    dialog, _, controller = preferences
    called = []
    controller.edit_project_compiler_options = lambda: called.append(True)
    dialog.project_defaults_button.click()
    assert called == [True]
    assert [dialog.tabWidget.tabText(i) for i in range(dialog.tabWidget.count())] == [
        'Editor', 'Style', 'Compiler', 'Run', 'SQL COBOL', 'Projects', 'Debugger', 'GixSQL']


def test_preferences_without_project(app):
    dialog = DlgPreferences(None)
    try:
        assert dialog.project_controls is None
        assert not dialog.project_defaults_button.isEnabled()
        dialog.accept()
        assert dialog.result() == dialog.Accepted
    finally:
        dialog.stop_backend()
        dialog.close()


def test_compiler_check_apply_does_not_save_project_draft(preferences):
    dialog, root, _ = preferences
    before = config.load(root)
    dialog.project_controls.use_runtime.setChecked(True)
    dialog.project_controls.debug.setChecked(True)
    dialog.apply()
    assert config.load(root) == before


def test_disabling_runtime_preserves_folders_and_debug(tmp_path, app):
    root = config.create_project(tmp_path, 'accepted')
    data = config.load(root)
    data['runtime'] = {'accepted': True, 'working_directory': '.', 'data_directories': ['data']}
    data['debug'] = {'enabled': True}
    config.save(root, data)
    controller = SimpleNamespace(app=SimpleNamespace(file=SimpleNamespace(project_root=root)))
    dialog = DlgPreferences(None, project_controller=controller)
    try:
        dialog.project_controls.use_runtime.setChecked(False)
        dialog.accept()
        saved = config.load(root)
        assert saved['runtime'] == dict(data['runtime'], accepted=False)
        assert saved['debug'] == data['debug']
    finally:
        dialog.stop_backend()
        dialog.close()


def test_compiler_settings_removed_from_cobol_menu_and_keys_open_preferences(app, monkeypatch):
    texts = [action.text() for action in app.win.ui.menuCobol.actions()]
    assert not any('compiler settings' in text.lower() or 'compiler options' in text.lower() for text in texts)
    calls = []
    monkeypatch.setattr(app.edit, 'edit_preferences', lambda **kwargs: calls.append(kwargs))
    app.cobol.project_settings_action.setEnabled(True)
    app.cobol.project_settings_action.trigger()
    app.cobol.source_settings_action.trigger()
    assert calls == [{'page': 'Compiler'}, {'page': 'Compiler'}]


def test_file_compiler_preferences_routes_saved_source(preferences):
    dialog, root, controller = preferences
    from types import SimpleNamespace
    calls = []
    controller.edit_source_compiler_options = calls.append
    # Modal Preferences holds the source selected when it opens.
    dialog.current_source = root + '/src/current.cbl'
    dialog.source_settings_button.setEnabled(True)
    dialog.source_settings_button.click()
    assert calls == [root + '/src/current.cbl']


def test_gixsql_save_changes_only_paths_and_cancel_is_safe(preferences):
    dialog, root, controller = preferences
    data = config.load(root)
    data['defaults']['flags'] = ['-Wall']
    data['defaults']['environment'] = {'cob_copy_dir': 'copybooks'}
    config.save(root, data)
    checked = []
    controller.validate_project_settings = lambda *args: checked.append(args) or True
    dialog.gix_fields['gixsql_copy_dir'].setText(root + '/copybooks')
    dialog.accept()
    saved = config.load(root)
    assert saved['defaults']['flags'] == ['-Wall']
    assert saved['defaults']['environment'] == {'cob_copy_dir': 'copybooks', 'gixsql_copy_dir': 'copybooks'}
    assert checked
    assert saved['sources'] == data['sources']


def test_gixsql_reset_defaults_and_cancel(preferences):
    dialog, root, controller = preferences
    data = config.load(root)
    data['defaults']['environment'] = {'gixpp_path': '/opt/gix/bin/gixpp'}
    config.save(root, data)
    dialog.tabWidget.setCurrentWidget(dialog.tabGixSQL)
    dialog.reset()
    assert dialog.gix_fields['gixpp_path'].text() == '/opt/gix/bin/gixpp'
    dialog.restore_defaults()
    assert not dialog.gix_fields['gixpp_path'].text()
    dialog.reject()
    assert config.load(root) == data


def test_invalid_gixsql_does_not_save_runtime_drafts(preferences):
    dialog, root, controller = preferences
    before = config.load(root)
    controller.validate_project_settings = lambda *args: False
    dialog.project_controls.use_runtime.setChecked(True)
    dialog.gix_fields['gixpp_path'].setText('/missing/gixpp')
    dialog.accept()
    assert dialog.result() != dialog.Accepted
    assert config.load(root) == before



def test_debugger_preferences_persist_only_on_ok(app, monkeypatch):
    from pyqode.qt import QtWidgets
    original = Settings().export_to_dict()
    def accepted(dialog):
        dialog.debugger_command.setText('/opt/bin/cobgdb-python-gui')
        return QtWidgets.QDialog.Accepted
    monkeypatch.setattr(DlgPreferences, 'exec_', accepted)
    try:
        DlgPreferences.edit_preferences(None)
        assert Settings().debugger_command == '/opt/bin/cobgdb-python-gui'
        def canceled(dialog):
            dialog.debugger_command.setText('/discarded/launcher')
            dialog.apply()  # The Check compiler action calls this.
            return QtWidgets.QDialog.Rejected
        monkeypatch.setattr(DlgPreferences, 'exec_', canceled)
        with pytest.raises(ValueError):
            DlgPreferences.edit_preferences(None)
        assert Settings().debugger_command == '/opt/bin/cobgdb-python-gui'
    finally:
        Settings().clear()
        Settings().import_from_dict(original)


def test_preferences_can_open_debugger_without_a_target(preferences):
    dialog, root, controller = preferences
    calls = []
    controller.open_debugger = calls.append
    dialog.debugger_command.setText('/usr/bin/cobgdb-python-gui')
    dialog.open_debugger_button.click()
    assert calls == ['/usr/bin/cobgdb-python-gui']


def test_runtime_review_defaults_to_bin_even_when_data_is_discovered(preferences):
    dialog, root, _ = preferences
    from pathlib import Path
    Path(root, 'src/input.cbl').write_text('       SELECT INFILE ASSIGN TO "records.dat".\n')
    Path(root, 'data/records.dat').touch()
    dialog.project_controls.rescan()
    assert dialog.project_controls.cwd.currentText() == 'bin'
    assert 'data' in dialog.project_controls.paths.toPlainText()
