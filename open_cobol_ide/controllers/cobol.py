"""
Controls the COBOL specific action (compile, run and change program type)

"""
import logging
import shlex
import os
import subprocess
import sys
import tempfile

from pyqode.core.api import TextHelper
from pyqode.core.modes import CheckerMessage, CheckerMessages
from pyqode.qt import QtCore, QtGui, QtWidgets
from .base import Controller
from open_cobol_ide import system
from open_cobol_ide.enums import FileType
from open_cobol_ide.compilers import GnuCobolCompiler, get_file_type, \
    DbpreCompiler, EsqlOCCompiler, find_build_script, \
    compile_with_build_script, get_build_script_output_directory
from open_cobol_ide.settings import Settings
from open_cobol_ide import trace_log


LOG_PAGE_COMPILER = 0
LOG_PAGE_ISSUES = 1
LOG_PAGE_RUN = 2

RUN_PROGRAM_SCRIPT = '''#! /bin/bash
cd %s

%s
'''
PATH_RUN_PROGRAM_SCRIPT = os.path.join(tempfile.gettempdir(), 'run_program.sh')

RUN_MODULE_SCRIPT = '''#! /bin/bash
cd %s

%s %s
'''
PATH_RUN_MODULE_SCRIPT = os.path.join(tempfile.gettempdir(), 'run_module.sh')


def create_script(path, script, args):
    import stat
    script = script % args
    with open(path, 'w') as f:
        f.write(script)
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)


class CompilationThread(QtCore.QThread):
    """
    Compiles a file and all its dependencies in a background thread.

    """
    #: signal emitted when a file has compile. Parameters are the file path,
    #: the compiler exit code and the list of possible errors messages.
    file_compiled = QtCore.Signal(str, int, list)

    #: signal emitted when an exception was raise by the compiler.
    errored = QtCore.Signal(str, Exception)

    #: signal emitted when the thread finished.
    finished = QtCore.Signal()

    command_started = QtCore.Signal(str)
    output_available = QtCore.Signal(str)

    #: path of the file to compile
    file_path = ''
    file_paths = None

    def run(self):
        """
        Compiles the file and all its dependencies.
        """
        def is_dbpre_cobol(path):
            if path.lower().endswith('.scb'):
                with open(path, 'r') as f:
                    return 'exec sql' in f.read().lower()
            return False

        def is_esqloc_cobol(path):
            if path.lower().endswith('.sqb'):
                with open(path, 'r') as f:
                    return 'exec sql' in f.read().lower()
            return False

        trace_log.event('compile.thread.enter', source=self.file_path)
        cobc = GnuCobolCompiler()
        cobc.started.connect(self.command_started.emit)
        cobc.output_available.connect(self.output_available.emit)

        dbpre = DbpreCompiler()
        dbpre.started.connect(self.command_started.emit)
        dbpre.output_available.connect(self.output_available.emit)

        esqloc = EsqlOCCompiler()
        esqloc.started.connect(self.command_started.emit)
        esqloc.output_available.connect(self.output_available.emit)

        files = list(self.file_paths) if self.file_paths is not None else [self.file_path]
        if self.file_paths is None and Settings().autodetect_submodules:
            files += cobc.get_dependencies(self.file_path, recursive=True)

        _logger().info('running compilation thread: %r', files)

        for f in dict.fromkeys(files):
            try:
                trace_log.event('compile.file.start', source=f)
                build_script = find_build_script(f)
                if build_script:
                    self.command_started.emit('bash %s %s' % (build_script, f))
                    status, messages = compile_with_build_script(
                        f, self.output_available.emit)
                elif is_dbpre_cobol(f):
                    status, messages = dbpre.compile(f)
                elif is_esqloc_cobol(f):
                    status, messages = esqloc.compile(f)
                else:
                    status, messages = cobc.compile(f, get_file_type(f))
            except Exception as e:
                trace_log.event('compile.file.exception', source=f,
                                exception=repr(e))
                _logger().exception('exception while compiling')
                self.errored.emit(f, e)
            else:
                trace_log.event('compile.file.finished', source=f,
                                status=status, messages=len(messages))
                self.file_compiled.emit(f, status, messages)
        trace_log.event('compile.thread.finished', files_count=len(files))
        self.finished.emit()


def _logger():
    return logging.getLogger(__name__)


class CobolController(Controller):
    """
    Controls the COBOL menu (compile, run, file type).
    """
    def __init__(self, app):
        super().__init__(app)
        self._compilation_thread = None
        group = QtWidgets.QActionGroup(self.main_window)
        group.addAction(self.ui.actionProgram)
        group.addAction(self.ui.actionSubprogram)
        self.compile_buttons = []
        self.run_buttons = []
        self.create_bt_compile()
        self.ui.toolBarCOBOL.insertWidget(
            self.ui.actionClean, self.compile_buttons[0])
        group.triggered.connect(self._on_program_type_changed)
        self.ui.actionCompile.triggered.connect(self.compile)
        self.ui.errorsTable.msg_activated.connect(self._goto_error_msg)
        self.ui.actionRun.triggered.connect(self.run)
        self._run_requested = False
        self.ui.consoleOutput.process_finished.connect(self._on_run_finished)
        self.ui.actionCancel.triggered.connect(self.cancel)
        self.ui.actionClean.triggered.connect(self.clean)
        self.ui.actionRebuild.triggered.connect(self.rebuild)
        self.project_compile_action = self.ui.menuCobol.addAction('Compile Project')
        self.project_compile_action.triggered.connect(self.compile_project)
        self.project_settings_action = self.ui.menuCobol.addAction('Project compiler settings...')
        self.project_settings_action.triggered.connect(self.edit_project_compiler_options)
        self.project_compile_action.setEnabled(bool(self.app.file.project_root))
        self.project_settings_action.setEnabled(bool(self.app.file.project_root))
        self._exception_flags = []
        listing_action = self.ui.menuCobol.addAction('Automatic listing filename')
        listing_action.setCheckable(True)
        listing_action.setChecked(Settings().automatic_listing)
        listing_action.toggled.connect(
            lambda enabled: setattr(Settings(), 'automatic_listing', enabled))
        source_action = self.ui.menuCobol.addAction('Compiler options for this file...')
        source_action.triggered.connect(self.edit_source_compiler_options)

    def edit_project_compiler_options(self):
        root = self.app.file.project_root
        if not root:
            QtWidgets.QMessageBox.information(
                self.main_window, 'Project compiler settings', 'Open a project first.')
            return
        from open_cobol_ide.view.dialogs.source_compiler_options import SourceCompilerOptionsDialog
        settings = Settings()
        options = settings.project_options(root)
        dialog = SourceCompilerOptionsDialog(
            root, settings.compiler_flags, options.get('flags'),
            options.get('environment', {}), self.main_window, project=True, options=options)
        enabled = QtWidgets.QCheckBox('Use these project settings')
        enabled.setChecked(options.get('enabled', True))
        dialog.layout().insertWidget(1, enabled)
        while dialog.exec_() == QtWidgets.QDialog.Accepted:
            try:
                flags, raw, cleaned = dialog.values()
                from open_cobol_ide import project_config as config
                updated = dict(options)
                updated.update(dialog.extra_values())
                updated.update(enabled=enabled.isChecked(), flags=flags, environment=cleaned)
                candidate = config.load(root)
                candidate['defaults'] = config.portable_options(root, updated)
                if not self.validate_project_settings(root, candidate):
                    continue
                settings.set_project_options(root, updated)
            except (ValueError, OSError) as error:
                QtWidgets.QMessageBox.warning(
                    self.main_window, 'Invalid project settings', str(error))
                continue
            break

    def edit_source_compiler_options(self, path=None):
        if not isinstance(path, str):
            editor = self.app.edit.current_editor
            if editor is None or not editor.file.path:
                return
            path = editor.file.path
        from open_cobol_ide.view.dialogs.source_compiler_options import \
            SourceCompilerOptionsDialog
        from open_cobol_ide import project_config as config
        settings = Settings()
        root = config.find_root(path)
        source_options = settings.source_build_options(path)
        dialog = SourceCompilerOptionsDialog(
            path, settings.inherited_flags(path), settings.source_flags(path),
            settings.source_environment(path), self.main_window, options=source_options)
        while dialog.exec_() == QtWidgets.QDialog.Accepted:
            try:
                flags, raw, cleaned = dialog.values()
            except ValueError as error:
                QtWidgets.QMessageBox.warning(
                    self.main_window, 'Invalid compiler options', str(error))
                continue
            changes = ['%s\n→ %s' % (raw[key], cleaned[key])
                       for key in ('compiler_path', 'path', 'cob_copy_dir')
                       if raw[key] != cleaned[key]]
            if changes:
                QtWidgets.QMessageBox.warning(
                    self.main_window, 'Spaces removed from directory paths',
                    'Leading or trailing spaces around directory components '
                    'can select a different path. They were removed:\n\n' +
                    '\n'.join(changes))
            try:
                extra = dialog.extra_values()
                if root:
                    candidate = config.load(root)
                    updated = dict(source_options)
                    updated.update(extra)
                    updated.update(flags=flags, environment=cleaned)
                    candidate['sources'][config.source_key(root, path)] = config.portable_options(root, updated)
                    if not self.validate_project_settings(root, candidate):
                        continue
                settings.set_source_compiler_options(path, flags, cleaned, extra)
            except (ValueError, OSError) as error:
                QtWidgets.QMessageBox.warning(self.main_window, 'Invalid source settings', str(error))
                continue
            break

    def validate_project_settings(self, root, document=None, paths=None):
        from open_cobol_ide.project_validation import validate_project
        try:
            diagnostics = validate_project(root, Settings(), document, paths)
        except (ValueError, OSError) as error:
            QtWidgets.QMessageBox.warning(self.main_window, 'Project configuration error', str(error))
            return False
        errors = [item for item in diagnostics if item['level'] == 'error']
        if document is not None and errors:
            # Let users repair existing conflicts incrementally, without accepting new ones.
            try:
                previous = validate_project(root, Settings(), sources=paths)
            except (ValueError, OSError):
                previous = []
            existing = [item for item in errors if item in previous]
            errors = [item for item in errors if item not in existing]
            diagnostics = [dict(item, level='warning', message='Existing conflict: ' + item['message'])
                           if item in existing else item for item in diagnostics]
        warnings = [item for item in diagnostics if item['level'] == 'warning']
        if errors:
            QtWidgets.QMessageBox.warning(self.main_window, 'Conflicting project settings',
                '\n\n'.join('%s: %s' % (d['source'], d['message']) for d in errors))
            return False
        if warnings:
            return QtWidgets.QMessageBox.question(self.main_window, 'Project settings warnings',
                '\n\n'.join('%s: %s' % (d['source'], d['message']) for d in warnings) +
                '\n\nContinue with these settings?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes
        return True

    def create_bt_compile(self):
        bt_compile = QtWidgets.QToolButton()
        bt_compile.setIcon(self.ui.actionCompile.icon())
        bt_compile.setMenu(self.ui.menuProgramType)
        bt_compile.setToolTip(self.ui.actionCompile.toolTip())
        bt_compile.setPopupMode(bt_compile.MenuButtonPopup)
        bt_compile.clicked.connect(self.compile)
        self.compile_buttons.append(bt_compile)
        bt_compile.setEnabled(self.ui.actionCompile.isEnabled())
        return bt_compile

    def display_file_type(self, editor):
        """
        Displays the current editor file type (changes the checked action in
        the file type drop down menu).

        """
        try:
            ftype = editor.file_type
        except (AttributeError, UnicodeDecodeError):
            pass
        else:
            self.ui.actionProgram.setChecked(ftype == FileType.EXECUTABLE)
            self.ui.actionSubprogram.setChecked(ftype != FileType.EXECUTABLE)
            for item in self.run_buttons + [self.ui.actionRun]:
                item.setEnabled(not self.ui.consoleOutput.is_running and self._can_build_current_source())

    def _on_program_type_changed(self, action):
        """
        Updates current editor file type and enables/disables run action.
        """
        if action == self.ui.actionProgram:
            self.ui.tabWidgetEditors.current_widget().file_type = \
                FileType.EXECUTABLE
            for item in self.run_buttons + [self.ui.actionRun]:
                item.setEnabled(not self.ui.consoleOutput.is_running)
        else:
            self.ui.tabWidgetEditors.current_widget().file_type = \
                FileType.MODULE
            for item in self.run_buttons + [self.ui.actionRun]:
                item.setEnabled(False)

    def check_compiler(self, dotted_extension):
        compiler_works = False
        msg = 'Invalid extension'
        if dotted_extension.lower() in Settings().cobc_extensions:
            compiler_works = GnuCobolCompiler().is_working()
            msg = 'GnuCOBOL compiler not found or not working'
        elif dotted_extension.lower() in Settings().dbpre_extensions:
            compiler_works = DbpreCompiler().is_working()
            msg = 'dbpre compiler not working, please check your SQL COBOL ' \
                'configuration'
        elif dotted_extension.lower() in Settings().esqloc_extensions:
            compiler_works = EsqlOCCompiler().is_working()
            msg = 'esqlOC compiler not working, please check your SQL COBOL ' \
                'configuration'
        return compiler_works, msg

    def compile_project(self):
        from open_cobol_ide.project import project_sources
        root = self.app.file.project_root
        if not root:
            QtWidgets.QMessageBox.information(
                self.main_window, 'Compile Project', 'Open a project directory first.')
            return
        settings = Settings()
        paths = project_sources(root, settings.cobc_extensions +
                                settings.dbpre_extensions + settings.esqloc_extensions)
        if not paths:
            QtWidgets.QMessageBox.information(
                self.main_window, 'Compile Project', 'No COBOL sources found.')
            return
        self._run_requested = False
        self._start_compilation(paths)

    def _start_compilation(self, paths=None):
        if self._compilation_thread is not None and self._compilation_thread.isRunning():
            return
        try:
            if self.ui.tabWidgetEditors.save_all() is False:
                return
        except OSError as error:
            QtWidgets.QMessageBox.warning(self.main_window, 'Cannot save sources', str(error))
            return
        sources = paths or [self.app.edit.current_editor.file.path]
        roots = {Settings().project_root_for_source(source) for source in sources}
        from open_cobol_ide.project_config import config_path
        for root in roots:
            if root and config_path(root).is_file():
                if not self.validate_project_settings(root, paths=[p for p in sources
                        if Settings().project_root_for_source(p) == root]):
                    return
        self.enable_compile(False)
        self.project_compile_action.setEnabled(False)
        self.enable_run(False)
        self.ui.errorsTable.clear()
        self._errors = 0
        self.ui.textEditCompilerOutput.clear()
        self.ui.tabWidgetLogs.setCurrentIndex(LOG_PAGE_COMPILER)
        self._compilation_thread = CompilationThread()
        self._compilation_thread.file_paths = paths
        self._compilation_thread.file_path = (
            paths[0] if paths else self.app.edit.current_editor.file.path)
        self._compilation_thread.file_compiled.connect(self._on_file_compiled)
        self._compilation_thread.errored.connect(self._on_build_exception)
        self._compilation_thread.command_started.connect(self._on_command_started)
        self._compilation_thread.output_available.connect(self._on_output_available)
        self._compilation_thread.finished.connect(self._on_compilation_finished)
        self._exception_flags[:] = []
        self._compilation_thread.start()

    def compile(self):
        """
        Compiles the current editor
        """
        if self.app.edit.current_editor is None:
            return
        # make sure the associated compiler is working, otherwise disable
        # compile/run actions
        path = self.app.edit.current_editor.file.path
        if os.path.splitext(path)[1].lower() == '.cpy':
            return
        trace_log.event('compile.requested', source=path,
                        run_requested=self._run_requested)
        dotted_extension = os.path.splitext(path)[1].upper()
        if Settings().project_root_for_source(path):
            compiler_works, msg = True, ''
        else:
            compiler_works, msg = self.check_compiler(dotted_extension)
        if not compiler_works:
            QtWidgets.QMessageBox.warning(
                self.app.win, 'Cannot compile file',
                'Cannot compile file: %r.\n\nReason: %s' % (
                    os.path.split(path)[1], msg))
            return
        self._start_compilation()

    def clean(self):
        path = self.app.edit.current_editor.file.path
        CobolController.clean_file(path)

    @staticmethod
    def clean_file(path):
        output_path = GnuCobolCompiler().get_output_filename(
            [os.path.split(path)[1]], get_file_type(path))
        output_dir = get_build_script_output_directory(path)
        if output_dir is None:
            output_dir = Settings().output_directory
            if not os.path.isabs(output_dir):
                output_dir = os.path.abspath(os.path.join(
                    os.path.dirname(path), output_dir))
        output_path = os.path.join(output_dir, output_path)
        try:
            os.remove(output_path)
        except OSError:
            _logger().debug('failed to remove output file %r', output_path)
        else:
            _logger().debug('file removed: %s', output_path)

    def rebuild(self):
        self.clean()
        self.compile()

    def _on_command_started(self, cmd):
        trace_log.event('compile.command.started', command=cmd)
        old_color = self.ui.textEditCompilerOutput.textColor()
        color = QtGui.QColor('#629755') if Settings().dark_style else \
            QtGui.QColor('#000080')
        self.ui.textEditCompilerOutput.setTextColor(color)
        self.ui.textEditCompilerOutput.append(cmd)
        self.ui.textEditCompilerOutput.setTextColor(old_color)

    def _on_output_available(self, output):
        if output:
            self.ui.textEditCompilerOutput.append(output)

    def _on_compilation_finished(self):
        """
        Runs the current file if the compilation came from a run request,
        otherwise enables actions/buttons.

        """
        trace_log.event('compile.ui.finished', errors=self._errors,
                        run_requested=self._run_requested)
        self.enable_compile(True)
        self.project_compile_action.setEnabled(bool(self.app.file.project_root))
        self.enable_run(True)
        self.ui.tabWidgetLogs.setCurrentIndex(LOG_PAGE_ISSUES)
        if self._run_requested:
            self._run_requested = False
            if self._errors == 0:
                self.enable_compile(False)
                self.enable_run(False)
                self._run()

    def _on_build_exception(self, path, exception):
        trace_log.event('compile.ui.exception', source=path,
                        exception=repr(exception))
        self.ui.errorsTable.add_message(
            CheckerMessage(
                    str(exception), CheckerMessages.ERROR, -1, path=path))
        self._errors += 1
        self.ui.dockWidgetLogs.show()
        self.ui.tabWidgetLogs.setCurrentIndex(LOG_PAGE_ISSUES)
        if type(exception) not in self._exception_flags:
            self._exception_flags.append(type(exception))
            QtWidgets.QMessageBox.critical(
                self.main_window, 'Exception while compiling a file',
                'An exception occured when compiling %r.\n\nError=%s' %
                (path, exception))

    def _on_file_compiled(self, filename, status, messages):
        """
        Displays compilation status in errors table.
        """
        self.ui.dockWidgetLogs.show()
        self.ui.tabWidgetLogs.setCurrentIndex(LOG_PAGE_COMPILER)
        if len(messages) == 0 and status == 0:
            ext = GnuCobolCompiler().extension_for_type(
                get_file_type(filename))
            name = os.path.splitext(os.path.split(filename)[1])[0]
            output_dir = get_build_script_output_directory(filename)
            if output_dir is None:
                output_dir = Settings().output_directory
                if not os.path.isabs(output_dir):
                    path = os.path.dirname(filename)
                    output_dir = os.path.abspath(os.path.join(
                        path, output_dir))
            path = os.path.join(output_dir, name + ext)
            self.ui.errorsTable.add_message(
                CheckerMessage(
                    'Compilation succeeded (output: %s)' % path,
                    CheckerMessages.INFO, -1,
                    path=filename))
        else:
            if status != 0 and not any(
                    msg[1] == CheckerMessages.ERROR for msg in messages):
                messages = list(messages) + [('Compiler exited with status %s' % status,
                             CheckerMessages.ERROR, -1, 0, None, None, filename)]
            for msg in messages:
                msg = CheckerMessage(*msg)
                if msg.status == CheckerMessages.ERROR:
                    self._errors += 1
                if len(msg.description.splitlines()) > 1:
                    msg.description = 'For full output see compiler tab...'
                self.ui.errorsTable.add_message(msg)

    def _goto_error_msg(self, msg):
        """
        Opens an editor and goes to the error line.
        """
        if os.path.exists(msg.path):
            self.app.file.open_file(msg.path)
            if msg.status:
                TextHelper(self.app.edit.current_editor).goto_line(msg.line)
                self.app.edit.current_editor.setFocus(True)

    def run(self):
        """
        Compiles and run the current editor.
        """
        if self.app.edit.current_editor is None:
            return
        source = os.path.abspath(self.app.edit.current_editor.file.path)
        if os.path.splitext(source)[1].lower() == '.cpy':
            return
        trace_log.event('run.requested', source=source)
        settings = QtCore.QSettings('OpenCobolIDE', 'OpenCobolIDE4')
        key = 'programArguments/' + source
        text = settings.value(key, '')
        while True:
            text, accepted = QtWidgets.QInputDialog.getText(
                self.main_window, 'Run program',
                'Program arguments (optional):\n'
                'Use quotes for spaces, for example: "customer name" 123',
                QtWidgets.QLineEdit.Normal, text)
            if not accepted:
                trace_log.event('run.arguments.cancelled', source=source)
                return
            try:
                arguments = shlex.split(text)
            except ValueError as exc:
                QtWidgets.QMessageBox.warning(
                    self.main_window, 'Invalid arguments', str(exc))
                continue
            break
        settings.setValue(key, text)
        self._program_arguments = arguments
        trace_log.event('run.arguments.accepted', source=source,
                        argument_count=len(arguments))
        self.ui.consoleOutput.clear()
        self._run_requested = True
        self.compile()

    def _run_in_external_terminal(self, program, wd, file_type):
        """
        Runs a program in an external terminal.

        :param program: program to run
        :param wd: working directory
        """
        arguments = getattr(self, '_program_arguments', [])
        trace_log.event('run.external.start', program=program,
                        working_directory=wd, file_type=int(file_type),
                        argument_count=len(arguments))
        pyqode_console = system.which('pyqode-console')
        cobc_run_insert_pos = 1
        if pyqode_console is None:
            from pyqode.core.tools import console
            pyqode_console = [sys.executable, console.__file__]
            cobc_run_insert_pos = 2
        else:
            pyqode_console = [pyqode_console]
        env = os.environ.copy()
        for k, v in Settings().run_environemnt.items():
            env[k] = v
        if 'PATH' not in Settings().run_environemnt.keys():
            env['PATH'] = GnuCobolCompiler.setup_process_environment().value(
                'PATH')
        if file_type == FileType.MODULE:
            program = QtCore.QFileInfo(program).baseName()
        if system.windows:
            cmd = pyqode_console + [program] + arguments
            if file_type == FileType.MODULE:
                cmd.insert(cobc_run_insert_pos, system.which('cobcrun'))
            try:
                _logger().debug("running program in external terminal: %r, %r, %r" % (cmd, wd, env))
                subprocess.Popen(cmd, cwd=wd, creationflags=subprocess.CREATE_NEW_CONSOLE, env=env)
            except (OSError, subprocess.CalledProcessError):
                msg = "Failed to launch program in external terminal (cmd=%s) " % ' '.join(cmd)
                _logger().exception(msg)
                self.ui.consoleOutput.appendPlainText(msg)
                return
        elif system.darwin:
            if file_type == FileType.MODULE:
                create_script(PATH_RUN_MODULE_SCRIPT, RUN_MODULE_SCRIPT, (shlex.quote(wd), shlex.quote(system.which('cobcrun')), ' '.join(shlex.quote(a) for a in [program] + arguments)))
                cmd = ['open', '-n', '-a', 'Terminal', '--args', PATH_RUN_MODULE_SCRIPT]
            else:
                create_script(PATH_RUN_PROGRAM_SCRIPT, RUN_PROGRAM_SCRIPT, (shlex.quote(wd), ' '.join(shlex.quote(a) for a in [program] + arguments)))
                cmd = ['open', '-n', '-a', 'Terminal', '--args', PATH_RUN_PROGRAM_SCRIPT]
            try:
                subprocess.Popen(cmd, cwd=wd, env=env)
            except (OSError, subprocess.CalledProcessError):
                msg = "Failed to launch program in external terminal (cmd=%s) " % ' '.join(cmd)
                _logger().exception(msg)
                self.ui.consoleOutput.appendPlainText(msg)
                return
        else:
            launch = pyqode_console[:]
            if file_type == FileType.MODULE:
                launch.append(system.which('cobcrun'))
            launch += [program] + arguments
            command = ' '.join(shlex.quote(a) for a in launch)
            cmd = system.shell_split(Settings().external_terminal_command.strip())
            cmd.append(command)
            try:
                subprocess.Popen(cmd, cwd=wd, env=env)
            except (OSError, subprocess.CalledProcessError):
                msg = "Failed to launch program in external terminal (cmd=%s) " % ' '.join(cmd)
                _logger().exception(msg)
                self.ui.consoleOutput.appendPlainText(msg)
                return
        _logger().info('running program in external terminal: %s', ' '.join(cmd))
        self.ui.consoleOutput.appendPlainText("Launched in external terminal: %s" % ' '.join(cmd))
        trace_log.event('run.external.launched', program=program)

    def _run(self):
        """
        Runs the current editor program.
        :return:
        """
        # compilation has finished, we can run the program that corresponds
        # to the current editor file
        editor = self.app.edit.current_editor
        file_type = editor.file_type
        self.ui.tabWidgetLogs.setCurrentIndex(LOG_PAGE_RUN)
        self.ui.dockWidgetLogs.show()
        self.ui.consoleOutput.clear()
        output_dir = get_build_script_output_directory(editor.file.path)
        if output_dir is None:
            output_dir = Settings().output_directory
            if not os.path.isabs(output_dir):
                output_dir = os.path.join(
                    os.path.dirname(editor.file.path), output_dir)
        if Settings().working_dir:
            wd = Settings().working_dir
        else:
            wd = output_dir
        filename = os.path.splitext(editor.file.name)[0] + \
            GnuCobolCompiler().extension_for_type(file_type)
        program = os.path.join(output_dir, filename)
        if not os.path.exists(program):
            trace_log.event('run.program.missing', program=program)
            _logger().warning('cannot run %s, file does not exists',
                              program)
            return
        _logger().info('running program: %r (working dir=%r)', program, wd)
        trace_log.event(
            'run.program.start', program=program, working_directory=wd,
            file_type=int(file_type), external_terminal=Settings().external_terminal,
            argument_count=len(getattr(self, '_program_arguments', [])))
        if Settings().external_terminal:
            self._run_in_external_terminal(program, wd, file_type)
            self.enable_run(True)
            self.enable_compile(True)
        else:
            self.ui.consoleOutput.setFocus(True)
            for item in self.run_buttons + [self.ui.actionRun]:
                item.setEnabled(False)
            path = GnuCobolCompiler.setup_process_environment().value('PATH')
            env = Settings().run_environemnt
            if 'PATH' not in env.keys():
                env['PATH'] = path
            if file_type == FileType.MODULE:
                cobcrun = system.which('cobcrun')
                self.ui.consoleOutput.start_process(
                    cobcrun, [os.path.splitext(editor.file.name)[0]] + getattr(self, '_program_arguments', []), working_dir=wd, env=env)
            else:
                self.ui.consoleOutput.start_process(program, getattr(self, '_program_arguments', []), working_dir=wd, env=env, print_command=True)
            trace_log.event(
                'run.process.start.called', program=program,
                process_state=int(self.ui.consoleOutput.process.state()),
                process_id=int(self.ui.consoleOutput.process.processId()))

    def _on_run_finished(self):
        process = self.ui.consoleOutput.process
        trace_log.event(
            'run.process.finished', exit_code=process.exitCode(),
            exit_status=int(process.exitStatus()), state=int(process.state()),
            process_id=int(process.processId()))
        self.enable_compile(True)
        self.enable_run(True)

    def _can_build_current_source(self):
        editor = self.app.edit.current_editor
        return editor is not None and os.path.splitext(editor.file.path or '')[1].lower() != '.cpy'

    def enable_compile(self, enable):
        enable = enable and self._can_build_current_source()
        for item in self.compile_buttons + [self.ui.actionCompile, self.ui.actionClean, self.ui.actionRebuild]:
            item.setEnabled(enable)

    def enable_run(self, enable):
        enable = enable and self._can_build_current_source()
        for item in self.run_buttons + [self.ui.actionRun]:
            item.setEnabled(enable)

    def cancel(self):
        """
        Cancels current any ongoing operations (run/compile).
        """
        trace_log.event(
            'operation.cancel.requested',
            compiling=bool(self._compilation_thread and
                           self._compilation_thread.isRunning()),
            console_running=self.ui.consoleOutput.is_running)
        if self._compilation_thread:
            self._compilation_thread.terminate()
        self.ui.consoleOutput.stop_process()
        trace_log.event('operation.cancel.finished')
        self.enable_compile(True)
        self.enable_run(True)
