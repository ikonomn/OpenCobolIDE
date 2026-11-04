import os
import sys
from pyqode.core.api.syntax_highlighter import PYGMENTS_STYLES, ColorScheme
from pyqode.qt import QtCore, QtGui, QtWidgets
from open_cobol_ide import system, compilers
from open_cobol_ide.enums import GnuCobolStandard
from open_cobol_ide.settings import Settings
from open_cobol_ide.view.forms import dlg_preferences_ui
from open_cobol_ide.view.dialogs.check_compiler import DlgCheckCompiler
from open_cobol_ide.view.dialogs.cobc_help import DlgCobcHelp
from open_cobol_ide.path_utils import clean_directory_path, clean_path_list

DEFAULT_TEMPLATE = '''      * Author:
      * Date:
      * Purpose:
      * Tectonics: cobc
       IDENTIFICATION DIVISION.
      *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
       PROGRAM-ID. YOUR-PROGRAM-NAME.
       ENVIRONMENT DIVISION.
      *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
       CONFIGURATION SECTION.
      *-----------------------
       INPUT-OUTPUT SECTION.
      *-----------------------
       DATA DIVISION.
      *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
       FILE SECTION.
      *-----------------------
       WORKING-STORAGE SECTION.
      *-----------------------
       PROCEDURE DIVISION.
      *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
       MAIN-PROCEDURE.
      **
      * The main procedure of the program
      **
            DISPLAY "Hello world"
            STOP RUN.
      ** add other procedures here
       END PROGRAM YOUR-PROGRAM-NAME.

'''


class DlgPreferences(QtWidgets.QDialog, dlg_preferences_ui.Ui_Dialog):
    flags_in_checkbox = [
        '-g', '-ftrace', '-ftraceall', '-fdebugging-line', '-static', '-debug', '-W', '-Wall'
    ]

    def __init__(self, parent, project_controller=None):
        super().__init__(parent, QtCore.Qt.WindowSystemMenuHint |
                         QtCore.Qt.WindowTitleHint |
                         QtCore.Qt.WindowCloseButtonHint)
        self.setupUi(self)
        self.project_controller = project_controller
        self.project_controls = None
        self.gix_fields = {}
        self._gix_initial = {}
        self._setup_project_pages()
        self._help_dlg = None
        themes = system.icon_themes()
        if themes:
            self.comboBoxIconTheme.addItems(themes)
        else:
            self.comboBoxIconTheme.hide()
            self.lblIconTheme.hide()
        self.tabWidget.setTabIcon(0, QtGui.QIcon.fromTheme(
            'accessories-text-editor',
            QtGui.QIcon(':/ide-icons/rc/cobol-mimetype.png')))
        theme = 'application-x-executable'
        if QtGui.QIcon.hasThemeIcon('run-build'):
            theme = 'run-build'
        self.tabWidget.setTabIcon(2, QtGui.QIcon.fromTheme(
            theme, QtGui.QIcon(':/ide-icons/rc/application-x-executable.png')))
        self.tabWidget.setTabIcon(1, QtGui.QIcon.fromTheme(
            'applications-graphics',
            QtGui.QIcon(':/ide-icons/rc/applications-graphics.png')))
        self.tabWidget.setTabIcon(3, QtGui.QIcon.fromTheme(
            'media-playback-start', QtGui.QIcon(
                ':/ide-icons/rc/media-playback-start.png')))
        icon_add = QtGui.QIcon.fromTheme(
            'list-add', QtGui.QIcon(':/ide-icons/rc/list-add.png'))
        icon_remove = QtGui.QIcon.fromTheme(
            'list-remove', QtGui.QIcon(':/ide-icons/rc/list-remove.png'))
        icon_open_folder = QtGui.QIcon.fromTheme(
            'folder-open', QtGui.QIcon(':/ide-icons/rc/document-open.png'))
        icon_clear = QtGui.QIcon.fromTheme(
            'edit-clear', QtGui.QIcon(':/ide-icons/rc/edit-clear.png'))
        self.bt_add_run_env.setIcon(icon_add)
        self.bt_rm_run_env.setIcon(icon_remove)
        self.bt_clear_run_env.setIcon(icon_clear)
        self.btAddAbsoluteCopyPath.setIcon(icon_open_folder)
        self.btAddRelativeCopyPath.setIcon(icon_add)
        self.btRemoveCopyPath.setIcon(icon_remove)
        self.toolButtonAddLibPath.setIcon(icon_open_folder)
        self.toolButtonAddRelativeLibPath.setIcon(icon_add)
        self.toolButtonRemoveLibPath.setIcon(icon_remove)
        self.toolButtonCheckCompiler.setIcon(QtGui.QIcon.fromTheme(
            'emblem-checked',
            QtGui.QIcon(':/ide-icons/rc/emblem-checked.png')))

        self.buttonBox.button(self.buttonBox.Reset).clicked.connect(self.reset)
        self.buttonBox.button(self.buttonBox.RestoreDefaults).clicked.connect(
            self.restore_defaults)
        self.checkBoxRunExtTerm.toggled.connect(
            self.lineEditRunTerm.setEnabled)
        self.listWidgetColorSchemes.currentItemChanged.connect(
            self.update_color_scheme_preview)
        self.plainTextEdit.setPlainText(DEFAULT_TEMPLATE, '', '')
        self.lineEditDbpre.setReadOnly(True)
        self.lineEditDbpreFramework.setReadOnly(True)
        self.lineEditCobmysqlapi.setReadOnly(True)
        self.toolButtonDbpre.clicked.connect(self._select_dbpre)
        self.toolButtonDbpreFramework.clicked.connect(
            self._select_dbpre_framework)
        self.toolButtonCobMySqlApiPath.clicked.connect(
            self._select_cobmysqlapi)
        self.checkBoxShowDbPass.stateChanged.connect(
            self._on_show_pass_state_changed)
        self.toolButtonVCVARS.clicked.connect(self._select_vcvarsall)
        self.toolButtonCustomCompilerPath.clicked.connect(
            self._select_custom_compiler_path)
        self.toolButtonAddLibPath.clicked.connect(self._add_lib_path)
        self.toolButtonAddRelativeLibPath.clicked.connect(
            self._add_rel_lib_path)
        self.toolButtonRemoveLibPath.clicked.connect(self._rm_lib_path)
        self.btAddAbsoluteCopyPath.clicked.connect(self._add_copy_path)
        self.btAddRelativeCopyPath.clicked.connect(
            self._add_rel_copy_path)
        self.btRemoveCopyPath.clicked.connect(self._rm_copy_path)
        self.toolButtonESQLOC.clicked.connect(self._select_esqloc)
        self.btCompilerFlagsHelp.clicked.connect(self._show_gnu_cobol_help)
        if not system.windows:
            self.labelVCVARS.hide()
            self.lineEditVCVARS.hide()
            self.toolButtonVCVARS.hide()
            self.combo_arch.hide()
            self.stackedWidgetSQL.setCurrentIndex(0)
        else:
            self.stackedWidgetSQL.setCurrentIndex(1)
        self.toolButtonCheckCompiler.clicked.connect(self._check_compiler)
        self.cbPATH.stateChanged.connect(self.PATH.setEnabled)
        self.cbCOB_CONFIG_DIR.stateChanged.connect(
            self.COB_CONFIG_DIR.setEnabled)
        self.cbCOB_COPY_DIR.stateChanged.connect(self.COB_COPY_DIR.setEnabled)
        self.cbCOB_INCLUDE_PATH.stateChanged.connect(
            self.COB_INCLUDE_PATH.setEnabled)
        self.cbCOB_LIB_PATH.stateChanged.connect(self.COB_LIB_PATH.setEnabled)

        self.PATH.setEnabled(self.cbPATH.isChecked())
        self.COB_CONFIG_DIR.setEnabled(self.cbCOB_CONFIG_DIR.isChecked())
        self.COB_COPY_DIR.setEnabled(self.cbCOB_COPY_DIR.isChecked())
        self.COB_INCLUDE_PATH.setEnabled(self.cbCOB_INCLUDE_PATH.isChecked())
        self.COB_LIB_PATH.setEnabled(self.cbCOB_LIB_PATH.isChecked())

        self.bt_add_run_env.clicked.connect(self._add_run_env_variable)
        self.bt_rm_run_env.clicked.connect(self._rm_run_env_variable)
        self.bt_clear_run_env.clicked.connect(self._clear_run_env)

        self._margin_spin_boxes = [
            self.spin_box_margin_1,
            self.spin_box_margin_2,
            self.spin_box_margin_3,
            self.spin_box_margin_4
        ]

        self._margin_color_pickers = [
            self.color_picker_1,
            self.color_picker_2,
            self.color_picker_3,
            self.color_picker_4
        ]

        self.bt_working_dir.clicked.connect(self._select_working_dir)

        self.initial_settings = Settings().export_to_dict()
        self.reset(all_tabs=True)

    def _setup_project_pages(self):
        # Append pages so existing persisted tab indices keep their meaning.
        self.tabProjects = QtWidgets.QWidget()
        self.tabDebugger = QtWidgets.QWidget()
        projects = QtWidgets.QVBoxLayout(self.tabProjects)
        debugger = QtWidgets.QVBoxLayout(self.tabDebugger)
        form = QtWidgets.QFormLayout()
        self.debugger_command = QtWidgets.QLineEdit()
        form.addRow('Installed debugger launcher:', self.debugger_command)
        debugger.addLayout(form)
        self.open_debugger_button = QtWidgets.QPushButton('Open installed debugger…')
        self.open_debugger_button.setEnabled(self.project_controller is not None)
        self.open_debugger_button.clicked.connect(
            lambda: self.project_controller.open_debugger(self.debugger_command.text()))
        debugger.addWidget(self.open_debugger_button)
        note = QtWidgets.QLabel(
            'Select the installed cobgdb-python-gui launcher (version 0.1.0-2 or later). '
            'Use COBOL → Debug executable to open the current binary. '
            'Enable debug compilation and rebuild for source-level debugging.')
        note.setWordWrap(True)
        debugger.addWidget(note)
        self.tabWidget.addTab(self.tabProjects, 'Projects')
        self.tabWidget.addTab(self.tabDebugger, 'Debugger')
        self.tabWidget.setTabText(4, 'SQL COBOL')
        self.tabGixSQL = QtWidgets.QWidget()
        gixsql = QtWidgets.QVBoxLayout(self.tabGixSQL)
        self.tabWidget.addTab(self.tabGixSQL, 'GixSQL')
        project_icon = QtGui.QIcon.fromTheme('folder-development',
                                            QtGui.QIcon(':/ide-icons/rc/folder.png'))
        debugger_icon = QtGui.QIcon.fromTheme('debug-run',
                                             QtGui.QIcon(':/ide-icons/rc/application-x-executable.png'))
        sql_icon = QtGui.QIcon.fromTheme('database',
                                        QtGui.QIcon(':/ide-icons/rc/database.png'))
        for page, icon in ((self.tabProjects, project_icon),
                           (self.tabDebugger, debugger_icon), (self.tabGixSQL, sql_icon)):
            self.tabWidget.setTabIcon(self.tabWidget.indexOf(page), icon)
        self.open_debugger_button.setIcon(debugger_icon)
        root = (self.project_controller.app.file.project_root
                if self.project_controller else None)
        for layout in (projects, debugger):
            label = QtWidgets.QLabel('Active project: ' + root if root else
                                     'Open a project to configure project settings.')
            label.setWordWrap(True)
            layout.addWidget(label)
        self.project_root = root
        editor = (getattr(self.project_controller.app.edit, 'current_editor', None)
                  if self.project_controller and hasattr(self.project_controller.app, 'edit') else None)
        self.current_source = editor.file.path if editor and editor.file.path else None
        self.project_defaults_button = QtWidgets.QPushButton('Project compiler settings…')
        self.project_defaults_button.setIcon(QtGui.QIcon.fromTheme(
            'preferences-system', QtGui.QIcon(':/ide-icons/rc/Preferences-system.png')))
        self.project_defaults_button.setEnabled(bool(root))
        self.project_defaults_button.clicked.connect(self._edit_project_defaults)
        self.source_settings_button = QtWidgets.QPushButton('File compiler settings…')
        self.source_settings_button.setIcon(QtGui.QIcon.fromTheme(
            'document-properties', QtGui.QIcon(':/ide-icons/rc/text-x-generic.png')))
        self.source_settings_button.setEnabled(bool(self.current_source))
        self.source_settings_button.clicked.connect(self._edit_source_options)
        compiler_buttons = QtWidgets.QHBoxLayout()
        compiler_buttons.addWidget(self.project_defaults_button)
        compiler_buttons.addWidget(self.source_settings_button)
        self.tabCompiler.layout().insertLayout(0, compiler_buttons)
        compiler_note = QtWidgets.QLabel(
            'Project and file dialogs save with their own OK. '
            'Preferences Cancel does not undo settings accepted in those dialogs.')
        compiler_note.setWordWrap(True)
        self.tabCompiler.layout().insertWidget(1, compiler_note)
        source_note = QtWidgets.QLabel('Current file: ' + self.current_source if self.current_source else
                                      'Open a saved source file to edit file compiler settings.')
        source_note.setWordWrap(True)
        self.tabCompiler.layout().insertWidget(2, source_note)
        note = QtWidgets.QLabel(
            'Project GixSQL paths. Blank fields inherit toolchain defaults; '
            'file overrides take precedence. These paths apply when project defaults are enabled. '
            'Edits save with Preferences OK; Cancel discards them.')
        note.setWordWrap(True)
        gixsql.addWidget(note)
        active = QtWidgets.QLabel('Active project: ' + root if root else
                                 'Open a project to configure GixSQL paths.')
        active.setWordWrap(True)
        gixsql.addWidget(active)
        form = QtWidgets.QFormLayout()
        for key, title in (('gixpp_path', 'GixSQL preprocessor:'),
                           ('gixsql_copy_dir', 'GixSQL copybook directory:'),
                           ('gixsql_library_dir', 'GixSQL library directory:')):
            field = QtWidgets.QLineEdit()
            field.setPlaceholderText('Inherit')
            field.setEnabled(bool(root))
            self.gix_fields[key] = field
            form.addRow(title, field)
        gixsql.addLayout(form)
        self.gix_source_button = QtWidgets.QPushButton('File compiler / GixSQL overrides…')
        self.gix_source_button.setIcon(sql_icon)
        self.gix_source_button.setEnabled(bool(self.current_source))
        self.gix_source_button.clicked.connect(self._edit_source_options)
        gixsql.addWidget(self.gix_source_button)
        gixsql.addStretch()
        if root:
            from .project_runtime import RuntimeFoldersWidget
            try:
                self.project_controls = RuntimeFoldersWidget(root, self.tabProjects)
            except (ValueError, OSError) as error:
                projects.addWidget(QtWidgets.QLabel('Cannot load project settings: ' + str(error)))
            else:
                projects.addWidget(self.project_controls)
                # Move the shared debug control to its own page.
                self.project_controls.layout().removeWidget(self.project_controls.debug)
                debugger.addWidget(self.project_controls.debug)
                note = QtWidgets.QLabel(
                    'Adds -g -fsource-location -ftraceall -O0 -save-temps. '
                    'Generated C/header files remain in debug_data/. '
                    'The independent debugger opens externally on the selected executable.')
                note.setWordWrap(True)
                debugger.addWidget(note)
                note = QtWidgets.QLabel(
                    'Runtime and debug edits are saved with Preferences OK; Cancel discards them. '
                    'Enable Use these runtime folders to accept the reviewed suggestions. '
                    'Compiler/source dialogs below save independently when their own OK is chosen.')
                note.setWordWrap(True)
                projects.addWidget(note)
            configure = QtWidgets.QPushButton('Project defaults, source overrides and validation…')
            configure.setIcon(project_icon)
            configure.clicked.connect(self._configure_project)
            projects.addWidget(configure)
        projects.addStretch()
        debugger.addStretch()

    def _reload_gixsql(self):
        if not self.project_root:
            return
        from open_cobol_ide import project_config as config
        try:
            environment = config.load(self.project_root).get('defaults', {}).get('environment', {})
        except (ValueError, OSError) as error:
            QtWidgets.QMessageBox.warning(self, 'Cannot load GixSQL settings', str(error))
            return
        self._gix_initial = {key: environment.get(key, '') for key in self.gix_fields}
        for key, field in self.gix_fields.items():
            field.setText(self._gix_initial[key])

    def _update_gixsql_config(self, candidate):
        from open_cobol_ide import project_config as config
        changed = {key: clean_directory_path(field.text())
                   for key, field in self.gix_fields.items()
                   if clean_directory_path(field.text()) != self._gix_initial.get(key, '')}
        if not changed:
            return False
        defaults = dict(candidate.get('defaults', {}))
        environment = dict(defaults.get('environment', {}))
        for key, value in changed.items():
            if value:
                environment[key] = config.portable_path(self.project_root, value)
            else:
                environment.pop(key, None)
        defaults['environment'] = environment
        candidate['defaults'] = defaults
        return True

    def _edit_source_options(self):
        if self.current_source:
            self.project_controller.edit_source_compiler_options(self.current_source)

    def _edit_project_defaults(self):
        self.project_controller.edit_project_compiler_options()

    def _configure_project(self):
        from .project_setup import ProjectSetupDialog
        ProjectSetupDialog(self.project_controller.app.file.project_root,
                           self.project_controller, self).exec_()

    def accept(self):
        if self.project_root:
            from open_cobol_ide import project_config as config
            try:
                original = config.load(self.project_root)
                candidate = dict(original)
                if self.project_controls:
                    self.project_controls.update_config(candidate)
                gix_changed = self._update_gixsql_config(candidate)
                if gix_changed and not self.project_controller.validate_project_settings(
                        self.project_root, candidate):
                    return
                if candidate != original:
                    config.save(self.project_root, candidate)
            except (ValueError, OSError) as error:
                QtWidgets.QMessageBox.warning(self, 'Cannot save project settings', str(error))
                return
        super().accept()

    def _select_working_dir(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Select working directory')
        if path:
            self.edit_working_dir.setText(path)

    def _check_compiler(self, *_):
        self.apply()
        pth = self.lineEditCompilerPath.text()
        if os.path.exists(pth) or system.which(pth) is not None:
            DlgCheckCompiler.check(self, pth)
        else:
            QtWidgets.QMessageBox.warning(
                self, 'Invalid compiler path',
                'Not a valid compiler path, path does not exists: %s!' % pth)

    def _add_lib_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Select a library directory')
        if path:
            self.listWidgetLibPaths.addItem(system.normpath(path))

    def _add_rel_lib_path(self):
        path, status = QtWidgets.QInputDialog.getText(
            self, 'Add relative library path', 'Path:')
        if status:
            self.listWidgetLibPaths.addItem(system.normpath(path))

    def _rm_lib_path(self):
        items = self.listWidgetLibPaths.selectedItems()
        for item in items:
            self.listWidgetLibPaths.takeItem(self.listWidgetLibPaths.row(item))

    def _add_copy_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Select a copybook path')
        if path:
            self.listWidgetCopyPaths.addItem(system.normpath(path))

    def _add_rel_copy_path(self):
        path, status = QtWidgets.QInputDialog.getText(
            self, 'Add relative copybook path', 'Path:')
        if status:
            self.listWidgetCopyPaths.addItem(system.normpath(path))

    def _rm_copy_path(self):
        items = self.listWidgetCopyPaths.selectedItems()
        for item in items:
            self.listWidgetCopyPaths.takeItem(
                self.listWidgetCopyPaths.row(item))

    def _select_vcvarsall(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Select vcvarsall.bat', self.lineEditVCVARS.text())
        if path:
            path = system.normpath(path)
            if os.path.isfile(path) and path.lower().endswith('vcvarsall.bat'):
                self.lineEditVCVARS.setText(path)
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Invalid vcvarsall batch path",
                    "%r is not a valid vcvarsall batch file" % path)

    def _select_custom_compiler_path(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Select path to a GnuCOBOL compiler executable',
            self.lineEditCompilerPath.text())
        if path:
            self.lineEditCompilerPath.setText(system.normpath(path))
            self._check_compiler()

    def _show_gnu_cobol_help(self):
        if self._help_dlg is None or not self._help_dlg.isVisible():
            help_text = compilers.GnuCobolCompiler.get_cobc_help()
            self._help_dlg = DlgCobcHelp(self, help_text)
            self._help_dlg.show()

    def _select_esqloc(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Select esqlOC folder', self.lineEditESQLOC.text())
        if path:
            self.lineEditESQLOC.setText(system.normpath(path))

    def _select_dbpre(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Select dbpre executable', self.lineEditDbpre.text())
        if path:
            self.lineEditDbpre.setText(system.normpath(path))
            self.labelDbpreVersion.setText(
                compilers.DbpreCompiler(path).get_version()
                if Settings().dbpre != '' else ''
            )

    def _select_cobmysqlapi(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Select cobmysqlapi object file',
            self.lineEditCobmysqlapi.text())
        if path:
            self.lineEditCobmysqlapi.setText(system.normpath(path))

    def _select_dbpre_framework(self):
        def bool_to_string(value):
            if value:
                return 'Found'
            else:
                return 'Missing'

        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Select dbpre framework directory',
            self.lineEditDbpreFramework.text())
        if path:
            path = system.normpath(path)
            pgctbbat = os.path.exists(os.path.join(path, 'PGCTBBAT'))
            pgctbparam = os.path.exists(os.path.join(path, 'PGCTBPARAM'))
            pgctbsub = os.path.exists(os.path.join(path, 'PGCTBSUB'))
            pgctbsubws = os.path.exists(os.path.join(path, 'PGCTBSUBWS'))
            sqlca = os.path.exists(os.path.join(path, 'SQLCA'))
            if pgctbparam and pgctbsub and sqlca and pgctbsubws and pgctbbat:
                self.lineEditDbpreFramework.setText(path)
            else:
                QtWidgets.QMessageBox.warning(
                    self, 'Invalid dpre framework directory',
                    'Missing one of the following files: \n'
                    'PGCTBBAT: %s\n'
                    'PGCTBPARAM: %s\n'
                    'PGCTBSUB: %s\n'
                    'PGCTBSUBWS: %s\n'
                    'SQLCA: %s\n' % (
                        bool_to_string(pgctbbat), bool_to_string(pgctbparam),
                        bool_to_string(pgctbsub), bool_to_string(pgctbsubws),
                        bool_to_string(sqlca)))

    def stop_backend(self):
        self.plainTextEdit.backend.stop()

    def _update_icon_theme(self, c):
        index = self.comboBoxIconTheme.findText(c)
        self.comboBoxIconTheme.setCurrentIndex(index)

    def _on_show_pass_state_changed(self, state):
        if state:
            self.lineEditDBPASSWD.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.lineEditDBPASSWD.setEchoMode(QtWidgets.QLineEdit.Password)

    @QtCore.Slot(bool)
    def on_radioButtonColorWhite_toggled(self, native):
        # choose an icon them that goes well with the selected style
        if not native:
            candidates = ['Faenza-Darkest', 'nouveGnomeGray', 'matefaenzadark',
                          'gnome', 'oxygen']
            available = system.icon_themes()
            for c in candidates:
                if c in available:
                    self._update_icon_theme(c)
                    break
        else:
            self._update_icon_theme('default')
        # choose a a color scheme that goes well with the selected style
        for i in range(self.listWidgetColorSchemes.count()):
            if (native and self.listWidgetColorSchemes.item(i).text() ==
                    'qt'):
                self.listWidgetColorSchemes.setCurrentRow(i)
                break
            elif (not native and
                    self.listWidgetColorSchemes.item(i).text() == 'darcula'):
                self.listWidgetColorSchemes.setCurrentRow(i)
                break

    def update_color_scheme_preview(self, item):
        if item:
            self.plainTextEdit.syntax_highlighter.color_scheme = ColorScheme(
                item.text())

    def setupUi(self, Dialog):
        super().setupUi(Dialog)
        self.setMinimumWidth(450)
        self.tabWidget.setCurrentIndex(0)

    def _add_run_env_variable(self):
        index = self.tw_run_env.rowCount()
        self.tw_run_env.insertRow(index)
        focus_item = QtWidgets.QTableWidgetItem()
        self.tw_run_env.setItem(index, 0, focus_item)
        self.tw_run_env.setItem(index, 1, QtWidgets.QTableWidgetItem())
        self.tw_run_env.scrollToItem(focus_item)
        self.tw_run_env.editItem(focus_item)

    def _rm_run_env_variable(self):
        self.tw_run_env.removeRow(self.tw_run_env.currentRow())

    def _clear_run_env(self):
        self.tw_run_env.clearContents()
        self.tw_run_env.setRowCount(0)

    def reset(self, all_tabs=False):
        settings = Settings()
        # Editor
        if self.tabWidget.currentIndex() == 0 or all_tabs:
            self.cb_cursor_pos_in_bytes.setChecked(
                settings.show_cursor_pos_in_bytes)
            self.checkBoxShowErrors.setChecked(settings.show_errors)
            self.checkBoxViewLineNumber.setChecked(settings.display_lines)
            self.checkBoxHighlightCurrentLine.setChecked(
                settings.highlight_caret)
            self.checkBoxHighlightWhitespaces.setChecked(
                settings.show_whitespaces)
            self.spinBoxEditorTabLen.setValue(settings.tab_len)
            self.checkBoxEditorAutoIndent.setChecked(
                settings.enable_autoindent)
            self.spinBoxEditorCCTriggerLen.setValue(
                settings.code_completion_trigger_len)
            self.rbLowerCaseKwds.setChecked(settings.lower_case_keywords)
            self.rbUpperCaseKwds.setChecked(not settings.lower_case_keywords)
            self.lineEditCommentIndicator.setText(settings.comment_indicator)
            self.checkBoxSmartBackspace.setChecked(
                settings.enable_smart_backspace)
            self.checkBoxAutodetectEOL.setChecked(settings.autodetect_eol)
            self.comboBoxPreferredEOL.setCurrentIndex(settings.preferred_eol)
            self.comboCcFilterMode.setCurrentIndex(
                settings.completion_filter_mode)
            for pos, spin_box, color, picker in zip(
                    settings.margin_positions, self._margin_spin_boxes,
                    settings.margin_colors, self._margin_color_pickers):
                spin_box.setValue(pos + 1)
                picker.color = QtGui.QColor(color)
        # Style
        if self.tabWidget.currentIndex() == 1 or all_tabs:
            rb = (self.radioButtonColorDark if settings.dark_style else
                  self.radioButtonColorWhite)
            rb.setChecked(True)
            index = self.comboBoxIconTheme.findText(QtGui.QIcon.themeName())
            if index != -1:
                self.comboBoxIconTheme.setCurrentIndex(index)
            self.fontComboBox.setCurrentFont(QtGui.QFont(settings.font))
            self.spinBoxFontSize.setValue(settings.font_size)
            self.listWidgetColorSchemes.clear()
            current_index = None
            self.listWidgetColorSchemes.clear()
            for style in PYGMENTS_STYLES:
                self.listWidgetColorSchemes.addItem(style)
                if style == settings.color_scheme:
                    current_index = self.listWidgetColorSchemes.count() - 1
            if current_index:
                self.listWidgetColorSchemes.setCurrentRow(current_index)
        # Run
        if self.tabWidget.currentIndex() == 3 or all_tabs:
            self.checkBoxRunExtTerm.setChecked(settings.external_terminal)
            self.lineEditRunTerm.setVisible(sys.platform != 'win32')
            self.lbl_external_terminal_command.setVisible(
                sys.platform != 'win32')
            self.lineEditRunTerm.setEnabled(settings.external_terminal)
            self.lineEditRunTerm.setText(settings.external_terminal_command)
            self.tw_run_env.clearContents()
            self.tw_run_env.setRowCount(0)
            for key, value in Settings().run_environemnt.items():
                index = self.tw_run_env.rowCount()
                self.tw_run_env.insertRow(index)
                self.tw_run_env.setItem(
                    index, 0, QtWidgets.QTableWidgetItem(key))
                self.tw_run_env.setItem(
                    index, 1, QtWidgets.QTableWidgetItem(value))
            self.edit_working_dir.setText(settings.working_dir)
        # compiler
        if self.tabWidget.currentIndex() == 2 or all_tabs:
            self.cbAutoDetectSublmodules.setChecked(
                Settings().autodetect_submodules)
            self.cb_copy_runtime_dlls.setVisible(sys.platform == 'win32')
            self.cb_copy_runtime_dlls.setChecked(Settings().copy_runtime_dlls)
            self.lineEditOutputDirectory.setText(Settings().output_directory)
            self.lineEditCobcExts.setText(';'.join(Settings().cobc_extensions))
            self.checkBoxFreeFormat.setChecked(settings.free_format)
            self.comboBoxStandard.setCurrentIndex(
                int(settings.cobol_standard))
            self.lineEditCompilerPath.setText(settings.compiler_path)
            flags = Settings().compiler_flags
            self.cb_debugging_line.setChecked(
                self.cb_debugging_line.text() in flags)
            self.cb_ftrace.setChecked(self.cb_ftrace.text().replace('&', '') in flags)
            self.cb_ftraceall.setChecked(self.cb_ftraceall.text().replace('&', '') in flags)
            self.cb_g.setChecked(self.cb_g.text().replace('&', '') in flags)
            self.cb_static.setChecked(self.cb_static.text().replace('&', '') in flags)
            self.cb_debug.setChecked(self.cb_debug.text().replace('&', '') in flags)
            self.cb_w.setChecked(self.cb_w.text().replace('&', '') in flags)
            self.cb_wall.setChecked(self.cb_wall.text().replace('&', '') in flags)
            for v in self.flags_in_checkbox:
                try:
                    flags.remove(v)
                except ValueError:
                    pass
            self.lineEditLibs.setText(settings.libraries)
            self.listWidgetLibPaths.clear()
            self.listWidgetLibPaths.addItems(
                [pth for pth in settings.library_search_path.split(';')
                 if pth])
            self.listWidgetCopyPaths.clear()
            self.listWidgetCopyPaths.addItems(
                [pth for pth in settings.copybook_paths.split(';')
                 if pth])
            self.le_compiler_flags.setText(' '.join(flags))
            if system.windows:
                self.lineEditVCVARS.setText(settings.vcvarsall)
                self.combo_arch.setCurrentIndex(
                    1 if settings.vcvarsall_arch == 'x64' else 0)
            self.PATH.setText(settings.path)
            self.cbPATH.setChecked(settings.path_enabled)
            self.COB_CONFIG_DIR.setText(settings.cob_config_dir)
            self.cbCOB_CONFIG_DIR.setChecked(settings.cob_config_dir_enabled)
            self.COB_COPY_DIR.setText(settings.cob_copy_dir)
            self.cbCOB_COPY_DIR.setChecked(settings.cob_copy_dir_enabled)
            self.COB_INCLUDE_PATH.setText(settings.cob_include_path)
            self.cbCOB_INCLUDE_PATH.setChecked(settings.cob_include_path_enabled)
            self.COB_LIB_PATH.setText(settings.cob_lib_path)
            self.cbCOB_LIB_PATH.setChecked(settings.cob_lib_path_enabled)

        # SQL Cobol
        if self.tabWidget.currentIndex() == 4 or all_tabs:
            self.lineEditDbpreExts.setText(';'.join(Settings().dbpre_extensions))
            self.lineEditDbpre.setText(settings.dbpre)
            self.lineEditDbpreFramework.setText(settings.dbpre_framework)
            self.lineEditCobmysqlapi.setText(settings.cobmysqlapi)
            self.lineEditDBHOST.setText(settings.dbhost)
            self.lineEditDBUSER.setText(settings.dbuser)
            self.lineEditDBPASSWD.setText(settings.dbpasswd)
            self.lineEditDBNAME.setText(settings.dbname)
            self.lineEditDBPORT.setText(settings.dbport)
            self.lineEditDBSOCKET.setText(settings.dbsocket)
            self.labelDbpreVersion.setText(
                compilers.DbpreCompiler().get_version()
                if Settings().dbpre != '' else '')
            self.lineEditESQLOC.setText(settings.esqloc)
            self.lineEditesqlOcExts.setText(';'.join(Settings().esqloc_extensions))

        if all_tabs or self.tabWidget.currentWidget() is self.tabDebugger:
            self.debugger_command.setText(settings.debugger_command)
        if all_tabs or self.tabWidget.currentWidget() is self.tabGixSQL:
            self._reload_gixsql()

        if self.project_controls:
            if all_tabs or self.tabWidget.currentWidget() is self.tabProjects:
                self.project_controls.reload_runtime()
            if all_tabs or self.tabWidget.currentWidget() is self.tabDebugger:
                self.project_controls.reload_debug()

    def restore_defaults(self):
        settings = Settings()
        index = self.tabWidget.currentIndex()
        if self.tabWidget.currentWidget() is self.tabDebugger:
            self.debugger_command.setText('cobgdb-python-gui')
            if self.project_controls:
                self.project_controls.debug.setChecked(False)
            return
        if self.tabWidget.currentWidget() is self.tabGixSQL:
            for field in self.gix_fields.values():
                field.clear()
            return
        # Editor
        if index == 0:
            settings.show_cursor_pos_in_bytes = False
            settings.show_error = True
            settings.display_lines = True
            settings.highlight_caret = True
            settings.show_whitespaces = False
            settings.tab_len = 4
            settings.enable_autoindent = True
            settings.code_completion_trigger_len = 1
            settings.comment_indicator = '*> '
            settings.enable_smart_backspace = False
            settings.lower_case_keywords = False
            settings.autodetect_eol = True
            settings.preferred_eol = 0
            settings.code_completion_trigger_len = 1
            settings.margin_positions = [7, 11, 72, 79]
            settings.margin_colors = ['red'] * 4
        # Style
        elif index == 1:
            settings.dark_style = False
            settings.icon_theme = ''
            settings.font = 'Source Code Pro'
            settings.font_size = 11
            settings.colorScheme = 'qt'
        # run
        elif index == 3:
            settings.external_terminal = False
            settings.external_terminal_command = None
            settings.run_environemnt = {}
            settings.working_dir = ''
        # compiler
        elif index == 2:
            settings.autodetect_submodules = True
            settings.output_directory = 'bin'
            settings.copy_runtime_dlls = False
            settings.free_format = False
            settings.cobol_standard = GnuCobolStandard.default
            settings.compiler_path = 'cobc.exe' if system.windows else 'cobc'
            settings.compiler_flags = ['-debug', '-Wall']
            settings.copybook_paths = ''
            settings.library_search_path = ''
            settings.libraries = ''
            settings.cobc_extensions = ['.cob', '.cbl', '.pco', '.lst']
            if system.windows:
                settings.vcvarsall = ''
                settings.vcvarsall_arch = 'x86'
            settings.path = settings.default_path()
            settings.path_enabled = True
            settings.cob_config_dir = settings.default_config_dir()
            settings.cob_config_dir_enabled = system.windows
            settings.cob_copy_dir = settings.default_copy_dir()
            settings.cob_copy_dir_enabled = system.windows
            settings.cob_include_path = settings.default_include_dir()
            settings.cob_include_path_enabled = system.windows
            settings.cob_lib_path = settings.default_lib_path()
            settings.cob_lib_path_enabled = system.windows
        elif index == 4:
            settings.dbpre = ''
            settings.dbpre_extensions = ['.scb']
            settings.dbpre_framework = ''
            settings.cobmysqlapi = ''
            settings.dbhost = 'localhost'
            settings.dbuser = ''
            settings.dbpasswd = ''
            settings.dbname = ''
            settings.dbport = '03306'
            settings.dbsocket = 'null'
            settings.esqloc = ''
            settings.esqloc_extensions = ['.sqb']
        if self.project_controls and self.tabWidget.currentWidget() is self.tabProjects:
            self.project_controls.use_runtime.setChecked(False)
            self.project_controls.cwd.setCurrentText('bin')
            self.project_controls.paths.clear()
            return
        if self.project_controls and self.tabWidget.currentWidget() is self.tabDebugger:
            self.project_controls.debug.setChecked(False)
            return
        self.reset()

    def apply(self):
        path_fields = [
            (self.lineEditCompilerPath, False),
            (self.PATH, os.pathsep),
            (self.COB_CONFIG_DIR, False),
            (self.COB_COPY_DIR, False),
            (self.COB_INCLUDE_PATH, os.pathsep),
            (self.COB_LIB_PATH, os.pathsep),
            (self.lineEditOutputDirectory, False),
            (self.edit_working_dir, False),
        ]
        corrections = []
        for widget, separator in path_fields:
            original = widget.text()
            cleaned = (clean_path_list(original, separator)
                       if separator else clean_directory_path(original))
            if cleaned != original:
                corrections.append('%s\n→ %s' % (original, cleaned))
                widget.setText(cleaned)
        for widget in (self.listWidgetCopyPaths, self.listWidgetLibPaths):
            for index in range(widget.count()):
                item = widget.item(index)
                original = item.text()
                cleaned = clean_directory_path(original)
                if cleaned != original:
                    corrections.append('%s\n→ %s' % (original, cleaned))
                    item.setText(cleaned)
        if corrections:
            QtWidgets.QMessageBox.warning(
                self, 'Spaces removed from directory paths',
                'Leading or trailing spaces around directory components can '
                'select a different path. They were removed:\n\n' +
                '\n'.join(corrections))
        # force next check (otherwise the cached result will be used)
        compilers.GnuCobolCompiler.check_compiler.reset()
        settings = Settings()
        settings.show_cursor_pos_in_bytes = \
            self.cb_cursor_pos_in_bytes.isChecked()
        settings.display_lines = self.checkBoxViewLineNumber.isChecked()
        settings.highlight_caret = self.checkBoxHighlightCurrentLine.isChecked()
        settings.show_whitespaces = \
            self.checkBoxHighlightWhitespaces.isChecked()
        settings.tab_len = self.spinBoxEditorTabLen.value()
        settings.enable_autoindent = self.checkBoxEditorAutoIndent.isChecked()
        settings.code_completion_trigger_len = \
            self.spinBoxEditorCCTriggerLen.value()
        settings.preferred_eol = self.comboBoxPreferredEOL.currentIndex()
        settings.autodetect_eol = self.checkBoxAutodetectEOL.isChecked()
        settings.dark_style = self.radioButtonColorDark.isChecked()
        settings.font = self.fontComboBox.currentFont().family()
        settings.font_size = self.spinBoxFontSize.value()
        settings.color_scheme = self.listWidgetColorSchemes.currentItem().text()
        settings.external_terminal = self.checkBoxRunExtTerm.isChecked()
        settings.external_terminal_command = self.lineEditRunTerm.text()
        settings.lower_case_keywords = self.rbLowerCaseKwds.isChecked()
        settings.compiler_path = self.lineEditCompilerPath.text()
        settings.vcvarsall = self.lineEditVCVARS.text()
        settings.vcvarsall_arch = self.combo_arch.currentText()
        settings.path = self.PATH.text()
        settings.path_enabled = self.cbPATH.isChecked()
        settings.cob_config_dir = self.COB_CONFIG_DIR.text()
        settings.cob_config_dir_enabled = self.cbCOB_CONFIG_DIR.isChecked()
        settings.cob_copy_dir = self.COB_COPY_DIR.text()
        settings.cob_copy_dir_enabled = self.cbCOB_COPY_DIR.isChecked()
        settings.cob_include_path = self.COB_INCLUDE_PATH.text()
        settings.cob_include_path_enabled = self.cbCOB_INCLUDE_PATH.isChecked()
        settings.cob_lib_path = self.COB_LIB_PATH.text()
        settings.cob_lib_path_enabled = self.cbCOB_LIB_PATH.isChecked()
        settings.free_format = self.checkBoxFreeFormat.isChecked()
        settings.comment_indicator = self.lineEditCommentIndicator.text()
        settings.autodetect_submodules = \
            self.cbAutoDetectSublmodules.isChecked()
        settings.cobol_standard = GnuCobolStandard(
            self.comboBoxStandard.currentIndex())
        settings.icon_theme = self.comboBoxIconTheme.currentText()
        settings.show_errors = self.checkBoxShowErrors.isChecked()
        settings.enable_smart_backspace = \
            self.checkBoxSmartBackspace.isChecked()
        paths = []
        for i in range(self.listWidgetLibPaths.count()):
            paths.append(self.listWidgetLibPaths.item(i).text())
        settings.library_search_path = ';'.join(paths)
        paths = []
        for i in range(self.listWidgetCopyPaths.count()):
            paths.append(self.listWidgetCopyPaths.item(i).text())
        settings.copybook_paths = ';'.join(paths)
        settings.libraries = self.lineEditLibs.text()
        settings.output_directory = self.lineEditOutputDirectory.text()
        settings.copy_runtime_dlls = self.cb_copy_runtime_dlls.isChecked()
        cb_flags = [self.cb_g, self.cb_ftrace, self.cb_ftraceall,
                    self.cb_debugging_line, self.cb_static, self.cb_debug,
                    self.cb_w, self.cb_wall]
        flags = [cb.text() for cb in cb_flags if cb.isChecked()]
        flags += system.shell_split(self.le_compiler_flags.text())
        settings.compiler_flags = flags
        # sql
        settings.dbpre = self.lineEditDbpre.text()
        settings.dbpre_framework = self.lineEditDbpreFramework.text()
        settings.cobmysqlapi = self.lineEditCobmysqlapi.text()
        settings.dbhost = self.lineEditDBHOST.text()
        settings.dbuser = self.lineEditDBUSER.text()
        settings.dbpasswd = self.lineEditDBPASSWD.text()
        settings.dbname = self.lineEditDBNAME.text()
        settings.dbport = self.lineEditDBPORT.text()
        settings.dbsocket = self.lineEditDBSOCKET.text()
        settings.esqloc = self.lineEditESQLOC.text()
        settings.completion_filter_mode = \
            self.comboCcFilterMode.currentIndex()
        settings.cobc_extensions = [
            ext.lower() for ext in
            self.lineEditCobcExts.text().split(';') if ext]
        settings.dbpre_extensions = [
            ext.lower() for ext in
            self.lineEditDbpreExts.text().split(';') if ext]
        settings.esqloc_extensions = [
            ext for ext in self.lineEditesqlOcExts.text().split(';') if ext]

        colors = []
        positions = []
        for spin_box, picker in zip(self._margin_spin_boxes,
                                    self._margin_color_pickers):
            positions.append(spin_box.value() - 1)
            colors.append(picker.color.name())
        settings.margin_positions = positions
        settings.margin_colors = colors

        env = {}
        for i in range(self.tw_run_env.rowCount()):
            env[self.tw_run_env.item(i, 0).text()] = self.tw_run_env.item(
                i, 1).text()
        settings.run_environemnt = env
        settings.working_dir = self.edit_working_dir.text()

    @classmethod
    def edit_preferences(cls, parent, project_controller=None, page=None):
        def restore_state(dlg):
            s = Settings()
            dlg.resize(s.preferences_width, s.preferences_height)
            dlg.tabWidget.setCurrentIndex(s.preferences_index)

        def save_state(dlg):
            s = Settings()
            s.preferences_width = dlg.width()
            s.preferences_height = dlg.height()
            s.preferences_index = dlg.tabWidget.currentIndex()

        dlg = cls(parent, project_controller=project_controller)
        restore_state(dlg)
        if page == 'Compiler':
            dlg.tabWidget.setCurrentWidget(dlg.tabCompiler)
        ret_val = dlg.exec_()
        dlg.stop_backend()
        if ret_val != dlg.Accepted:
            Settings().import_from_dict(dlg.initial_settings)
            raise ValueError()
        save_state(dlg)
        dlg.apply()
        settings = Settings()
        settings.debugger_command = clean_directory_path(dlg.debugger_command.text())
