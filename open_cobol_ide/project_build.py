"""Content-based project build history; failed/incomplete builds are never cached."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from .build_tools.detect_sql import TOKEN, COMMENT


def dependencies(source, directories, free=False, seen=None):
    source = Path(source).resolve()
    seen = set() if seen is None else seen
    identity = (source, free)
    if identity in seen:
        return set()
    seen.add(identity)
    result, tokens = {source}, []
    for line in source.read_text(errors='replace').splitlines():
        if not free and len(line) > 6 and line[6] in '*/':
            continue
        pattern = r'^\s*>>\s*SOURCE\s+(?:FORMAT\s+)?(?:IS\s+)?(FREE|FIXED)'
        directive = re.match(pattern, line, re.I)
        if directive is None and not free:
            directive = re.match(pattern, line[7:], re.I)
        if directive:
            free = directive.group(1).upper() == 'FREE'
            continue
        if not free:
            if len(line) > 6 and line[6] in '*/':
                continue
            line = line[7:72]
        line = COMMENT.sub(lambda m: '' if m.group().startswith('*>') else m.group(), line)
        tokens.extend((m.group(), free) for m in TOKEN.finditer(line))
    for i, (token, mode) in enumerate(tokens[:-1]):
        if token.upper() == 'COPY':
            name = tokens[i+1][0].strip("'\"")
        elif (token.upper() == 'INCLUDE' and i >= 2 and
              [t[0].upper() for t in tokens[i-2:i]] == ['EXEC', 'SQL']):
            name = tokens[i+1][0].strip("'\"")
        else:
            continue
        if i+2 < len(tokens) and tokens[i+2][0].upper() in ('IN', 'OF'):
            raise ValueError('Library-qualified COPY requires a conservative rebuild')
        found = set()
        # Include all matching candidates: compiler and SQL preprocessor search
        # orders can differ, so tracking only the first risks stale builds.
        for directory in [source.parent] + [Path(d) for d in directories]:
            for suffix in ('', '.cpy', '.CPY', '.cob', '.cbl'):
                candidate = directory/(name+suffix)
                if candidate.is_file():
                    found.add(candidate.resolve())
        if not found:
            raise FileNotFoundError('Cannot resolve copybook %s' % name)
        for candidate in found:
            result.update(dependencies(candidate, directories, mode, seen))
    return result


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def artifact_stamp(path):
    stat = Path(path).stat()
    return [stat.st_mtime_ns, stat.st_size]


def snapshot(source):
    """Describe actual compiler inputs/settings and required output artifacts."""
    from .settings import Settings
    from .compilers import GnuCobolCompiler, get_file_type, find_build_script
    from .source_format import read_source_format
    source = Path(source).resolve()
    settings = Settings()
    root = settings.project_root_for_source(str(source))
    script = find_build_script(str(source))
    if root is None or script is None:
        return None  # Other SQL backends are conservatively rebuilt.
    compiler = GnuCobolCompiler()
    options = settings.effective_build_options(str(source))
    mode = get_file_type(str(source))
    pgm, args = compiler.make_command([source.name], mode, 'bin', source_path=str(source),
        default_listing=str(Path(root)/'build'/(source.stem+'.lst')))
    env = compiler.setup_process_environment(str(source))
    free = read_source_format(str(source))
    if free is None:
        selected = options['source_format']
        free = settings.free_format if selected == 'inherit' else selected == 'free'
    if '-free' in args: free = True
    if '-fixed' in args: free = False
    directories = [os.environ.get('PROJECT_COPY_DIR') or str(Path(root)/'copybooks'),
                   env.value('GIXSQL_COPY_DIR') or '/usr/share/gixsql/copy']
    directories += [p for p in env.value('COB_COPY_DIR').split(os.pathsep) if p]
    directories.append(root)  # Compiler working directory.
    for i, arg in enumerate(args):
        if arg == '-I' and i+1 < len(args): directories.append(args[i+1])
        elif arg.startswith('-I') and len(arg)>2: directories.append(arg[2:])
    directories = [str(Path(root)/p) if not os.path.isabs(p) else p for p in directories]
    inputs = {str(p): digest(p) for p in dependencies(source, directories, free)}
    for name in ('build.sh', 'detect_sql.py'):
        path = Path(script).parent/name
        inputs[str(path)] = digest(path)
    tools = {}
    for command in (pgm, env.value('GIXPP') or 'gixpp'):
        path = shutil.which(command, path=env.value('PATH'))
        tools[command] = [path, artifact_stamp(path)] if path else None
    payload = [1, inputs, pgm, args, sorted(env.toStringList()), tools, options, mode]
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    outputs = [str(Path(root)/'bin'/(source.stem+compiler.extension_for_type(mode)))]
    if options['listing'].get('enabled', True):
        for i, arg in enumerate(args[:-1]):
            if arg in ('-T', '-t'):
                outputs.append(args[i+1])
    outputs = [str(Path(root)/p) if not os.path.isabs(p) else p for p in outputs]
    return {'fingerprint': fingerprint, 'outputs': outputs}


class BuildState:
    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root/'build/.ocide-build-state.json'
        try:
            data = json.loads(self.path.read_text())
            if not isinstance(data, dict): raise ValueError('Invalid build history')
            self.entries = data['entries'] if data.get('version') == 1 else {}
            if not isinstance(self.entries, dict): self.entries = {}
        except (OSError, ValueError, KeyError, TypeError):
            self.entries = {}

    def key(self, source):
        return os.path.relpath(source, self.root)

    def current(self, source, inputs):
        if inputs is None: return False
        saved = self.entries.get(self.key(source))
        try:
            return (isinstance(saved, dict) and saved['inputs'] == inputs and
                    saved['artifacts'] == {p: artifact_stamp(p) for p in inputs['outputs']})
        except (OSError, KeyError, TypeError):
            return False

    def invalidate(self, source):
        self.entries.pop(self.key(source), None)
        self.save()

    def record(self, source, inputs):
        if inputs is None: return
        try:
            stamps = {p: artifact_stamp(p) for p in inputs['outputs']}
        except OSError:
            return
        self.entries[self.key(source)] = {'inputs': inputs, 'artifacts': stamps}
        self.save()

    def save(self):
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', dir=str(self.path.parent), delete=False) as f:
                temporary = f.name
                json.dump({'version': 1, 'entries': self.entries}, f)
            os.replace(temporary, self.path)
        except OSError:
            pass  # Cache failures must never turn a successful compile into an error.
        finally:
            if temporary and os.path.exists(temporary): os.unlink(temporary)
