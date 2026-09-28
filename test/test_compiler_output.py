from open_cobol_ide.compilers import GnuCobolCompiler


def test_cobc_version_timestamp_is_not_an_error():
    output = (
        'cobc (GnuCOBOL) 3.1.2.0\n'
        'Built May 19 2021 23:32:34 Packaged Dec 23 2020 12:04:58 UTC\n'
        'C version "Clang 10.0.0 "\n'
    )

    assert GnuCobolCompiler.parse_output(output, '/tmp') == []
