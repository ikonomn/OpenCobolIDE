import locale
import os
from pyqode.qt import QtCore, QtWidgets
from pyqode.core.managers import FileManager
from open_cobol_ide.settings import Settings
from open_cobol_ide.view.forms import dlg_file_type_ui


EXE_TEMPLATE = '''      ******************************************************************
      * Author:
      * Date:
      * Purpose:
      * Tectonics: cobc
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. YOUR-PROGRAM-NAME.
       DATA DIVISION.
       FILE SECTION.
       WORKING-STORAGE SECTION.
       PROCEDURE DIVISION.
       MAIN-PROCEDURE.
            DISPLAY "Hello world"
            STOP RUN.
       END PROGRAM YOUR-PROGRAM-NAME.

'''

MODULE_TEMPLATE = '''      ******************************************************************
      * Author:
      * Date:
      * Purpose:
      * Tectonics: cobc
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. YOUR-PROGRAM.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       LINKAGE SECTION.
       01 PARAMETRES.
           02 PA-RETURN-CODE PIC 99 VALUE 0.
       PROCEDURE DIVISION USING PARAMETRES.
       MAIN-PROCEDURE.
           DISPLAY "Hello world"
           MOVE 0 TO PA-RETURN-CODE
           STOP RUN.
       END PROGRAM YOUR-PROGRAM.
'''

TEMPLATES = [EXE_TEMPLATE, MODULE_TEMPLATE, '']


EXE_TEMPLATE_FREE = '''*>****************************************************************
*> Author:
*> Date:
*> Purpose:
*> Tectonics: cobc
*>****************************************************************
IDENTIFICATION DIVISION.
PROGRAM-ID. YOUR-PROGRAM-NAME.
DATA DIVISION.
FILE SECTION.
WORKING-STORAGE SECTION.
PROCEDURE DIVISION.
MAIN-PROCEDURE.
    DISPLAY "Hello world"
    STOP RUN.
END PROGRAM YOUR-PROGRAM-NAME.
'''

MODULE_TEMPLATE_FREE = '''*>****************************************************************
*> Author:
*> Date:
*> Purpose:
*> Tectonics: cobc
*>*****************************************************************
IDENTIFICATION DIVISION.
PROGRAM-ID. YOUR-PROGRAM.
DATA DIVISION.
WORKING-STORAGE SECTION.
LINKAGE SECTION.
01 PARAMETRES.
   02 PA-RETURN-CODE PIC 99 VALUE 0.
PROCEDURE DIVISION USING PARAMETRES.
MAIN-PROCEDURE.
   DISPLAY "Hello world"
   MOVE 0 TO PA-RETURN-CODE
   STOP RUN.
END PROGRAM YOUR-PROGRAM.
'''

FREE_TEMPLATES = [EXE_TEMPLATE_FREE, MODULE_TEMPLATE_FREE, '']


class DlgNewFile(QtWidgets.QDialog, dlg_file_type_ui.Ui_Dialog):
    """
    New file dialog. Prompts the user for a file template, a file name and
    the path were to create the file.

    To use this dialog, use the ``create_new_file`` convenience method.
    """
    def __init__(self, parent, path):
        super().__init__(parent)
        self.setupUi(self)
        self.enable_ok()
        completer = QtWidgets.QCompleter(self)
        completer.setModel(QtWidgets.QDirModel(completer))
        self.lineEditPath.setCompleter(completer)
        if not path:
            self.lineEditPath.setText(os.path.expanduser("~"))
        else:
            self.lineEditPath.setText(path)
        self.prev_pth = ""
        # Copybooks are creation/editing types, not standalone compile targets.
        extensions = sorted(set(Settings().all_extensions + ['.cpy']))
        self.comboBoxExtension.addItems(extensions)
        self.comboBoxExtension.addItems([ext.upper() for ext in extensions])
        existing = sorted(set(Settings().all_extensions))
        if existing:
            self.comboBoxExtension.setCurrentIndex(self.comboBoxExtension.findText(existing[0]))
        self._copybook_selected = False
        self._previous_template = self.comboBoxType.currentIndex()
        self._source_default = None
        self._copy_default = None
        self._auto_directory = True
        directory = os.path.abspath(self.lineEditPath.text())
        root = Settings().project_root_for_source(os.path.join(directory, 'new.cbl'))
        if root and directory in (root, os.path.join(root, 'src')):
            copybooks = os.path.join(root, 'copybooks')
            if os.path.isdir(copybooks):
                self._source_default = directory
                self._copy_default = copybooks
        self.lineEditPath.textEdited.connect(self._directory_edited)
        self.comboBoxExtension.currentTextChanged.connect(self._extension_changed)
        self._extension_changed(self.comboBoxExtension.currentText())

    def _directory_edited(self, text):
        self._auto_directory = False

    def _extension_changed(self, extension):
        copybook = extension.lower() == '.cpy'
        if copybook and not self._copybook_selected:
            self._previous_template = self.comboBoxType.currentIndex()
            self.comboBoxType.setCurrentIndex(2)
            if (self._auto_directory and self._copy_default and
                    os.path.abspath(self.lineEditPath.text()) == self._source_default):
                self.lineEditPath.setText(self._copy_default)
        elif self._copybook_selected and not copybook:
            self.comboBoxType.setCurrentIndex(self._previous_template)
            if (self._auto_directory and self._copy_default and
                    os.path.abspath(self.lineEditPath.text()) == self._copy_default):
                self.lineEditPath.setText(self._source_default)
        self.comboBoxType.setEnabled(not copybook)
        self._copybook_selected = copybook

    def path(self):
        """
        Returns the path of the file to create.
        :return: new file path
        """
        return os.path.join(
            self.lineEditPath.text(),
            self.lineEditName.text() + self.comboBoxExtension.currentText())

    def template(self):
        """
        Gets the selected file template
        """
        if self.comboBoxExtension.currentText().lower() == '.cpy':
            return ''
        if Settings().free_format:
            return FREE_TEMPLATES[self.comboBoxType.currentIndex()]
        else:
            return TEMPLATES[self.comboBoxType.currentIndex()]

    @QtCore.Slot(str)
    def on_lineEditName_textChanged(self, txt):
        self.enable_ok()

    @QtCore.Slot(str)
    def on_lineEditPath_textChanged(self, txt):
        self.enable_ok()

    @QtCore.Slot()
    def on_toolButton_clicked(self):
        ret = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Choose the file directory',
            Settings().last_path)
        if ret:
            self._auto_directory = False
            self.lineEditPath.setText(ret)

    def enable_ok(self):
        pth = str(self.lineEditPath.text())
        bt = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        name = self.lineEditName.text()
        enable = name != "" and os.path.exists(pth) and os.path.isdir(pth)
        bt.setEnabled(enable)
        self.prev_pth = pth

    @classmethod
    def create_new_file(cls, parent, path=None):
        """
        Creates a new file. Shows the new file dialog and creates the file
        on disk if the dialog has been accepted and the destination does not
        overwrite any file (or the user choose to overwrite existing file).

        :param parent: Parent widget
        :return: Path or None if the dialog has been cancelled.

        """
        dlg = cls(parent, path=path)
        if dlg.exec_() == dlg.Accepted:
            path = dlg.path()
            if os.path.exists(path):
                answer = QtWidgets.QMessageBox.question(
                    parent, 'Overwrite file',
                    'The file %s already exists. '
                    'Do you want to overwrite it?' % path,
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No)
                if answer == QtWidgets.QMessageBox.No:
                    return None
            eol = FileManager.EOL.string(Settings().preferred_eol)
            text = eol.join(dlg.template().splitlines()) + eol
            data = text.encode(locale.getpreferredencoding())
            with open(path, 'wb') as f:
                f.write(data)
            return path
        return None
