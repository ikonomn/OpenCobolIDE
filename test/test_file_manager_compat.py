"""Compatibility tests for the bundled PyQode file manager."""
import builtins

from pyqode.core.api import CodeEdit  # noqa: F401 - initialize PyQode API
from pyqode.core.managers import file as file_manager_module


class _Cache:
    def set_file_encoding(self, path, encoding):
        pass


class _Editor:
    def __init__(self):
        self.file = None
        self.modes = []
        self.tab_length = 4
        self.content = None
        self.title = None
        self.read_only = None

    def setPlainText(self, content, mimetype, encoding):
        self.content = content

    def setDocumentTitle(self, title):
        self.title = title

    def setReadOnly(self, read_only):
        self.read_only = read_only


def test_file_manager_opens_files_without_removed_universal_mode(
        tmp_path, monkeypatch):
    path = tmp_path / 'line-endings.cbl'
    path.write_bytes(b'first\r\nsecond\r\n')
    modes = []

    def checked_open(filename, mode='r', **kwargs):
        modes.append(mode)
        assert 'U' not in mode
        return builtins.open(filename, mode, **kwargs)

    monkeypatch.setattr(file_manager_module, 'open', checked_open)
    monkeypatch.setattr(file_manager_module, 'Cache', _Cache)

    editor = _Editor()
    manager = file_manager_module.FileManager(editor)
    editor.file = manager
    manager.restore_cursor = False

    assert manager.open(str(path), encoding='utf-8',
                        use_cached_encoding=False)
    assert modes == ['r']
    assert editor.content == 'first\nsecond\n'
    assert editor.title == path.name
