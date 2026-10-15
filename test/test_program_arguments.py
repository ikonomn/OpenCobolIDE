"""Program argument entry and forwarding regressions."""
import shlex
from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest
from open_cobol_ide.controllers import cobol
from open_cobol_ide.enums import FileType


@pytest.mark.parametrize('text, expected', [
    ('18090212 18650415', ['18090212', '18650415']),
    ('123 "customer name" ""', ['123', 'customer name', '']),
    ('', []),
])
def test_run_arguments(monkeypatch, text, expected):
    saved = {}
    settings = NS(value=lambda key, default: saved.get(key, default),
                  setValue=lambda key, value: saved.__setitem__(key, value))
    monkeypatch.setattr(cobol.QtCore, 'QSettings', lambda *a: settings)
    dialog = Mock(return_value=(text, True))
    monkeypatch.setattr(cobol.QtWidgets.QInputDialog, 'getText', dialog)
    obj = NS(app=NS(edit=NS(current_editor=NS(file=NS(path='/tmp/bio2.cbl')))),
             main_window=None, compile=Mock(),
             ui=NS(consoleOutput=NS(clear=Mock())))
    cobol.CobolController.run(obj)
    assert obj._program_arguments == expected
    obj.compile.assert_called_once_with()
    cobol.CobolController.run(obj)
    assert dialog.call_args.args[-1] == text


def test_cancel_does_not_compile(monkeypatch):
    monkeypatch.setattr(cobol.QtCore, 'QSettings',
                        lambda *a: NS(value=lambda *a: 'old'))
    monkeypatch.setattr(cobol.QtWidgets.QInputDialog, 'getText',
                        lambda *a: ('new', False))
    obj = NS(app=NS(edit=NS(current_editor=NS(file=NS(path='/tmp/bio2.cbl')))),
             main_window=None, compile=Mock())
    cobol.CobolController.run(obj)
    obj.compile.assert_not_called()


def test_invalid_quotes_prompt_again(monkeypatch):
    settings = NS(value=lambda *a: '', setValue=Mock())
    monkeypatch.setattr(cobol.QtCore, 'QSettings', lambda *a: settings)
    monkeypatch.setattr(cobol.QtWidgets.QInputDialog, 'getText',
                        Mock(side_effect=[('"bad', True), ('good', True)]))
    warning = Mock()
    monkeypatch.setattr(cobol.QtWidgets.QMessageBox, 'warning', warning)
    obj = NS(app=NS(edit=NS(current_editor=NS(file=NS(path='/tmp/bio2.cbl')))),
             main_window=None, compile=Mock(),
             ui=NS(consoleOutput=NS(clear=Mock())))
    cobol.CobolController.run(obj)
    warning.assert_called_once()
    assert obj._program_arguments == ['good']
    obj.compile.assert_called_once_with()


@pytest.mark.parametrize('file_type', [FileType.EXECUTABLE, FileType.MODULE])
def test_external_arguments_are_quoted(monkeypatch, file_type):
    monkeypatch.setattr(cobol.system, 'windows', False)
    monkeypatch.setattr(cobol.system, 'darwin', False)
    monkeypatch.setattr(cobol.system, 'which', lambda name: '/usr/bin/' + name)
    monkeypatch.setattr(cobol, 'Settings', lambda: NS(
        run_environemnt={'PATH': '/usr/bin'},
        external_terminal_command='x-terminal-emulator -e'))
    launch = Mock()
    monkeypatch.setattr(cobol.subprocess, 'Popen', launch)
    arguments = ['18090212', 'hello world', '', '$(touch unwanted)', 'a;b']
    obj = NS(_program_arguments=arguments,
             ui=NS(consoleOutput=NS(appendPlainText=Mock())))
    cobol.CobolController._run_in_external_terminal(
        obj, '/tmp/my program', '/tmp', file_type)
    cmd = launch.call_args.args[0]
    expected = ['/usr/bin/pyqode-console']
    if file_type == FileType.MODULE:
        expected += ['/usr/bin/cobcrun', 'my program']
    else:
        expected += ['/tmp/my program']
    assert cmd[:2] == ['x-terminal-emulator', '-e']
    assert shlex.split(cmd[2]) == expected + arguments
    assert 'shell' not in launch.call_args.kwargs
