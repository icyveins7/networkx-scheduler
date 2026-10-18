import networkx as nx

from networkx_scheduler.scheduler import schedule
from networkx_scheduler.threads import ExecutionThread


def build_graph() -> nx.DiGraph:
    """Build the multi-thread sample graph and return it.

    Graph (node values are durations):

    A [10] ──> B [5] ──┐
                       ├──> D [3]
    C [20] ────────────┘

    Threads T1: A -> B  and  T2: C -> D.
    The cross-thread dependency B -> D forces D to wait for both.
    """
    graph = nx.DiGraph()

    thread1 = ExecutionThread(graph, "T1")
    thread1.add_task("A", duration=10)
    thread1.add_task("B", duration=5)

    thread2 = ExecutionThread(graph, "T2")
    thread2.add_task("C", duration=20)
    thread2.add_task("D", duration=3)

    graph.add_edge("B", "D")
    return graph


def test_thread_attributes() -> None:
    """Verify each node records its thread and duration."""
    graph = build_graph()

    assert graph.nodes["A"]["thread_id"] == "T1"
    assert graph.nodes["A"]["duration"] == 10
    assert graph.nodes["B"]["thread_id"] == "T1"
    assert graph.nodes["B"]["duration"] == 5
    assert graph.nodes["C"]["thread_id"] == "T2"
    assert graph.nodes["C"]["duration"] == 20
    assert graph.nodes["D"]["thread_id"] == "T2"
    assert graph.nodes["D"]["duration"] == 3


def test_thread_edges() -> None:
    """Verify intra-thread and cross-thread dependency edges."""
    graph = build_graph()

    assert graph.has_edge("A", "B")
    assert graph.has_edge("C", "D")
    assert graph.has_edge("B", "D")


def test_scheduler_task_times() -> None:
    """Verify the scheduler honors per-thread and cross-thread dependencies."""
    graph = build_graph()
    task_times, makespan = schedule(graph)

    assert task_times["A"] == (0, 10)
    assert task_times["B"] == (10, 15)
    assert task_times["C"] == (0, 20)
    assert task_times["D"] == (20, 23)
    assert makespan == 23


def test_threads_run_independently() -> None:
    """Verify threads start independently until a dependency forces sync.

    A (T1) and C (T2) both start at time 0: finishing C does not delay A, and
    finishing A and B does not delay C. Only D must wait, because the explicit
    cross-thread edge B -> D requires it to synchronize with B.
    """
    graph = build_graph()
    task_times, _ = schedule(graph)

    assert task_times["A"][0] == 0
    assert task_times["C"][0] == 0
    assert task_times["D"][0] == 20


def test_duplicate_task_id_rejected() -> None:
    """Adding a task ID that already exists must raise instead of overwrite."""
    graph = nx.DiGraph()
    thread = ExecutionThread(graph, "T1")
    thread.add_task("A", duration=10)

    try:
        thread.add_task("A", duration=5)
    except ValueError as exc:
        assert "A" in str(exc)
        return
    raise AssertionError("duplicate task ID was not rejected")
