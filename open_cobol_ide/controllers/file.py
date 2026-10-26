"""
This module contains the FileController.

"""
import pickle
import weakref
import logging
import os
from pyqode.core import widgets
from pyqode.qt import QtGui, QtWidgets
from open_cobol_ide import system
from open_cobol_ide.view.editors import CobolCodeEdit
from open_cobol_ide.settings import Settings
from open_cobol_ide.view.dialogs.new_file import DlgNewFile
from .base import Controller
from open_cobol_ide.view.widgets import FileIconProvider


def _logger():
    return logging.getLogger(__name__)


UNC_WARNING = '''You are about to open a file using a UNC pathname.

UNC pathnames are not fully supported by the IDE, some features such as the file explorer tree view will not work. Depending on the compiler you're using, this might also lead to some compilation errors.

You will have better results if you map your share as a network drive...

Do you still want to continue opening this file?'''  # noqa


class FileController(Controller):
    """
    Controls file operations (new file, open, recent files, ...).

    """
    def __init__(self, app):
        super().__init__(app)
        self.recent_files_manager = widgets.RecentFilesManager(
            'OpenCobolIDE', 'OpenCobolIDE4')
        self.menu_recents = widgets.MenuRecentFiles(
            self.ui.menuFile, title='Recents',
            recent_files_manager=self.recent_files_manager,
            icon_provider=FileIconProvider())
        self.menu_recents.setIcon(QtGui.QIcon.fromTheme(
            'document-open-recent'))
        self.menu_recents.clear_icon = QtGui.QIcon.fromTheme(
            'edit-clear', QtGui.QIcon(':/ide-icons/rc/edit-clear.png'))
        self.menu_recents.open_requested.connect(self.open_file)
        self.menu_recents.clear_requested.connect(
            self.recent_files_manager.clear)
        self.ui.menuFile.clear()
        self.ui.menuFile.addAction(self.ui.actionNew)
        self.ui.menuFile.addAction(self.ui.actionOpen)
        self.project_root = None
        self._project_setup_dialog = None
        self.new_project_action = self.ui.menuFile.addAction('New Project...')
        self.new_project_action.triggered.connect(self.request_new_project)
        self.open_project_action = self.ui.menuFile.addAction('Open Project...')
        self.open_project_action.triggered.connect(self.request_open_project)
        self.configure_project_action = self.ui.menuFile.addAction('Configure Project...')
        self.configure_project_action.triggered.connect(self.show_project_setup)
        self.close_project_action = self.ui.menuFile.addAction('Close Project')
        self.close_project_action.triggered.connect(self.close_project)
        self._update_project_actions()
        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addMenu(self.menu_recents)
        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction(self.ui.actionImport_preferences)
        self.ui.menuFile.addAction(self.ui.actionExport_preferences)
        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction(self.ui.actionSave)
        self.ui.menuFile.addAction(self.ui.actionSaveAs)
        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction(self.ui.actionQuit)
        self.menu_recents.update_actions()
        self.recent_files_manager.updated.connect(
            self.menu_recents.update_actions)
        self.ui.actionOpen.triggered.connect(self.request_open)
        self.ui.actionNew.triggered.connect(self.request_new)
        self.ui.actionSave.triggered.connect(
            self.save_current)
        self.ui.actionImport_preferences.triggered.connect(
            self.import_preferences)
        self.ui.actionExport_preferences.triggered.connect(
            self.export_preferences)
        self.ui.actionSaveAs.triggered.connect(self.save_as)
        self.ui.actionQuit.triggered.connect(self.quit)
        self.ui.tabWidgetEditors.register_code_edit(CobolCodeEdit)
        self.ui.tabWidgetEditors.icon_provider_klass = FileIconProvider
        self.ui.tvFileSystem.set_icon_provider(FileIconProvider())
        self._warning_unc = False

    def request_open_project(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self.main_window, 'Open Project', Settings().last_path)
        if path:
            self.open_project(path, configure=True)

    @staticmethod
    def _inside_project(path, root):
        if not path:
            return False
        path = os.path.normcase(os.path.realpath(path))
        root = os.path.normcase(os.path.realpath(root))
        try:
            return os.path.commonpath([path, root]) == root
        except ValueError:
            return False

    def _update_project_actions(self):
        active = self.project_root is not None
        self.close_project_action.setEnabled(active)
        self.configure_project_action.setEnabled(active)
        cobol = getattr(self.app, 'cobol', None)
        if cobol is not None:
            cobol.project_compile_action.setEnabled(active)
            cobol.project_settings_action.setEnabled(active)

    def _can_change_project(self):
        cobol = getattr(self.app, 'cobol', None)
        thread = getattr(cobol, '_compilation_thread', None)
        if ((thread is not None and thread.isRunning()) or
                getattr(cobol, '_run_requested', False) or self.ui.consoleOutput.is_running):
            QtWidgets.QMessageBox.information(
                self.main_window, 'Project is busy',
                'Stop the current compilation or running program before closing or changing projects.')
            return False
        return True

    def _project_editors(self):
        """Collect project views across split editors and detached windows."""
        views, managers = [], set()

        def visit(manager):
            if id(manager) in managers:
                return
            managers.add(id(manager))
            for editor in manager.widgets(include_clones=True):
                if self._inside_project(editor.file.path, self.project_root):
                    if editor not in views:
                        views.append(editor)
            def detached(splitter):
                for window in tuple(splitter.main_tab_widget.detached_tabs):
                    child = window.centralWidget() if hasattr(window, 'centralWidget') else window
                    if hasattr(child, 'widgets'):
                        visit(child)
                for child in splitter.child_splitters:
                    detached(child)
            detached(manager)
        visit(self.ui.tabWidgetEditors)
        return views

    def _prepare_project_close(self):
        views = self._project_editors()
        dirty, seen = [], set()
        for view in views:
            editor = view.original or view
            if id(editor) not in seen:
                seen.add(id(editor))
                if editor.dirty:
                    dirty.append(editor)
        if dirty:
            filenames = '\n'.join(editor.file.path for editor in dirty)
            choice = QtWidgets.QMessageBox.question(
                self.main_window, 'Unsaved project files',
                'Save changes before closing this project?\n\n' + filenames,
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Save)
            if choice == QtWidgets.QMessageBox.Cancel:
                return None
            if choice == QtWidgets.QMessageBox.Save:
                for editor in dirty:
                    try:
                        saved = editor.parent_tab_widget.save_widget(editor)
                    except Exception as error:
                        QtWidgets.QMessageBox.warning(self.main_window, 'Cannot save project file', str(error))
                        return None
                    if not saved:
                        return None
                    # The legacy tab API can return True after a failed save.
                    if editor.dirty:
                        QtWidgets.QMessageBox.warning(
                            self.main_window, 'Cannot close project',
                            'The file was not saved. The project remains open:\n' + editor.file.path)
                        return None
            elif choice != QtWidgets.QMessageBox.Discard:
                return None
        return views

    def _release_project(self, views):
        if self._project_setup_dialog is not None:
            self._project_setup_dialog.close()
            self._project_setup_dialog = None
        self.project_root = None
        Settings().lock_fs_path = ''
        self.ui.btFSLock.setChecked(False)
        for editor in views:
            tab = editor.parent_tab_widget
            index = tab.indexOf(editor)
            if index >= 0:
                tab.remove_tab(index)
        manager = self.ui.tabWidgetEditors
        remaining = manager.widgets(include_clones=True)
        current = manager.current_widget()
        if current not in remaining:
            current = remaining[0] if remaining else None
        manager._current = weakref.ref(current) if current is not None else None
        if current is None:
            self.app.cobol.enable_compile(False)
            self.app.cobol.enable_run(False)
        tree = self.ui.tvFileSystem
        tree._path_to_set = None
        tree._root_path = None
        tree.root_path = ''
        tree.setModel(None)
        self.ui.errorsTable.clear()
        self.ui.textEditCompilerOutput.clear()
        self.ui.consoleOutput.clear()
        self._update_project_actions()

    def close_project(self):
        if self.project_root is None:
            return True
        if not self._can_change_project():
            return False
        old_root = self.project_root
        views = self._prepare_project_close()
        if views is None:
            return False
        self._release_project(views)
        Settings().last_path = os.path.dirname(old_root)
        editor = self.ui.tabWidgetEditors.current_widget()
        if editor is None:
            self.main_window.setWindowTitle(self.app.title)
            self.app.view.show_home_page()
        else:
            self.app.view.show_edit_page()
            self.ui.tvFileSystem.set_root_path(os.path.dirname(editor.file.path))
            self.main_window.setWindowTitle('%s [%s] - %s' % (
                editor.file.name, editor.file.path, self.app.title))
        return True

    def open_project(self, path, configure=False):
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            raise NotADirectoryError(path)
        if not self._can_change_project():
            return False
        # Validate an existing document before asking to leave the current project.
        from open_cobol_ide.project_config import config_path, load
        try:
            if config_path(path).is_file():
                load(path)
        except (ValueError, OSError) as error:
            QtWidgets.QMessageBox.warning(self.main_window, 'Cannot open project', str(error))
            return False
        changing = (self.project_root is not None and
                    os.path.normcase(os.path.realpath(path)) !=
                    os.path.normcase(os.path.realpath(self.project_root)))
        views = self._prepare_project_close() if changing else []
        if views is None:
            return False
        try:
            Settings().initialize_project_config(path)
        except (ValueError, OSError) as error:
            QtWidgets.QMessageBox.warning(self.main_window, 'Cannot open project', str(error))
            return False
        if changing:
            self._release_project(views)
        self.project_root = path
        Settings().register_project(path)
        self._update_project_actions()
        self.app.view.show_edit_page()
        self.ui.tvFileSystem.set_root_path(path)
        self.ui.dockWidgetFileSystem.show()
        from open_cobol_ide.project import project_sources
        sources = project_sources(path, Settings().all_extensions)
        for source in sources:
            self.open_file(source)
        if not sources:
            self.main_window.setWindowTitle('%s [%s] - %s' % (os.path.basename(path), path, self.app.title))
        Settings().last_path = path
        if configure:
            self.show_project_setup()
        return True

    def request_new_project(self):
        if not self._can_change_project():
            return
        from open_cobol_ide.view.dialogs.project_setup import NewProjectDialog
        from open_cobol_ide.project_config import create_project
        dialog = NewProjectDialog(self.main_window, Settings().last_path)
        while dialog.exec_() == QtWidgets.QDialog.Accepted:
            try:
                parent = dialog.directory.text().strip()
                if not os.path.isdir(parent):
                    raise ValueError('Choose an existing parent folder.')
                root = create_project(parent, dialog.name.text())
            except (ValueError, OSError) as error:
                QtWidgets.QMessageBox.warning(self.main_window, 'Cannot create project', str(error))
                continue
            self.open_project(root, configure=True)
            break

    def show_project_setup(self):
        if not self.project_root:
            QtWidgets.QMessageBox.information(self.main_window, 'Configure Project', 'Open a project first.')
            return
        from open_cobol_ide.view.dialogs.project_setup import ProjectSetupDialog
        if self._project_setup_dialog is not None:
            self._project_setup_dialog.close()
        self._project_setup_dialog = ProjectSetupDialog(self.project_root, self.app.cobol, self.main_window)
        self._project_setup_dialog.show()

    def open_created_file(self, path):
        self.open_file(path)
        if os.path.splitext(path)[1].lower() == '.cpy':
            return
        if Settings().project_root_for_source(path):
            choice = QtWidgets.QMessageBox.question(
                self.main_window, 'Source compiler settings',
                'This source inherits the project settings. Configure source overrides now?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.Yes:
                self.app.cobol.edit_source_compiler_options(path)

    def request_new(self, path=None):
        """
        Requests the creation of a new file, show the new file wizard and open
        if wizard completed sucessfully.

        """
        if not path and self.project_root:
            source_dir = os.path.join(self.project_root, 'src')
            path = source_dir if os.path.isdir(source_dir) else self.project_root
        if path and os.path.isfile(path):
            path = os.path.abspath(os.path.join(path, os.pardir))
        path = DlgNewFile.create_new_file(self.main_window, path=path)
        if path:
            self.open_created_file(path)

    def request_open(self):
        """
        Prompts the user for a file to open and open it.
        """
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self.main_window, 'Open a file', directory=Settings().last_path,
            filter=widgets.splittable_tab_widget.CodeEditTabWidget.get_filter(
                'text/x-cobol') + ';;Other files (*)')
        if paths:
            for path in paths:
                self.open_file(path)

    def open_file(self, path):
        """
        Open a file in the edit view. If there is an editor already open for
        the requested file, we simply give it the focus.

        :param path: path of the file to open.
        """
        if system.windows:
            if not self._warning_unc and os.path.splitunc(path)[0]:
                answer = QtWidgets.QMessageBox.warning(
                    self.main_window, 'UNC pathnames not fully supported',
                    UNC_WARNING,
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No)
                if answer == QtWidgets.QMessageBox.No:
                    return
        self.app.edit.add_editor(path)
        self.app.view.show_edit_page()
        self.app.file.recent_files_manager.open_file(path)
        Settings().last_path = path

    def save_current(self):
        try:
            self.ui.tabWidgetEditors.save_current()
        except PermissionError as e:
            QtWidgets.QMessageBox.warning(
                self.main_window, 'Failed to save file',
                str(e))

    def save_as(self):
        """
        Saves the currend editor content as.
        """
        try:
            fn = self.ui.tabWidgetEditors.save_current_as()
        except PermissionError:
            QtWidgets.QMessageBox.warning(
                self.main_window, 'Failed to save file',
                'Failed to save file, permission error...')
        else:
            self.recent_files_manager.open_file(fn)
            Settings().last_path = fn
        editor = self.ui.tabWidgetEditors.current_widget()
        self.main_window.setWindowTitle(
            '%s [%s] - %s' % (
                editor.file.name, editor.file.path, self.app.title))

    def quit(self):
        """
        Quits the application, but contrarily asks the user first.
        """
        if QtWidgets.QMessageBox.question(
                self.main_window, 'Quit OpenCobolIDE?',
                'Are you sure you want to quit OpenCobolIDE?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
            _logger().debug('quit action triggered')
            self.app.exit()

    def import_preferences(self):
        """
        Import preferences from a json file.
        """
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.main_window, 'Import preferences',
            os.path.join(os.path.expanduser('~'), 'ocide_preferences.dat'))
        if path:
            try:
                with open(path, 'rb') as f:
                    Settings().import_from_dict(pickle.load(f))
            except (ValueError, IOError, OSError):
                _logger().exception('failed to import preferences')
                QtWidgets.QMessageBox.information(
                    self.main_window, 'Import preferences failure',
                    'Failed to restore preferences. See the log for more '
                    'information...')
            else:
                QtWidgets.QMessageBox.information(
                    self.main_window, 'Preferences imported',
                    'Preferences successfully imported!')

    def export_preferences(self):
        """
        Export preferences to a json file
        """
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.main_window, "Export preferences",
            os.path.join(os.path.expanduser('~'), 'ocide_preferences.dat'))
        if path:
            try:
                with open(path, 'wb') as f:
                    pickle.dump(Settings().export_to_dict(), f)
            except (ValueError, IOError, OSError):
                _logger().exception('failed to export preferences')
                QtWidgets.QMessageBox.information(
                    self.main_window, 'Export preferences failure',
                    'Failed to export preferences. See the log for more '
                    'information...')
            else:
                QtWidgets.QMessageBox.information(
                    self.main_window, 'Preferences exported',
                    'Preferences successfully exported!')
