"""Collect a text summary of recent git activity for AI-drafted entries.

Git output is untrusted input: commit messages, file names, and branch names
are attacker-influenced if a repository accepts contributions from others.
The summary returned here is therefore wrapped in explicit delimiters before
being handed to a model, so the drafting layer can mark it as data rather
than instructions.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

MAX_ACTIVITY_CHARS = 8000
_GIT_TIMEOUT_SECONDS = 15.0

# Limit git to the project folder and leave out mem's own state and lock files.
_PATHSPEC = ["--", ".", ":(exclude).memory"]

_ACTIVITY_OPEN = "<<<GIT_ACTIVITY"
_ACTIVITY_CLOSE = "GIT_ACTIVITY>>>"


class GitActivityError(Exception):
    """Raised when git activity cannot be collected for the given root."""


class GitCommandError(GitActivityError):
    """Raised when git ran but exited non-zero (for example, not a repository)."""


def _run_git(args: list[str], *, root: Path) -> str:
    """Run a git command in `root` and return stripped stdout.

    Raises:
        GitActivityError: If git is missing, times out, or exits non-zero.
    """
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise GitActivityError("git is not installed or not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitActivityError(
            f"git {args[0]} timed out after {_GIT_TIMEOUT_SECONDS:.0f}s"
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip() or f"exit code {exc.returncode}"
        raise GitCommandError(f"git {args[0]} failed: {detail}") from exc
    return completed.stdout.rstrip().lstrip("\n")


def _neutralise_delimiters(text: str) -> str:
    """Stop untrusted text from containing the block delimiters.

    A commit message holding ``GIT_ACTIVITY>>>`` could otherwise appear to
    close the data block early and pass what follows off as instructions.
    """
    return text.replace("GIT_ACTIVITY", "GIT-ACTIVITY")


def collect_git_activity(root: Path, *, since_minutes: int = 720) -> str:
    """Summarise recent git activity in `root`.

    Works when `root` is the repository root or any folder inside it, as in a
    monorepo; activity is then limited to changes under `root`. A repository
    with no commits yet reports its uncommitted files instead.

    Args:
        root: Project folder to inspect.
        since_minutes: How far back to look, in minutes. Defaults to 12 hours,
            which comfortably covers a single working session.

    Returns:
        A combined ``git log`` and ``git diff --stat`` summary wrapped in
        ``<<<GIT_ACTIVITY ... GIT_ACTIVITY>>>`` delimiters, or an explanatory
        message when `root` is not in a repository or git cannot be run.
    """
    try:
        try:
            _run_git(["rev-parse", "--is-inside-work-tree"], root=root)
        except GitCommandError:
            return "(not a git repository, no automatic activity summary available)"
        try:
            _run_git(["rev-parse", "--verify", "--quiet", "HEAD"], root=root)
            has_commits = True
        except GitCommandError:
            has_commits = False

        parts: list[str] = []
        if has_commits:
            log = _run_git(
                ["log", f"--since={since_minutes}.minutes.ago", "--oneline", *_PATHSPEC], root=root
            )
            changes = _run_git(["diff", "--stat", "HEAD", *_PATHSPEC], root=root)
            changes_label = "Uncommitted changes"
            if log:
                parts.append(f"Recent commits:\n{log}")
        else:
            changes = _run_git(
                ["status", "--short", "--untracked-files=all", *_PATHSPEC], root=root
            )
            changes_label = "Uncommitted changes (no commits yet)"
    except GitActivityError as exc:
        return f"(git activity lookup failed: {exc})"

    if changes:
        parts.append(f"{changes_label}:\n{changes}")
    body = "\n\n".join(parts) if parts else "(no recent git activity found)"
    body = _neutralise_delimiters(body)
    if len(body) > MAX_ACTIVITY_CHARS:
        body = body[:MAX_ACTIVITY_CHARS] + "\n... (truncated)"
    return f"{_ACTIVITY_OPEN}\n{body}\n{_ACTIVITY_CLOSE}"
