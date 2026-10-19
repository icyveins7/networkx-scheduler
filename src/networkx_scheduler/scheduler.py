import math
from numbers import Real

import networkx as nx


def _validate_durations(graph: nx.DiGraph) -> None:
    """Validate that every node has a finite, non-negative real duration.

    Raises
    ------
    ValueError
        If any node is missing a valid ``duration`` attribute.
    """
    for node in graph.nodes:
        duration = graph.nodes[node].get("duration")
        if (
            not isinstance(duration, Real)
            or isinstance(duration, bool)
            or not math.isfinite(duration)
            or duration < 0
        ):
            raise ValueError(f"node {node!r} has an invalid duration {duration!r}")


def _validate_lags(graph: nx.DiGraph) -> None:
    """Validate that every edge has an optional finite, non-negative real lag.

    Raises
    ------
    ValueError
        If any edge has an invalid ``lag`` attribute.
    """
    for source, target, data in graph.edges(data=True):
        lag = data.get("lag", 0)
        if (
            not isinstance(lag, Real)
            or isinstance(lag, bool)
            or not math.isfinite(lag)
            or lag < 0
        ):
            raise ValueError(
                f"edge {source!r} -> {target!r} has an invalid lag {lag!r}"
            )


def schedule(graph: nx.DiGraph) -> tuple[dict[str, tuple[float, float]], float]:
    """Schedule tasks in ``graph`` respecting dependency edges.

    Parameters
    ----------
    graph : nx.DiGraph
        A directed graph in which each node has a finite, non-negative real
        ``duration`` attribute. An edge ``A -> B`` means ``B`` cannot start until
        ``A`` finishes. An edge may carry an optional finite, non-negative real
        ``lag`` attribute, added to ``A``'s finish time before ``B`` starts.

    Returns
    -------
    tuple[dict[str, tuple[float, float]], float]
        A ``(task_times, makespan)`` tuple. ``task_times`` maps each node ID to
        its ``(start_time, end_time)``. ``makespan`` is the maximum end time, or
        zero for an empty graph.

    Raises
    ------
    ValueError
        If any duration is missing or if any duration or lag is invalid.
    """
    _validate_durations(graph)
    _validate_lags(graph)

    order = list(nx.topological_sort(graph))

    task_times = {}
    for node in order:
        duration = graph.nodes[node]["duration"]
        start_time = max(
            (
                task_times[predecessor][1]
                + graph.edges[predecessor, node].get("lag", 0)
                for predecessor in graph.predecessors(node)
            ),
            default=0,
        )
        task_times[node] = (start_time, start_time + duration)

    makespan = max((end for _, end in task_times.values()), default=0)
    return task_times, makespan


def critical_path(graph: nx.DiGraph) -> list[str]:
    """Return the dependency path that determines the scheduled makespan.

    Parameters
    ----------
    graph : nx.DiGraph
        A directed graph with finite, non-negative real node durations and
        optional finite, non-negative real edge lags.

    Returns
    -------
    list[str]
        The task IDs along the path with the greatest combined node durations
        and edge lags, ordered from first task to last. Returns an empty list for
        an empty graph. When several paths tie, any one may be returned.

    Raises
    ------
    ValueError
        If any duration or lag is invalid.
    """
    _validate_durations(graph)
    _validate_lags(graph)

    earliest_finish = {}
    best_predecessor = {}

    for node in nx.topological_sort(graph):
        duration = graph.nodes[node]["duration"]
        latest = None
        latest_arrival = 0
        for predecessor in graph.predecessors(node):
            arrival = (
                earliest_finish[predecessor]
                + graph.edges[predecessor, node].get("lag", 0)
            )
            if latest is None or arrival > latest_arrival:
                latest = predecessor
                latest_arrival = arrival
        best_predecessor[node] = latest
        earliest_finish[node] = duration + latest_arrival

    tail = max(earliest_finish, key=earliest_finish.get) if earliest_finish else None
    if tail is None:
        return []

    path = [tail]
    while best_predecessor[tail] is not None:
        tail = best_predecessor[tail]
        path.append(tail)
    path.reverse()
    return path
