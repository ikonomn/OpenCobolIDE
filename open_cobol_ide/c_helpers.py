"""Associate literal COBOL calls with local C definitions; never execute sources."""
import os
from pathlib import Path
import re
from .build_tools.detect_sql import TOKEN, COMMENT

SKIP = {'bin', 'build', 'debug_data', 'venv', '__pycache__', 'dist'}
DEBUG_FLAGS = ('-g', '-fsource-location', '-ftraceall', '-O0', '-save-temps')


def output_name(source, options=None, extension=''):
    name = (options or {}).get('output_name', '') or Path(source).stem
    if (not isinstance(name, str) or name in ('.', '..') or name.startswith('-')
            or any(ch in name for ch in '/\\\\:\0\r\n') or not name.strip()):
        raise ValueError('Executable name must be a filename, without a directory or drive.')
    if extension and name.lower().endswith(extension.lower()):
        return name
    return name + extension


def calls(source, free):
    tokens = []
    for line in Path(source).read_text(errors='replace').splitlines():
        directive = re.search(r'>>\s*SOURCE\s+(?:FORMAT\s+)?(?:IS\s+)?(FREE|FIXED)', line, re.I)
        if directive:
            free = directive.group(1).upper() == 'FREE'
            continue
        if not free:
            if len(line) > 6 and line[6] in '*/':
                continue
            line = line[7:72]
        line = COMMENT.sub(lambda m: '' if m.group().startswith('*>') else m.group(), line)
        tokens.extend(m.group() for m in TOKEN.finditer(line))
    result = set()
    for i, token in enumerate(tokens):
        if token.upper() != 'CALL':
            continue
        j = i + 1
        if j < len(tokens) and tokens[j].upper() == 'STATIC':
            j += 1
        if j < len(tokens) and tokens[j][:1] in ('"', "'"):
            result.add(tokens[j][1:-1])
    return result


def c_text(path):
    text = Path(path).read_text(errors='replace')
    # Preserve strings while removing comments so commented-out includes don't count.
    return re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                  lambda m: ' ' if m.group().startswith(('/',)) else m.group(), text, flags=re.S)


def plan(source, root, options=None, free=True, windows=None, include_directories=()):
    options = options or {}
    root = Path(root).resolve()
    windows = os.name == 'nt' if windows is None else windows
    manual = options.get('c_sources')
    selected = set()
    if manual is not None:
        for value in manual:
            path = Path(value)
            path = path if path.is_absolute() else root/path
            if not path.is_file() or path.suffix.lower() != '.c':
                raise ValueError('C helper source is missing or is not a .c file: ' + str(path))
            selected.add(path.resolve())
    else:
        candidates = []
        for directory, folders, files in os.walk(root, followlinks=False):
            folders[:] = [f for f in folders if f not in SKIP and not f.startswith('.')
                          and not (Path(directory)/f).is_symlink()]
            candidates.extend(Path(directory)/f for f in files if f.lower().endswith('.c')
                              and not (Path(directory)/f).is_symlink())
        symbols = calls(source, free)
        definitions = {symbol: [] for symbol in symbols}
        for path in candidates:
            text = c_text(path)
            text = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', ' ', text)
            for symbol in symbols:
                if re.search(r'\b' + re.escape(symbol) + r'\s*\([^;{}]*\)\s*\{', text):
                    definitions[symbol].append(path.resolve())
        for symbol, matches in definitions.items():
            if len(matches) > 1:
                raise ValueError('Several C helpers define %s; select C helper sources in File compiler settings: %s' %
                                 (symbol, ', '.join(str(p) for p in matches)))
            selected.update(matches)
    dependencies = set(selected)
    libraries = set()
    visited = set()
    def headers(path):
        if path in visited:
            return
        visited.add(path)
        text = c_text(path)
        # These are explicit supported platform mappings, not a general linker inference.
        if not windows and re.search(r'#\s*include\s*[<"]X11/', text):
            libraries.add('X11')
        if windows and re.search(r'\bMessageBox[AW]?\s*\(', text):
            libraries.add('user32')
        for name in re.findall(r'#\s*include\s*"([^"]+)"', text):
            for directory in [path.parent, root] + [Path(d) for d in include_directories]:
                candidate = (directory/name).resolve()
                if candidate.is_file():
                    dependencies.add(candidate)
                    headers(candidate)
                    break
    for path in sorted(selected):
        headers(path)
    return {'sources': [str(p) for p in sorted(selected)],
            'dependencies': [str(p) for p in sorted(dependencies)],
            'libraries': sorted(libraries)}
