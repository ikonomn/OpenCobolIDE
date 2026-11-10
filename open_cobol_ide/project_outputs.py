"""Resolve project output locations without imposing a bin directory."""
import os
from pathlib import Path
from . import project_config as config


def discover(root):
    root = Path(root).resolve()
    result = {'executables': set(), 'libraries': set()}
    for directory, folders, files in os.walk(root, followlinks=False):
        folders[:] = [name for name in folders if not name.startswith('.')
                      and name not in ('debug_data', 'venv', '__pycache__')
                      and not (Path(directory)/name).is_symlink()]
        for name in files:
            path = Path(directory)/name
            if name.startswith('.') or path.is_symlink():
                continue
            library = path.suffix.lower() in ('.so', '.dll', '.dylib', '.a') or '.so.' in name.lower()
            try:
                with path.open('rb') as stream:
                    magic = stream.read(8)
            except OSError:
                continue
            native = magic.startswith((b'\x7fELF', b'MZ', b'!<arch>'))
            if not native or (not library and not (magic.startswith(b'MZ') or os.access(path, os.X_OK))):
                continue
            kind = 'libraries' if library else 'executables'
            result[kind].add(str(path.parent.relative_to(root)) or '.')
    return {key: sorted(paths) for key, paths in result.items()}


def output_directory(root, module=False):
    root = Path(root).resolve()
    data = config.load(root) if config.config_path(root).is_file() else {}
    kind = 'libraries' if module else 'executables'
    selected = data.get('output_directories', {}).get(kind)
    if selected:
        return config.resolve_path(root, selected)
    if (root/'bin').is_dir():
        return str(root/'bin')
    candidates = discover(root)[kind]
    if len(candidates) > 1:
        raise ValueError('Several project output folders found; reopen the project to choose: ' + ', '.join(candidates))
    return config.resolve_path(root, candidates[0] if candidates else '.')
