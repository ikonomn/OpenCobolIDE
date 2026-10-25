"""Create a project and review inherited settings for its source files."""
import os
from pyqode.qt import QtCore, QtWidgets
from open_cobol_ide import project_config as config
from open_cobol_ide.project import project_sources
from open_cobol_ide.project_validation import validate_project
from open_cobol_ide.settings import Settings


class NewProjectDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, directory=''):
        super().__init__(parent)
        self.setWindowTitle('New Project')
        self.setMinimumWidth(540)
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        self.name = QtWidgets.QLineEdit()
        self.name.setPlaceholderText('MyProject')
        form.addRow('Project name:', self.name)
        self.directory = QtWidgets.QLineEdit(directory if os.path.isdir(directory) else os.path.dirname(directory))
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.directory)
        browse = QtWidgets.QPushButton('Browse…')
        browse.clicked.connect(self.browse)
        row.addWidget(browse)
        form.addRow('Parent folder:', row)
        layout.addLayout(form)
        note = QtWidgets.QLabel('Creates src, copybooks, bin, build, data and config folders. '
                                'Existing project files are preserved.')
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Parent folder', self.directory.text())
        if directory:
            self.directory.setText(directory)


class ProjectSetupDialog(QtWidgets.QDialog):
    def __init__(self, root, controller, parent=None):
        super().__init__(parent)
        self.root, self.controller = root, controller
        self.setWindowTitle('Configure Project — ' + os.path.basename(root))
        self.resize(820, 560)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel('Set project defaults, then select any source that needs overrides. '
                                 'Executable/module mode is detected automatically.')
        label.setWordWrap(True)
        layout.addWidget(label)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(['Source', 'Compiler settings', 'Validation'])
        layout.addWidget(self.tree)
        row = QtWidgets.QHBoxLayout()
        defaults = QtWidgets.QPushButton('Project defaults…')
        defaults.clicked.connect(self.edit_defaults)
        row.addWidget(defaults)
        self.source_button = QtWidgets.QPushButton('Selected source settings…')
        self.source_button.clicked.connect(self.edit_source)
        row.addWidget(self.source_button)
        check = QtWidgets.QPushButton('Validate settings')
        check.clicked.connect(self.refresh)
        row.addWidget(check)
        layout.addLayout(row)
        self.report = QtWidgets.QPlainTextEdit()
        self.report.setReadOnly(True)
        self.report.setMaximumHeight(150)
        layout.addWidget(self.report)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)
        self.refresh()

    def refresh(self):
        selected = self.tree.currentItem()
        selected = selected.data(0, QtCore.Qt.UserRole) if selected else None
        self.tree.clear()
        try:
            data = config.load(self.root)
            sources = project_sources(self.root, Settings().all_extensions)
            diagnostics = validate_project(self.root, Settings(), data, sources)
            for source in sources:
                key = config.source_key(self.root, source)
                override = data['sources'].get(key, {})
                specific = config.has_overrides(override)
                issues = [d for d in diagnostics if d['source'] == key]
                status = 'Error' if any(d['level'] == 'error' for d in issues) else 'Warning' if issues else 'OK'
                item = QtWidgets.QTreeWidgetItem([key, 'Source overrides' if specific else 'Inherit project defaults', status])
                item.setData(0, QtCore.Qt.UserRole, source)
                self.tree.addTopLevelItem(item)
                if selected == source: self.tree.setCurrentItem(item)
            if self.tree.currentItem() is None and self.tree.topLevelItemCount():
                self.tree.setCurrentItem(self.tree.topLevelItem(0))
            self.source_button.setEnabled(bool(sources))
            self.tree.resizeColumnToContents(0)
            self.tree.resizeColumnToContents(1)
            self.report.setPlainText('\n'.join('%s — %s: %s' %
                (d['level'].upper(), d['source'], d['message']) for d in diagnostics) or
                'Settings are valid. All sources inherit project defaults unless overridden.')
        except (ValueError, OSError) as error:
            self.report.setPlainText(str(error))

    def edit_defaults(self):
        self.controller.edit_project_compiler_options()
        self.refresh()

    def edit_source(self):
        item = self.tree.currentItem()
        if item:
            self.controller.edit_source_compiler_options(item.data(0, QtCore.Qt.UserRole))
            self.refresh()
