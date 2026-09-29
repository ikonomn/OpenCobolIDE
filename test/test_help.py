from pathlib import Path
from html.parser import HTMLParser

from open_cobol_ide.controllers.help import HelpController


def test_local_help_manual_is_used_from_source_tree():
    location = HelpController.help_location()

    assert location.isLocalFile()
    path = Path(location.toLocalFile())
    assert path.name == 'OpenCobolIDE-modern9.html'
    assert path.is_file()


def test_local_help_manual_contains_every_documentation_page():
    path = Path(HelpController.help_location().toLocalFile())
    manual = path.read_text(encoding='utf-8')

    for source in Path('doc/source').glob('*.rst'):
        assert '>%s<' % source.name in manual


def test_local_help_internal_links_resolve():
    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.anchors = set()
            self.targets = set()

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if 'id' in attrs:
                self.anchors.add(attrs['id'])
            if tag == 'a' and attrs.get('href', '').startswith('#'):
                self.targets.add(attrs['href'][1:])

    parser = Links()
    path = Path(HelpController.help_location().toLocalFile())
    parser.feed(path.read_text(encoding='utf-8'))

    assert parser.targets <= parser.anchors
