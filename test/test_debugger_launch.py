"""External debugger launches are executable-only and shell-free."""
import os
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest
from pyqode.qt import QtWidgets

from open_cobol_ide import project_config as config
from open_cobol_ide.enums import FileType
from open_cobol_ide.settings import Settings


@pytest.fixture
def debug_project(tmp_path, app):
    app.file.close_project()
    saved = Settings().export_to_dict()
    root = Path(config.create_project(tmp_path, 'Debug Project'))
    source = root / 'src/main.cbl'
    source.write_text('       identification division.\n       program-id. main.\n'
                      '       procedure division.\n           stop run.\n')
    frontend = tmp_path / 'Installed Debugger' / 'cobgdb-python-gui'
    frontend.parent.mkdir()
    frontend.write_text('#!/bin/sh\nexit 0\n')
    frontend.chmod(0o755)
    Settings().debugger_command = str(frontend)
    app.file.open_project(str(root))
    app.file.open_file(str(source))
    assert (root / 'debug_data').is_dir()
    data = config.load(root)
    data['debug'] = {'enabled': True}
    config.save(root, data)
    artifacts = root / 'debug_data/src/main'
    artifacts.mkdir(parents=True)
    (artifacts / 'main.c').touch()
    (artifacts / 'main.h').touch()
    program = Path(app.cobol._debug_executable_path())
    program.write_text('placeholder executable; never run by these tests')
    yield app, root, source, program, frontend
    app.file.close_project()
    Settings().clear()
    Settings().import_from_dict(saved)


def test_launch_uses_independent_frontend_executable_source_and_runtime(debug_project, monkeypatch):
    from open_cobol_ide.controllers import cobol
    app, root, source, program, frontend = debug_project
    data = config.load(root)
    data['runtime'] = {'accepted': True, 'working_directory': '.', 'data_directories': ['data']}
    config.save(root, data)
    calls = []
    monkeypatch.setattr(cobol.subprocess, 'Popen', lambda *args, **kwargs: calls.append((args, kwargs)))
    app.cobol.enable_run(True)
    assert app.cobol.debug_action.isEnabled()
    app.cobol.debug_action.trigger()
    command = calls[0][0][0]
    assert command[:2] == [str(frontend), str(program)]
    assert '--frontend-dir' not in command
    assert command[command.index('--source') + 1] == str(source)
    assert calls[0][1]['cwd'] == str(root)
    assert calls[0][1]['env']['COB_FILE_PATH'] == str(root / 'data')
    assert calls[0][1]['start_new_session']
    assert not calls[0][1].get('shell')


def test_module_and_copybook_cannot_launch_debugger(debug_project, monkeypatch):
    from open_cobol_ide.controllers import cobol
    app, root, source, program, frontend = debug_project
    calls = []
    monkeypatch.setattr(cobol.subprocess, 'Popen', lambda *args, **kwargs: calls.append(args))
    app.edit.current_editor.file_type = FileType.MODULE
    app.cobol.enable_run(True)
    assert not app.cobol.debug_action.isEnabled()
    app.cobol.debug_executable()
    assert not calls
    copybook = root / 'copybooks/test.cpy'
    copybook.write_text('       01 field pic x.\n')
    app.file.open_file(str(copybook))
    app.cobol.enable_run(True)
    assert not app.cobol.debug_action.isEnabled()
    app.cobol.debug_executable()
    assert not calls


def test_missing_executable_or_installed_launcher_reported_without_launch(debug_project, monkeypatch):
    from open_cobol_ide.controllers import cobol
    app, root, source, program, frontend = debug_project
    warnings, calls = [], []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', lambda *args: warnings.append(args))
    monkeypatch.setattr(cobol.subprocess, 'Popen', lambda *args, **kwargs: calls.append(args))
    program.unlink()
    app.cobol.enable_run(True)
    assert not app.cobol.debug_action.isEnabled()
    app.cobol.debug_executable()
    assert warnings
    program.touch()
    Settings().debugger_command = str(root / 'missing-launcher')
    app.cobol.debug_executable()
    assert len(warnings) == 2
    assert not calls




def test_open_debugger_without_arguments(debug_project, monkeypatch):
    from open_cobol_ide.controllers import cobol
    app, root, source, program, launcher = debug_project
    calls = []
    monkeypatch.setattr(cobol.subprocess, 'Popen', lambda *args, **kwargs: calls.append((args, kwargs)))
    app.cobol.open_debugger()
    assert calls[0][0][0] == [str(launcher)]
    assert calls[0][1]['start_new_session']


def test_missing_debug_headers_prevent_project_launch(debug_project, monkeypatch):
    from open_cobol_ide.controllers import cobol
    app, root, source, program, launcher = debug_project
    (root / 'debug_data/src/main/main.h').unlink()
    warnings = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', lambda *args: warnings.append(args))
    monkeypatch.setattr(cobol.subprocess, 'Popen', lambda *args, **kwargs: pytest.fail('Unexpected launch'))
    app.cobol.debug_executable()
    assert 'Enable Debug compilation' in warnings[0][2]
