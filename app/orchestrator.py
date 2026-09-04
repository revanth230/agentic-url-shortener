from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from time import perf_counter


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class WorkflowTask:
    name: str
    dependencies: list[str] = field(default_factory=list)
    requires_approval: bool = False
    max_retries: int = 2
    fallback_action: str | None = None


def build_greenfield_graph() -> dict[str, WorkflowTask]:
    return {
        "requirement_analysis": WorkflowTask(
            name="requirement_analysis",
        ),

        "architecture_design": WorkflowTask(
            name="architecture_design",
            dependencies=["requirement_analysis"],
            fallback_action="human_architecture_review",
        ),

        "risk_review": WorkflowTask(
            name="risk_review",
            dependencies=["requirement_analysis"],
            fallback_action="manual_risk_review",
        ),

        "implementation": WorkflowTask(
            name="implementation",
            dependencies=[
                "architecture_design",
                "risk_review",
            ],
            requires_approval=True,
            fallback_action="manual_implementation_review",
        ),

        "testing": WorkflowTask(
            name="testing",
            dependencies=["implementation"],
            fallback_action="manual_test_review",
        ),

        "documentation": WorkflowTask(
            name="documentation",
            dependencies=["implementation"],
        ),

        "release_review": WorkflowTask(
            name="release_review",
            dependencies=[
                "testing",
                "documentation",
            ],
            requires_approval=True,
            fallback_action="manual_release_hold",
        ),
    }


class AgenticOrchestrator:
    def __init__(
        self,
        tasks: dict[str, WorkflowTask],
    ):
        self.tasks = tasks

        self.statuses = {
            task_name: TaskStatus.PENDING
            for task_name in tasks
        }

        self.retry_counts = {
            task_name: 0
            for task_name in tasks
        }

        self.approved_tasks = set()

        self.audit_log = []

        self.safe_stopped = False

        self.task_start_times = {}
        self.task_durations = {}

        self.failure_start_times = {}
        self.recovery_durations = []

        self.rollback_count = 0
        self.fallback_count = 0

        self.workflow_start_time = None
        self.workflow_end_time = None

    # ---------------------------------------------------------
    # AUDIT / TRACEABILITY
    # ---------------------------------------------------------

    def record_event(
        self,
        task_name: str,
        event: str,
        details: str | None = None,
    ):
        record = {
            "task": task_name,
            "event": event,
            "status": self.statuses[task_name].value,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        if details is not None:
            record["details"] = details

        self.audit_log.append(record)

    def record_workflow_event(
        self,
        event: str,
        details: str | None = None,
    ):
        record = {
            "task": "workflow",
            "event": event,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        if details is not None:
            record["details"] = details

        self.audit_log.append(record)

    # ---------------------------------------------------------
    # DEPENDENCY / ENTRY GATES
    # ---------------------------------------------------------

    def dependencies_succeeded(
        self,
        task_name: str,
    ) -> bool:
        task = self.tasks[task_name]

        return all(
            self.statuses[dependency]
            == TaskStatus.SUCCEEDED
            for dependency in task.dependencies
        )

    def get_ready_tasks(self) -> list[str]:
        if self.safe_stopped:
            return []

        ready_tasks = []

        for task_name, task in self.tasks.items():

            if (
                self.statuses[task_name]
                != TaskStatus.PENDING
            ):
                continue

            if not self.dependencies_succeeded(
                task_name
            ):
                continue

            if (
                task.requires_approval
                and task_name
                not in self.approved_tasks
            ):
                self.statuses[task_name] = (
                    TaskStatus.WAITING_APPROVAL
                )

                self.record_event(
                    task_name,
                    "waiting_for_human_approval",
                )

                continue

            ready_tasks.append(task_name)

        return ready_tasks

    # ---------------------------------------------------------
    # HUMAN APPROVAL
    # ---------------------------------------------------------

    def approve_task(
        self,
        task_name: str,
    ):
        if task_name not in self.tasks:
            raise ValueError(
                "Unknown task"
            )

        task = self.tasks[task_name]

        if not task.requires_approval:
            raise ValueError(
                "This task does not require approval"
            )

        if (
            self.statuses[task_name]
            != TaskStatus.WAITING_APPROVAL
        ):
            raise ValueError(
                "Task is not waiting for approval"
            )

        self.approved_tasks.add(task_name)

        self.statuses[task_name] = (
            TaskStatus.PENDING
        )

        self.record_event(
            task_name,
            "human_approval_granted",
        )

    # ---------------------------------------------------------
    # START TASK
    # ---------------------------------------------------------

    def start_task(
        self,
        task_name: str,
    ):
        if self.safe_stopped:
            raise ValueError(
                "Workflow is in safe-stop mode"
            )

        ready_tasks = self.get_ready_tasks()

        if task_name not in ready_tasks:
            raise ValueError(
                f"Task '{task_name}' is not ready"
            )

        self.statuses[task_name] = (
            TaskStatus.RUNNING
        )

        self.task_start_times[
            task_name
        ] = perf_counter()

        if self.workflow_start_time is None:
            self.workflow_start_time = (
                perf_counter()
            )

        self.record_event(
            task_name,
            "task_started",
        )

    # ---------------------------------------------------------
    # SUCCESS
    # ---------------------------------------------------------

    def complete_task(
        self,
        task_name: str,
    ):
        if (
            self.statuses[task_name]
            != TaskStatus.RUNNING
        ):
            raise ValueError(
                "Only running tasks can be completed"
            )

        self.statuses[task_name] = (
            TaskStatus.SUCCEEDED
        )

        start_time = (
            self.task_start_times.get(task_name)
        )

        if start_time is not None:
            self.task_durations[
                task_name
            ] = (
                perf_counter()
                - start_time
            )

        # If this task previously failed and then
        # recovered, measure recovery time.
        failure_time = (
            self.failure_start_times.pop(
                task_name,
                None,
            )
        )

        if failure_time is not None:
            recovery_time = (
                perf_counter()
                - failure_time
            )

            self.recovery_durations.append(
                recovery_time
            )

            self.record_event(
                task_name,
                "task_recovered",
                details=(
                    f"Recovery took "
                    f"{recovery_time:.4f} seconds"
                ),
            )

        self.record_event(
            task_name,
            "task_succeeded",
        )

        # If all tasks succeeded, workflow is done.
        if all(
            status == TaskStatus.SUCCEEDED
            for status in self.statuses.values()
        ):
            self.workflow_end_time = (
                perf_counter()
            )

            self.record_workflow_event(
                "workflow_completed",
            )

    # ---------------------------------------------------------
    # FAILURE / RETRY / SAFE STOP
    # ---------------------------------------------------------

    def fail_task(
        self,
        task_name: str,
        reason: str,
    ):
        if (
            self.statuses[task_name]
            != TaskStatus.RUNNING
        ):
            raise ValueError(
                "Only running tasks can fail"
            )

        if (
            task_name
            not in self.failure_start_times
        ):
            self.failure_start_times[
                task_name
            ] = perf_counter()

        self.retry_counts[
            task_name
        ] += 1

        task = self.tasks[task_name]

        if (
            self.retry_counts[task_name]
            <= task.max_retries
        ):
            self.statuses[task_name] = (
                TaskStatus.PENDING
            )

            self.record_event(
                task_name,
                "retry_scheduled",
                details=reason,
            )

            return

        self.statuses[task_name] = (
            TaskStatus.FAILED
        )

        self.record_event(
            task_name,
            "task_failed_permanently",
            details=reason,
        )

        if task.fallback_action:
            self.activate_fallback(
                task_name,
                task.fallback_action,
            )

        self.block_downstream_tasks(
            task_name
        )

        self.safe_stopped = True

        self.record_workflow_event(
            "workflow_safe_stopped",
            details=(
                f"Permanent failure in "
                f"{task_name}"
            ),
        )

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------

    def activate_fallback(
        self,
        task_name: str,
        fallback_action: str,
    ):
        self.fallback_count += 1

        self.record_event(
            task_name,
            "fallback_activated",
            details=fallback_action,
        )

    # ---------------------------------------------------------
    # BLOCK DOWNSTREAM WORK
    # ---------------------------------------------------------

    def block_downstream_tasks(
        self,
        failed_task_name: str,
    ):
        changed = True

        while changed:
            changed = False

            for (
                task_name,
                task,
            ) in self.tasks.items():

                if self.statuses[
                    task_name
                ] not in {
                    TaskStatus.PENDING,
                    TaskStatus.WAITING_APPROVAL,
                }:
                    continue

                dependency_failed = any(
                    self.statuses[
                        dependency
                    ] in {
                        TaskStatus.FAILED,
                        TaskStatus.BLOCKED,
                    }
                    for dependency
                    in task.dependencies
                )

                if dependency_failed:

                    self.statuses[
                        task_name
                    ] = TaskStatus.BLOCKED

                    self.record_event(
                        task_name,
                        "task_blocked_by_dependency",
                        details=(
                            failed_task_name
                        ),
                    )

                    changed = True

    # ---------------------------------------------------------
    # ROLLBACK
    # ---------------------------------------------------------

    def rollback_task(
        self,
        task_name: str,
        reason: str,
    ):
        if task_name not in self.tasks:
            raise ValueError(
                "Unknown task"
            )

        if (
            self.statuses[task_name]
            != TaskStatus.SUCCEEDED
        ):
            raise ValueError(
                "Only succeeded tasks can be rolled back"
            )

        self.rollback_count += 1

        self.statuses[task_name] = (
            TaskStatus.PENDING
        )

        self.approved_tasks.discard(
            task_name
        )

        self.task_durations.pop(
            task_name,
            None,
        )

        self.record_event(
            task_name,
            "task_rolled_back",
            details=reason,
        )

        self.invalidate_downstream_tasks(
            task_name,
            reason=(
                f"Upstream rollback: {task_name}"
            ),
        )

        self.workflow_end_time = None

    # ---------------------------------------------------------
    # DYNAMIC REPLANNING
    # ---------------------------------------------------------

    def replan_from(
        self,
        task_name: str,
        reason: str,
    ):
        if task_name not in self.tasks:
            raise ValueError(
                "Unknown task"
            )

        self.safe_stopped = False
        self.workflow_end_time = None

        self.statuses[task_name] = (
            TaskStatus.PENDING
        )

        self.retry_counts[
            task_name
        ] = 0

        self.approved_tasks.discard(
            task_name
        )

        self.task_durations.pop(
            task_name,
            None,
        )

        self.record_event(
            task_name,
            "task_replanned",
            details=reason,
        )

        self.invalidate_downstream_tasks(
            task_name,
            reason=reason,
        )

    def invalidate_downstream_tasks(
        self,
        upstream_task_name: str,
        reason: str,
    ):
        queue = [
            upstream_task_name
        ]

        visited = set()

        while queue:

            current = queue.pop(0)

            if current in visited:
                continue

            visited.add(current)

            for (
                task_name,
                task,
            ) in self.tasks.items():

                if (
                    current
                    not in task.dependencies
                ):
                    continue

                self.statuses[
                    task_name
                ] = TaskStatus.PENDING

                self.retry_counts[
                    task_name
                ] = 0

                self.approved_tasks.discard(
                    task_name
                )

                self.task_durations.pop(
                    task_name,
                    None,
                )

                self.record_event(
                    task_name,
                    "invalidated_by_upstream_change",
                    details=reason,
                )

                queue.append(
                    task_name
                )

    # ---------------------------------------------------------
    # HUMAN RECOVERY FROM SAFE STOP
    # ---------------------------------------------------------

    def resume_after_human_review(
        self,
        reason: str,
    ):
        if not self.safe_stopped:
            raise ValueError(
                "Workflow is not safe-stopped"
            )

        self.safe_stopped = False

        self.record_workflow_event(
            "workflow_resumed_by_human",
            details=reason,
        )

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    def get_status(
        self,
    ) -> dict[str, str]:

        return {
            task_name: status.value
            for (
                task_name,
                status,
            ) in self.statuses.items()
        }

    def get_retry_counts(
        self,
    ) -> dict[str, int]:

        return self.retry_counts.copy()

    # ---------------------------------------------------------
    # RELIABILITY METRICS
    # ---------------------------------------------------------

    def get_metrics(
        self,
    ) -> dict:

        total_tasks = len(
            self.tasks
        )

        succeeded_tasks = sum(
            1
            for status
            in self.statuses.values()
            if status
            == TaskStatus.SUCCEEDED
        )

        failed_tasks = sum(
            1
            for status
            in self.statuses.values()
            if status
            == TaskStatus.FAILED
        )

        blocked_tasks = sum(
            1
            for status
            in self.statuses.values()
            if status
            == TaskStatus.BLOCKED
        )

        waiting_approval_tasks = sum(
            1
            for status
            in self.statuses.values()
            if status
            == TaskStatus.WAITING_APPROVAL
        )

        total_retries = sum(
            self.retry_counts.values()
        )

        success_rate = 0.0

        if total_tasks > 0:
            success_rate = (
                succeeded_tasks
                / total_tasks
            ) * 100

        mttr = None

        if self.recovery_durations:
            mttr = (
                sum(
                    self.recovery_durations
                )
                / len(
                    self.recovery_durations
                )
            )

        end_to_end_latency = None

        if (
            self.workflow_start_time
            is not None
        ):
            end_time = (
                self.workflow_end_time
                if self.workflow_end_time
                is not None
                else perf_counter()
            )

            end_to_end_latency = (
                end_time
                - self.workflow_start_time
            )

        return {
            "total_tasks": total_tasks,
            "succeeded_tasks": succeeded_tasks,
            "failed_tasks": failed_tasks,
            "blocked_tasks": blocked_tasks,
            "waiting_approval_tasks": (
                waiting_approval_tasks
            ),
            "total_retries": total_retries,
            "rollback_count": (
                self.rollback_count
            ),
            "fallback_count": (
                self.fallback_count
            ),
            "success_rate_percent": round(
                success_rate,
                2,
            ),
            "mttr_seconds": (
                round(mttr, 4)
                if mttr is not None
                else None
            ),
            "task_durations_seconds": {
                task_name: round(
                    duration,
                    4,
                )
                for (
                    task_name,
                    duration,
                ) in self.task_durations.items()
            },
            "end_to_end_latency_seconds": (
                round(
                    end_to_end_latency,
                    4,
                )
                if end_to_end_latency
                is not None
                else None
            ),
            "safe_stopped": (
                self.safe_stopped
            ),
        }