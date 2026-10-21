"""Utilities for detecting source format directives in COBOL code."""
import re


_SOURCE_FORMAT_RE = re.compile(
    r'^\s*>>\s*SOURCE(?:\s+FORMAT(?:\s+IS)?)?\s+(FREE|FIXED)\b',
    re.IGNORECASE | re.MULTILINE)


def detect_source_format(source):
    """Return ``True`` for FREE, ``False`` for FIXED, or ``None``.

    GnuCOBOL permits a source-format directive after the fixed-format
    sequence area as well as at the beginning of a free-format line.  The
    first directive determines how the editor initially presents the file.
    The compiler still receives the source unchanged and handles any later
    format switches itself.
    """
    match = _SOURCE_FORMAT_RE.search(source or '')
    if match is None:
        return None
    return match.group(1).upper() == 'FREE'


def source_has_format_directive(source):
    """Return whether *source* contains a supported format directive."""
    return detect_source_format(source) is not None


def read_source_format(path):
    """Detect the source format in *path*, returning ``None`` on read error."""
    if not path:
        return None
    try:
        with open(path, 'r', errors='replace') as source_file:
            return detect_source_format(source_file.read())
    except (OSError, TypeError):
        return None
