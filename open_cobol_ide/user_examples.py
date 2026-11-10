"""Create writable per-user examples from packaged, read-only templates."""
from pathlib import Path
import logging
import shutil


def copy_examples(source, destination):
    """Add missing files, preserving edits and avoiding symbolic links."""
    source, destination = Path(source), Path(destination)
    if destination.is_symlink():
        raise OSError('Examples destination is a symbolic link: %s' % destination)
    destination.mkdir(parents=True, exist_ok=True)
    for entry in source.iterdir():
        if entry.is_symlink() or entry.name in ('__pycache__', '.git', '.gitkeep', '.gitignore'):
            continue
        target = destination / entry.name
        if target.is_symlink():
            continue
        if entry.is_dir():
            if not target.exists() or target.is_dir():
                copy_examples(entry, target)
        elif entry.is_file():
            try:
                with target.open('xb') as output, entry.open('rb') as input_file:
                    shutil.copyfileobj(input_file, output)
            except FileExistsError:
                pass
    return destination


def ensure_user_examples(candidates, folder_name):
    source = next((Path(p) for p in candidates if Path(p).is_dir()), None)
    if source is None:
        return None
    try:
        return copy_examples(source, Path.home() / folder_name)
    except OSError:
        logging.getLogger(__name__).exception('Could not prepare writable examples')
        return None


def examples_directory():
    import sys
    return ensure_user_examples((
        Path(__file__).with_name('example_templates'),
        Path(__file__).resolve().parents[1] / 'examples' / 'common',
        Path(sys.executable).resolve().parent / 'examples',
        Path(sys.prefix) / 'share/doc/opencobolide/examples',
        Path('/usr/share/doc/opencobolide/examples'),
    ), 'OpenCobolIDE-examples')
