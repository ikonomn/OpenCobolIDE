"""Crash-oriented execution tracing for difficult native failures.

Tracing is deliberately opt-in.  Set ``OCIDE_TRACE_LOG`` to a file path, or
to ``1`` to use the default cache location.  Each event is flushed and synced
to disk so the last completed operation survives an abrupt native abort.
"""
import atexit
import datetime
import faulthandler
import json
import os
import platform
import sys
import threading
import time


_lock = threading.RLock()
_stream = None
_path = None
_sequence = 0


def _default_path():
    cache_root = os.environ.get(
        'XDG_CACHE_HOME', os.path.expanduser(os.path.join('~', '.cache')))
    return os.path.join(
        cache_root, 'OpenCobolIDE',
        'OpenCobolIDE-trace-%d.jsonl' % os.getpid())


def configure(value=None):
    """Enable tracing and return the trace path, or ``None`` when disabled."""
    global _stream, _path
    if value is None:
        value = os.environ.get('OCIDE_TRACE_LOG', '')
    if not value or str(value).lower() in ('0', 'false', 'no', 'off'):
        return None
    with _lock:
        if _stream is not None:
            return _path
        if str(value).lower() in ('1', 'true', 'yes', 'on'):
            value = _default_path()
        _path = os.path.abspath(os.path.expanduser(str(value)))
        directory = os.path.dirname(_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        _stream = open(_path, 'a', encoding='utf-8', buffering=1)
        try:
            faulthandler.enable(file=_stream, all_threads=True)
        except (RuntimeError, OSError):
            # Normal trace events remain useful even when faulthandler is not
            # available on a particular Python build or output device.
            pass
        event(
            'trace.enabled', path=_path, argv=sys.argv,
            python=sys.version.replace('\n', ' '), platform=platform.platform(),
            executable=sys.executable, cwd=os.getcwd(),
            session_type=os.environ.get('XDG_SESSION_TYPE'),
            qt_api=os.environ.get('QT_API'),
            qt_platform=os.environ.get('QT_QPA_PLATFORM'),
            display=bool(os.environ.get('DISPLAY')),
            wayland_display=bool(os.environ.get('WAYLAND_DISPLAY')))
        return _path


def enabled():
    return _stream is not None


def path():
    return _path


def event(name, **fields):
    """Write one durable trace event without letting tracing break the IDE."""
    global _sequence
    stream = _stream
    if stream is None:
        return
    try:
        with _lock:
            _sequence += 1
            record = {
                'time': datetime.datetime.now(
                    datetime.timezone.utc).astimezone().isoformat(),
                'monotonic': round(time.monotonic(), 6),
                'sequence': _sequence,
                'pid': os.getpid(),
                'thread': threading.current_thread().name,
                'thread_id': threading.get_ident(),
                'event': name,
            }
            record.update(fields)
            stream.write(json.dumps(
                record, ensure_ascii=False, default=repr,
                sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        # Diagnostics must never alter normal program behaviour.
        pass


def _at_exit():
    event('python.atexit')


atexit.register(_at_exit)
