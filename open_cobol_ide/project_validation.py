"""Validate merged project/source settings before writing or compiling."""
import os
from pathlib import Path
import re
import shutil

from . import project_config as config
from .source_format import read_source_format


def validate_project(root, settings, document=None, sources=None):
    from .project import project_sources
    root = str(Path(root).resolve())
    document = config.load(root) if document is None else document
    config.validate_schema(document)
    defaults = document['defaults'] if document['defaults'].get('enabled', True) else {}
    sources = (project_sources(root, settings.all_extensions) if sources is None else sources)
    diagnostics = []
    outputs, listings, intermediates = {}, {}, {}

    def report(level, source, message):
        diagnostics.append({'level': level, 'source': source, 'message': message})

    def collision(table, filename, label, kind):
        filename = os.path.normcase(os.path.realpath(filename))
        if filename in table and table[filename] != label:
            report('error', label, '%s conflicts with %s: %s' % (kind, table[filename], filename))
        table[filename] = label

    for path in sources or [None]:
        label = config.source_key(root, path) if path else 'Project'
        source = document['sources'].get(label, {}) if path else {}
        flags = source.get('flags')
        if flags is None:
            flags = defaults.get('flags')
        flags = list(settings.compiler_flags if flags is None else flags)
        env = dict(defaults.get('environment', {}))
        source_env = source.get('environment', {})
        for key, value in source_env.items():
            if value and key not in ('path', 'path_mode'):
                env[key] = value
        if source_env.get('path_mode', 'inherit') != 'inherit':
            env.update(path_mode=source_env['path_mode'], path=source_env.get('path', ''))
        tools_path = os.environ.get('PATH', '')
        if settings.path_enabled:
            tools_path = settings.path + os.pathsep + tools_path
        if env.get('path_mode') == 'replace':
            tools_path = ''
        if env.get('path') and env.get('path_mode', 'inherit') != 'inherit':
            tool_dirs = [config.resolve_path(root, p) for p in env['path'].split(os.pathsep)]
            tools_path = os.pathsep.join(tool_dirs + ([tools_path] if tools_path else []))
            for directory in tool_dirs:
                if not os.path.isdir(directory):
                    report('error', label, 'Tools directory does not exist: ' + directory)
        compiler = env.get('compiler_path') or settings.compiler_path
        compiler = config.resolve_path(root, compiler) if '/' in compiler or '\\' in compiler else compiler
        if not shutil.which(compiler, path=tools_path):
            report('error', label, 'Compiler not found or not executable: ' + compiler)
        for key in ('cob_copy_dir', 'gixsql_copy_dir', 'gixsql_library_dir'):
            if env.get(key) and not os.path.isdir(config.resolve_path(root, env[key])):
                report('error', label, '%s directory does not exist: %s' % (key, env[key]))
        include_dirs, library_dirs, listing_flags = [], [], []
        free, fixed = False, False
        index = 0
        while index < len(flags):
            flag = flags[index]
            if flag in ('-x', '-m'):
                report('error', label, 'Remove %s: executable/module mode is detected automatically.' % flag)
            if flag == '-o':
                report('error', label, 'Remove -o: the IDE manages output filenames in bin/.')
            if flag in ('-E', '-C', '-S', '-c', '-fsyntax-only'):
                report('error', label, 'Remove %s: it prevents a complete project build.' % flag)
            if flag in ('-Xrefr', '--Xrefr'):
                report('error', label, 'Use --Xref for cross references; %s is not a compiler option.' % flag)
            free = free or flag == '-free'
            fixed = fixed or flag == '-fixed'
            if flag in ('-I', '-L', '-l', '-T', '-t'):
                if index + 1 >= len(flags) or flags[index+1].startswith('-'):
                    if flag not in ('-T', '-t'):
                        report('error', label, '%s requires an operand.' % flag)
                else:
                    index += 1
                    value = flags[index]
                    if flag == '-I': include_dirs.append(value)
                    elif flag == '-L': library_dirs.append(value)
                    elif flag in ('-T', '-t'): listing_flags.append(value)
            elif flag.startswith('-I') and len(flag) > 2:
                include_dirs.append(flag[2:])
            elif flag.startswith('-L') and len(flag) > 2:
                library_dirs.append(flag[2:])
            index += 1
        if free and fixed:
            report('error', label, 'Both fixed and free source formats are selected.')
        selected_format = source.get('source_format', 'inherit')
        if selected_format == 'inherit': selected_format = defaults.get('source_format', 'inherit')
        if selected_format == 'free' and fixed or selected_format == 'fixed' and free:
            report('error', label, 'Source format conflicts with the extra compiler flags.')
        directive = read_source_format(path) if path else None
        if directive is not None and (directive and (fixed or selected_format == 'fixed') or
                                       not directive and (free or selected_format == 'free')):
            report('error', label, 'Compiler source format conflicts with the source FORMAT directive.')
        for key, target, global_value in (
                ('copybook_paths', include_dirs, settings.copybook_paths),
                ('library_paths', library_dirs, settings.library_search_path)):
            values = source.get(key)
            if values is None: values = defaults.get(key)
            target.extend([p for p in global_value.split(';') if p] if values is None else values)
            for value in target:
                resolved = config.resolve_path(root, value)
                if not os.path.isdir(resolved):
                    report('error', label, '%s directory does not exist: %s' % (key, resolved))
        if not path:
            continue
        listing = dict(defaults.get('listing', {}))
        listing.update(source.get('listing', {}))
        source_listing = source.get('listing', {})
        if source.get('flags') is None and (source_listing.get('filename') or
                source_listing.get('enabled') is False):
            listing_flags = []
        if len(set(listing_flags)) > 1:
            report('error', label, 'Multiple listing destinations are specified in compiler flags.')
        if listing_flags and not listing.get('enabled', True):
            report('error', label, 'Listing flags conflict with disabled listing generation.')
        filename = listing_flags[-1] if listing_flags else listing.get('filename', 'build/{stem}.lst')
        if re.search(r'\{(?!stem\})', filename):
            report('error', label, 'Listing filenames support only the {stem} placeholder.')
        filename = filename.replace('{stem}', Path(path).stem)
        if listing.get('enabled', True):
            if not filename.strip():
                report('error', label, 'A listing filename is required.')
            else:
                listing_path = config.resolve_path(root, filename)
                parent = Path(listing_path).parent
                if not parent.is_dir() and parent != Path(root)/'build':
                    report('error', label, 'Listing directory does not exist: ' + str(parent))
                collision(listings, listing_path, label, 'Listing destination')
        # Determine the same automatic mode as the compiler, without executing a source.
        from .compilers import get_file_type, GnuCobolCompiler
        extension = GnuCobolCompiler().extension_for_type(get_file_type(path))
        collision(outputs, os.path.join(root, 'bin', Path(path).stem + extension), label, 'Output filename')
        if Path(path).suffix.lower() not in ('.cbl', '.cob', '.pco'):
            continue
        try:
            from .build_tools.detect_sql import has_sql
            free_mode = directive if directive is not None else (
                selected_format == 'free' if selected_format != 'inherit' else free or settings.free_format)
            copy_environment = env.get('cob_copy_dir') or (
                settings.cob_copy_dir if settings.cob_copy_dir_enabled else os.environ.get('COB_COPY_DIR', ''))
            sql_dirs = include_dirs + [p for p in copy_environment.split(os.pathsep) if p]
            sql = has_sql(path, [config.resolve_path(root, p) for p in sql_dirs] +
                          [config.resolve_path(root, env.get('gixsql_copy_dir') or '/usr/share/gixsql/copy')], free=free_mode)
            if sql:
                gixpp = env.get('gixpp_path') or os.environ.get('GIXPP', 'gixpp')
                if '/' in gixpp: gixpp = config.resolve_path(root, gixpp)
                if not shutil.which(gixpp, path=tools_path):
                    report('error', label, 'GixSQL preprocessor not found: ' + gixpp)
                collision(intermediates, os.path.join(root, 'build', Path(path).stem + '.cbsql'), label,
                          'SQL intermediate filename')
        except OSError as error:
            report('error', label, 'Cannot inspect SQL/COPY dependencies: ' + str(error))
    for key in document['sources']:
        if not (Path(root)/key).is_file():
            report('warning', key, 'Saved source settings refer to a file that is missing.')
    # A listing must not overwrite a binary or SQL intermediate from another source.
    for path, label in listings.items():
        if path in outputs or path in intermediates:
            report('error', label, 'Listing destination would overwrite a build artifact: ' + path)
        inputs = {os.path.normcase(os.path.realpath(p)) for p in sources}
        inputs.add(os.path.normcase(os.path.realpath(config.config_path(root))))
        inputs.update(os.path.normcase(os.path.realpath(p)) for p in Path(root).rglob('*.cpy'))
        if path in inputs:
            report('error', label, 'Listing destination would overwrite a project input file: ' + path)
    unique = []
    for item in diagnostics:
        if item not in unique: unique.append(item)
    return unique
