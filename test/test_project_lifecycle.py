"""Close/switch project isolation, unsaved changes and active work guards."""
from pathlib import Path
from types import SimpleNamespace
import pytest
from pyqode.qt import QtCore, QtWidgets
from open_cobol_ide import project_config as config
from open_cobol_ide.controllers.view import Page


@pytest.fixture
def clean_workspace(app):
    for editor in app.win.ui.tabWidgetEditors.widgets(include_clones=True):
        editor.document().setModified(False)
    app.file.close_project()
    app.win.ui.tabWidgetEditors.close_all()
    app.win.show()
    app.app.processEvents()
    yield app
    for editor in app.win.ui.tabWidgetEditors.widgets(include_clones=True):
        editor.document().setModified(False)
    app.file.close_project()
    app.win.ui.tabWidgetEditors.close_all()


def make_project(parent, name, portable=True):
    root = parent / name
    if portable:
        config.create_project(parent, name)
    else:
        (root / 'src').mkdir(parents=True)
    source = root / 'src/shared.cbl'
    source.write_text('       identification division.\n       program-id. example.\n'
                      '       procedure division.\n           goback.\n')
    return root, source


def paths(app):
    return {editor.file.path for editor in app.win.ui.tabWidgetEditors.widgets(include_clones=True)}


def dirty_editor(app):
    editor = app.edit.current_editor
    editor.appendPlainText('      * Unsaved project edit')
    assert editor.dirty
    return editor


def test_close_project_menu_clears_context_but_keeps_files(clean_workspace, tmp_path):
    app = clean_workspace
    assert not app.file.close_project_action.isEnabled()
    assert not app.cobol.project_compile_action.isEnabled()
    root, source = make_project(tmp_path, 'First')
    before = source.read_bytes()
    assert app.file.open_project(str(root), configure=True)
    review = app.file._project_setup_dialog
    app.win.ui.textEditCompilerOutput.setPlainText('old build output')
    app.file.close_project_action.trigger()
    assert app.file.project_root is None
    assert not paths(app)
    assert not review.isVisible()
    assert app.file._project_setup_dialog is None
    assert app.win.ui.tvFileSystem.root_path == ''
    assert not app.file.close_project_action.isEnabled()
    assert not app.file.configure_project_action.isEnabled()
    assert not app.cobol.project_compile_action.isEnabled()
    assert not app.cobol.project_settings_action.isEnabled()
    assert app.win.ui.textEditCompilerOutput.toPlainText() == ''
    assert source.read_bytes() == before
    assert config.config_path(root).is_file()
    assert app.win.ui.stackedWidget.currentIndex() == int(Page.HOME)


def test_switch_same_named_sources_closes_old_tabs_and_compiles_only_new(clean_workspace, tmp_path, monkeypatch):
    app = clean_workspace
    old, first = make_project(tmp_path, 'First')
    new, second = make_project(tmp_path, 'Second')
    app.file.open_project(str(old), configure=True)
    review = app.file._project_setup_dialog
    assert app.file.open_project(str(new))
    assert paths(app) == {str(second)}
    assert app.file.project_root == str(new)
    assert app.win.ui.tvFileSystem.root_path == str(new)
    assert not review.isVisible()
    calls = []
    monkeypatch.setattr(app.cobol, '_start_compilation', lambda paths, **kw: calls.append(paths))
    app.cobol.compile_project()
    assert calls == [[str(second)]]
    assert first.is_file()


@pytest.mark.parametrize('choice', [QtWidgets.QMessageBox.Save, QtWidgets.QMessageBox.Discard])
def test_switch_save_or_discard(clean_workspace, tmp_path, monkeypatch, choice):
    app = clean_workspace
    old, first = make_project(tmp_path, 'First')
    new, second = make_project(tmp_path, 'Second')
    app.file.open_project(str(old))
    before = first.read_text()
    editor = dirty_editor(app)
    changed = editor.toPlainText()
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question', lambda *args: choice)
    assert app.file.open_project(str(new))
    assert paths(app) == {str(second)}
    assert first.read_text() == (changed.rstrip('\n') + '\n' if choice == QtWidgets.QMessageBox.Save else before)


def test_cancel_switch_keeps_old_context_and_does_not_create_config(clean_workspace, tmp_path, monkeypatch):
    app = clean_workspace
    old, first = make_project(tmp_path, 'First')
    new, second = make_project(tmp_path, 'Second', portable=False)
    app.file.open_project(str(old), configure=True)
    review = app.file._project_setup_dialog
    editor = dirty_editor(app)
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question', lambda *args: QtWidgets.QMessageBox.Cancel)
    assert not app.file.open_project(str(new))
    assert app.file.project_root == str(old)
    assert paths(app) == {str(first)}
    assert editor.dirty and review.isVisible()
    assert app.win.ui.tvFileSystem.root_path == str(old)
    assert not config.config_path(new).exists()


def test_cancel_close_keeps_project_open(clean_workspace, tmp_path, monkeypatch):
    app = clean_workspace
    root, source = make_project(tmp_path, 'First')
    app.file.open_project(str(root))
    dirty_editor(app)
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question', lambda *args: QtWidgets.QMessageBox.Cancel)
    assert not app.file.close_project()
    assert app.file.project_root == str(root)
    assert paths(app) == {str(source)}
    assert app.file.close_project_action.isEnabled()


@pytest.mark.parametrize('failure', ['cancel_save', 'still_dirty', 'exception'])
def test_failed_save_does_not_close_any_tabs(clean_workspace, tmp_path, monkeypatch, failure):
    app = clean_workspace
    old, first = make_project(tmp_path, 'First')
    second = old / 'src/second.cbl'
    second.write_text(first.read_text())
    new, target = make_project(tmp_path, 'Second', portable=False)
    app.file.open_project(str(old))
    editor = dirty_editor(app)
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question', lambda *args: QtWidgets.QMessageBox.Save)
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', lambda *args: None)
    def save(widget):
        if failure == 'exception': raise OSError('disk full')
        return failure == 'still_dirty'
    monkeypatch.setattr(editor.parent_tab_widget, 'save_widget', save)
    assert not app.file.open_project(str(new))
    assert app.file.project_root == str(old)
    assert paths(app) == {str(first), str(second)}
    assert editor.dirty
    assert not config.config_path(new).exists()


def test_invalid_target_does_not_prompt_or_close_old_project(clean_workspace, tmp_path, monkeypatch):
    app = clean_workspace
    old, first = make_project(tmp_path, 'First')
    new, second = make_project(tmp_path, 'Second')
    config.config_path(new).write_text('{broken')
    app.file.open_project(str(old))
    editor = dirty_editor(app)
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question', lambda *args: pytest.fail('Target was not validated first'))
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', lambda *args: None)
    assert not app.file.open_project(str(new))
    assert app.file.project_root == str(old)
    assert editor.dirty and paths(app) == {str(first)}


def test_reopening_same_project_preserves_unsaved_editor(clean_workspace, tmp_path, monkeypatch):
    app = clean_workspace
    root, source = make_project(tmp_path, 'First')
    app.file.open_project(str(root))
    editor = dirty_editor(app)
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question', lambda *args: pytest.fail('Same-project reopen prompted'))
    assert app.file.open_project(str(root / '..' / root.name))
    assert paths(app) == {str(source)}
    assert app.edit.current_editor is editor and editor.dirty


def test_closing_last_source_keeps_project_menu_accessible(clean_workspace, tmp_path):
    app = clean_workspace
    root, source = make_project(tmp_path, 'First')
    app.file.open_project(str(root))
    app.win.ui.tabWidgetEditors.close_document(str(source))
    assert app.file.project_root == str(root)
    assert app.file.close_project_action.isEnabled()
    assert app.win.ui.stackedWidget.currentIndex() == int(Page.EDIT)
    assert root.name in app.win.windowTitle()
    assert app.file.close_project()


@pytest.mark.parametrize('busy', ['compile', 'run_request', 'console'])
def test_busy_project_cannot_close_or_switch(clean_workspace, tmp_path, monkeypatch, busy):
    app = clean_workspace
    old, first = make_project(tmp_path, 'First')
    new, second = make_project(tmp_path, 'Second', portable=False)
    app.file.open_project(str(old))
    with monkeypatch.context() as patch:
        patch.setattr(QtWidgets.QMessageBox, 'information', lambda *args: None)
        if busy == 'compile':
            patch.setattr(app.cobol, '_compilation_thread', SimpleNamespace(isRunning=lambda: True))
        elif busy == 'run_request':
            patch.setattr(app.cobol, '_run_requested', True)
        else:
            patch.setattr(type(app.win.ui.consoleOutput), 'is_running', property(lambda self: True))
        assert not app.file.close_project()
        assert not app.file.open_project(str(new))
        assert app.file.project_root == str(old)
        assert paths(app) == {str(first)}
        assert not config.config_path(new).exists()


def test_close_leaves_unrelated_unsaved_file_alone(clean_workspace, tmp_path, monkeypatch):
    app = clean_workspace
    root, source = make_project(tmp_path, 'First')
    outside = tmp_path / 'outside.cbl'
    outside.write_text(source.read_text())
    app.file.open_project(str(root))
    app.file.open_file(str(outside))
    editor = dirty_editor(app)
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question', lambda *args: pytest.fail('Unrelated file prompted'))
    assert app.file.close_project()
    assert app.file.project_root is None
    assert paths(app) == {str(outside)}
    assert editor.dirty
    assert app.win.ui.tvFileSystem.root_path == str(tmp_path)


def test_split_project_views_close_with_one_unsaved_prompt(clean_workspace, tmp_path, monkeypatch):
    app = clean_workspace
    root, source = make_project(tmp_path, 'First')
    app.file.open_project(str(root))
    editor = app.edit.current_editor
    app.win.ui.tabWidgetEditors.split(editor, QtCore.Qt.Vertical)
    dirty_editor(app)
    assert len(app.file._project_editors()) == 2
    calls = []
    def discard(*args):
        calls.append(args)
        return QtWidgets.QMessageBox.Discard
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question', discard)
    assert app.file.close_project()
    assert len(calls) == 1
    assert not paths(app)


def test_switch_closes_detached_project_source(clean_workspace, tmp_path, monkeypatch):
    app = clean_workspace
    old, first = make_project(tmp_path, 'First')
    new, second = make_project(tmp_path, 'Second')
    app.file.open_project(str(old))
    tab = app.edit.current_editor.parent_tab_widget
    monkeypatch.setattr(tab, 'tab_under_menu', lambda: tab.indexOf(app.edit.current_editor))
    tab.detach_tab()
    assert len(app.file._project_editors()) == 1
    assert app.file.open_project(str(new))
    assert paths(app) == {str(second)}
    assert not tab.detached_tabs


def test_rapid_open_close_processes_pending_cursor_callbacks(clean_workspace, tmp_path):
    app = clean_workspace
    for index in range(4):
        root, source = make_project(tmp_path, 'Project%d' % index)
        assert app.file.open_project(str(root))
        assert app.file.close_project()
        app.app.processEvents()
        assert app.file.project_root is None and not paths(app)


@pytest.mark.parametrize('status,expected_errors', [(0, 0), (8, 1)])
def test_native_warning_diagnostics_do_not_block_run(clean_workspace, tmp_path,
                                                    status, expected_errors, monkeypatch):
    from open_cobol_ide.compilers import GnuCobolCompiler
    app = clean_workspace
    root, source = make_project(tmp_path, 'native-diagnostics')
    app.file.open_project(str(root))
    output = ('cobc: invalid parameter: -I\n'
              'cobc: ignoring nonexistent directory "/usr/share/gixsql/copy"\n')
    messages = GnuCobolCompiler.parse_output(output, str(root))
    app.cobol._errors = 0
    app.cobol._on_file_compiled(str(source), status, messages)
    assert app.cobol._errors == expected_errors
    launched = []
    monkeypatch.setattr(app.cobol, '_run', lambda: launched.append(True))
    app.cobol._run_requested = True
    app.cobol._on_compilation_finished()
    assert bool(launched) == (status == 0)


def test_opened_parent_controls_sources_with_nested_config(clean_workspace, tmp_path):
    from open_cobol_ide.settings import Settings
    from open_cobol_ide.compilers import compile_with_build_script
    from open_cobol_ide.project_validation import validate_project
    app = clean_workspace
    root, source = make_project(tmp_path, 'parent-project')
    source.write_text('       identification division.\n       program-id. example.\n'
                      '       data division.\n       working-storage section.\n'
                      '       COPY copybook.\n       procedure division.\n           goback.\n')
    (root/'copybooks/copybook.cpy').write_text('       01 VALUE-ITEM PIC X.\n')
    nested = root/'src'
    config.save(nested, config.default_config(nested))
    nested_before = config.config_path(nested).read_bytes()
    assert config.find_root(source) == str(nested)
    assert app.file.open_project(str(root))
    assert config.find_root(source) == str(root)
    assert Settings().project_root_for_source(str(source)) == str(root)
    assert not [d for d in validate_project(str(root), Settings()) if d['level']=='error']
    status, messages = compile_with_build_script(str(source))
    assert status == 0, messages
    assert (root/'bin/shared').exists()
    assert (root/'build/shared.lst').exists()
    from open_cobol_ide.linter import lint
    from pyqode.core.modes import CheckerMessages
    context = app.edit.current_editor.linter_mode.request_context()
    assert context['project_root'] == str(root)
    # Simulate a backend with no session state of its own.
    config.set_active_root(None)
    lint_messages = lint(dict(context, code=source.read_text(), path=str(source)))
    assert not [m for m in lint_messages if m[1] == CheckerMessages.ERROR]
    assert config.get_active_root() is None
    config.set_active_root(root)
    assert config.config_path(nested).read_bytes() == nested_before
    assert app.file.close_project()
    assert config.find_root(source) == str(nested)
    # Explicitly selecting the nested project still makes it the active root.
    assert app.file.open_project(str(nested))
    assert Settings().project_root_for_source(str(source)) == str(nested)


def test_open_single_file_detects_project_and_keeps_standalone_tab(clean_workspace, tmp_path):
    app = clean_workspace
    loose = tmp_path/'standalone.cbl'
    loose.write_text('       identification division.\n')
    app.file.open_file(str(loose))
    root, source = make_project(tmp_path, 'detected-project')
    app.file.open_file(str(source))
    assert app.file.project_root == str(root)
    assert config.find_root(source) == str(root)
    assert str(loose) in paths(app)
    assert app.edit.current_editor.file.path == str(source)


def test_open_single_file_with_two_projects_asks_owner(clean_workspace, tmp_path, monkeypatch):
    app = clean_workspace
    root, source = make_project(tmp_path, 'parent')
    config.save(root/'src', config.default_config(root/'src'))
    choices = []
    def choose(parent, title, label, items, *args):
        choices.extend(items)
        return str(root), True
    monkeypatch.setattr(QtWidgets.QInputDialog, 'getItem', choose)
    app.file.open_file(str(source))
    assert set(choices) == {str(root), str(root/'src')}
    assert app.file.project_root == str(root)
    assert config.find_root(source) == str(root)


def test_open_foreign_project_file_does_not_switch_current_project(clean_workspace, tmp_path):
    app = clean_workspace
    root, source = make_project(tmp_path, 'first')
    other, other_source = make_project(tmp_path, 'other')
    app.file.open_project(str(root))
    app.file.open_file(str(other_source))
    assert app.file.project_root == str(root)
    assert str(source) in paths(app)
    assert str(other_source) in paths(app)
    assert str(other) in app.win.statusBar().currentMessage()
