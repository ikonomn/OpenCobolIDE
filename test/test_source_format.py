from open_cobol_ide.source_format import detect_source_format


def test_detects_supported_free_directives():
    assert detect_source_format('>>SOURCE FREE\nIDENTIFICATION DIVISION.') is True
    assert detect_source_format(
        '       >>SOURCE FORMAT IS FREE\nIDENTIFICATION DIVISION.') is True


def test_detects_supported_fixed_directives_case_insensitively():
    assert detect_source_format('>>source fixed') is False
    assert detect_source_format('       >>Source Format Is Fixed') is False


def test_first_directive_controls_editor_initial_format():
    source = '>>SOURCE FREE\n>>SOURCE FORMAT IS FIXED\n'
    assert detect_source_format(source) is True


def test_no_directive_uses_global_fallback():
    assert detect_source_format('IDENTIFICATION DIVISION.') is None
