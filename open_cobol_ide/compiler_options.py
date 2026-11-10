"""Compiler option handling without Qt dependencies."""
import os
import re
import shlex
import subprocess


def listing_options(flags, source, automatic=False, syntax_only=False,
                    default_filename=None):
    result = []
    index = 0
    found = False
    stem = os.path.splitext(os.path.basename(source))[0]
    while index < len(flags):
        flag = flags[index]
        if flag in ('-T', '-t'):
            found = True
            index += 1
            filename = default_filename or stem + '.lst'
            if index < len(flags) and not flags[index].startswith('-'):
                filename = flags[index].replace('{stem}', stem)
                index += 1
            if not syntax_only:
                result.extend([flag, filename])
        else:
            if not syntax_only or flag not in ('-X', '--Xref', '-ftsymbols'):
                result.append(flag)
            index += 1
    if automatic and not found and not syntax_only:
        result.extend(['-T', default_filename or stem + '.lst'])
    return result


def expand_pkg_config(flags, cwd=None, env=None):
    """Resolve pkg-config substitutions without running a shell."""
    result = []
    expression = []
    closing = None
    expanded = False
    for flag in flags:
        if closing is None:
            if flag.startswith('`'):
                closing = '`'
            elif flag.startswith('$('):
                closing = ')'
            else:
                result.append(flag)
                continue
        expression.append(flag)
        if not flag.endswith(closing) or flag == '`':
            continue
        opening_length = 1 if closing == '`' else 2
        command = ' '.join(expression)[opening_length:-1].split()
        queries = {
            '--cflags': '-A', '--cflags-only-I': '-A', '--cflags-only-other': '-A',
            '--libs': '-Q', '--libs-only-l': '-Q', '--libs-only-L': '-Q',
            '--libs-only-other': '-Q',
        }
        modifiers = {'--static', '--shared', '--keep-system-cflags', '--keep-system-libs'}
        requested = [arg for arg in command[1:] if arg in queries]
        packages = [arg for arg in command[1:] if not arg.startswith('-')]
        if (not command or command[0] != 'pkg-config' or not requested or not packages
                or any(arg.startswith('-') and arg not in queries and arg not in modifiers
                       for arg in command[1:])):
            raise ValueError('Use pkg-config with compiler or linker flag options and package names.')
        common = [arg for arg in command[1:] if arg not in queries]
        for phase in ('-A', '-Q'):
            selection = [query for query in requested if queries[query] == phase]
            if not selection:
                continue
            try:
                output = subprocess.run(['pkg-config', *selection, *common],
                                        cwd=cwd, env=env, text=True,
                                        capture_output=True, check=True, timeout=15)
            except subprocess.CalledProcessError as error:
                raise ValueError(error.stderr.strip() or 'pkg-config failed.') from error
            except (OSError, subprocess.TimeoutExpired) as error:
                raise ValueError('Cannot run pkg-config: ' + str(error)) from error
            arguments = shlex.split(output.stdout)
            if phase == '-Q' and all(re.fullmatch(r'-[lL].+', arg) for arg in arguments):
                result.extend(arguments)
            elif arguments:
                quoted = subprocess.list2cmdline(arguments) if os.name == 'nt' else ' '.join(
                    shlex.quote(arg) for arg in arguments)
                result.extend((phase, quoted))
        expanded = True
        expression.clear()
        closing = None
    if closing is not None:
        raise ValueError('Unclosed pkg-config substitution in compiler flags.')
    if expanded and not any(flag in ('--static', '-static') for flag in result):
        result.insert(0, '--static')
    return result



def gtk_link_flags(source, flags, libraries, free, output_callback=None):
    """Select GTK from version-specific literal calls when no GTK link was specified."""
    explicit = ' '.join([*flags, *libraries])
    if re.search(r'(?<![\w+.-])(?:-l\s*)?(?:gtk\+-3\.0|gtk4|gtk-[34])(?![\w+.-])',
                 explicit):
        return flags
    if not os.path.isfile(source):
        return flags
    from .c_helpers import calls
    symbols = {symbol.lower() for symbol in calls(source, free)}
    gtk3 = symbols & {'gtk_main', 'gtk_main_quit', 'gtk_widget_show_all',
                      'gtk_builder_connect_signals', 'gtk_container_add',
                      'gtk_container_remove', 'gtk_dialog_run'}
    gtk4 = symbols & {'gtk_window_get_toplevels', 'gtk_window_set_child',
                      'gtk_window_destroy', 'gtk_box_append', 'gtk_box_prepend',
                      'gtk_widget_add_controller', 'gtk_editable_set_text'}
    if bool(gtk3) == bool(gtk4):
        return flags
    package = 'gtk+-3.0' if gtk3 else 'gtk4'
    if output_callback is not None:
        output_callback('Detected GTK%s (%s)\n' % (3 if gtk3 else 4, package))
    return [*flags, '$(pkg-config --libs ' + package + ')']



def with_debug_flags(flags):
    from .c_helpers import DEBUG_FLAGS
    result = []
    has_optimization = any(re.fullmatch(r'-O(?:[0-9]+|s|z|g|fast)?', flag) for flag in flags)
    for flag in flags:
        if flag not in DEBUG_FLAGS or flag not in result:
            result.append(flag)
    for flag in DEBUG_FLAGS:
        if flag not in result and not (flag == '-O0' and has_optimization):
            result.append(flag)
    return result
