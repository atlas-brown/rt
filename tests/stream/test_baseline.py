from pathlib import Path

from stream.scripts import baseline


def test_get_ltsh_typedb_path_resolves_repo_relative(monkeypatch):
    monkeypatch.setitem(baseline.CONFIG._config, "ltsh_typedb_path", "ltsh_config/typedb")

    assert baseline.get_ltsh_typedb_path() == baseline.REPO_ROOT / "ltsh_config/typedb"


def test_check_ltsh_uses_configured_typedb_env(monkeypatch, tmp_path):
    typedb_path = tmp_path / "typedb"
    typedb_path.write_text("::echo\n>0: None\n<1: <Seq Char>\n", encoding="utf-8")

    monkeypatch.setitem(baseline.CONFIG._config, "ltsh_command", "/usr/bin/fake-ltsh")
    monkeypatch.setitem(baseline.CONFIG._config, "ltsh_typedb_path", str(typedb_path))

    calls = []

    class Result:
        stdout = ""
        stderr = ""
        returncode = 0

    def fake_run(args, input=None, capture_output=None, text=None, timeout=None, env=None):
        calls.append({
            "args": args,
            "input": input,
            "env": env,
        })
        return Result()

    monkeypatch.setattr(baseline.subprocess, "run", fake_run)

    status, output = baseline.check_ltsh("echo test\n# comment\n")

    assert status == "OK"
    assert output == ""
    assert len(calls) == 1
    assert calls[0]["args"] == ["/usr/bin/fake-ltsh"]
    assert calls[0]["input"] == "echo test"
    assert calls[0]["env"]["TYPEDB"] == str(typedb_path)
