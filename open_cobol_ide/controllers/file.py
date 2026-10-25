"""
This module contains the FileController.

"""
import pickle
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

    def open_project(self, path, configure=False):
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            raise NotADirectoryError(path)
        try:
            Settings().initialize_project_config(path)
        except (ValueError, OSError) as error:
            QtWidgets.QMessageBox.warning(self.main_window, 'Cannot open project', str(error))
            return
        self.project_root = path
        Settings().register_project(path)
        self.app.view.show_edit_page()
        self.ui.tvFileSystem.set_root_path(path)
        self.ui.dockWidgetFileSystem.show()
        from open_cobol_ide.project import project_sources
        for source in project_sources(path, Settings().all_extensions):
            self.open_file(source)
        Settings().last_path = path
        if configure:
            self.show_project_setup()

    def request_new_project(self):
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
