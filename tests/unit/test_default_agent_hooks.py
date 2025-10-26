from pathlib import Path

from orchestrator import BrainConfig, DefaultAgentHooks, SensoryConfig


def test_default_agent_hooks_capture_stdout(monkeypatch, tmp_path: Path) -> None:
    class FakeBrain:
        def __init__(self) -> None:
            self.ran = False

        def run(self, instructions: str):  # pragma: no cover - executed via hook
            print("hello from brain")
            self.ran = True
            return {"status": "ok"}

    fake_brain = FakeBrain()

    monkeypatch.setattr(
        "orchestrator.create_brain_agent",
        lambda project_path, config, run_id: fake_brain,
    )

    hooks = DefaultAgentHooks(
        project_path=tmp_path,
        brain_config=BrainConfig(),
        sensory_config=SensoryConfig(),
        run_id="run_test",
    )

    hooks.run_brain("do work", pass_index=1)

    captured = hooks.consume_brain_log(pass_index=1)
    assert captured is not None
    assert "hello from brain" in captured
    # logs are one-shot – subsequent calls should return nothing
    assert hooks.consume_brain_log(pass_index=1) is None
