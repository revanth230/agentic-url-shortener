from app.orchestrator import (
    AgenticOrchestrator,
    TaskStatus,
    build_greenfield_graph,
)


def create_orchestrator():
    return AgenticOrchestrator(
        build_greenfield_graph()
    )


def test_initial_ready_task():
    orchestrator = create_orchestrator()

    ready = orchestrator.get_ready_tasks()

    assert ready == ["requirement_analysis"]


def test_parallel_tasks_after_requirements():
    orchestrator = create_orchestrator()

    orchestrator.start_task("requirement_analysis")
    orchestrator.complete_task("requirement_analysis")

    ready = orchestrator.get_ready_tasks()

    assert "architecture_design" in ready
    assert "risk_review" in ready


def test_human_approval_gate():
    orchestrator = create_orchestrator()

    orchestrator.start_task("requirement_analysis")
    orchestrator.complete_task("requirement_analysis")

    orchestrator.start_task("architecture_design")
    orchestrator.complete_task("architecture_design")

    orchestrator.start_task("risk_review")
    orchestrator.complete_task("risk_review")

    ready = orchestrator.get_ready_tasks()

    assert ready == []

    assert (
        orchestrator.statuses["implementation"]
        == TaskStatus.WAITING_APPROVAL
    )

    orchestrator.approve_task("implementation")

    ready = orchestrator.get_ready_tasks()

    assert "implementation" in ready


def test_retry_behavior():
    orchestrator = create_orchestrator()

    orchestrator.start_task("requirement_analysis")
    orchestrator.complete_task("requirement_analysis")

    orchestrator.start_task("architecture_design")

    orchestrator.fail_task(
        "architecture_design",
        "Design validation failed",
    )

    assert (
        orchestrator.retry_counts["architecture_design"]
        == 1
    )

    assert (
        orchestrator.statuses["architecture_design"]
        == TaskStatus.PENDING
    )


def test_safe_stop_after_retry_exhaustion():
    orchestrator = create_orchestrator()

    orchestrator.start_task("requirement_analysis")
    orchestrator.complete_task("requirement_analysis")

    for _ in range(3):
        orchestrator.start_task("architecture_design")

        orchestrator.fail_task(
            "architecture_design",
            "Repeated design failure",
        )

    assert (
        orchestrator.statuses["architecture_design"]
        == TaskStatus.FAILED
    )

    assert orchestrator.safe_stopped is True


def test_replan_invalidates_downstream_tasks():
    orchestrator = create_orchestrator()

    orchestrator.start_task("requirement_analysis")
    orchestrator.complete_task("requirement_analysis")

    orchestrator.start_task("architecture_design")
    orchestrator.complete_task("architecture_design")

    orchestrator.start_task("risk_review")
    orchestrator.complete_task("risk_review")

    orchestrator.get_ready_tasks()

    orchestrator.approve_task("implementation")

    orchestrator.start_task("implementation")
    orchestrator.complete_task("implementation")

    orchestrator.replan_from(
        "requirement_analysis",
        "Requirement changed",
    )

    assert (
        orchestrator.statuses["requirement_analysis"]
        == TaskStatus.PENDING
    )

    assert (
        orchestrator.statuses["architecture_design"]
        == TaskStatus.PENDING
    )

    assert (
        orchestrator.statuses["implementation"]
        == TaskStatus.PENDING
    )