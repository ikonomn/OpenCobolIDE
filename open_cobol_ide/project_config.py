"""Portable project configuration and safe project creation (no Qt dependency)."""
import copy
import json
import os
from pathlib import Path
import tempfile

FOLDERS = ('src', 'copybooks', 'bin', 'build', 'data', 'config')
_active_root = None


def get_active_root():
    return str(_active_root) if _active_root is not None else None


def set_active_root(root):
    """Keep sources attached to the project explicitly opened in this session."""
    global _active_root
    _active_root = Path(root).resolve() if root else None

ENV_KEYS = ('compiler_path', 'path_mode', 'path', 'cob_copy_dir',
            'gixpp_path', 'gixsql_copy_dir', 'gixsql_library_dir')


def config_path(root):
    return Path(root) / 'config' / 'project.json'


def roots_for_source(source):
    """Return enclosing portable project folders, nearest first."""
    path = Path(source).resolve().parent
    return [str(directory) for directory in (path,) + tuple(path.parents)
            if config_path(directory).is_file()]


def find_root(source):
    path = Path(source).resolve().parent
    # A leftover src/config/project.json must not hijack an opened parent
    # project's copybooks, source overrides or output directories.
    if _active_root is not None and config_path(_active_root).is_file():
        try:
            path.relative_to(_active_root)
        except ValueError:
            pass
        else:
            return str(_active_root)
    for directory in (path,) + tuple(path.parents):
        if config_path(directory).is_file():
            return str(directory)
    return None


def source_key(root, source):
    try:
        return Path(source).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        raise ValueError('Source file is outside the project directory: ' + str(source))


def default_config(root):
    return {'schema_version': 1, 'name': Path(root).name,
            'defaults': {'enabled': True, 'flags': None,
                         'environment': {}, 'copybook_paths': ['copybooks'],
                         'listing': {'enabled': True, 'filename': 'build/{stem}.lst'}},
            'sources': {}}


def validate_options(options):
    if not isinstance(options, dict):
        raise ValueError('Compiler settings must be an object.')
    if options.get('flags') is not None and (not isinstance(options['flags'], list) or
            not all(isinstance(item, str) for item in options['flags'])):
        raise ValueError('Compiler flags must be a list of strings or null.')
    for key in ('copybook_paths', 'library_paths', 'libraries'):
        if options.get(key) is not None and (not isinstance(options[key], list) or
                not all(isinstance(item, str) for item in options[key])):
            raise ValueError(key + ' must be a list of strings or null.')
    if 'enabled' in options and not isinstance(options['enabled'], bool):
        raise ValueError('enabled must be true or false.')
    environment = options.get('environment', {})
    if not isinstance(environment, dict) or not all(
            isinstance(v, str) for v in environment.values()):
        raise ValueError('Environment settings must contain string values.')
    if environment.get('path_mode', 'inherit') not in ('inherit', 'prepend', 'replace'):
        raise ValueError('Invalid tools directory mode.')
    if options.get('source_format', 'inherit') not in ('inherit', 'free', 'fixed'):
        raise ValueError('Source format must be inherit, free or fixed.')
    listing = options.get('listing', {})
    if not isinstance(listing, dict):
        raise ValueError('Listing settings must be an object.')
    if 'enabled' in listing and not isinstance(listing['enabled'], bool):
        raise ValueError('Listing enabled must be true or false.')
    if 'filename' in listing and not isinstance(listing['filename'], str):
        raise ValueError('Listing filename must be a string.')


def validate_schema(data):
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('Unsupported project configuration. Expected schema_version 1.')
    if not isinstance(data.get('name'), str) or not isinstance(data.get('sources'), dict):
        raise ValueError('Project configuration requires name and sources.')
    validate_options(data.get('defaults'))
    for key, options in data['sources'].items():
        if (not isinstance(key, str) or not key or '\\' in key or
                Path(key).is_absolute() or ':' in key or '..' in Path(key).parts):
            raise ValueError('Source settings must use relative paths inside the project.')
        validate_options(options)
    return data


def load(root):
    path = config_path(root)
    try:
        with path.open(encoding='utf-8') as stream:
            return validate_schema(json.load(stream))
    except (ValueError, OSError) as error:
        raise ValueError('Cannot read %s: %s' % (path, error)) from error


def save(root, data):
    validate_schema(data)
    path = config_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         dir=str(path.parent), delete=False) as stream:
            temporary = stream.name
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def source_options(path):
    root = find_root(path)
    if root is None:
        return None
    return load(root)['sources'].get(source_key(root, path), {})


def set_source_options(path, options):
    root = find_root(path)
    if root is None:
        return False
    data = load(root)
    key = source_key(root, path)
    data['sources'][key] = copy.deepcopy(options)
    save(root, data)
    return True


def create_project(parent, name):
    name = name.strip()
    if not name or name in ('.', '..') or any(c in name for c in '/\\:') or any(ord(c) < 32 for c in name):
        raise ValueError('Enter a project name without path separators.')
    root = Path(parent).resolve() / name
    # Check all destinations before creating anything. Existing files are never replaced.
    if root.exists() and not root.is_dir():
        raise ValueError('The project location is an existing file.')
    for folder in FOLDERS:
        target = root / folder
        if target.exists() and (not target.is_dir() or target.is_symlink()):
            raise ValueError('Cannot create project folder: ' + str(target))
    if config_path(root).exists():
        load(root)
    for folder in FOLDERS:
        (root / folder).mkdir(parents=True, exist_ok=True)
    if not config_path(root).exists():
        save(root, default_config(root))
    return str(root)


def resolve_path(root, value):
    if not value or not root or os.path.isabs(value):
        return value
    return os.path.normpath(os.path.join(root, value))


def portable_path(root, value):
    if not value or not os.path.isabs(value):
        return value
    try:
        return Path(value).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return value


def map_flags(flags, root, portable=False):
    if flags is None:
        return None
    convert = portable_path if portable else resolve_path
    result = []
    operand = False
    for flag in flags:
        if operand and not flag.startswith('-'):
            result.append(convert(root, flag))
            operand = False
            continue
        operand = False
        if flag in ('-I', '-L', '-T', '-t'):
            result.append(flag)
            operand = True
        elif flag.startswith(('-I', '-L')) and len(flag) > 2:
            result.append(flag[:2] + convert(root, flag[2:]))
        else:
            result.append(flag)
    return result


def portable_options(root, options):
    options = copy.deepcopy(options)
    if 'flags' in options:
        options['flags'] = map_flags(options['flags'], root, portable=True)
    for key in ('copybook_paths', 'library_paths'):
        if options.get(key) is not None:
            options[key] = [portable_path(root, path) for path in options[key]]
    env = options.get('environment', {})
    for key in ENV_KEYS:
        if key in ('path_mode',) or not env.get(key):
            continue
        if key == 'path':
            env[key] = os.pathsep.join(portable_path(root, p) for p in env[key].split(os.pathsep))
        else:
            env[key] = portable_path(root, env[key])
    if options.get('listing', {}).get('filename'):
        options['listing']['filename'] = portable_path(root, options['listing']['filename'])
    return options


def has_overrides(options):
    if options.get('flags') is not None:
        return True
    if any(options.get(key) is not None for key in ('copybook_paths', 'library_paths', 'libraries')):
        return True
    if options.get('source_format', 'inherit') != 'inherit':
        return True
    listing = options.get('listing', {})
    if 'enabled' in listing or listing.get('filename'):
        return True
    env = options.get('environment', {})
    return any(value for key, value in env.items() if key != 'path_mode') or env.get('path_mode', 'inherit') != 'inherit'
