from pathlib import Path
import shutil
import pytest
from open_cobol_ide.c_helpers import plan, output_name, calls
from open_cobol_ide import project_config as config


@pytest.fixture(autouse=True)
def restore_compiler_flags():
    from open_cobol_ide.settings import Settings
    flags = list(Settings().compiler_flags)
    yield
    Settings().compiler_flags = flags


def test_gui_platform_detection_and_caller_name(tmp_path):
    example = Path(__file__).resolve().parents[1]/'examples/common/gui'
    for name in ('score.cob', 'score_window.c'):
        shutil.copyfile(example/name, tmp_path/name)
    result = plan(tmp_path/'score.cob', tmp_path, free=False, windows=False)
    assert result['sources'] == [str(tmp_path/'score_window.c')]
    assert result['libraries'] == ['X11']
    assert plan(tmp_path/'score.cob', tmp_path, windows=True)['libraries'] == ['user32']
    assert output_name(tmp_path/'score.cob') == 'score'
    assert output_name(tmp_path/'score.cob', {'output_name':'gui-score'}, '.exe') == 'gui-score.exe'
    assert output_name(tmp_path/'score.cob', {'output_name':'gui-score.exe'}, '.exe') == 'gui-score.exe'


def test_ignore_comments_strings_and_dynamic_calls(tmp_path):
    source = tmp_path/'caller.cob'
    source.write_text('*> call "comment"\ndisplay \'call "text"\'\ncall variable-name\ncall static "real"\n')
    assert calls(source, True) == {'real'}
    source.write_text('      *call "comment"\n           call "fixed"\n')
    assert calls(source, False) == {'fixed'}


def test_headers_duplicates_manual_and_disable(tmp_path):
    source = tmp_path/'caller.cob';source.write_text('call static "choose"\n')
    (tmp_path/'helper.c').write_text('#include "local.h"\nint choose(void) { return VALUE; }\n')
    (tmp_path/'local.h').write_text('#define VALUE 1\n')
    (tmp_path/'prototype.c').write_text('/* int choose(void) { } */\nint choose(void);\n')
    result = plan(source,tmp_path)
    assert set(result['dependencies']) == {str(tmp_path/'helper.c'),str(tmp_path/'local.h')}
    (tmp_path/'other.c').write_text('int choose(void) { return 2; }\n')
    with pytest.raises(ValueError,match='Several C helpers'):
        plan(source,tmp_path)
    assert plan(source,tmp_path,{'c_sources':[]})['sources'] == []
    assert plan(source,tmp_path,{'c_sources':['helper.c']})['sources'] == [str(tmp_path/'helper.c')]
    with pytest.raises(ValueError,match='missing'):
        plan(source,tmp_path,{'c_sources':['absent.c']})


@pytest.mark.parametrize('name',['../score','folder/score','C:\\score','-bad','..'])
def test_reject_output_paths(name):
    with pytest.raises(ValueError):
        config.validate_options({'output_name': name})


def test_file_dialog_preview(app,tmp_path):
    from open_cobol_ide.view.dialogs.source_compiler_options import SourceCompilerOptionsDialog
    example = Path(__file__).resolve().parents[1]/'examples/common/gui'
    for name in ('score.cob','score_window.c'):shutil.copyfile(example/name,tmp_path/name)
    config.save(tmp_path, config.default_config(tmp_path))
    dialog=SourceCompilerOptionsDialog(str(tmp_path/'score.cob'),['-debug','-Wall'],None,{},options={})
    command=dialog.proposed_c_command()
    assert str(tmp_path/'score_window.c') in command
    assert '-lX11' in command
    assert '-free' in command and '-fixed' not in command
    assert command[command.index('-o')+1] == str(tmp_path/'score')
    dialog.output_name_field.setText('my-score')
    assert dialog.proposed_c_command()[command.index('-o')+1] == str(tmp_path/'my-score')
    dialog.c_auto.setChecked(False)
    assert dialog.extra_values()['c_sources'] == []
    dialog.close()


@pytest.mark.skipif(not shutil.which('cobc'),reason='GnuCOBOL required')
def test_real_project_c_helper_build_and_incremental(app,tmp_path):
    from open_cobol_ide.compilers import compile_with_build_script
    from open_cobol_ide.project_build import snapshot
    from open_cobol_ide.settings import Settings
    source=tmp_path/'caller.cob'
    source.write_text('       identification division.\n       program-id. mixed-test.\n       procedure division.\n           call static "choose"\n           goback.\n')
    (tmp_path/'helper.c').write_text('#include "local.h"\nint choose(void) { return VALUE; }\n')
    header=tmp_path/'local.h';header.write_text('#define VALUE 1\n')
    config.save(tmp_path,config.default_config(tmp_path))
    assert app.file.open_project(str(tmp_path))
    Settings().compiler_flags=[]
    data=config.load(tmp_path)
    data['debug']={'enabled':True}
    data['sources']['caller.cob']={'output_name':'my-caller'}
    config.save(tmp_path,data)
    before=snapshot(str(source))
    status,messages=compile_with_build_script(str(source))
    assert status==0, messages
    assert (tmp_path/'my-caller').exists()
    assert not (tmp_path/'helper').exists()
    assert app.cobol._debug_executable_path() == str(tmp_path/'my-caller')
    assert list((tmp_path/'debug_data/caller').glob('*.c'))
    header.write_text('#define VALUE 2\n')
    assert before['fingerprint'] != snapshot(str(source))['fingerprint']


@pytest.mark.skipif(not shutil.which('cobc') or not Path('/usr/include/X11/Xlib.h').exists(),
                    reason='GnuCOBOL and X11 development headers required')
def test_real_gui_example_links_x11(app,tmp_path):
    from open_cobol_ide.compilers import compile_with_build_script
    from open_cobol_ide.settings import Settings
    example=Path(__file__).resolve().parents[1]/'examples/common/gui'
    for name in ('score.cob','score_window.c'):shutil.copyfile(example/name,tmp_path/name)
    config.save(tmp_path,config.default_config(tmp_path))
    assert app.file.open_project(str(tmp_path))
    Settings().compiler_flags=['-free']
    data=config.load(tmp_path)
    data['debug']={'enabled':True}
    config.save(tmp_path,data)
    log=[]
    status,messages=compile_with_build_script(str(tmp_path/'score.cob'),log.append)
    assert status==0, ''.join(log)
    assert (tmp_path/'score').is_file()
    assert not (tmp_path/'score_window').exists()
    assert '-lX11' in ''.join(log)
