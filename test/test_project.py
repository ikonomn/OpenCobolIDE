"""Project discovery, UI routing, batch dispatch, and build-script contracts."""
import json
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from open_cobol_ide import compilers
from open_cobol_ide.controllers.cobol import CompilationThread, CobolController
from open_cobol_ide.controllers.file import FileController
from open_cobol_ide.enums import FileType
from open_cobol_ide.project import project_sources
from open_cobol_ide.settings import Settings


def test_project_discovery(tmp_path):
    for name in ['src/a.cbl', 'src/B.COB', 'copy/a.cpy', 'build/generated.cbl',
                 'bin/a.cbl', '.git/a.cbl', 'src/a.lst', 'src/a.prn']:
        path = tmp_path / name
        path.parent.mkdir(exist_ok=True)
        path.write_text('')
    (tmp_path / 'src/link.cbl').symlink_to(tmp_path / 'src/a.cbl')
    assert project_sources(str(tmp_path), ['.cbl', '.cob', '.cpy', '.lst']) == [
        str(tmp_path / 'src/B.COB'), str(tmp_path / 'src/a.cbl')]


@pytest.mark.parametrize('free', [False, True])
def test_detection_ignores_comments_and_literals_and_honors_override(tmp_path, free):
    source = tmp_path / 'mode.cbl'
    prefix = '' if free else '       '
    source.write_text(('>>source format free\n' if free else '') +
                      prefix + 'display "LINKAGE SECTION PROCEDURE DIVISION USING".\n' +
                      prefix + '*> LINKAGE SECTION PROCEDURE DIVISION USING\n')
    assert compilers.get_file_type(str(source)) == FileType.EXECUTABLE
    source.write_text(source.read_text() + prefix + 'linkage section.\n' +
                      prefix + 'procedure division\n' + prefix + 'using item.\n')
    assert compilers.get_file_type(str(source)) == FileType.MODULE
    settings = Settings()
    settings.set_file_type(str(source), FileType.EXECUTABLE)
    assert compilers.get_file_type(str(source)) == FileType.EXECUTABLE


def test_open_project_without_editor(tmp_path):
    calls = []
    ui = SimpleNamespace(tvFileSystem=SimpleNamespace(set_root_path=calls.append),
                         dockWidgetFileSystem=SimpleNamespace(show=lambda: calls.append('show')))
    fake = SimpleNamespace(ui=ui, app=SimpleNamespace(view=SimpleNamespace(
        show_edit_page=lambda: calls.append('edit'))))
    FileController.open_project(fake, str(tmp_path))
    assert fake.project_root == str(tmp_path)
    assert calls == ['edit', str(tmp_path), 'show']


def test_batch_dispatch_deduplicates_and_continues_after_failure(monkeypatch, tmp_path):
    from open_cobol_ide.controllers import cobol
    paths = [str(tmp_path / name) for name in ('main.cbl', 'worker.cbl')]
    for path in paths:
        Path(path).write_text('       identification division.\n')
    called = []
    def compile_source(self, source, mode):
        called.append(source)
        if source == paths[0]:
            raise RuntimeError('first build failed')
        return 0, []
    monkeypatch.setattr(cobol.GnuCobolCompiler, 'compile', compile_source)
    monkeypatch.setattr(cobol.GnuCobolCompiler, 'get_dependencies',
                        lambda *a, **k: pytest.fail('batch must not expand dependencies'))
    thread = CompilationThread()
    thread.file_paths = paths + paths
    thread.file_path = paths[0]
    errors, completed = [], []
    thread.errored.connect(lambda source, error: errors.append(source))
    thread.file_compiled.connect(lambda source, status, messages: completed.append(source))
    thread.run()
    assert called == paths
    assert errors == paths[:1]
    assert completed == paths[1:]


def test_build_contract_preserves_source_options(monkeypatch, tmp_path):
    source = tmp_path / 'worker.cbl'
    source.write_text('       linkage section.\n       procedure division using item.\n')
    script = tmp_path / 'build.sh'
    script.write_text('#!/bin/sh\n')
    script.chmod(0o755)
    settings = Settings()
    settings.register_project(str(tmp_path))
    flags = ['-Wall', '-T', 'listing with spaces.prn']
    settings.set_source_flags(str(source), flags)
    settings.set_source_environment(str(source), {'compiler_path': '/opt/custom/cobc',
        'path_mode': 'prepend', 'path': '/opt/custom/bin', 'cob_copy_dir': '/opt/copy'})
    captured = {}
    def run(*args, **kwargs):
        captured.update(kwargs)
        return 0, ''
    monkeypatch.setattr(compilers, 'run_command', run)
    compilers.compile_with_build_script(str(source))
    env = captured['process_environment']
    assert env.value('OCIDE_COMPILE_MODE') == '-m'
    assert env.value('OCIDE_OUTPUT_EXTENSION') == '.so'
    assert env.value('COBC') == '/opt/custom/cobc'
    assert env.value('COB_COPY_DIR') == '/opt/copy'
    assert env.value('PATH').split(os.pathsep)[0] == '/opt/custom/bin'
    options = json.loads(env.value('OCIDE_COMPILER_FLAGS'))
    assert options[options.index('-T') + 1] == str(tmp_path / 'listing with spaces.prn')
    assert settings.source_flags(str(source)) == flags


@pytest.mark.parametrize('mode,extension', [('-x', ''), ('-m', '.so')])
def test_template_uses_mode_flags_and_sql_preprocessing(tmp_path, mode, extension):
    template = Path(__file__).resolve().parents[1] / 'examples/gixsql'
    for name in ('build.sh', 'detect_sql.py'):
        shutil.copy2(template / name, tmp_path / name)
    source = tmp_path / 'arbitrary.cbl'
    source.write_text('           EXEC SQL SELECT 1 END-EXEC.\n')
    gixpp = tmp_path / 'fake-gixpp'
    gixpp.write_text('#!/bin/bash\nwhile (($#)); do\nif [[ "$1" == -o ]]; then shift; touch "$1"; fi\nshift\ndone\n')
    compiler = tmp_path / 'fake-cobc'
    compiler.write_text('#!/bin/bash\nprintf "%s\\0" "$@" > "$ARGUMENT_LOG"\n')
    for executable in (gixpp, compiler):
        executable.chmod(0o755)
    log = tmp_path / 'args'
    env = dict(os.environ, GIXPP=str(gixpp), COBC=str(compiler), ARGUMENT_LOG=str(log),
               OCIDE_COMPILE_MODE=mode, OCIDE_OUTPUT_EXTENSION=extension,
               OCIDE_COMPILER_FLAGS=json.dumps(['-Wall', '-T', 'custom listing.prn']))
    result = subprocess.run(['bash', str(tmp_path / 'build.sh'), str(source)],
                            env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    args = log.read_bytes().decode().split('\0')[:-1]
    assert args[0] == mode
    assert args[args.index('-T') + 1] == 'custom listing.prn'
    assert args[args.index('-o') + 1] == str(tmp_path / 'bin' / ('arbitrary' + extension))
    assert args[-1] == str(tmp_path / 'build/arbitrary.cbsql')
    assert '-lgixsql' in args
    assert args.count('-T') == 1
    assert '-v' in args
    assert 'custom listing.prn' in result.stdout
    assert '$ ' + str(gixpp) in result.stdout
    assert '$ ' + str(compiler) in result.stdout


def test_project_action_and_f8_remain_independent(app, tmp_path, monkeypatch):
    source = tmp_path / 'nested' / 'sample.cbl'
    source.parent.mkdir()
    source.write_text('       identification division.\n       program-id. sample.\n'
                      '       procedure division.\n           goback.\n')
    app.win.show()
    app.app.processEvents()
    from pyqode.qt import QtWidgets
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getExistingDirectory',
                        lambda *args, **kwargs: str(tmp_path))
    second = source.parent / 'second.cob'
    second.write_text(source.read_text().replace('sample.', 'second.'))
    opened = []
    real_open = app.file.open_file
    def record_open(path):
        opened.append(path)
        real_open(path)
    monkeypatch.setattr(app.file, 'open_file', record_open)
    app.win.ui.btOpenProject.click()
    assert opened == [str(source), str(second)]
    assert app.file.project_root == str(tmp_path)
    assert app.win.ui.tvFileSystem.root_path == str(tmp_path)
    calls = []
    monkeypatch.setattr(app.cobol, '_start_compilation', lambda paths=None: calls.append(paths))
    monkeypatch.setattr(app.cobol, 'check_compiler', lambda extension: (True, ''))
    app.cobol.project_compile_action.trigger()
    app.win.ui.actionCompile.trigger()
    assert calls == [[str(source), str(second)], None]
    assert app.win.ui.actionCompile.shortcut().toString() == 'F8'


@pytest.mark.parametrize('header', [
    '       procedure division using argument.\n',
    '       procedure division\n       using argument.\n',
    '000100 PROCEDURE DIVISION\n000200     USING ARGUMENT.\n',
    '       >>source format free\nprocedure division using argument.\n',
])
def test_using_selects_module_without_inline_linkage(tmp_path, header):
    source = tmp_path / 'callable.cbl'
    source.write_text(header)
    assert compilers.get_file_type(str(source)) == FileType.MODULE
    _, args = compilers.GnuCobolCompiler().make_command(
        [source.name], compilers.get_file_type(str(source)), 'bin',
        source_path=str(source))
    assert args[0] == '-m'


def test_batch_and_custom_script_receive_using_mode(monkeypatch, tmp_path):
    from open_cobol_ide.controllers import cobol
    source = tmp_path / 'callable.cbl'
    source.write_text('       procedure division using argument.\n')
    calls = []
    monkeypatch.setattr(compilers.GnuCobolCompiler, 'compile',
                        lambda self, path, mode: (calls.append((path, mode)) or (0, [])))
    thread = CompilationThread()
    thread.file_paths = [str(source)]
    errors = []
    thread.errored.connect(lambda path, error: errors.append(error))
    thread.run()
    assert not errors
    assert calls == [(str(source), FileType.MODULE)]
    Settings().register_project(str(tmp_path))
    def run(pgm, args, working_dir='', process_environment=None):
        assert process_environment.value('OCIDE_COMPILE_MODE') == '-m'
        return 0, ''
    monkeypatch.setattr(compilers, 'run_command', run)
    thread.run()
    assert not errors


@pytest.mark.skipif(shutil.which('cobc') is None, reason='GnuCOBOL required')
def test_real_module_with_linkage_in_copybook(tmp_path):
    source = tmp_path / 'callable.cbl'
    (tmp_path / 'args.cpy').write_text(
        '       linkage section.\n       01 argument pic x.\n')
    source.write_text('       identification division.\n'
                      '       program-id. callable.\n'
                      '       data division.\n'
                      '       copy "args.cpy".\n'
                      '       procedure division using argument.\n'
                      '           goback.\n')
    template = Path(__file__).resolve().parents[1] / 'examples/gixsql'
    for name in ('build.sh', 'detect_sql.py'):
        shutil.copy2(template / name, tmp_path / name)
    Settings().register_project(str(tmp_path))
    status, messages = compilers.compile_with_build_script(str(source))
    assert status == 0, messages
    assert (tmp_path / 'bin/callable.so').is_file()
    assert not (tmp_path / 'bin/callable').exists()


@pytest.mark.parametrize('sql', [False, True])
def test_internal_script_ignores_local_builder_and_owns_sql_detection(tmp_path, sql):
    root = tmp_path / 'project with spaces'
    source_dir = root / 'src'
    source_dir.mkdir(parents=True)
    source = source_dir / 'callable.cbl'
    source.write_text('       identification division.\n'
                      '       program-id. callable.\n'
                      '       data division.\n'
                      '       linkage section.\n'
                      '       01 argument pic x.\n'
                      '       procedure division using argument.\n' +
                      ('           EXEC SQL SELECT 1 END-EXEC.\n' if sql else '') +
                      '           goback.\n')
    local = root / 'build.sh'
    local.write_text('#!/bin/sh\ntouch LOCAL_SCRIPT_WAS_RUN\nexit 99\n')
    local.chmod(0o755)
    gixpp = root / 'fake-gixpp'
    gixpp.write_text('#!/bin/bash\nwhile (($#)); do\n'
                      'case "$1" in\n-i) shift; input=$1;;\n-o) shift; output=$1;;\nesac\nshift\ndone\n'
                      'sed "/EXEC SQL/d" "$input" > "$output"\n')
    gixpp.chmod(0o755)
    script = Path(compilers.__file__).parent / 'build_tools/build.sh'
    env = dict(os.environ, OCIDE_PROJECT_DIR=str(root), OCIDE_COMPILE_MODE='-m',
               OCIDE_COMPILER_FLAGS='[]', GIXPP=str(gixpp))
    # The fake preprocessor emits plain COBOL, so no SQL runtime is needed here.
    compiler = root / 'compiler'
    compiler.write_text('#!/bin/bash\nargs=()\nfor arg in "$@"; do\n'
                        '[[ "$arg" == -lgixsql ]] || args+=("$arg")\ndone\n'
                        'exec cobc "${args[@]}"\n')
    compiler.chmod(0o755)
    env['COBC'] = str(compiler)
    result = subprocess.run(['bash', str(script), str(source)], cwd=root,
                            env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert not (root / 'LOCAL_SCRIPT_WAS_RUN').exists()
    assert not (root / 'detect_sql.py').exists()
    assert (root / 'bin/callable.so').exists()
    listing = root / 'build/callable.lst'
    text = listing.read_text()
    import re
    assert re.search(r'^NAME\s+DEFINED\s+REFERENCES\s*$', text, re.M)
    assert re.search(r'^LABEL\s+DEFINED\s+REFERENCES\s*$', text, re.M)
    assert re.search(r'^SIZE\s+TYPE\s+LVL\s+NAME\s+PICTURE\s*$', text, re.M)
    assert '--Xref' in result.stdout
    assert 'parsing:' in result.stderr + result.stdout
    assert ('SQL detection: sql' if sql else 'SQL detection: plain') in result.stdout
