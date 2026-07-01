from stream import type_checker as type_checker_module


def test_script_checker_propagates_pipeline_runtime_details(monkeypatch):
    class FakePipelineNode:
        items = []

        def pretty(self):
            return "echo broken"

    class FakeShellParser:
        def __init__(self, *args, **kwargs):
            self.pipeline_nodes = [FakePipelineNode()]
            self.annotations = {}
            self.env_annotations = {}

        def parse_pipeline(self):
            return [[("unused-signature", "unused-invocation")]]

    class FakePipelineChecker:
        def __init__(self, *args, **kwargs):
            self.pipeline_length = 1
            self.max_automata_size = 3
            self.statistics_time = 0.0
            self.self_contained = False
            self.runtime_error_kind = None
            self.runtime_error_message = None
            self.runtime_error_type = None
            self.runtime_error_traceback = None

        def check(self, pipeline_node, parsed_commands, initial_output_type):
            self.runtime_error_kind = "tool runtime error"
            self.runtime_error_message = "synthetic inner failure"
            self.runtime_error_type = "RuntimeError"
            self.runtime_error_traceback = (
                "Traceback (most recent call last):\n"
                "RuntimeError: synthetic inner failure\n"
            )
            return []

    monkeypatch.setattr(type_checker_module, "ShellParser", FakeShellParser)
    monkeypatch.setattr(type_checker_module, "PipelineChecker", FakePipelineChecker)

    checker = type_checker_module.ScriptChecker("fake.sh")
    result = checker.check_next()

    assert result is not None
    assert result.pipeline_content == "echo broken"
    assert result.pipeline_length == 1
    assert result.max_automata_size == 3
    assert result.self_contained is False
    assert result.runtime_error_kind == "tool runtime error"
    assert result.runtime_error_message == "synthetic inner failure"
    assert result.runtime_error_type == "RuntimeError"
    assert "synthetic inner failure" in result.runtime_error_traceback
