from pathlib import Path
import os
import shutil
import subprocess
import pytest
from open_cobol_ide import project_config as config
from open_cobol_ide.project_outputs import discover, output_directory
from open_cobol_ide.project_runtime import launch_settings


def project(tmp_path):
    (tmp_path/'src').mkdir()
    (tmp_path/'src/main.cob').write_text('       identification division.\n       program-id. layout-test.\n       procedure division.\n           display "OK".\n           goback.\n')
    config.save(tmp_path, config.default_config(tmp_path))
    return tmp_path


def test_missing_bin_falls_back_to_root_and_old_runtime(tmp_path):
    root = project(tmp_path)
    assert output_directory(root) == str(root)
    data = config.load(root)
    data['runtime'] = {'accepted': True, 'working_directory': 'bin', 'data_directories': []}
    config.save(root, data)
    assert launch_settings(str(root), 'unused', {})[0] == str(root)
    assert not (root/'bin').exists()


def test_detect_executable_and_library_locations(tmp_path):
    root = project(tmp_path)
    for folder,name in [('programs','main'),('modules','main.so')]:
        (root/folder).mkdir()
        (root/folder/name).write_bytes(b'\x7fELFtest')
        (root/folder/name).chmod(0o755)
    assert discover(root) == {'executables': ['programs'], 'libraries': ['modules']}
    assert output_directory(root) == str(root/'programs')
    assert output_directory(root, True) == str(root/'modules')
    data = config.load(root)
    data['output_directories'] = {'executables': 'custom'}
    config.save(root, data)
    assert output_directory(root) == str(root/'custom')


def test_ambiguous_output_requires_selection(tmp_path):
    root = project(tmp_path)
    for folder in ('first','second'):
        (root/folder).mkdir()
        (root/folder/'main').write_bytes(b'\x7fELFtest')
        (root/folder/'main').chmod(0o755)
    with pytest.raises(ValueError, match='Several project output folders'):
        output_directory(root)


@pytest.mark.skipif(not shutil.which('cobc'), reason='GnuCOBOL required')
def test_real_build_without_bin_retains_debug_files(tmp_path):
    root = project(tmp_path)
    output = root/'programs'; output.mkdir()
    script = Path(__file__).resolve().parents[1]/'open_cobol_ide/build_tools/build.sh'
    result = subprocess.run(['bash', str(script), str(root/'src/main.cob')],
        env=dict(os.environ, OCIDE_PROJECT_DIR=str(root), OCIDE_OUTPUT_DIR=str(output),
                 OCIDE_DEBUG_BUILD='1', OCIDE_COMPILER_FLAGS='[]'), capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (output/'main').is_file()
    assert list((root/'debug_data/src/main').glob('*.c'))
    assert list((root/'debug_data/src/main').glob('*.h'))
    assert not (root/'bin').exists()


def test_open_existing_project_creates_only_debug_folder(app, tmp_path):
    root = project(tmp_path)
    (root/'programs').mkdir()
    (root/'programs/main').write_bytes(b'\x7fELFtest')
    (root/'programs/main').chmod(0o755)
    assert app.file.open_project(str(root))
    assert (root/'debug_data').is_dir()
    assert not (root/'bin').exists()
    assert not (root/'build').exists()
    assert config.load(root)['output_directories']['executables'] == 'programs'
