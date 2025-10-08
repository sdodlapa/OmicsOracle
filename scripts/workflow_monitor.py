#!/usr/bin/env python3
"""
Advanced GitHub Actions Workflow Monitor for OmicsOracle

Step 1: Enhanced Base Classes and Enums
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class WorkflowStatus(Enum):
    """Enhanced workflow status tracking"""

    SUCCESS = "success"
    FAILURE = "failure"
    IN_PROGRESS = "in_progress"
    QUEUED = "queued"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"


class AlertSeverity(Enum):
    """Alert severity levels for notifications"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class WorkflowRun:
    """Enhanced workflow run representation"""

    id: int
    name: str
    status: str
    conclusion: Optional[str]
    created_at: str
    updated_at: str
    html_url: str
    head_branch: str
    head_sha: str
    repository: str
    run_number: int = 0
    event: str = "push"
    actor: Optional[str] = None
    duration_seconds: Optional[int] = None

    @property
    def workflow_status(self) -> WorkflowStatus:
        """Convert GitHub status to our enhanced enum"""
        if self.conclusion == "success":
            return WorkflowStatus.SUCCESS
        elif self.conclusion == "failure":
            return WorkflowStatus.FAILURE
        elif self.conclusion == "timed_out":
            return WorkflowStatus.TIMED_OUT
        elif self.conclusion == "cancelled":
            return WorkflowStatus.CANCELLED
        elif self.conclusion == "skipped":
            return WorkflowStatus.SKIPPED
        elif self.status == "in_progress":
            return WorkflowStatus.IN_PROGRESS
        elif self.status == "queued":
            return WorkflowStatus.QUEUED
        else:
            return WorkflowStatus.QUEUED


@dataclass
class ErrorPattern:
    """Represents a common error pattern with fix suggestions"""

    pattern: str
    category: str
    severity: AlertSeverity
    fix_suggestion: str
    count: int = 0


@dataclass
class MonitoringAlert:
    """Alert for workflow issues"""

    severity: AlertSeverity
    message: str
    repository: str
    workflow_name: str
    timestamp: datetime
    run_url: Optional[str] = None


class OmicsOracleWorkflowMonitor:
    """Enhanced workflow monitoring system for OmicsOracle"""

    def __init__(self) -> None:
        """Initialize with OmicsOracle-specific configuration"""
        # Repository configuration for OmicsOracle multi-remote setup
        self.repositories = {
            "origin": "sdodlapati3/OmicsOracle",
            "sanjeeva": "SanjeevaRDodlapati/OmicsOracle",
            "backup": "sdodlapa/OmicsOracle",
        }

        # Create results directory
        self.results_dir = Path("workflow_analytics")
        self.results_dir.mkdir(exist_ok=True)

        # Error patterns specific to OmicsOracle
        self.error_patterns = [
            ErrorPattern(
                pattern="ASCII.*violation",
                category="ASCII Compliance",
                severity=AlertSeverity.ERROR,
                fix_suggestion="Run scripts/ascii_enforcer.py --fix",
            ),
            ErrorPattern(
                pattern="ModuleNotFoundError",
                category="Dependencies",
                severity=AlertSeverity.ERROR,
                fix_suggestion="Update requirements.txt and reinstall",
            ),
            ErrorPattern(
                pattern="would reformat",
                category="Code Formatting",
                severity=AlertSeverity.WARNING,
                fix_suggestion="Run black --line-length 79 .",
            ),
            ErrorPattern(
                pattern="import.*incorrectly sorted",
                category="Import Sorting",
                severity=AlertSeverity.WARNING,
                fix_suggestion="Run isort --profile black .",
            ),
        ]

        self.alerts: List[MonitoringAlert] = []

    def _run_gh_command(self, command: str) -> Optional[str]:
        """Execute GitHub CLI command safely"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"GitHub CLI error: {result.stderr.strip()}")
                return None
        except subprocess.TimeoutExpired:
            print(f"GitHub CLI command timed out: {command}")
            return None
        except (subprocess.SubprocessError, OSError) as e:
            print(f"Error running GitHub CLI: {e}")
            return None

    def _calculate_duration(self, start_time: str, end_time: str) -> Optional[int]:
        """Calculate workflow duration in seconds"""
        try:
            start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            return int((end - start).total_seconds())
        except (ValueError, TypeError):
            return None

    def fetch_workflow_runs(self, repo_name: str, limit: int = 10) -> List[WorkflowRun]:
        """Fetch recent workflow runs with enhanced parsing"""
        command = (
            f"gh run list --repo {repo_name} --limit {limit} "
            f"--json databaseId,name,status,conclusion,"
            f"createdAt,updatedAt,url,headBranch,headSha,number,event"
        )

        output = self._run_gh_command(command)
        if not output:
            return []

        try:
            runs_data = json.loads(output)
            workflow_runs = []

            for run_data in runs_data:
                duration = None
                if run_data.get("updatedAt") and run_data.get("createdAt"):
                    duration = self._calculate_duration(run_data["createdAt"], run_data["updatedAt"])

                workflow_run = WorkflowRun(
                    id=run_data["databaseId"],
                    name=run_data["name"],
                    status=run_data["status"],
                    conclusion=run_data.get("conclusion"),
                    created_at=run_data["createdAt"],
                    updated_at=run_data["updatedAt"],
                    html_url=run_data["url"],
                    head_branch=run_data["headBranch"],
                    head_sha=run_data["headSha"],
                    repository=repo_name,
                    run_number=run_data.get("number", 0),
                    event=run_data.get("event", "push"),
                    actor=None,  # Not available in current API
                    duration_seconds=duration,
                )
                workflow_runs.append(workflow_run)

            return workflow_runs

        except json.JSONDecodeError as e:
            print(f"Failed to parse workflow data: {e}")
            return []

    def analyze_workflow_errors(self, workflow_run: WorkflowRun) -> List[str]:
        """Analyze workflow for errors and failures"""
        if workflow_run.workflow_status == WorkflowStatus.SUCCESS:
            return []

        command = f"gh run view {workflow_run.id} --repo " f"{workflow_run.repository} --log-failed"

        log_output = self._run_gh_command(command)
        if not log_output:
            return ["Unable to fetch workflow logs"]

        error_lines = []
        for line in log_output.split("\n"):
            line = line.strip()
            if any(keyword in line.lower() for keyword in ["error:", "failed:", "exception:", "traceback"]):
                error_lines.append(line)

        return error_lines[:10]  # Limit to first 10 errors

    def categorize_errors(self, error_list: List[str]) -> Dict[str, List[str]]:
        """Categorize errors using defined patterns"""
        error_categories: Dict[str, List[str]] = {}

        for error_msg in error_list:
            matched = False
            for pattern in self.error_patterns:
                if pattern.pattern.lower() in error_msg.lower():
                    if pattern.category not in error_categories:
                        error_categories[pattern.category] = []
                    error_categories[pattern.category].append(error_msg)
                    pattern.count += 1
                    matched = True
                    break

            if not matched:
                if "Unknown" not in error_categories:
                    error_categories["Unknown"] = []
                error_categories["Unknown"].append(error_msg)

        return error_categories

    def generate_fix_recommendations(self, error_categories: Dict[str, List[str]]) -> Dict[str, str]:
        """Generate automated fix recommendations"""
        fix_recommendations = {}

        for category in error_categories.keys():
            for pattern in self.error_patterns:
                if pattern.category == category:
                    fix_recommendations[category] = pattern.fix_suggestion
                    break

            if category not in fix_recommendations:
                if category == "Unknown":
                    fix_recommendations[category] = "Review logs manually and check documentation"
                else:
                    fix_recommendations[category] = f"Address {category} issues in the codebase"

        return fix_recommendations


if __name__ == "__main__":
    print("[OK] Step 3 Complete: Enhanced monitoring core")
    monitor = OmicsOracleWorkflowMonitor()
    print(f"[DATA] Configured repositories: {list(monitor.repositories.keys())}")
    print(f"[TOOL] Error patterns defined: {len(monitor.error_patterns)}")

    # Test workflow fetching for first repository
    first_repo = list(monitor.repositories.values())[0]
    print(f"[SEARCH] Testing workflow fetch for: {first_repo}")

    runs = monitor.fetch_workflow_runs(first_repo, limit=3)
    print(f"[CHART] Found {len(runs)} recent workflow runs")

    if runs:
        latest_run = runs[0]
        status_value = latest_run.workflow_status.value
        print(f"[REFRESH] Latest run: {latest_run.name} ({status_value})")

        if latest_run.workflow_status != WorkflowStatus.SUCCESS:
            errors_found = monitor.analyze_workflow_errors(latest_run)
            if errors_found:
                print(f"[ERROR] Found {len(errors_found)} error(s)")
                categories = monitor.categorize_errors(errors_found)
                recommendations = monitor.generate_fix_recommendations(categories)
                rec_count = len(recommendations)
                print(f"[TOOL] Generated {rec_count} fix recommendation(s)")
            else:
                print("[OK] No errors found in logs")
    else:
        print("[INFO]  No workflow runs found")
