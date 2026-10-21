import os
import shlex

from pyqode.qt import QtWidgets

from open_cobol_ide import system
from open_cobol_ide.path_utils import clean_directory_path


class SourceCompilerOptionsDialog(QtWidgets.QDialog):
    """Edit compiler flags and environment overrides for one source file."""
    def __init__(self, source_path, global_flags, flags, environment, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Compiler options for this file')
        self.setMinimumWidth(620)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel(os.path.abspath(source_path)))

        self.use_global_flags = QtWidgets.QCheckBox('Use global extra compiler flags')
        self.use_global_flags.setChecked(flags is None)
        layout.addWidget(self.use_global_flags)
        form = QtWidgets.QFormLayout()
        self.flags = QtWidgets.QLineEdit(' '.join(
            shlex.quote(f) for f in (global_flags if flags is None else flags)))
        self.flags.setToolTip('Custom flags replace the global extra compiler flags.')
        form.addRow('Extra compiler flags:', self.flags)
        self.compiler_path = QtWidgets.QLineEdit(environment.get('compiler_path', ''))
        self.compiler_path.setPlaceholderText('Use the global compiler')
        form.addRow('Compiler path:', self.compiler_path)
        self.path = QtWidgets.QLineEdit(environment.get('path', ''))
        self.path.setPlaceholderText(
            'Optional directory containing gcc, clang or other build tools')
        self.path.setToolTip(
            'This directory is searched before the existing PATH. Use '
            'Compiler path above to select cobc directly.')
        form.addRow('Additional tools directory:', self.path)
        self.cob_copy_dir = QtWidgets.QLineEdit(environment.get('cob_copy_dir', ''))
        self.cob_copy_dir.setPlaceholderText('Inherit global COB_COPY_DIR')
        form.addRow('COB_COPY_DIR:', self.cob_copy_dir)
        layout.addLayout(form)
        note = QtWidgets.QLabel(
            'Blank fields inherit global settings. Use Compiler path to select '
            'cobc. The additional tools directory is only needed for tools such '
            'as gcc, clang, or a preprocessor.')
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel |
            QtWidgets.QDialogButtonBox.Reset)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QtWidgets.QDialogButtonBox.Reset).clicked.connect(self.reset)
        layout.addWidget(buttons)
        self.use_global_flags.toggled.connect(self.flags.setDisabled)
        self.flags.setDisabled(self.use_global_flags.isChecked())

    def reset(self):
        self.use_global_flags.setChecked(True)
        self.compiler_path.clear()
        self.path.clear()
        self.cob_copy_dir.clear()

    def values(self):
        flags = None
        if not self.use_global_flags.isChecked():
            flags = shlex.split(self.flags.text(), posix=not system.windows)
        raw = {
            'compiler_path': self.compiler_path.text(),
            'path_mode': 'prepend' if self.path.text().strip() else 'inherit',
            'path': self.path.text(),
            'cob_copy_dir': self.cob_copy_dir.text(),
        }
        cleaned = dict(raw)
        cleaned['compiler_path'] = clean_directory_path(raw['compiler_path'])
        cleaned['path'] = clean_directory_path(raw['path'])
        cleaned['path_mode'] = ('prepend' if cleaned['path'] else 'inherit')
        cleaned['cob_copy_dir'] = clean_directory_path(raw['cob_copy_dir'])
        return flags, raw, cleaned
