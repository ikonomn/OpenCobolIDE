import json

from open_cobol_ide import trace_log

def test_trace_disabled_before_configuration():
    assert not trace_log.enabled()


def test_trace_writes_durable_json_events(tmp_path):
    output = tmp_path / 'trace.jsonl'
    assert trace_log.configure(str(output)) == str(output)
    trace_log.event('test.checkpoint', answer=42)

    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert records[0]['event'] == 'trace.enabled'
    assert records[-1]['event'] == 'test.checkpoint'
    assert records[-1]['answer'] == 42
    assert records[-1]['sequence'] > records[0]['sequence']


def test_default_trace_path_uses_cache_directory(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path))
    output = trace_log._default_path()
    assert output.startswith(str(tmp_path / 'OpenCobolIDE'))
    assert output.endswith('.jsonl')
