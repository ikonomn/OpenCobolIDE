"""Window-wide shortcuts for the modern project workflow and supporting actions."""
from html import escape
from pyqode.qt import QtGui, QtWidgets

# Existing editor keys (including Ctrl+Shift+O, Ctrl+Shift+W and Ctrl+Alt+M)
# remain available. F8 and Shift+F8 retain their single-source meanings.
SHORTCUTS = (
    ('New Project', 'Ctrl+Alt+N', 'file.new_project_action'),
    ('Open Project', 'Ctrl+Alt+O', 'file.open_project_action'),
    ('Close Project', 'Ctrl+Alt+W', 'file.close_project_action'),
    ('Configure Project', 'Ctrl+Alt+P', 'file.configure_project_action'),
    ('Compile Project — changed files', 'Ctrl+F8', 'cobol.project_compile_action'),
    ('Rebuild Project — all files', 'Ctrl+Shift+F8', 'cobol.project_rebuild_action'),
    ('Project compiler settings', 'Ctrl+Alt+B', 'cobol.project_settings_action'),
    ('Source compiler settings', 'Ctrl+Alt+S', 'cobol.source_settings_action'),
    ('Automatic listing filename', 'Ctrl+Alt+G', 'cobol.listing_action'),
    ('Cancel compilation or run', 'Shift+F5', 'win.ui.actionCancel'),
    ('Background syntax checking', 'Ctrl+Alt+K', 'win.ui.actionEnableLinter'),
    ('Import preferences', 'Ctrl+Alt+I', 'win.ui.actionImport_preferences'),
    ('Export preferences', 'Ctrl+Alt+E', 'win.ui.actionExport_preferences'),
    ('Executable program override', 'Ctrl+Alt+X', 'win.ui.actionProgram'),
    ('Module program override', 'Ctrl+Alt+U', 'win.ui.actionSubprogram'),
    ('About OpenCobolIDE', 'Ctrl+F1', 'win.ui.actionAbout'),
    ('Report an issue', 'Ctrl+Shift+F1', 'win.ui.actionReport_a_bug'),
    ('Restore factory defaults', 'Ctrl+K, Ctrl+R', 'win.ui.actionRestore_factory_defaults'),
)


def resolve(app, path):
    obj = app
    for name in path.split('.'):
        obj = getattr(obj, name)
    return obj


def install_shortcuts(app):
    for label, key, path in SHORTCUTS:
        action = resolve(app, path)
        action.setShortcut(QtGui.QKeySequence(key))
        app.win.addAction(action)
    for key, name in [('Ctrl+Alt+1', 'dockWidgetFileSystem'),
                      ('Ctrl+Alt+2', 'dockWidgetNavPanel'),
                      ('Ctrl+Alt+3', 'dockWidgetOffsets'),
                      ('Ctrl+Alt+4', 'dockWidgetLogs')]:
        action = getattr(app.win.ui, name).toggleViewAction()
        action.setShortcut(QtGui.QKeySequence(key))
        app.win.addAction(action)
    action = app.win.ui.menu.addAction('Keyboard shortcuts...')
    action.setShortcut(QtGui.QKeySequence('Ctrl+Alt+H'))
    app.win.addAction(action)
    rows = [(label, key) for label, key, path in SHORTCUTS]
    rows += [('New file / copybook', 'Ctrl+N'), ('Open file', 'Ctrl+O'),
             ('Compile current file', 'F8'), ('Rebuild current file', 'Shift+F8'),
             ('Run current program', 'F5'), ('Offline guide', 'F1'),
             ('Show/hide file tree, outline, offsets, output', 'Ctrl+Alt+1 / 2 / 3 / 4'),
             ('Keyboard shortcuts', 'Ctrl+Alt+H')]
    text = '<table>' + ''.join('<tr><td>%s</td><td>&nbsp; %s</td></tr>' %
                              (escape(label), escape(key)) for label, key in rows) + '</table>'
    action.triggered.connect(lambda: QtWidgets.QMessageBox.information(
        app.win, 'Keyboard shortcuts', text))
    app.keyboard_shortcuts_action = action
