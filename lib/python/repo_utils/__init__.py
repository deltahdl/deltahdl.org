"""Repository path utilities."""

from pathlib import Path


def _find_repo_root_from_path(start_path: Path) -> Path:
    """Find the repository root starting from a given path.

    Args:
        start_path: The path to start searching from.

    Returns:
        The repository root path.

    Raises:
        RuntimeError: If no .git directory is found in any parent.
    """
    for parent in [start_path] + list(start_path.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repository root")


def find_repo_root() -> Path:
    """Find the repository root by looking for .git directory."""
    return _find_repo_root_from_path(Path(__file__).resolve())


REPO_ROOT = find_repo_root()


def extract_brace_block(content: str, start_pos: int) -> str:
    """Extract content of a brace-delimited block starting at the given position.

    Args:
        content: The full text content to extract from.
        start_pos: Position of the opening brace in content.

    Returns:
        The block content including braces, or remaining content if no closing brace found.
    """
    brace_count = 0
    for i, char in enumerate(content[start_pos:]):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                return content[start_pos:start_pos + i + 1]
    return content[start_pos:]
