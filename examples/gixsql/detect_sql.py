#!/usr/bin/env python3
"""Classify COBOL including COPY files; never execute the program."""
import re
import sys
from pathlib import Path

TOKEN = re.compile(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|[A-Za-z0-9_/-]+|[.]")
COMMENT = re.compile(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|\*>.*")

def has_sql(source, directories, visited=None, free=False):
    source = Path(source).resolve()
    visited = set() if visited is None else visited
    identity = (source, free)
    if identity in visited:
        return False
    visited.add(identity)
    lines = []
    for line in source.read_text(errors='replace').splitlines():
        directive = re.search(r'>>SOURCE\s+(?:FORMAT\s+)?(?:IS\s+)?(FREE|FIXED)', line, re.I)
        if directive:
            free = directive.group(1).upper() == 'FREE'
            continue
        if not free:
            if len(line) > 6 and line[6] in '*/':
                continue
            line = line[7:72]
        line = COMMENT.sub(lambda m: '' if m.group().startswith('*>') else m.group(), line)
        lines.append((line, free))
    tokens = []
    for line, mode in lines:
        tokens.extend((match.group(), mode) for match in TOKEN.finditer(line))
    words = [token.upper() for token, mode in tokens]
    if any(words[i:i+2] == ['EXEC', 'SQL'] for i in range(len(words)-1)):
        return True
    for i, (token, mode) in enumerate(tokens[:-1]):
        if token.upper() != 'COPY':
            continue
        name = tokens[i+1][0].strip("'\"")
        found = None
        for directory in [source.parent] + [Path(d) for d in directories]:
            for suffix in ['', '.cpy', '.CPY', '.cob', '.cbl']:
                candidate = directory / (name + suffix)
                if candidate.is_file():
                    found = candidate
                    break
            if found:
                break
        if found is None:
            raise FileNotFoundError('Cannot inspect COPY %s in %s' % (name, source))
        if has_sql(found, directories, visited, mode):
            return True
    return False

if __name__ == '__main__':
    try:
        print('sql' if has_sql(sys.argv[1], sys.argv[2:]) else 'plain')
    except (OSError, IndexError) as error:
        sys.exit(str(error))
