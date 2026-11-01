"""Review folder suggestions before saving portable project runtime settings."""
import os
from pyqode.qt import QtWidgets
from open_cobol_ide import project_config as config
from open_cobol_ide.project_runtime import scan
from open_cobol_ide.settings import Settings


class RuntimeFoldersDialog(QtWidgets.QDialog):
    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = root
        self.setWindowTitle('Review Project Folders')
        self.resize(950, 570)
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
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.rescan()
        data = config.load(root)
        runtime = data.get('runtime', {})
        if runtime.get('accepted'):
            self.cwd.setCurrentText(runtime.get('working_directory', '.'))
            self.paths.setPlainText('\n'.join(runtime.get('data_directories', [])))
        self.debug.setChecked(data.get('debug', {}).get('enabled', False))

    def rescan(self):
        result = scan(self.root, free=Settings().free_format)
        self.table.setRowCount(len(result['rows']))
        for i, row in enumerate(result['rows']):
            for j, value in enumerate([row['source'], row['select'], row['assignment'],
                                       '\n'.join(row['matches']), row['status']]):
                self.table.setItem(i, j, QtWidgets.QTableWidgetItem(value))
        self.table.resizeColumnsToContents()
        self.cwd.clear()
        self.cwd.addItems(list(dict.fromkeys([result['working_directory'], '.'] + result['folders'])))
        self.paths.setPlainText('\n'.join(result['folders']))

    def accept(self):
        try:
            cwd = self.cwd.currentText().strip()
            paths = [p.strip() for p in self.paths.toPlainText().splitlines() if p.strip()]
            for path in [cwd] + paths:
                if not path or not os.path.isdir(config.resolve_path(self.root, path)):
                    raise ValueError('Choose an existing folder: '+path)
            data = config.load(self.root)
            data['runtime'] = {'accepted': True, 'working_directory': config.portable_path(self.root, cwd),
                               'data_directories': [config.portable_path(self.root, p) for p in paths]}
            data['debug'] = {'enabled': self.debug.isChecked()}
            config.save(self.root, data)
        except (ValueError, OSError) as error:
            QtWidgets.QMessageBox.warning(self, 'Cannot save project folders', str(error))
            return
        super().accept()
