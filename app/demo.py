from concurrent.futures import ThreadPoolExecutor
from pprint import pprint

from app.agents import (
    ArchitectureAgent,
    DocumentationAgent,
    ImplementationAgent,
    RequirementAgent,
    RiskAgent,
    TestingAgent,
)
from app.orchestrator import (
    AgenticOrchestrator,
    build_greenfield_graph,
)


def request_human_approval(message: str) -> bool:
    print()
    print("=" * 60)
    print("HUMAN APPROVAL REQUIRED")
    print(message)
    print("=" * 60)

    answer = input(
        "Type APPROVE to continue: "
    ).strip().lower()

    return answer == "approve"


def stop_by_human(
    orchestrator: AgenticOrchestrator,
    reason: str,
):
    orchestrator.safe_stopped = True

    orchestrator.record_workflow_event(
        "workflow_stopped_by_human",
        details=reason,
    )

    print()
    print("Workflow stopped safely by human decision.")


def run_demo():
    print()
    print("Agentic Software Engineering Demo")
    print("=" * 60)

    requirement = (
        "Build a production-style URL shortener "
        "with redirect and click analytics."
    )

    graph = build_greenfield_graph()

    orchestrator = AgenticOrchestrator(
        graph
    )

    requirement_agent = RequirementAgent()
    architecture_agent = ArchitectureAgent()
    risk_agent = RiskAgent()
    implementation_agent = ImplementationAgent()
    testing_agent = TestingAgent()
    documentation_agent = DocumentationAgent()

    outputs = {}

    # -----------------------------------------------------
    # 1. REQUIREMENT ANALYSIS
    # -----------------------------------------------------

    print()
    print("1. Requirement analysis")

    orchestrator.start_task(
        "requirement_analysis"
    )

    requirement_result = (
        requirement_agent.execute(requirement)
    )

    if not requirement_result.success:
        orchestrator.fail_task(
            "requirement_analysis",
            "Requirement agent failed",
        )

        return

    outputs["requirement_analysis"] = (
        requirement_result.output
    )

    orchestrator.complete_task(
        "requirement_analysis"
    )

    print("Requirement analysis completed.")

    # -----------------------------------------------------
    # 2. PARALLEL ARCHITECTURE + RISK REVIEW
    # -----------------------------------------------------

    print()
    print(
        "2. Architecture design and risk review "
        "are ready in parallel"
    )

    ready_tasks = (
        orchestrator.get_ready_tasks()
    )

    print("Ready tasks:", ready_tasks)

    orchestrator.start_task(
        "architecture_design"
    )

    orchestrator.start_task(
        "risk_review"
    )

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        architecture_future = executor.submit(
            architecture_agent.execute,
            requirement_result,
        )

        risk_future = executor.submit(
            risk_agent.execute,
            requirement_result,
        )

        architecture_result = (
            architecture_future.result()
        )

        risk_result = (
            risk_future.result()
        )

    if architecture_result.success:
        outputs["architecture_design"] = (
            architecture_result.output
        )

        orchestrator.complete_task(
            "architecture_design"
        )

    else:
        orchestrator.fail_task(
            "architecture_design",
            "Architecture agent failed",
        )

    if risk_result.success:
        outputs["risk_review"] = (
            risk_result.output
        )

        orchestrator.complete_task(
            "risk_review"
        )

    else:
        orchestrator.fail_task(
            "risk_review",
            "Risk agent failed",
        )

    if orchestrator.safe_stopped:
        print("Workflow entered safe-stop mode.")
        return

    print(
        "Architecture and risk review completed."
    )

    # -----------------------------------------------------
    # 3. HUMAN IMPLEMENTATION APPROVAL
    # -----------------------------------------------------

    orchestrator.get_ready_tasks()

    approved = request_human_approval(
        "Architecture and risk review are complete. "
        "Approve implementation?"
    )

    if not approved:
        stop_by_human(
            orchestrator,
            "Implementation approval rejected",
        )
        return

    orchestrator.approve_task(
        "implementation"
    )

    # -----------------------------------------------------
    # 4. IMPLEMENTATION
    # -----------------------------------------------------

    print()
    print("3. Implementation")

    orchestrator.start_task(
        "implementation"
    )

    implementation_result = (
        implementation_agent.execute(
            architecture_result,
            risk_result,
        )
    )

    if not implementation_result.success:
        orchestrator.fail_task(
            "implementation",
            "Implementation agent failed",
        )
        return

    outputs["implementation"] = (
        implementation_result.output
    )

    orchestrator.complete_task(
        "implementation"
    )

    print("Implementation completed.")

    # -----------------------------------------------------
    # 5. PARALLEL TESTING + DOCUMENTATION
    # -----------------------------------------------------

    print()
    print(
        "4. Testing and documentation "
        "are ready in parallel"
    )

    ready_tasks = (
        orchestrator.get_ready_tasks()
    )

    print("Ready tasks:", ready_tasks)

    orchestrator.start_task(
        "testing"
    )

    orchestrator.start_task(
        "documentation"
    )

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        testing_future = executor.submit(
            testing_agent.execute
        )

        documentation_future = executor.submit(
            documentation_agent.execute
        )

        testing_result = (
            testing_future.result()
        )

        documentation_result = (
            documentation_future.result()
        )

    if testing_result.success:
        outputs["testing"] = (
            testing_result.output
        )

        orchestrator.complete_task(
            "testing"
        )

    else:
        orchestrator.fail_task(
            "testing",
            "Testing agent failed",
        )

    if documentation_result.success:
        outputs["documentation"] = (
            documentation_result.output
        )

        orchestrator.complete_task(
            "documentation"
        )

    else:
        orchestrator.fail_task(
            "documentation",
            "Documentation agent failed",
        )

    if orchestrator.safe_stopped:
        print("Workflow entered safe-stop mode.")
        return

    print(
        "Testing and documentation completed."
    )

    # -----------------------------------------------------
    # 6. HUMAN RELEASE APPROVAL
    # -----------------------------------------------------

    orchestrator.get_ready_tasks()

    approved = request_human_approval(
        "Testing and documentation are complete. "
        "Approve final release review?"
    )

    if not approved:
        stop_by_human(
            orchestrator,
            "Release approval rejected",
        )
        return

    orchestrator.approve_task(
        "release_review"
    )

    # -----------------------------------------------------
    # 7. RELEASE REVIEW
    # -----------------------------------------------------

    print()
    print("5. Final release review")

    orchestrator.start_task(
        "release_review"
    )

    orchestrator.complete_task(
        "release_review"
    )

    print("Release review completed.")

    # -----------------------------------------------------
    # FINAL OUTPUT
    # -----------------------------------------------------

    print()
    print("=" * 60)
    print("WORKFLOW COMPLETE")
    print("=" * 60)

    print()
    print("Final workflow status:")

    pprint(
        orchestrator.get_status()
    )

    print()
    print("Reliability metrics:")

    pprint(
        orchestrator.get_metrics()
    )

    print()
    print("Agent outputs:")

    pprint(outputs)

    print()
    print("Audit trail:")

    pprint(
        orchestrator.audit_log
    )


if __name__ == "__main__":
    run_demo()