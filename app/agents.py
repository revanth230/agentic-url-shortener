from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class AgentResult:
    agent_name: str
    success: bool
    output: dict
    timestamp: str


class EngineeringAgent:
    def __init__(self, name: str):
        self.name = name

    def build_result(
        self,
        success: bool,
        output: dict,
    ) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            success=success,
            output=output,
            timestamp=datetime.now(
                timezone.utc
            ).isoformat(),
        )


class RequirementAgent(EngineeringAgent):
    def __init__(self):
        super().__init__("requirement_agent")

    def execute(
        self,
        requirement: str,
    ) -> AgentResult:
        if not requirement.strip():
            return self.build_result(
                success=False,
                output={
                    "error": "Requirement cannot be empty"
                },
            )

        return self.build_result(
            success=True,
            output={
                "normalized_requirement": requirement.strip(),
                "questions": [],
                "assumptions": [
                    "API-first implementation",
                    "Prototype runs locally",
                ],
            },
        )


class ArchitectureAgent(EngineeringAgent):
    def __init__(self):
        super().__init__("architecture_agent")

    def execute(
        self,
        requirement_result: AgentResult,
    ) -> AgentResult:
        if not requirement_result.success:
            return self.build_result(
                success=False,
                output={
                    "error": (
                        "Requirement analysis did not succeed"
                    )
                },
            )

        return self.build_result(
            success=True,
            output={
                "components": [
                    "FastAPI service",
                    "SQLAlchemy persistence layer",
                    "SQLite prototype database",
                    "Agentic orchestration engine",
                    "Automated test suite",
                ],
                "decisions": [
                    (
                        "FastAPI provides a small, testable "
                        "API surface and OpenAPI documentation."
                    ),
                    (
                        "SQLAlchemy separates persistence "
                        "logic from API behavior."
                    ),
                    (
                        "SQLite keeps the prototype easy "
                        "to run locally."
                    ),
                ],
            },
        )


class RiskAgent(EngineeringAgent):
    def __init__(self):
        super().__init__("risk_agent")

    def execute(
        self,
        requirement_result: AgentResult,
    ) -> AgentResult:
        if not requirement_result.success:
            return self.build_result(
                success=False,
                output={
                    "error": (
                        "Cannot perform risk review "
                        "without valid requirements"
                    )
                },
            )

        return self.build_result(
            success=True,
            output={
                "risks": [
                    "Short-code collision",
                    "Invalid input URL",
                    "Persistence failure",
                    "Unsafe autonomous change",
                    "Regression during enhancement",
                ],
                "controls": [
                    "Unique database constraint",
                    "Pydantic URL validation",
                    "Automated tests",
                    "Human approval gates",
                    "Bounded retries and safe stop",
                ],
            },
        )


class ImplementationAgent(EngineeringAgent):
    def __init__(self):
        super().__init__("implementation_agent")

    def execute(
        self,
        architecture_result: AgentResult,
        risk_result: AgentResult,
    ) -> AgentResult:
        if (
            not architecture_result.success
            or not risk_result.success
        ):
            return self.build_result(
                success=False,
                output={
                    "error": (
                        "Architecture and risk review "
                        "must succeed before implementation"
                    )
                },
            )

        return self.build_result(
            success=True,
            output={
                "artifacts": [
                    "app/main.py",
                    "app/database.py",
                    "app/models.py",
                    "app/orchestrator.py",
                ],
                "summary": (
                    "Core URL-shortener and governed "
                    "workflow implementation prepared."
                ),
            },
        )


class TestingAgent(EngineeringAgent):
    def __init__(self):
        super().__init__("testing_agent")

    def execute(self) -> AgentResult:
        return self.build_result(
            success=True,
            output={
                "test_areas": [
                    "health endpoint",
                    "URL validation",
                    "short URL creation",
                    "redirect behavior",
                    "analytics",
                    "dependency gates",
                    "approval gates",
                    "retry and safe-stop behavior",
                    "dynamic replanning",
                ],
                "recommendation": (
                    "Run python -m pytest -v "
                    "before release approval."
                ),
            },
        )


class DocumentationAgent(EngineeringAgent):
    def __init__(self):
        super().__init__("documentation_agent")

    def execute(self) -> AgentResult:
        return self.build_result(
            success=True,
            output={
                "required_documents": [
                    "README",
                    "architecture overview",
                    "scenario descriptions",
                    "testing approach",
                    "limitations and trade-offs",
                ],
            },
        )