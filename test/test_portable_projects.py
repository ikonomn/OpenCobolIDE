"""Portable projects, migration, conflict checks, and creation UI regressions."""
import copy
import json
from pathlib import Path
import re
import shutil

import pytest
from open_cobol_ide import project_config as config
from open_cobol_ide.compilers import GnuCobolCompiler, compile_with_build_script, get_file_type
from open_cobol_ide.enums import FileType
from open_cobol_ide.project_validation import validate_project
from open_cobol_ide.settings import Settings


def make_project(tmp_path, name='Sample'):
    root = Path(config.create_project(tmp_path, name))
    source = root / 'src/main.cbl'
    source.write_text('       identification division.\n       program-id. example.\n'
                      '       procedure division.\n           goback.\n')
    return root, source


def errors(root, document=None, sources=None):
    return [d['message'] for d in validate_project(str(root), Settings(), document, sources)
            if d['level'] == 'error']


def test_create_project_preserves_existing_files_and_settings(tmp_path):
    root, source = make_project(tmp_path)
    data = config.load(root)
    data['defaults']['flags'] = ['-Wall']
    config.save(root, data)
    before = config.config_path(root).read_bytes()
    config.create_project(tmp_path, 'Sample')
    assert all((root / folder).is_dir() for folder in config.FOLDERS)
    assert source.read_text().startswith('       identification')
    assert config.config_path(root).read_bytes() == before
    assert not (root / 'build.sh').exists()
    assert not (root / 'detect_sql.py').exists()


@pytest.mark.parametrize('name', ['', '..', '../outside', '/absolute', 'a/b', 'a\\b'])
def test_invalid_project_name_creates_nothing(tmp_path, name):
    with pytest.raises(ValueError): config.create_project(tmp_path, name)
    assert not list(tmp_path.iterdir())


def test_creation_preflights_all_folder_conflicts(tmp_path):
    root = tmp_path / 'Sample'
    root.mkdir()
    (root / 'data').write_text('keep me')
    with pytest.raises(ValueError): config.create_project(tmp_path, 'Sample')
    assert not (root / 'src').exists()
    assert (root / 'data').read_text() == 'keep me'


def test_invalid_config_is_never_replaced(tmp_path):
    root = tmp_path / 'Sample'
    (root / 'config').mkdir(parents=True)
    path = config.config_path(root)
    path.write_text('{broken JSON')
    with pytest.raises(ValueError): config.create_project(tmp_path, 'Sample')
    assert path.read_text() == '{broken JSON'
    assert not (root / 'src').exists()


def test_atomic_save_failure_preserves_document(tmp_path, monkeypatch):
    root, source = make_project(tmp_path)
    before = config.config_path(root).read_bytes()
    data = config.load(root)
    data['name'] = 'changed'
    monkeypatch.setattr(config.os, 'replace', lambda *args: (_ for _ in ()).throw(OSError('disk error')))
    with pytest.raises(OSError): config.save(root, data)
    assert config.config_path(root).read_bytes() == before
    assert list((root / 'config').iterdir()) == [config.config_path(root)]


def test_migration_keeps_legacy_project_and_source_overrides(tmp_path):
    root = tmp_path / 'Legacy'
    (root / 'src').mkdir(parents=True)
    (root / 'copybooks').mkdir()
    source = root / 'src/main.cbl'
    source.write_text('       procedure division.\n')
    settings = Settings()
    settings.set_project_options(str(root), {'enabled': True, 'flags': ['-Wall', '-T', 'build/{stem}.lst']})
    settings.set_source_flags(str(source), ['-debug', '-I', str(root / 'copybooks')])
    settings.set_source_environment(str(source), {'cob_copy_dir': str(root / 'copybooks')})
    settings.initialize_project_config(str(root))
    data = config.load(root)
    assert data['defaults']['flags'] == ['-Wall', '-T', 'build/{stem}.lst']
    assert data['sources']['src/main.cbl']['flags'] == ['-debug', '-I', 'copybooks']
    assert data['sources']['src/main.cbl']['environment']['cob_copy_dir'] == 'copybooks'
    assert str(root) not in config.config_path(root).read_text()


def test_moved_project_keeps_source_settings_and_relative_paths(tmp_path):
    root, source = make_project(tmp_path)
    settings = Settings()
    settings.set_source_compiler_options(str(source), ['-Wall', '-I', str(root / 'copybooks')],
                                         {'cob_copy_dir': str(root / 'copybooks')},
                                         {'listing': {'filename': 'build/{stem}.prn'}})
    moved = tmp_path / 'Moved'
    shutil.copytree(root, moved)
    source = str(moved / 'src/main.cbl')
    assert Settings().project_root_for_source(source) == str(moved)
    assert settings.source_flags(source) == ['-Wall', '-I', 'copybooks']
    assert settings.effective_flags(source) == ['-Wall', '-I', str(moved / 'copybooks')]
    assert settings.effective_environment(source)['cob_copy_dir'] == str(moved / 'copybooks')
    assert settings.effective_build_options(source)['listing']['filename'] == str(moved / 'build/{stem}.prn')


def test_source_reset_restores_inheritance_without_changing_project(tmp_path):
    root, source = make_project(tmp_path)
    settings = Settings()
    defaults = config.load(root)['defaults']
    defaults['flags'] = ['-Wall']
    settings.set_project_options(str(root), defaults)
    settings.set_source_compiler_options(str(source), [], {'cob_copy_dir': 'data'})
    assert settings.effective_flags(str(source)) == []
    settings.set_source_compiler_options(str(source), None, {}, {'listing': {}})
    assert settings.effective_flags(str(source)) == ['-Wall']
    assert config.load(root)['defaults']['flags'] == ['-Wall']


@pytest.mark.parametrize('flags,fragment', [
    (['-x'], 'detected automatically'), (['-m'], 'detected automatically'),
    (['-free', '-fixed'], 'Both fixed and free'),
    (['-I'], 'requires an operand'),
        (['-o', 'custom'], 'manages output'),
    (['-Xrefr'], 'Use --Xref'),
    (['-I', 'missing'], 'does not exist'),
    (['-L', 'missing'], 'does not exist'),
])
def test_invalid_settings_report_clear_conflicts(tmp_path, flags, fragment):
    root, source = make_project(tmp_path)
    data = config.load(root)
    data['defaults']['flags'] = flags
    assert any(fragment in message for message in errors(root, data))


def test_source_directive_conflict(tmp_path):
    root, source = make_project(tmp_path)
    source.write_text('       >>source format free\nprocedure division.\n')
    data = config.load(root)
    data['defaults']['source_format'] = 'fixed'
    assert any('FORMAT directive' in message for message in errors(root, data))


def test_duplicate_output_and_listing_conflicts(tmp_path):
    root, source = make_project(tmp_path)
    second = root / 'src/sub/main.cbl'
    second.parent.mkdir()
    second.write_text(source.read_text())
    messages = errors(root)
    assert any('Output filename conflicts' in message for message in messages)
    assert any('Listing destination conflicts' in message for message in messages)


def test_shared_listing_for_distinct_sources_is_rejected(tmp_path):
    root, source = make_project(tmp_path)
    (root / 'src/second.cbl').write_text(source.read_text().replace('main.', 'second.'))
    data = config.load(root)
    data['defaults']['flags'] = ['-T', 'build/shared.lst']
    assert any('Listing destination conflicts' in message for message in errors(root, data))


def test_listing_cannot_overwrite_project_inputs(tmp_path):
    root, source = make_project(tmp_path)
    data = config.load(root)
    data['defaults']['listing']['filename'] = 'config/project.json'
    assert any('overwrite a project input' in message for message in errors(root, data))


def test_missing_compiler_and_missing_saved_source(tmp_path):
    root, source = make_project(tmp_path)
    data = config.load(root)
    data['defaults']['environment']['compiler_path'] = 'tools/missing-cobc'
    data['sources']['src/not-created.cbl'] = {}
    diagnostics = validate_project(str(root), Settings(), data)
    assert any(d['level'] == 'error' and 'Compiler not found' in d['message'] for d in diagnostics)
    assert any(d['level'] == 'warning' and 'missing' in d['message'] for d in diagnostics)


def test_source_keys_cannot_escape_project(tmp_path):
    root, source = make_project(tmp_path)
    data = config.load(root)
    data['sources']['../outside.cbl'] = {}
    with pytest.raises(ValueError): config.save(root, data)


def test_portable_settings_reach_real_internal_build(tmp_path):
    root, source = make_project(tmp_path)
    source.write_text('       identification division.\n       program-id. example.\n'
                      '       data division.\n       linkage section.\n'
                      '       01 argument pic x.\n'
                      '       procedure division using argument.\n           goback.\n')
    settings = Settings()
    settings.register_project(str(root))
    config.set_source_options(str(source), {'flags': ['-Wall'],
        'copybook_paths': ['copybooks'], 'listing': {'filename': 'build/custom-{stem}.lst'}})
    assert not errors(root)
    assert get_file_type(str(source)) == FileType.MODULE
    status, messages = compile_with_build_script(str(source))
    assert status == 0, messages
    assert (root / 'bin/main.so').is_file()
    text = (root / 'build/custom-main.lst').read_text()
    assert re.search(r'^NAME\s+DEFINED\s+REFERENCES\s*$', text, re.M)
    assert '-m' not in config.config_path(root).read_text()


def test_new_project_button_and_review(app, tmp_path, monkeypatch):
    from open_cobol_ide.view.dialogs.project_setup import NewProjectDialog
    from pyqode.qt import QtWidgets
    def accept(dialog):
        dialog.name.setText('NewProject')
        dialog.directory.setText(str(tmp_path))
        return QtWidgets.QDialog.Accepted
    monkeypatch.setattr(NewProjectDialog, 'exec_', accept)
    app.win.ui.btNewProject.click()
    root = tmp_path / 'NewProject'
    assert app.file.project_root == str(root)
    assert config.config_path(root).is_file()
    assert app.file._project_setup_dialog.windowTitle().startswith('Configure Project')
    app.file._project_setup_dialog.close()


def test_precompile_conflicts_block_thread_start(app, tmp_path, monkeypatch):
    from pyqode.qt import QtWidgets
    root, source = make_project(tmp_path)
    app.file.open_project(str(root))
    data = config.load(root)
    data['defaults']['flags'] = ['-free', '-fixed']
    config.save(root, data)
    warnings = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', lambda *args: warnings.append(args[2]))
    from open_cobol_ide.controllers import cobol
    monkeypatch.setattr(cobol.CompilationThread, 'start', lambda self: pytest.fail('Invalid settings compiled'))
    app.cobol._start_compilation([str(source)])
    assert any('fixed and free' in warning for warning in warnings)


def test_new_source_offers_source_configuration(app, tmp_path, monkeypatch):
    from pyqode.qt import QtWidgets
    root, source = make_project(tmp_path)
    app.file.open_project(str(root))
    called = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'question', lambda *args: QtWidgets.QMessageBox.Yes)
    monkeypatch.setattr(app.cobol, 'edit_source_compiler_options', called.append)
    created = root / 'src/created.cbl'
    created.write_text(source.read_text().replace('main.', 'created.'))
    app.file.open_created_file(str(created))
    assert called == [str(created)]


def test_bare_listing_option_keeps_automatic_filename(tmp_path):
    root, source = make_project(tmp_path)
    data = config.load(root)
    data['defaults']['flags'] = ['-T', '-Wall']
    config.save(root, data)
    assert not errors(root)
    status, messages = compile_with_build_script(str(source))
    assert status == 0, messages
    assert (root / 'build/main.lst').is_file()


def test_source_paths_and_libraries_override_project_defaults(tmp_path):
    root, source = make_project(tmp_path)
    (root / 'lib').mkdir()
    (root / 'other-copy').mkdir()
    data = config.load(root)
    data['defaults'].update(library_paths=['lib'], libraries=['one'])
    data['sources']['src/main.cbl'] = {'copybook_paths': ['other-copy'], 'libraries': []}
    config.save(root, data)
    settings = Settings()
    build = settings.effective_build_options(str(source))
    assert build['copybook_paths'] == [str(root / 'other-copy')]
    assert build['library_paths'] == [str(root / 'lib')]
    assert build['libraries'] == []
    _, args = GnuCobolCompiler().make_command(['main.cbl'], FileType.EXECUTABLE, 'bin', source_path=str(source))
    assert '-I' + str(root / 'other-copy') in args
    assert '-L' + str(root / 'lib') in args
    assert '-lone' not in args


def test_free_format_flags_still_detect_module_automatically(tmp_path):
    root, source = make_project(tmp_path)
    source.write_text('identification division.\nprogram-id. callable.\n'
                      'data division.\nlinkage section.\n01 argument pic x.\n'
                      'procedure division using argument.\ngoback.\n')
    data = config.load(root)
    data['defaults']['flags'] = ['-free']
    config.save(root, data)
    assert not errors(root)
    assert get_file_type(str(source)) == FileType.MODULE
    status, messages = compile_with_build_script(str(source))
    assert status == 0, messages
    assert (root / 'bin/main.so').is_file()


def test_listing_can_be_disabled_per_source(tmp_path):
    root, source = make_project(tmp_path)
    config.set_source_options(str(source), {'listing': {'enabled': False}})
    assert not errors(root)
    status, messages = compile_with_build_script(str(source))
    assert status == 0, messages
    assert (root / 'bin/main').is_file()
    assert not list((root / 'build').glob('*.lst'))


def test_bad_config_open_keeps_current_project(app, tmp_path, monkeypatch):
    from pyqode.qt import QtWidgets
    root, source = make_project(tmp_path)
    app.file.open_project(str(root))
    broken = tmp_path / 'Broken'
    (broken / 'config').mkdir(parents=True)
    config.config_path(broken).write_text('{broken')
    warnings = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', lambda *args: warnings.append(args[2]))
    app.file.open_project(str(broken))
    assert app.file.project_root == str(root)
    assert warnings and '{broken' == config.config_path(broken).read_text()


def test_invalid_candidate_settings_are_not_saved(app, tmp_path, monkeypatch):
    from pyqode.qt import QtWidgets
    root, source = make_project(tmp_path)
    candidate = config.load(root)
    before = config.config_path(root).read_bytes()
    candidate['defaults']['flags'] = ['-m']
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', lambda *args: None)
    assert not app.cobol.validate_project_settings(str(root), candidate)
    assert config.config_path(root).read_bytes() == before


def test_source_listing_overrides_inherited_listing_flag(tmp_path):
    root, source = make_project(tmp_path)
    data = config.load(root)
    data['defaults']['flags'] = ['-T', 'build/default.lst', '-Wall']
    data['sources']['src/main.cbl'] = {'listing': {'filename': 'build/source-{stem}.lst'}}
    config.save(root, data)
    assert not errors(root)
    status, messages = compile_with_build_script(str(source))
    assert status == 0, messages
    assert (root / 'build/source-main.lst').exists()
    assert not (root / 'build/default.lst').exists()


def test_reset_is_displayed_as_inherited_settings():
    assert not config.has_overrides({'flags': None, 'environment': {
        'path_mode': 'inherit', 'compiler_path': '', 'path': '', 'cob_copy_dir': ''},
        'source_format': 'inherit', 'listing': {}, 'copybook_paths': None})
    assert config.has_overrides({'flags': []})
    assert config.has_overrides({'listing': {'enabled': False}})


def test_cross_reference_flags_do_not_break_syntax_checking(tmp_path):
    import subprocess
    from open_cobol_ide.linter import make_linter_command
    root, source = make_project(tmp_path)
    data = config.load(root)
    data['defaults']['flags'] = ['--Xref', '-ftsymbols', '-T', 'build/{stem}.lst', '-Wall']
    config.save(root, data)
    pgm, args = make_linter_command(str(source), str(source), source.read_text())
    assert '--Xref' not in args and '-ftsymbols' not in args and '-T' not in args
    result = subprocess.run([pgm] + args, cwd=root, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_source_can_disable_listing_inherited_from_project_flags(tmp_path):
    root, source = make_project(tmp_path)
    data = config.load(root)
    data['defaults']['flags'] = ['--Xref', '-T', 'build/{stem}.lst', '-Wall']
    data['sources']['src/main.cbl'] = {'listing': {'enabled': False}}
    config.save(root, data)
    assert not errors(root)
    status, messages = compile_with_build_script(str(source))
    assert status == 0, messages
    assert (root / 'bin/main').is_file()
    assert not list((root / 'build').glob('*.lst'))


@pytest.mark.parametrize('paths,enabled', [(None, True), ([], True), (['copybooks'], False)])
@pytest.mark.parametrize('sql', [False, True])
def test_validation_uses_implicit_project_copybooks(tmp_path, monkeypatch, paths, enabled, sql):
    root, source = make_project(tmp_path)
    source.write_text('       COPY copybook.\n')
    (root/'copybooks/copybook.cpy').write_text(
        '           EXEC SQL SELECT 1 END-EXEC.\n' if sql else '       01 VALUE-ITEM PIC X.\n')
    data = config.load(root)
    data['defaults'].update(copybook_paths=paths, enabled=enabled)
    data['sources']['src/main.cbl'] = {'copybook_paths': None}
    monkeypatch.setattr(Settings, 'copybook_paths', property(lambda self: ''))
    monkeypatch.setattr(Settings, 'cob_copy_dir_enabled', property(lambda self: False))
    monkeypatch.delenv('COB_COPY_DIR', raising=False)
    monkeypatch.delenv('PROJECT_COPY_DIR', raising=False)
    monkeypatch.setenv('GIXPP', 'ocide-test-missing-gixpp')
    messages = errors(root, data)
    assert not any('Cannot inspect' in m for m in messages), messages
    assert any('GixSQL preprocessor not found' in m for m in messages) == sql


def test_validation_implicit_copybooks_still_reports_missing_copy(tmp_path, monkeypatch):
    root, source = make_project(tmp_path)
    source.write_text('       COPY missing-copybook.\n')
    monkeypatch.delenv('PROJECT_COPY_DIR', raising=False)
    assert any('Cannot inspect COPY missing-copybook' in m for m in errors(root))


def test_validation_uses_builder_project_copy_override(tmp_path, monkeypatch):
    root, source = make_project(tmp_path)
    source.write_text('       COPY custom-book.\n')
    custom = root/'custom-copy'
    custom.mkdir()
    (custom/'custom-book.cpy').write_text('       01 VALUE-ITEM PIC X.\n')
    monkeypatch.setenv('PROJECT_COPY_DIR', 'custom-copy')
    assert not errors(root)
