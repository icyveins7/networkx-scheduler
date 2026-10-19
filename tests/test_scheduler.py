import networkx as nx

import pytest

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


def test_critical_path_with_edge_lag() -> None:
    """Verify edge lag can make a shorter-duration branch critical.

    Graph (node values are durations):

    A [10] -----------\
                       >-- C [1]
    B [5] --lag=10---/

    A reaches C at 10, while B reaches C at 15 because of its lag. The critical
    path is therefore B -> C even though B has the shorter node duration.
    """
    graph = nx.DiGraph()
    graph.add_node("A", duration=10)
    graph.add_node("B", duration=5)
    graph.add_node("C", duration=1)
    graph.add_edge("A", "C")
    graph.add_edge("B", "C", lag=10)

    path = critical_path(graph)
    assert path == ["B", "C"]
    assert _path_runtime(graph, path) == 16
    assert schedule(graph)[1] == 16


def test_critical_path_empty() -> None:
    """An empty graph has no critical path."""
    assert critical_path(nx.DiGraph()) == []


def test_schedule_without_lag() -> None:
    """Verify existing behavior when an edge has no lag.

    Graph (node values are durations):

    A [10] ──┐
             ├──> B [5]

    A runs 0-10; B starts when A finishes and runs 10-15; makespan is 15.
    """
    graph = nx.DiGraph()
    graph.add_node("A", duration=10)
    graph.add_node("B", duration=5)
    graph.add_edge("A", "B")

    task_times, makespan = schedule(graph)
    assert task_times["A"] == (0, 10)
    assert task_times["B"] == (10, 15)
    assert makespan == 15


def test_schedule_with_edge_lag() -> None:
    """Verify scheduling when an edge carries a lag.

    Graph (node values are durations):

    A [10] --lag=3--\
                    >-- B [5]

    A runs 0-10, then a 3-unit delay, so B starts at 13 and finishes at 18.
    """
    graph = nx.DiGraph()
    graph.add_node("A", duration=10)
    graph.add_node("B", duration=5)
    graph.add_edge("A", "B", lag=3)

    task_times, makespan = schedule(graph)
    assert task_times["A"] == (0, 10)
    assert task_times["B"] == (13, 18)
    assert makespan == 18


def test_schedule_with_fractional_duration_and_lag() -> None:
    """Schedule tasks with subsecond durations and lag.

    Graph (node values are durations):

    A [1.25] --lag=0.5--> B [2.75]

    A runs from 0 to 1.25. B starts at 1.75 and finishes at 4.5.
    """
    graph = nx.DiGraph()
    graph.add_node("A", duration=1.25)
    graph.add_node("B", duration=2.75)
    graph.add_edge("A", "B", lag=0.5)

    task_times, makespan = schedule(graph)
    assert task_times["A"] == (0, 1.25)
    assert task_times["B"] == (1.75, 4.5)
    assert makespan == 4.5
    assert critical_path(graph) == ["A", "B"]


def test_schedule_multiple_predecessors_with_lags() -> None:
    """Verify scheduling with multiple predecessors and differing lags.

    Graph (node values are durations):

    A [10] --lag=3--\
                   >-- C [5]
    B [20] --lag=2--/

    C starts at max(10 + 3, 20 + 2) = 22, finishes at 27; makespan is 27.
    """
    graph = nx.DiGraph()
    graph.add_node("A", duration=10)
    graph.add_node("B", duration=20)
    graph.add_node("C", duration=5)
    graph.add_edge("A", "C", lag=3)
    graph.add_edge("B", "C", lag=2)

    task_times, makespan = schedule(graph)
    assert task_times["A"] == (0, 10)
    assert task_times["B"] == (0, 20)
    assert task_times["C"] == (22, 27)
    assert makespan == 27


@pytest.mark.parametrize(
    "duration",
    [None, -1, "one", float("inf"), float("nan"), True],
)
def test_schedule_invalid_durations(duration: object) -> None:
    """Reject missing, non-numeric, non-finite, negative, and Boolean durations.

    Graph (node value is the invalid duration):

    A [duration]
    """
    graph = nx.DiGraph()
    graph.add_node("A", duration=duration)

    with pytest.raises(ValueError):
        schedule(graph)
    with pytest.raises(ValueError):
        critical_path(graph)


def test_schedule_invalid_lags() -> None:
    """Reject negative and non-numeric lags.

    Graph (node values are durations):

    A [10] --invalid lag--> B [5]
    """
    # Negative lag
    graph = nx.DiGraph()
    graph.add_node("A", duration=10)
    graph.add_node("B", duration=5)
    graph.add_edge("A", "B", lag=-1)
    with pytest.raises(ValueError):
        schedule(graph)
    with pytest.raises(ValueError):
        critical_path(graph)

    # Non-numeric lag
    graph = nx.DiGraph()
    graph.add_node("A", duration=10)
    graph.add_node("B", duration=5)
    graph.add_edge("A", "B", lag="one")
    with pytest.raises(ValueError):
        schedule(graph)
    with pytest.raises(ValueError):
        critical_path(graph)


def _path_runtime(graph: nx.DiGraph, path: list[str]) -> float:
    """Return the summed node durations and edge lags along ``path``."""
    duration = sum(graph.nodes[node]["duration"] for node in path)
    lag = sum(
        graph.edges[source, target].get("lag", 0)
        for source, target in zip(path, path[1:])
    )
    return duration + lag
