"""
This is the application entry. This is where we create and run the
Application.
"""
import os
import sys


def override_sys_path():
    """
    Add the bundled, pure-Python dependencies as a fallback.

    This directory also contains compatibility modules which predate modern
    Python.  Appending it is important: prepending it makes the old ``enum``
    backport shadow Python's standard library and prevents the application
    from starting on Python 3.6 and newer.
    """
    import open_cobol_ide
    extlibs_pth = os.path.join(
        os.path.dirname(open_cobol_ide.__file__),
        'extlibs')
    if extlibs_pth not in sys.path:
        sys.path.append(extlibs_pth)
    os.environ['OCIDE_EXTLIBS_PATH'] = extlibs_pth
    import pyqode.core


def main():
    """
    Application entry point.
    """
    from open_cobol_ide import trace_log
    trace_path = trace_log.configure()
    trace_log.event('main.enter', trace_path=trace_path)
    dev_mode = os.environ.get('OCIDE_DEV_MODE')
    if not hasattr(sys, 'frozen') and dev_mode is None:
        trace_log.event('main.override_sys_path.start')
        override_sys_path()
        trace_log.event('main.override_sys_path.finished')
    from pyqode.qt import QtGui
    from open_cobol_ide import system
    from open_cobol_ide.app import Application
    from open_cobol_ide.settings import Settings
    trace_log.event('application.create.start')
    app = Application()
    trace_log.event('application.create.finished')
    if system.linux:
        QtGui.QIcon.setThemeName(Settings().icon_theme)
    trace_log.event('event_loop.start')
    ret_code = app.run()
    trace_log.event('event_loop.returned', return_code=ret_code)
    trace_log.event('application.close.start')
    app.close()
    trace_log.event('application.close.finished')
    trace_log.event('main.return', return_code=ret_code)
    return ret_code
