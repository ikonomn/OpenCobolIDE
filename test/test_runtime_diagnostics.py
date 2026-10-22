"""Runtime diagnostics are display text, independent of compiler checks."""
import pytest
from open_cobol_ide import compilers
from open_cobol_ide.compilers import GnuCobolCompiler
from open_cobol_ide.view.dialogs.about import DlgAbout


@pytest.mark.parametrize('option', ['--runtime-config', '--info'])
@pytest.mark.parametrize('status', [0, 1])
def test_cobcrun_diagnostics(monkeypatch, option, status):
    monkeypatch.setattr(compilers.shutil, 'which', lambda *a, **kw: '/bin/cobcrun')
    calls = []

    def run(pgm, args):
        calls.append((pgm, args))
        return status, 'runtime output'

    monkeypatch.setattr(compilers, 'run_command', run)
    output = (GnuCobolCompiler.get_cobcrun_infos() if option == '--runtime-config'
              else GnuCobolCompiler.get_cobcrun_infos(option))
    assert calls == [('/bin/cobcrun', [option])]
    if status:
        assert 'cobcrun %s' % option in output
        assert 'exit code 1' in output
        assert 'runtime output' in output
    else:
        assert output == 'runtime output'


def test_missing_cobcrun(monkeypatch):
    monkeypatch.setattr(compilers.shutil, 'which', lambda *a, **kw: None)
    def unexpected_run(*args):
        pytest.fail('must not execute a missing loader')
    monkeypatch.setattr(compilers, 'run_command', unexpected_run)
    assert 'could not be found' in GnuCobolCompiler.get_cobcrun_infos()


def test_diagnostics_report(monkeypatch):
    monkeypatch.setattr(GnuCobolCompiler, 'get_cobc_infos', lambda: 'compiler build')
    monkeypatch.setattr(GnuCobolCompiler, 'get_cobcrun_infos',
                        lambda option='--runtime-config': {
                            '--info': 'runtime build',
                            '--runtime-config': 'runtime settings'}[option])
    report = DlgAbout.get_cobc_runtime_env()
    for heading, output in [('cobc --info', 'compiler build'),
                            ('cobcrun --info', 'runtime build'),
                            ('cobcrun --runtime-config', 'runtime settings')]:
        assert heading in report
        assert output in report
    assert '--runtime-env' not in report
