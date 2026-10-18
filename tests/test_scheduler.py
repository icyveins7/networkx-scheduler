import networkx as nx

from networkx_scheduler.scheduler import critical_path, schedule


def build_graph() -> nx.DiGraph:
    """Build the sample A/B -> C dependency graph and return it.

    Graph (node values are durations):

    A [10] ──┐
             ├──> C [5]
    B [20] ──┘

    C starts when both A and B have finished.
    """
    graph = nx.DiGraph()
    graph.add_node("A", duration=10)
    graph.add_node("B", duration=20)
    graph.add_node("C", duration=5)
    graph.add_edge("A", "C")
    graph.add_edge("B", "C")
    return graph


def test_schedule() -> None:
    """Verify task times and makespan for the sample dependency graph."""
    graph = build_graph()
    task_times, makespan = schedule(graph)

    assert task_times["A"] == (0, 10)
    assert task_times["B"] == (0, 20)
    assert task_times["C"] == (20, 25)
    assert makespan == 25

    # A (3) no longer blocks C; C still waits for B (20), so C's times and the makespan are unchanged.
    graph.nodes["A"]["duration"] = 3
    task_times, makespan = schedule(graph)

    assert task_times["A"] == (0, 3)
    assert task_times["C"] == (20, 25)
    assert makespan == 25


def test_critical_path() -> None:
    """Verify the longest-duration path for the sample dependency graph."""
    graph = build_graph()

    path = critical_path(graph)
    assert path == ["B", "C"]
    assert _path_runtime(graph, path) == 25

    # A (3) is no longer the longest predecessor of C, so the critical path stays B -> C.
    graph.nodes["A"]["duration"] = 3
    path = critical_path(graph)
    assert path == ["B", "C"]
    assert _path_runtime(graph, path) == 25

    # Reset A, then shorten B to 5: A -> C (15) is now longer than B -> C (10).
    graph.nodes["A"]["duration"] = 10
    graph.nodes["B"]["duration"] = 5
    path = critical_path(graph)
    assert path == ["A", "C"]
    assert _path_runtime(graph, path) == 15


def test_critical_path_empty() -> None:
    """An empty graph has no critical path."""
    assert critical_path(nx.DiGraph()) == []


def _path_runtime(graph: nx.DiGraph, path: list[str]) -> int:
    """Return the summed node durations along ``path``."""
    return sum(graph.nodes[node]["duration"] for node in path)
