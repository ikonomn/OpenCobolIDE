"""Runtime discovery requires acceptance; debug artifacts must remain usable."""
import os
from pathlib import Path
import shutil
import subprocess
import pytest
from open_cobol_ide import project_config as config
from open_cobol_ide.project_runtime import scan, launch_settings


def project(tmp_path):
    return Path(config.create_project(tmp_path, 'runtime'))


def test_discovery_matches_ambiguity_dynamic_and_comments(tmp_path):
    root = project(tmp_path)
    (root/'input').mkdir()
    (root/'data/customers.dat').write_text('A')
    (root/'input/customers.dat').write_text('B')
    (root/'copybooks/files.cpy').write_text('       SELECT CLIENT ASSIGN TO "customers.dat".\n')
    (root/'src/main.cbl').write_text('       SELECT OUTFILE ASSIGN TO "report.txt".\n'
        '       SELECT VARIABLE-FILE ASSIGN TO DYNAMIC FILE-NAME.\n'
        '      * SELECT COMMENTED ASSIGN TO "ignored".\n'
        '           DISPLAY \'SELECT FAKE ASSIGN TO "ignored".\'.\n')
    result = scan(root)
    rows = {row['select']: row for row in result['rows']}
    assert set(rows) == {'CLIENT', 'OUTFILE', 'VARIABLE-FILE'}
    assert len(rows['CLIENT']['matches']) == 2
    assert 'Ambiguous' in rows['CLIENT']['status']
    assert 'Missing' in rows['OUTFILE']['status']
    assert 'Dynamic' in rows['VARIABLE-FILE']['status']
    assert result['working_directory'] == '.'
    assert not config.load(root).get('runtime')
    assert launch_settings(str(root), 'fallback', {'A':'B'}) == ('fallback', {'A':'B'})


def test_portable_accepted_paths_and_missing_folder(tmp_path):
    root = project(tmp_path)
    data = config.load(root)
    data['runtime'] = {'accepted':True, 'working_directory':'.', 'data_directories':['data']}
    config.save(root, data)
    moved = tmp_path/'moved'
    root.rename(moved)
    cwd, env = launch_settings(str(moved), 'fallback', {'OTHER':'keep'})
    assert cwd == str(moved)
    assert env == {'OTHER':'keep','COB_FILE_PATH':str(moved/'data')}
    (moved/'data').rmdir()
    with pytest.raises(ValueError, match='missing'):
        launch_settings(str(moved), 'fallback', {})


def test_relative_assignment_and_free_format(tmp_path):
    root = project(tmp_path)
    (root/'data/accounts.dat').touch()
    (root/'src/main.cbl').write_text('>>SOURCE FORMAT FREE\n'
        'select account assign to "data/accounts.dat".\n')
    result = scan(root)
    assert result['working_directory'] == '.'
    assert result['rows'][0]['matches'] == ['data/accounts.dat']


def test_schema_rejects_bad_runtime_and_debug(tmp_path):
    root = project(tmp_path)
    data = config.load(root)
    data['debug'] = {'enabled':'yes'}
    with pytest.raises(ValueError): config.save(root, data)
    data['debug'] = {'enabled':True}
    data['runtime'] = {'data_directories':'data'}
    with pytest.raises(ValueError): config.save(root, data)


@pytest.mark.skipif(not shutil.which('cobc'), reason='GnuCOBOL needed')
@pytest.mark.parametrize('mode', ['-x', '-m'])
def test_real_debug_build_retains_only_c_headers_and_exit_status(tmp_path, mode):
    root = project(tmp_path)
    source = root/'src/test.cbl'
    source.write_text('       identification division.\n       program-id. test.\n'
        '       procedure division'+(' using item.\n' if mode == '-m' else '.\n')+'           goback.\n')
    if mode == '-m':
        source.write_text(source.read_text().replace('       procedure division',
            '       data division.\n       linkage section.\n       01 item pic x.\n       procedure division'))
    script = Path(__file__).resolve().parents[1]/'open_cobol_ide/build_tools/build.sh'
    env = dict(os.environ, OCIDE_PROJECT_DIR=str(root), OCIDE_COMPILE_MODE=mode, OCIDE_DEBUG_BUILD='1',
               OCIDE_COMPILER_FLAGS='[]')
    result = subprocess.run(['bash',str(script),str(source)],env=env,capture_output=True,text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    generated = list((root/'debug_data/src/test').iterdir())
    assert any(p.suffix == '.c' for p in generated)
    assert any(p.suffix == '.h' for p in generated)
    assert all(p.suffix in ('.c','.h') for p in generated)
    assert not list((root/'build').glob('.debug-*'))
    assert (root/'build/test.lst').is_file()
    output = root/('bin/test.so' if mode == '-m' else 'bin/test')
    assert output.is_file()
    if mode == '-x':
        assert subprocess.run([str(output)]).returncode == 0
    source.write_text('       invalid cobol !!!\n')
    failed = subprocess.run(['bash',str(script),str(source)],env=env,capture_output=True)
    assert failed.returncode != 0
    assert not list((root/'build').glob('.debug-*'))


def test_runtime_dialog_cancel_and_accept(tmp_path, app):
    from open_cobol_ide.view.dialogs.project_runtime import RuntimeFoldersDialog
    root = project(tmp_path)
    dialog = RuntimeFoldersDialog(str(root))
    dialog.debug.setChecked(True)
    dialog.reject()
    assert 'runtime' not in config.load(root)
    dialog = RuntimeFoldersDialog(str(root))
    dialog.debug.setChecked(True)
    dialog.accept()
    data = config.load(root)
    assert data['runtime']['accepted']
    assert data['debug']['enabled']


def test_debug_incremental_tracks_headers_and_mode(tmp_path):
    from test.test_incremental_project import make_project, batch
    root, paths = make_project(tmp_path)
    data = config.load(root)
    data['debug'] = {'enabled':True}
    config.save(root, data)
    assert batch(paths) == ['first','second','independent']
    assert batch(paths) == []
    next((root/'debug_data/src/first').glob('*.h')).unlink()
    assert batch(paths) == ['first']
    data['debug']['enabled'] = False
    config.save(root, data)
    assert batch(paths) == ['first','second','independent']
    assert batch(paths) == []


@pytest.mark.skipif(not shutil.which('cobc'), reason='GnuCOBOL needed')
def test_real_runtime_data_search(tmp_path):
    root = project(tmp_path)
    (root/'data/value.dat').write_text('FOUND\n')
    source = root/'src/read.cbl'
    source.write_text('''       identification division.
       program-id. readfile.
       environment division.
       input-output section.
       file-control.
           select infile assign to "value.dat"
               organization line sequential.
       data division.
       file section.
       fd infile.
       01 item pic x(5).
       procedure division.
           open input infile
           read infile
           display item
           close infile
           goback.
''')
    output = root/'bin/read'
    subprocess.run(['cobc','-x','-o',str(output),str(source)],check=True,capture_output=True)
    data = config.load(root)
    data['runtime'] = {'accepted':True,'working_directory':'.','data_directories':['data']}
    config.save(root,data)
    cwd, env = launch_settings(str(root), str(root/'bin'), os.environ)
    result = subprocess.run([str(output)],cwd=cwd,env=env,capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'FOUND'


@pytest.mark.skipif(not shutil.which('gixpp') or not shutil.which('cobc'), reason='GixSQL needed')
def test_real_gixsql_debug_build(tmp_path):
    root = project(tmp_path)
    repo = Path(__file__).resolve().parents[1]
    source = root/'src/database-test.cbl'
    shutil.copy(repo/'examples/gixsql/src/database-test.cbl', source)
    shutil.copytree(repo/'examples/gixsql/copybooks', root/'copybooks', dirs_exist_ok=True)
    env = dict(os.environ,OCIDE_PROJECT_DIR=str(root),OCIDE_COMPILE_MODE='-x',
               OCIDE_DEBUG_BUILD='1',OCIDE_COMPILER_FLAGS='[]')
    result = subprocess.run(['bash',str(repo/'open_cobol_ide/build_tools/build.sh'),str(source)],
                            env=env,capture_output=True,text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    assert 'SQL detection: sql' in result.stdout
    assert (root/'build/database-test.cbsql').is_file()
    files = list((root/'debug_data/src/database-test').iterdir())
    assert any(p.suffix == '.c' for p in files)
    assert all(p.suffix in ('.c','.h') for p in files)
    if shutil.which('gdb'):
        check = subprocess.run(['gdb','-batch','-ex','info sources',str(root/'bin/database-test')],
                               capture_output=True,text=True)
        assert str(root/'debug_data/src/database-test') in check.stdout
        assert '.debug-' not in check.stdout


def test_scan_uses_project_source_format_and_named_folder(tmp_path):
    root = project(tmp_path)
    (root/'customer-data').mkdir()
    (root/'src/main.cbl').write_text('select f assign to "missing.dat".\n')
    data = config.load(root)
    data['defaults']['source_format'] = 'free'
    config.save(root,data)
    result = scan(root)
    assert result['rows'][0]['select'] == 'f'
    assert 'customer-data' in result['folders']
