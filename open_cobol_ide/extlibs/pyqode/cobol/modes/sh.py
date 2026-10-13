"""
This module contains a native python syntax highlighter.
"""
import logging
import re
from pyqode.qt import QtGui
from pyqode.core.api import SyntaxHighlighter as BaseSH
from pyqode.cobol.api import keywords as kw


def any(name, alternates):
    """Return a named group pattern matching list of alternates."""
    return "(?P<%s>" % name + "|".join(alternates) + ")"


def make_cobol_patterns(fixed_format=True):
    if fixed_format:
        comment = any('comment', [r"\*>[^\n]*|(^.{6})\*[^\n]*"])
    else:
        comment = any('comment', [r"\*>[^\n]*"])
    keywords_reserved = any(
        'keyword_reserved',
        [r'(^|(?<=[^0-9a-zA-Z_-]))(%s)\s*($|(?=[^0-9a-zA-Z_-]))' %
         '|'.join(kw.RESERVED + kw.SQL_COBOL_KEYWORDS + kw.MNEMONICS)])
    constants = any(
        'constant',
        [r'(^|(?<=[^0-9a-zA-Z_-]))'
         r'(^|(?<=[^0-9a-zA-Z_-]))(equal|equals|ne|lt|le|gt|ge|'
         r'greater|less|than|not|and|or)\s*($|(?=[^0-9a-zA-Z_-]))'])
    types = any('type', [
        r'(PIC\s+.+?(?=(\s|\.\s?))|PICTURE\s+.+?(?=(\s|\.\s?))|'
        r'(COMPUTATIONAL)(-[1-5X])?|(COMP)(-[1-5X])?|'
        r'BINARY-C-LONG|'
        r'BINARY-CHAR|BINARY-DOUBLE|BINARY-LONG|BINARY-SHORT|'
        r'BINARY)\s*($|(?=[^0-9a-zA-Z_-]))'])
    # operator = any('operator', ['(\*\*|\*|\+|-|/|<=|>=|<|>|==|/=|=)'])
    punctuation = any('punctuation', ['([(),;:&%.])'])
    name_builtin = any(
        'builtin', [
            r'(^|(?<=[^0-9a-zA-Z_-]))(true|false)\s*($|(?=[^0-9a-zA-Z_-]))'])
    string = any('string', [r'"[^"\n]*("|\n)', r"'[^'\n]*('|\n)"])
    numbers = any('number', [
        r'\d+(\s*|\.$|$)',
        r'[+-]?\d*\.\d+([eE][-+]?\d+)?',
        r'[+-]?\d+\.\d*([eE][-+]?\d+)?'
    ])
    variable = any(
        'instance',
        [r'[a-zA-Z0-9]([_a-zA-Z0-9\-]*[a-zA-Z0-9]+)?'])

    return "|".join(
        [
            keywords_reserved,
            constants,
            types,
            comment,
            punctuation,
            name_builtin,
            string,
            numbers,
            variable,
            any("SYNC", [r"\n"])
        ]
    )


def _logger():
    return logging.getLogger(__name__)


class CobolSyntaxHighlighter(BaseSH):
    """
    Native cobol highlighter (fixed format).
    """
    PROG_FIXED_FMT = re.compile(make_cobol_patterns(), re.S)
    PROG_FREE_FMT = re.compile(make_cobol_patterns(fixed_format=False), re.S)

    def highlight_cobol(self, text):
        text = text.upper()
        self.setFormat(0, len(text), self.formats["instance"])
        if self.editor.free_format:
            match = self.PROG_FREE_FMT.search(text)
        else:
            match = self.PROG_FIXED_FMT.search(text)
        while match:
            for key, value in list(match.groupdict().items()):
                if value:
                    start, end = match.span(key)
                    try:
                        fmt = self.formats[key]
                        fmt.setFontWeight(QtGui.QFont.Normal)
                    except KeyError:
                        _logger().debug('unsupported format: %s' % key)
                    else:
                        self.setFormat(start, end - start, fmt)
            match = self.PROG_FIXED_FMT.search(text, match.end())

    def highlight_disabled_columns(self, text):
        fmt = QtGui.QTextCharFormat()
        fmt.setForeground(QtGui.QBrush(self.editor.whitespaces_foreground))
        try:
            self.setFormat(0, 6 if text[6] in ['*', '-'] else 7, fmt)
        except IndexError:
            self.setFormat(0, len(text), fmt)

    def highlight_block(self, text, block):
        self.highlight_cobol(text)
        if not self.editor.free_format:
            self.highlight_disabled_columns(text)
