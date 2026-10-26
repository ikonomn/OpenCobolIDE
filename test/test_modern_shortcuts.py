"""Project shortcuts coexist with single-file compile keys and editor actions."""
from pyqode.qt import QtCore, QtWidgets
from PyQt5 import QtTest
from open_cobol_ide.shortcuts import SHORTCUTS, resolve
from open_cobol_ide import project_config as config


def test_modern_shortcuts_are_assigned_and_do_not_conflict(app, tmp_path):
    root = config.create_project(tmp_path, 'keys')
    source = tmp_path/'keys/src/main.cbl'
    source.write_text('       procedure division.\n           goback.\n')
    app.file.open_project(root)
    assigned = {}
    for label, key, path in SHORTCUTS:
        action = resolve(app,path)
        assert action.shortcut().toString() == key
        assert key not in assigned
        assigned[key] = action
    for other in app.win.findChildren(QtWidgets.QAction):
        key = other.shortcut().toString()
        if key in assigned:
            assert other is assigned[key], (key,other.text())
    assert app.win.ui.actionCompile.shortcut().toString() == 'F8'
    assert app.win.ui.actionRebuild.shortcut().toString() == 'Shift+F8'
    assert app.keyboard_shortcuts_action.shortcut().toString() == 'Ctrl+Alt+H'
    app.file.close_project()


def test_project_compile_and_rebuild_keyboard_routes(app,tmp_path,monkeypatch):
    root = config.create_project(tmp_path,'keyroutes')
    source = tmp_path/'keyroutes/src/main.cbl'
    source.write_text('       procedure division.\n           goback.\n')
    app.file.open_project(root)
    app.win.show()
    app.win.activateWindow()
    app.edit.current_editor.setFocus()
    app.app.processEvents()
    calls = []
    monkeypatch.setattr(app.cobol,'_start_compilation',
                        lambda paths=None,force_project=False: calls.append(force_project))
    QtTest.QTest.keyClick(app.edit.current_editor,QtCore.Qt.Key_F8,QtCore.Qt.ControlModifier)
    QtTest.QTest.keyClick(app.edit.current_editor,QtCore.Qt.Key_F8,
                         QtCore.Qt.ControlModifier|QtCore.Qt.ShiftModifier)
    app.app.processEvents()
    assert calls == [False,True]
    assert 'changed' in app.cobol.project_compile_action.toolTip()
    assert 'every' in app.cobol.project_rebuild_action.toolTip()
    app.file.close_project()
    assert not app.cobol.project_rebuild_action.isEnabled()


def test_program_type_shortcuts_ignore_copybooks(app,tmp_path):
    root = config.create_project(tmp_path,'copykeys')
    copybook = tmp_path/'copykeys/copybooks/record.cpy'
    copybook.write_text('       01 RECORD-ITEM PIC X.\n')
    app.file.open_project(root)
    app.file.open_file(str(copybook))
    app.win.ui.actionProgram.trigger()
    assert not app.win.ui.actionRun.isEnabled()
    app.file.close_project()
