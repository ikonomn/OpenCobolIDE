"""Review folder suggestions before saving portable project runtime settings."""
import os
from pyqode.qt import QtWidgets
from open_cobol_ide import project_config as config
from open_cobol_ide.project_runtime import scan
from open_cobol_ide.settings import Settings


class RuntimeFoldersWidget(QtWidgets.QWidget):
    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = root
        layout = QtWidgets.QVBoxLayout(self)
        note = QtWidgets.QLabel('Suggestions from FILE-CONTROL assignments, matching files and folder names. '
            'Review ambiguous, missing and dynamic assignments. Nothing changes until you accept. '
            'Explicit file paths and application settings may override the data search folders.')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(['Source / copybook', 'SELECT', 'ASSIGN', 'Matching files', 'Result'])
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)
        self.use_runtime = QtWidgets.QCheckBox('Use these runtime folders for this project')
        layout.addWidget(self.use_runtime)
        form = QtWidgets.QFormLayout()
        self.cwd = QtWidgets.QComboBox()
        self.cwd.setEditable(True)
        form.addRow('Working directory (relative to project):', self.cwd)
        self.paths = QtWidgets.QPlainTextEdit()
        self.paths.setMaximumHeight(75)
        form.addRow('Data search folders (one per line):', self.paths)
        self.debug = QtWidgets.QCheckBox('Debug compilation: retain generated .c and .h in debug_data/')
        form.addRow(self.debug)
        layout.addLayout(form)
        rescan = QtWidgets.QPushButton('Rescan Project Folders')
        rescan.clicked.connect(self.rescan)
        layout.addWidget(rescan)
        self.reload_runtime()
        self.reload_debug()

    def reload_runtime(self):
        self.rescan()
        runtime = config.load(self.root).get('runtime', {})
        self.use_runtime.setChecked(runtime.get('accepted', False))
        if runtime.get('accepted'):
            self.cwd.setCurrentText(runtime.get('working_directory', 'bin'))
            self.paths.setPlainText('\n'.join(runtime.get('data_directories', [])))
        self._runtime_initial = self.runtime_values()

    def reload_debug(self):
        self.debug.setChecked(config.load(self.root).get('debug', {}).get('enabled', False))
        self._debug_initial = self.debug.isChecked()

    def runtime_values(self):
        return (self.use_runtime.isChecked(), self.cwd.currentText().strip(),
                [p.strip() for p in self.paths.toPlainText().splitlines() if p.strip()])

    def update_config(self, data, accept_runtime=False):
        """Validate a draft and update the supplied configuration, without writing."""
        accepted, cwd, paths = self.runtime_values()
        if accept_runtime or (accepted, cwd, paths) != self._runtime_initial:
            accepted = accepted or accept_runtime
            if accepted:
                for path in [cwd] + paths:
                    if not path or not os.path.isdir(config.resolve_path(self.root, path)):
                        raise ValueError('Choose an existing folder: ' + path)
            runtime = dict(data.get('runtime', {}))
            runtime.update(accepted=accepted, working_directory=config.portable_path(self.root, cwd),
                           data_directories=[config.portable_path(self.root, p) for p in paths])
            data['runtime'] = runtime
        if self.debug.isChecked() != self._debug_initial:
            debug = dict(data.get('debug', {}))
            debug['enabled'] = self.debug.isChecked()
            data['debug'] = debug
        return data

    def rescan(self):
        result = scan(self.root, free=Settings().free_format)
        self.table.setRowCount(len(result['rows']))
        for i, row in enumerate(result['rows']):
            for j, value in enumerate([row['source'], row['select'], row['assignment'],
                                       '\n'.join(row['matches']), row['status']]):
                self.table.setItem(i, j, QtWidgets.QTableWidgetItem(value))
        self.table.resizeColumnsToContents()
        self.cwd.clear()
        self.cwd.addItems(list(dict.fromkeys(['bin', result['working_directory'], '.'] + result['folders'])))
        self.paths.setPlainText('\n'.join(result['folders']))

class RuntimeFoldersDialog(QtWidgets.QDialog):
    """Standalone review, sharing the same draft controls as Preferences."""
    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = root
        self.setWindowTitle('Review Project Folders')
        self.resize(950, 570)
        layout = QtWidgets.QVBoxLayout(self)
        self.controls = RuntimeFoldersWidget(root, self)
        layout.addWidget(self.controls)
        self.controls.use_runtime.hide()
        # Keep the existing dialog API for callers and extensions.
        for name in ('table', 'cwd', 'paths', 'debug'):
            setattr(self, name, getattr(self.controls, name))
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def rescan(self):
        self.controls.rescan()

    def accept(self):
        try:
            data = self.controls.update_config(config.load(self.root), accept_runtime=True)
            config.save(self.root, data)
        except (ValueError, OSError) as error:
            QtWidgets.QMessageBox.warning(self, 'Cannot save project folders', str(error))
            return
        super().accept()
