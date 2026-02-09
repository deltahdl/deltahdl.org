"""Contract tests for workflow_dependencies.json.

These tests verify that the workflow dependency graph aligns with the actual
workflow files in .github/workflows/. Per docs/tenets/tests/PRE_DEPLOYMENT_INTEGRATION_TESTS.md,
Layer 1 contract tests validate cross-file compatibility without making AWS calls.
"""

import yaml

from repo_utils import REPO_ROOT


WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


def test_all_graph_keys_have_workflow_files(
    dependency_graph: dict, workflow_files: set
) -> None:
    """Verify each graph key has a corresponding workflow file."""
    graph_keys = set(dependency_graph.keys())
    missing = graph_keys - workflow_files

    assert not missing, (
        f"Graph keys without workflow files: {sorted(missing)}. "
        f"Either create .github/workflows/<key>.yml or remove from graph."
    )


def test_first_path_is_workflow_file(dependency_graph: dict) -> None:
    """Verify first path in each workflow entry is its own .yml file."""
    violations = []

    for key, config in dependency_graph.items():
        paths = config.get("paths", [])
        if not paths:
            violations.append(f"{key}: no paths defined")
            continue

        expected_first = f".github/workflows/{key}.yml"
        actual_first = paths[0]

        if actual_first != expected_first:
            violations.append(
                f"{key}: first path is '{actual_first}', "
                f"expected '{expected_first}'"
            )

    assert not violations, (
        "Workflow path violations:\n  " + "\n  ".join(violations)
    )


def test_all_dependencies_are_valid_keys(dependency_graph: dict) -> None:
    """Verify all depends_on values reference existing graph keys."""
    graph_keys = set(dependency_graph.keys())
    invalid_deps = []

    for key, config in dependency_graph.items():
        for dep in config.get("depends_on", []):
            if dep not in graph_keys:
                invalid_deps.append(f"{key} depends on unknown '{dep}'")

    assert not invalid_deps, (
        "Invalid dependencies:\n  " + "\n  ".join(invalid_deps)
    )


def test_graph_names_match_workflow_yaml_names(
    dependency_graph: dict
) -> None:
    """Verify graph 'name' values match workflow file 'name:' fields."""
    mismatches = []

    for key, config in dependency_graph.items():
        graph_name = config.get("name")
        if not graph_name:
            continue

        workflow_file = WORKFLOWS_DIR / f"{key}.yml"
        if not workflow_file.exists():
            continue  # Covered by other test

        with open(workflow_file, encoding="utf-8") as wf_handle:
            try:
                workflow_yaml = yaml.safe_load(wf_handle)
            except yaml.YAMLError:
                mismatches.append(f"{key}: could not parse YAML")
                continue

        yaml_name = workflow_yaml.get("name")
        if yaml_name != graph_name:
            mismatches.append(
                f"{key}: graph name '{graph_name}' != "
                f"workflow name '{yaml_name}'"
            )

    assert not mismatches, (
        "Name mismatches between graph and workflow files:\n  " +
        "\n  ".join(mismatches)
    )


def test_graph_has_no_cycles(dependency_graph: dict) -> None:
    """Verify the dependency graph is acyclic."""
    # Use DFS to detect cycles
    visited: set = set()
    rec_stack: set = set()
    cycles: list = []

    def has_cycle(node: str, path: list) -> bool:
        visited.add(node)
        rec_stack.add(node)

        for dep in dependency_graph.get(node, {}).get("depends_on", []):
            if dep not in dependency_graph:
                continue  # Invalid dep, covered by other test

            if dep not in visited:
                if has_cycle(dep, path + [dep]):
                    return True
            elif dep in rec_stack:
                cycle_start = path.index(dep) if dep in path else 0
                cycles.append(
                    " -> ".join(path[cycle_start:] + [dep])
                )
                return True

        rec_stack.remove(node)
        return False

    for key in dependency_graph:
        if key not in visited:
            has_cycle(key, [key])

    assert not cycles, (
        "Cyclic dependencies detected:\n  " + "\n  ".join(cycles)
    )
