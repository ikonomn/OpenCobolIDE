"""Compiler option handling without Qt dependencies."""
import os


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
            filename = default_filename or stem + '.prn'
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
        result.extend(['-T', default_filename or stem + '.prn'])
    return result
