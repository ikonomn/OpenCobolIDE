import os
import shlex

from pyqode.qt import QtWidgets

from open_cobol_ide import system
from open_cobol_ide.path_utils import clean_directory_path


class SourceCompilerOptionsDialog(QtWidgets.QDialog):
    """Edit compiler flags and environment overrides for one source file."""
    def __init__(self, source_path, global_flags, flags, environment, parent=None, project=False, options=None):
        super().__init__(parent)
        options = options or {}
        self.setWindowTitle('Project compiler settings' if project else
                            'Compiler options for this file')
        self.setMinimumWidth(620)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(os.path.abspath(source_path))
        label.setWordWrap(True)
        layout.addWidget(label)

        self.use_global_flags = QtWidgets.QCheckBox('Use IDE default compiler flags' if project else
                                                        'Inherit project / IDE compiler flags')
        self.use_global_flags.setChecked(flags is None)
        layout.addWidget(self.use_global_flags)
        form = QtWidgets.QFormLayout()
        self.flags = QtWidgets.QLineEdit(' '.join(
            shlex.quote(f) for f in (global_flags if flags is None else flags)))
        self.flags.setToolTip('Custom flags replace the inherited extra compiler flags.')
        form.addRow('Extra compiler flags:', self.flags)
        self.compiler_path = QtWidgets.QLineEdit(environment.get('compiler_path', ''))
        self.compiler_path.setPlaceholderText('Inherit compiler')
        form.addRow('Compiler path:', self.compiler_path)
        self.path = QtWidgets.QLineEdit(environment.get('path', ''))
        self.path.setPlaceholderText(
            'Optional directory containing gcc, clang or other build tools')
        self.path.setToolTip(
            'This directory is searched before the existing PATH. Use '
            'Compiler path above to select cobc directly.')
        form.addRow('Additional tools directory:', self.path)
        self.cob_copy_dir = QtWidgets.QLineEdit(environment.get('cob_copy_dir', ''))
        self.cob_copy_dir.setPlaceholderText('Inherit COB_COPY_DIR')
        form.addRow('COB_COPY_DIR:', self.cob_copy_dir)
        self.gix_fields = {}
        for key, title in (('gixpp_path', 'GixSQL preprocessor:'),
                           ('gixsql_copy_dir', 'GixSQL copybook directory:'),
                           ('gixsql_library_dir', 'GixSQL library directory:')):
            field = QtWidgets.QLineEdit(environment.get(key, ''))
            field.setPlaceholderText('Inherit')
            self.gix_fields[key] = field
            form.addRow(title, field)
        self.path_fields = {}
        for key, title in (('copybook_paths', 'Copybook paths:'),
                           ('library_paths', 'Library paths:'), ('libraries', 'Libraries:')):
            row = QtWidgets.QHBoxLayout()
            inherit = QtWidgets.QCheckBox('Inherit')
            values = options.get(key)
            inherit.setChecked(values is None)
            text = (' '.join(shlex.quote(v) for v in values) if key == 'libraries'
                    else '; '.join(values)) if values is not None else ''
            field = QtWidgets.QLineEdit(text)
            field.setPlaceholderText('Library names separated by spaces' if key == 'libraries'
                                     else 'Project-relative folders separated by semicolons')
            field.setDisabled(inherit.isChecked())
            inherit.toggled.connect(field.setDisabled)
            row.addWidget(inherit)
            row.addWidget(field)
            form.addRow(title, row)
            self.path_fields[key] = (inherit, field)
        self.source_format = QtWidgets.QComboBox()
        for label, value in (('Inherit', 'inherit'), ('Fixed', 'fixed'), ('Free', 'free')):
            self.source_format.addItem(label, value)
        self.source_format.setCurrentIndex(self.source_format.findData(options.get('source_format', 'inherit')))
        form.addRow('Source format:', self.source_format)
        listing = options.get('listing', {})
        self.listing_enabled = QtWidgets.QComboBox()
        for label, value in (('Inherit', None), ('Generate listing', True), ('No listing', False)):
            self.listing_enabled.addItem(label, value)
        self.listing_enabled.setCurrentIndex(self.listing_enabled.findData(listing.get('enabled')))
        form.addRow('Listing:', self.listing_enabled)
        self.listing_filename = QtWidgets.QLineEdit(listing.get('filename', ''))
        self.listing_filename.setPlaceholderText('Inherit; for example build/{stem}.lst')
        form.addRow('Listing filename:', self.listing_filename)
        layout.addLayout(form)
        note = QtWidgets.QLabel(
            'Blank fields inherit settings from the level above. Use Compiler path to select '
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
        for field in self.gix_fields.values(): field.clear()
        for inherit, field in self.path_fields.values():
            inherit.setChecked(True)
            field.clear()
        self.source_format.setCurrentIndex(0)
        self.listing_enabled.setCurrentIndex(0)
        self.listing_filename.clear()

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
        raw.update({key: field.text() for key, field in self.gix_fields.items()})
        cleaned = dict(raw)
        cleaned['compiler_path'] = clean_directory_path(raw['compiler_path'])
        cleaned['path'] = clean_directory_path(raw['path'])
        cleaned['path_mode'] = ('prepend' if cleaned['path'] else 'inherit')
        cleaned['cob_copy_dir'] = clean_directory_path(raw['cob_copy_dir'])
        for key in self.gix_fields:
            cleaned[key] = clean_directory_path(raw[key])
        return flags, raw, cleaned

    def extra_values(self):
        result = {'source_format': self.source_format.currentData(), 'listing': {}}
        for key, (inherit, field) in self.path_fields.items():
            result[key] = None if inherit.isChecked() else (
                shlex.split(field.text(), posix=not system.windows) if key == 'libraries' else
                [clean_directory_path(value) for value in field.text().split(';') if value.strip()])
        enabled = self.listing_enabled.currentData()
        if enabled is not None:
            result['listing']['enabled'] = enabled
        if self.listing_filename.text().strip():
            result['listing']['filename'] = clean_directory_path(self.listing_filename.text())
        return result
