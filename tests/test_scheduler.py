import networkx as nx

from networkx_scheduler.scheduler import schedule


def build_graph() -> nx.DiGraph:
    """Build the sample A/B -> C dependency graph and return it."""
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

    graph.nodes["A"]["duration"] = 3
    task_times, makespan = schedule(graph)

    assert task_times["A"] == (0, 3)
    assert task_times["C"] == (20, 25)
    assert makespan == 25
