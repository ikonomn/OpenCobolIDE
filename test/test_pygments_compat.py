"""Compatibility checks for the bundled Pygments regular expressions."""
import warnings

from pygments.lexers.julia import JuliaLexer
from pygments.lexers.rdf import SparqlLexer
from pygments.lexers.templates import MasonLexer, MyghtyLexer
from pygments.util import guess_decode, tag_re


def _lex_without_regex_warnings(lexer, source):
    with warnings.catch_warnings():
        warnings.simplefilter('error', DeprecationWarning)
        return list(lexer.get_tokens(source))


def test_html_detection_regex_uses_leading_flags():
    assert tag_re.search('<html>\n<body>text</body>\n</html>') is not None
    assert guess_decode(b'<html>\n<body>text</body>\n</html>')[1]


def test_bundled_lexer_regexes_use_compatible_inline_flags():
    samples = [
        (JuliaLexer(), '`first\nsecond`'),
        (SparqlLexer(), 'SELECT (STR(?value) AS ?text) WHERE {}'),
        (MyghtyLexer(), '<%def name>first\nsecond</%name>'),
        (MasonLexer(), '<%doc>first\nsecond</%doc>'),
    ]

    for lexer, source in samples:
        assert _lex_without_regex_warnings(lexer, source)
