import sys
from open_cobol_ide.settings import Settings


def test_parse_args(app):
    argv = sys.argv
    path = 'test/testfiles/HelloWorld.cbl'
    sys.argv = [argv[0], path, '--verbose']
    args = app.parse_args()
    assert args.verbose is True
    assert len(args.files) == 1
    assert args.files[0] == path


def test_update_style(app):
    Settings().dark_style = True
    app.update_app_style()
    assert app.app.styleSheet() != ''
    Settings().dark_style = False
    app.update_app_style()
    assert app.app.styleSheet() == ''


def test_window_close_stops_console_only_when_accepted():
    from types import SimpleNamespace
    from unittest.mock import Mock
    from open_cobol_ide.view.main_window import MainWindow

    console = SimpleNamespace(stop_process=Mock(),
                              backend=SimpleNamespace(stop=Mock()))
    window = SimpleNamespace(ui=SimpleNamespace(
        tabWidgetEditors=SimpleNamespace(closeEvent=Mock()),
        consoleOutput=console))
    event = SimpleNamespace(isAccepted=lambda: False)
    MainWindow.closeEvent(window, event)
    console.stop_process.assert_not_called()
    console.backend.stop.assert_not_called()
    event.isAccepted = lambda: True
    MainWindow.closeEvent(window, event)
    console.stop_process.assert_called_once_with()
    console.backend.stop.assert_called_once_with()
