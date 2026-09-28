from pathlib import Path

from pyqode.qt import QtCore, QtGui, QtWidgets
from open_cobol_ide.settings import Settings
from open_cobol_ide.view.dialogs.about import DlgAbout
from .base import Controller

import qcrash.api as qcrash


class HelpController(Controller):
    """
    Controls the ? menu: show help contents and about dialog.
    """
    #: Online fallback used only when the packaged and source manuals are
    #: unavailable.
    help_url = ('https://github.com/ikonomn/OpenCobolIDE/tree/'
                'modern-python/doc/source')

    @staticmethod
    def local_help_candidates():
        """Return the source-tree and installed local manual locations."""
        source_root = Path(__file__).resolve().parents[2]
        return (
            source_root / 'doc' / 'OpenCobolIDE-modern9.html',
            Path('/usr/share/doc/opencobolide/manual.html'),
        )

    @classmethod
    def help_location(cls):
        """Return a local-file URL when possible, otherwise the web URL."""
        for path in cls.local_help_candidates():
            if path.is_file():
                return QtCore.QUrl.fromLocalFile(str(path))
        return QtCore.QUrl(cls.help_url)

    def __init__(self, app):
        super().__init__(app)
        self.ui.actionHelp.triggered.connect(self.show_help_contents)
        self.ui.actionAbout.triggered.connect(self.show_about_dlg)
        self.ui.btAbout.clicked.connect(self.show_about_dlg)
        self.ui.actionReport_a_bug.triggered.connect(self.report_bug)
        self.ui.actionRestore_factory_defaults.triggered.connect(
            self.restore_factory_defaults)

    def show_help_contents(self):
        """
        Open the packaged manual in the default browser.
        """
        QtGui.QDesktopServices.openUrl(self.help_location())

    def show_about_dlg(self):
        """
        Shows the about dialog.
        """
        dlg = DlgAbout(self.main_window)
        dlg.exec_()

    def report_bug(self):
        qcrash.show_report_dialog(
            window_icon=self.main_window.windowIcon(),
            parent=self.main_window, include_log=False, include_sys_info=False)

    def restore_factory_defaults(self):
        answer = QtWidgets.QMessageBox.question(
            self.main_window, 'Restory factory defaults?',
            'Are you sure you want to restore factory defaults?\n\n'
            'Clicking yes will remove all your preferences and restart the '
            "IDE with clean settings. Use this only if you're experiencing a "
            "problem!")
        if answer == QtWidgets.QMessageBox.Yes:
            Settings().clear()
            self.app.restart()
