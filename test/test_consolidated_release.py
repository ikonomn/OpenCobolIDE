"""The shipped portable demo builds; native RPM scripts refuse the Mint host."""
from pathlib import Path
import re
import shutil
import subprocess
import pytest
from open_cobol_ide import project_config as config
from open_cobol_ide.compilers import compile_with_build_script, get_file_type
from open_cobol_ide.enums import FileType
from open_cobol_ide.project_validation import validate_project
from open_cobol_ide.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


def test_shipped_demo_builds_after_copying(tmp_path):
    demo = ROOT / 'examples/project-demo'
    assert not list((demo / 'bin').glob('[!.]*'))
    assert not list((demo / 'build').glob('[!.]*'))
    target = tmp_path / 'demo moved'
    shutil.copytree(demo, target)
    config.load(target)
    settings = Settings()
    settings.register_project(str(target))
    assert not [d for d in validate_project(str(target), settings) if d['level'] == 'error']
    for name, mode in [('test01',FileType.EXECUTABLE),('worker',FileType.MODULE)]:
        source = target / 'src' / (name + '.cbl')
        assert get_file_type(str(source)) == mode
        status, messages = compile_with_build_script(str(source))
        assert status == 0, messages
        text = (target / 'build' / (name + '.lst')).read_text()
        assert re.search(r'^NAME\s+DEFINED\s+REFERENCES\s*$',text,re.M)
        assert re.search(r'^LABEL\s+DEFINED\s+REFERENCES\s*$',text,re.M)
    result = subprocess.run([str(target / 'bin/test01')], cwd=target / 'bin', capture_output=True,text=True,timeout=5)
    assert result.returncode == 0, result.stderr
    assert 'HELLO from OpenCobolIDE modern11.6' in result.stdout


@pytest.mark.parametrize('script,target', [
    ('packaging/mageia/build-mageia10-rpm.sh','Mageia 10'),
    ('packaging/fedora/build-fedora44-rpm.sh','Fedora 44')])
def test_rpm_builders_refuse_wrong_host(script, target):
    import platform
    system = platform.freedesktop_os_release()
    if (target == 'Mageia 10' and system.get('ID') == 'mageia') or (
            target == 'Fedora 44' and system.get('ID') == 'fedora'):
        pytest.skip('Wrong-host guard check is for another distribution')
    result = subprocess.run(['bash',str(ROOT/script)],capture_output=True,text=True)
    assert result.returncode != 0
    assert target in result.stderr
