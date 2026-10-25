"""Directory projects: deterministic source discovery without generated files."""
import os


def project_sources(root, extensions):
    extensions = {ext.lower() for ext in extensions} - {'.cpy', '.lst', '.prn', '.cbsql'}
    sources = []
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.') and
                         d not in ('bin', 'build', '__pycache__', 'venv'))
        for name in sorted(files):
            path = os.path.join(directory, name)
            if (not name.startswith('.') and not os.path.islink(path) and
                    os.path.splitext(name)[1].lower() in extensions):
                sources.append(os.path.abspath(path))
    return sources
