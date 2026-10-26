"""Project builds track content and successful outputs, never just source mtimes."""
import os
from pathlib import Path

import pytest
from open_cobol_ide import project_config as config
from open_cobol_ide.controllers.cobol import CompilationThread
from open_cobol_ide.project_build import BuildState, dependencies, snapshot
from open_cobol_ide.settings import Settings


def make_project(tmp_path):
    root = Path(config.create_project(tmp_path, 'incremental'))
    (root/'copybooks/shared.cpy').write_text('       COPY nested.\n')
    (root/'copybooks/nested.cpy').write_text('       01 SHARED-ITEM PIC X.\n')
    paths = []
    for name in ['first', 'second', 'independent']:
        path = root/'src'/(name+'.cbl')
        path.write_text('       identification division.\n       program-id. '+name+'.\n'
                        '       data division.\n       working-storage section.\n'+
                       ('       COPY shared.\n' if name != 'independent' else '')+
                       '       procedure division.\n           goback.\n')
        paths.append(str(path))
    return root, paths


def batch(paths, force=False, incremental=True):
    thread = CompilationThread()
    thread.file_paths = paths
    thread.incremental = incremental
    thread.force_project = force
    built, failed = [], []
    thread.file_compiled.connect(lambda path, status, messages: built.append((Path(path).stem,status)))
    thread.errored.connect(lambda path, error: failed.append(error))
    thread.run()
    assert not failed, failed
    assert all(status == 0 for name,status in built), built
    return [name for name,status in built]


def test_incremental_source_copybook_settings_and_artifacts(tmp_path):
    root, paths = make_project(tmp_path)
    assert batch(paths) == ['first','second','independent']
    assert batch(paths) == []
    source = Path(paths[0])
    stamp = source.stat()
    source.write_text(source.read_text()+'      * changed\n')
    os.utime(source, ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
    assert batch(paths) == ['first']
    copybook = root/'copybooks/nested.cpy'
    copybook.write_text('       01 SHARED-ITEM PIC XX.\n')
    assert batch(paths) == ['first','second']
    data = config.load(root)
    data['sources']['src/first.cbl'] = {'flags':['-Wall']}
    config.save(root,data)
    assert batch(paths) == ['first']
    (root/'build/second.lst').unlink()
    assert batch(paths) == ['second']
    (root/'bin/independent').unlink()
    assert batch(paths) == ['independent']
    assert batch(paths,force=True) == ['first','second','independent']
    assert batch(paths) == []
    # F8's thread mode does not skip an unchanged source.
    assert batch(paths[:1],incremental=False) == ['first']
    assert batch(paths) == []


def test_failed_rebuild_is_retried_and_does_not_keep_previous_success(tmp_path,monkeypatch):
    from open_cobol_ide.controllers import cobol
    root, paths = make_project(tmp_path)
    batch(paths)
    original = cobol.compile_with_build_script
    with monkeypatch.context() as patch:
        patch.setattr(cobol,'compile_with_build_script',lambda *a,**k: (7,[]))
        thread = CompilationThread()
        thread.file_paths = paths[:1]
        thread.incremental = True
        thread.force_project = True
        thread.run()
    assert batch(paths) == ['first']
    assert batch(paths) == []
    with monkeypatch.context() as patch:
        patch.setattr(cobol,'compile_with_build_script',lambda *a,**k: (7,[]))
        thread = CompilationThread()
        thread.file_paths = paths[:1]
        thread.run()  # A failed forced single-file compile also invalidates success.
    assert batch(paths) == ['first']
    (root/'build/.ocide-build-state.json').write_text('{broken')
    assert batch(paths) == ['first','second','independent']


def test_dependency_cycles_and_sql_include(tmp_path):
    source = tmp_path/'sql.cbl'
    source.write_text('       COPY first.\n           EXEC SQL INCLUDE sql-vars END-EXEC.\n'
                      '      * COPY ignored.\n           DISPLAY "COPY ignored".\n')
    first = tmp_path/'first.cpy'
    first.write_text('       COPY second.\n')
    second = tmp_path/'second.cpy'
    second.write_text('       COPY first.\n')
    sql = tmp_path/'sql-vars.cpy'
    sql.write_text('       01 SQL-VALUE PIC X.\n')
    assert dependencies(source,[tmp_path]) == {source,first,second,sql}
    sql.unlink()
    with pytest.raises(FileNotFoundError): dependencies(source,[tmp_path])


def test_dependency_shadowing_is_tracked_conservatively(tmp_path):
    source = tmp_path/'main.cbl'
    source.write_text('       COPY record.\n')
    paths = []
    for name in ['first','second']:
        directory = tmp_path/name
        directory.mkdir()
        p = directory/'record.cpy'
        p.write_text('       01 RECORD-ITEM PIC X.\n')
        paths.append(p)
    assert dependencies(source,[p.parent for p in paths]) == {source,*paths}


def test_dependency_format_directives_ignore_literals_and_comments(tmp_path):
    source = tmp_path/'main.cbl'
    source.write_text('>>SOURCE FORMAT FREE\n'
                      'DISPLAY ">>SOURCE FORMAT FIXED".\n'
                      '*> >>SOURCE FORMAT FIXED\nCOPY record.\n')
    copybook = tmp_path/'record.cpy'
    copybook.write_text('01 RECORD-ITEM PIC X.\n')
    assert dependencies(source,[tmp_path]) == {source,copybook}


def test_incremental_project_with_gnucobol32(tmp_path,monkeypatch):
    compiler = os.environ.get('OCIDE_TEST_COBC32')
    if not compiler:
        pytest.skip('Set OCIDE_TEST_COBC32 for GnuCOBOL 3.2 incremental checks')
    monkeypatch.setattr(Settings,'compiler_path',property(lambda self: compiler))
    root, paths = make_project(tmp_path)
    assert batch(paths) == ['first','second','independent']
    assert batch(paths) == []
    (root/'copybooks/nested.cpy').write_text('       01 SHARED-ITEM PIC XXX.\n')
    assert batch(paths) == ['first','second']


def test_wrong_shaped_build_history_is_ignored(tmp_path):
    root, paths = make_project(tmp_path)
    (root/'build/.ocide-build-state.json').write_text('[]')
    assert BuildState(root).entries == {}
