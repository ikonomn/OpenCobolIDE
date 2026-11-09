import os
import shlex

from pyqode.qt import QtWidgets

from open_cobol_ide import system
from open_cobol_ide.path_utils import clean_directory_path


class SourceCompilerOptionsDialog(QtWidgets.QDialog):
    """Edit compiler flags and environment overrides for one source file."""
    def __init__(self, source_path, global_flags, flags, environment, parent=None, project=False, options=None, debug_enabled=False):
        super().__init__(parent)
        options = options or {}
        self._compiler_inherited_flags = list(global_flags)
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
        self.c_auto = None
        self.file_debug = None
        if not project:
            self._source_path = source_path
            self.file_debug = QtWidgets.QCheckBox('Compile this file with debug')
            self.file_debug.setChecked(options.get('compile_debug', False))
            self.file_debug.setToolTip(
                'Add -g -fsource-location -ftraceall -O0 -save-temps. '
                'Explicit optimization is preserved. Project debug settings also apply.')
            form.addRow(self.file_debug)
            self.output_name_field = QtWidgets.QLineEdit(options.get('output_name', ''))
            self.output_name_field.setPlaceholderText(os.path.splitext(os.path.basename(source_path))[0])
            self.output_name_field.setToolTip('Optional filename override; no folder. Used consistently by Build, Run and Debug.')
            form.addRow('Executable name (optional):', self.output_name_field)
            self.c_auto = QtWidgets.QCheckBox('Detect C helpers from literal COBOL CALLs (default)')
            self.c_auto.setChecked(options.get('c_sources') is None)
            form.addRow(self.c_auto)
            self.c_sources = QtWidgets.QPlainTextEdit('\n'.join(options.get('c_sources') or []))
            self.c_sources.setMaximumHeight(55)
            self.c_sources.setPlaceholderText('C helper paths relative to the project; one file per line. Blank manual list disables helpers.')
            self.c_sources.setDisabled(self.c_auto.isChecked())
            self.c_auto.toggled.connect(self.c_sources.setDisabled)
            form.addRow('Manual C helper sources:', self.c_sources)
            preview = QtWidgets.QPushButton('Preview proposed C build command…')
            preview.clicked.connect(self.preview_c_build)
            form.addRow(preview)
        self.debug = None
        if project:
            self.debug = QtWidgets.QCheckBox('Compile with debug')
            self.debug.setChecked(debug_enabled)
            form.addRow(self.debug)
            self.debug_note = QtWidgets.QLabel()
            self.debug_note.setWordWrap(True)
            form.addRow(self.debug_note)
            self._inherited_flags = list(global_flags)
            self.debug.toggled.connect(self.update_debug_note)
            self.flags.textChanged.connect(self.update_debug_note)
            self.use_global_flags.toggled.connect(self.update_debug_note)
            self.update_debug_note()
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
        form_widget = QtWidgets.QWidget()
        form_widget.setLayout(form)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)
        self.resize(760, 730)
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

    def update_debug_note(self, *unused):
        if not self.debug.isChecked():
            self.debug_note.setText('Debug compilation is off. Extra compiler flags are preserved.')
            return
        try:
            flags = (self._inherited_flags if self.use_global_flags.isChecked() else
                     shlex.split(self.flags.text(), posix=not system.windows))
        except ValueError:
            self.debug_note.setText('Finish quoting the extra compiler flags to preview debug options.')
            return
        import re
        optimizations = [flag for flag in flags if re.fullmatch(r'-O(?:[0-9]+|s|z|g|fast)?', flag)]
        optimization = optimizations[-1] if optimizations else '-O0'
        text = ('Debug options: -g -fsource-location -ftraceall %s -save-temps. '
                'Matching flags are used once; extra flags are preserved. '
                'Generated C and headers are retained in debug_data/. '
                'Changing this setting makes the next project build recompile affected sources. ' % optimization)
        if optimization != '-O0':
            text += ('Your explicit %s is preserved; optimized code can make stepping and '
                     'variable inspection less predictable.' % optimization)
        else:
            text += ('Mageia and other hardened toolchains may warn that _FORTIFY_SOURCE '
                     'requires optimization with -O0. Compiler warnings remain visible; '
                     'specify -O2 explicitly if optimized debugging is intended.')
        self.debug_note.setText(text)

    def reset(self):
        self.use_global_flags.setChecked(True)
        if self.debug is not None:
            self.debug.setChecked(False)
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
        if self.c_auto is not None:
            self.file_debug.setChecked(False)
            self.output_name_field.clear()
            self.c_auto.setChecked(True)
            self.c_sources.clear()

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
        if self.c_auto is not None:
            from open_cobol_ide.c_helpers import output_name
            result['compile_debug'] = self.file_debug.isChecked()
            result['output_name'] = self.output_name_field.text().strip()
            output_name(self._source_path, result)
            result['c_sources'] = (None if self.c_auto.isChecked() else
                [value.strip() for value in self.c_sources.toPlainText().splitlines() if value.strip()])
        return result

    def proposed_c_command(self):
        from open_cobol_ide import project_config as config
        from open_cobol_ide.c_helpers import plan, output_name
        from open_cobol_ide.project_outputs import output_directory
        from open_cobol_ide.settings import Settings
        from open_cobol_ide.compilers import get_file_type, GnuCobolCompiler
        from open_cobol_ide.enums import FileType
        from open_cobol_ide.source_format import read_source_format
        root = config.find_root(self._source_path)
        if not root:
            raise ValueError('Open this source as a project to link C helper sources.')
        settings = Settings()
        options = settings.effective_build_options(self._source_path)
        draft = self.extra_values()
        for key in ('output_name', 'c_sources'):
            options[key] = draft[key]
        for key in ('copybook_paths', 'library_paths', 'libraries'):
            if draft[key] is not None:
                options[key] = draft[key]
        flags, raw, cleaned = self.values()
        if flags is None:
            flags = self._compiler_inherited_flags
        flags = list(flags)
        free = read_source_format(self._source_path)
        if free is None:
            selected = self.source_format.currentData()
            free = settings.free_format if selected == 'inherit' else selected == 'free'
        if '-free' in flags: free = True
        if '-fixed' in flags: free = False
        from open_cobol_ide.compiler_options import gtk_link_flags
        flags = gtk_link_flags(self._source_path, flags, options['libraries'], free)
        if any(flag.startswith(('`', '$(')) for flag in flags):
            from open_cobol_ide.compiler_options import expand_pkg_config
            environment = dict(entry.split('=', 1) for entry in
                               GnuCobolCompiler.setup_process_environment(self._source_path).toStringList())
            flags = expand_pkg_config(flags, cwd=root, env=environment)
        if '-free' not in flags and '-fixed' not in flags:
            flags.append('-free' if free else '-fixed')
        if self.file_debug.isChecked() or config.debug_enabled(root):
            from open_cobol_ide.compiler_options import with_debug_flags
            flags = with_debug_flags(flags)
        helpers = plan(self._source_path, root, options, free, system.windows, options['copybook_paths'])
        mode = get_file_type(self._source_path)
        extension = GnuCobolCompiler().extension_for_type(mode)
        output = os.path.join(output_directory(root, mode != FileType.EXECUTABLE),
                              output_name(self._source_path, options, extension))
        command = [cleaned['compiler_path'] or settings.effective_environment(self._source_path).get('compiler_path')
                   or settings.compiler_path, '-x' if mode == FileType.EXECUTABLE else '-m']
        command += flags
        for key, switch in (('copybook_paths', '-I'), ('library_paths', '-L')):
            for value in options[key]: command += [switch, config.resolve_path(root, value)]
        command += ['-o', output, self._source_path] + helpers['sources']
        for library in list(options['libraries']) + helpers['libraries']:
            if '-l'+library not in command: command.append('-l'+library)
        return command

    def preview_c_build(self):
        try:
            command = self.proposed_c_command()
        except (ValueError, OSError) as error:
            QtWidgets.QMessageBox.warning(self, 'Cannot propose C helper build', str(error))
            return
        import subprocess
        text = (subprocess.list2cmdline(command) if system.windows else
                ' '.join(shlex.quote(value) for value in command))
        QtWidgets.QMessageBox.information(self, 'Proposed C helper build',
            text + '\n\nThe project builder also adds listing, diagnostic and retained-debug-source options. '
            'OK in File compiler settings saves manual choices; automatic detection applies by default.')
