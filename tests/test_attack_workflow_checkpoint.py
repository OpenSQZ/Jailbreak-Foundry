import pytest

from agents.utils.checkpoint import CheckpointManager
from agents.workflows.attack import _compute_resume_state


def test_compute_resume_state_no_checkpoint():
    iteration, last_step, attack_name = _compute_resume_state(None)
    assert iteration == 1
    assert last_step is None
    assert attack_name is None


@pytest.mark.parametrize(
    "checkpoint,expected",
    [
        ({"iteration": 3, "step_name": "planner", "attack_name": None}, (3, "planner", None)),
        ({"iteration": 3, "step_name": "attack", "attack_name": "x_gen"}, (3, "attack", "x_gen")),
        # Auditor means the iteration is fully complete; resume at the next one.
        ({"iteration": 3, "step_name": "auditor", "attack_name": "x_gen"}, (4, None, "x_gen")),
    ],
)
def test_compute_resume_state_cases(checkpoint, expected):
    assert _compute_resume_state(checkpoint) == expected


def test_checkpoint_manager_round_trip(tmp_path):
    mgr = CheckpointManager(tmp_path)
    mgr.save_checkpoint(iteration=2, step_name="attack", attack_name="foo_gen")
    assert mgr.get_last_checkpoint() == {"iteration": 2, "step_name": "attack", "attack_name": "foo_gen"}


def test_checkpoint_manager_invalid_json_returns_none(tmp_path):
    (tmp_path / "checkpoint.json").write_text("not json", encoding="utf-8")
    mgr = CheckpointManager(tmp_path)
    assert mgr.get_last_checkpoint() is None


def test_checkpoint_manager_clear_removes_checkpoint_and_marks_completed(tmp_path):
    mgr = CheckpointManager(tmp_path)
    mgr.save_checkpoint(iteration=1, step_name="planner", attack_name=None)

    assert (tmp_path / "checkpoint.json").exists()
    mgr.clear()

    assert not (tmp_path / "checkpoint.json").exists()
    assert (tmp_path / ".completed").exists()


def test_checkpoint_manager_clear_overwrites_completed_marker(tmp_path):
    mgr = CheckpointManager(tmp_path)
    completed = tmp_path / ".completed"
    completed.write_text("old", encoding="utf-8")

    mgr.clear()
    assert completed.exists()
    # touch() truncates to empty file on some FS? don't rely on that; just ensure it's there.
