"""Read-only runtime folder discovery; apply only settings accepted by the user."""
import os
from pathlib import Path
import re
from . import project_config as config

EXCLUDED = {'bin', 'build', 'debug_data', '__pycache__', 'venv'}
NAMES = {'data', 'files', 'input', 'output', 'datasets', 'records', 'reports', 'dat', 'datafiles'}


def scan(root, free=False):
    root = Path(root).resolve()
    files, folders = [], []
    for directory, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d not in EXCLUDED
                         and not Path(directory, d).is_symlink())
        folder = Path(directory)
        if set(re.split(r'[-_ ]+', folder.name.lower())) & NAMES:
            folders.append(folder.relative_to(root).as_posix())
        files.extend(Path(directory, n) for n in sorted(names)
                     if not n.startswith('.') and not Path(directory, n).is_symlink())
    rows = []
    # Copybooks are inspected too, including FILE-CONTROL declarations in COPY.
    sources = [p for p in files if p.suffix.lower() in ('.cbl', '.cob', '.pco', '.cpy')]
    settings = config.load(root) if config.config_path(root).is_file() else {}
    for source in sources:
        options = dict(settings.get('defaults', {}))
        options.update(settings.get('sources', {}).get(source.relative_to(root).as_posix(), {}))
        selected = options.get('source_format', 'inherit')
        mode = free if selected == 'inherit' else selected == 'free'
        flags = options.get('flags') or []
        if '-free' in flags: mode = True
        if '-fixed' in flags: mode = False
        lines = []
        for line in source.read_text(errors='replace').splitlines():
            directive = re.search(r'>>\s*SOURCE\s+(?:FORMAT\s+)?(?:IS\s+)?(FREE|FIXED)', line, re.I)
            if directive:
                mode = directive[1].upper() == 'FREE'
                continue
            if not mode:
                if len(line) > 6 and line[6] in '*/':
                    continue
                line = line[7:72]
            from .build_tools.detect_sql import COMMENT
            lines.append(COMMENT.sub(lambda m: '' if m[0].startswith('*>') else m[0], line))
        text = '\n'.join(lines)
        # Do not interpret SELECT/ASSIGN text inside literals as declarations.
        tokens = re.findall(r'''"(?:""|[^"])*"|'(?:''|[^'])*'|[\w-]+|[.]''', text)
        for i, token in enumerate(tokens):
            if token.upper() != 'SELECT':
                continue
            j = i + 1
            if j < len(tokens) and tokens[j].upper() == 'OPTIONAL': j += 1
            if j >= len(tokens): continue
            logical = tokens[j]
            end = next((k for k in range(j+1, len(tokens)) if tokens[k] == '.'), len(tokens))
            clause = tokens[j+1:end]
            assign = next((k for k, t in enumerate(clause) if t.upper() == 'ASSIGN'), None)
            if assign is None: continue
            values = clause[assign+1:]
            while values and values[0].upper() in ('TO', 'IS', 'EXTERNAL', 'DYNAMIC'):
                values = values[1:]
            if not values: continue
            value = values[0]
            literal = value.startswith(('"', "'"))
            name = value[1:-1].replace(value[0]*2, value[0]) if literal else value
            matches = []
            if literal and not Path(name).is_absolute() and '..' not in Path(name).parts:
                matches = [p.relative_to(root).as_posix() for p in files
                           if p.relative_to(root).as_posix() == name or
                           p.relative_to(root).as_posix().endswith('/'+name)]
            status = ('Match' if len(matches) == 1 else 'Ambiguous: choose folder' if matches
                      else 'Missing / output file: confirm folder' if literal
                      else 'Dynamic assignment: location needs review')
            rows.append({'source': source.relative_to(root).as_posix(), 'select': logical,
                         'assignment': name, 'matches': matches, 'status': status})
    matched_folders = [str(Path(m).parent) for row in rows for m in row['matches']]
    candidates = list(dict.fromkeys(matched_folders + folders))
    # Full relative assignments (data/x.dat) need the project root as cwd.
    relative_match = any('/' in row['assignment'] and row['matches'] for row in rows)
    cwd = '.' if relative_match or len(set(matched_folders)) > 1 else (candidates[0] if candidates else '.')
    return {'rows': rows, 'folders': candidates, 'working_directory': cwd}


def validate_runtime(value):
    if not isinstance(value, dict): raise ValueError('Runtime settings must be an object.')
    cwd = value.get('working_directory', '.')
    paths = value.get('data_directories', [])
    if not isinstance(cwd, str) or not cwd:
        raise ValueError('Choose a runtime working directory.')
    if not isinstance(paths, list) or not all(isinstance(p, str) and p for p in paths):
        raise ValueError('Data directories must be a list of paths.')
    if 'accepted' in value and not isinstance(value['accepted'], bool):
        raise ValueError('Runtime acceptance must be true or false.')


def launch_settings(root, fallback, environment):
    """Use per-project accepted paths for both embedded and external consoles."""
    env = dict(environment)
    runtime = config.load(root).get('runtime', {}) if root and config.config_path(root).is_file() else {}
    if not runtime.get('accepted'):
        from .project_outputs import output_directory
        return (output_directory(root) if root else fallback), env
    cwd = config.resolve_path(root, runtime.get('working_directory', 'bin'))
    # Older accepted defaults may still name a bin folder the project never had.
    if runtime.get('working_directory', 'bin') == 'bin' and not os.path.isdir(cwd):
        from .project_outputs import output_directory
        cwd = output_directory(root)
    paths = [config.resolve_path(root, p) for p in runtime.get('data_directories', [])]
    for path in [cwd] + paths:
        if not os.path.isdir(path):
            raise ValueError('Project runtime folder is missing: '+path+'\nRescan Project Folders to update it.')
    if paths: env['COB_FILE_PATH'] = os.pathsep.join(paths)
    return cwd, env
