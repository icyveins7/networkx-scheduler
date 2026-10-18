import networkx as nx


def _validate_durations(graph: nx.DiGraph) -> None:
    """Validate that every node has a non-negative ``duration`` attribute.

    Raises
    ------
    ValueError
        If any node is missing a ``duration`` attribute or has a negative one.
    """
    for node in graph.nodes:
        duration = graph.nodes[node].get("duration")
        if duration is None:
            raise ValueError(f"node {node!r} is missing a 'duration' attribute")
        if duration < 0:
            raise ValueError(f"node {node!r} has a negative duration")


def _validate_lags(graph: nx.DiGraph) -> None:
    """Validate that every edge has an optional non-negative integer ``lag``.

    Raises
    ------
    ValueError
        If any edge has a ``lag`` attribute that is negative or not an integer.
    """
    for _, _, data in graph.edges(data=True):
        lag = data.get("lag")
        if lag is None:
            continue
        if not isinstance(lag, int) or lag < 0:
            raise ValueError(
                f"edge {data.get('source')!r} -> {data.get('target')!r} has an invalid lag {lag!r}"
            )


def schedule(graph: nx.DiGraph) -> tuple[dict[str, tuple[int, int]], int]:
    """Schedule tasks in ``graph`` respecting dependency edges.

    Parameters
    ----------
    graph : nx.DiGraph
        A directed graph in which each node has a ``duration`` attribute, a
        non-negative integer. An edge ``A -> B`` means ``B`` cannot start until
        ``A`` finishes. An edge may carry an optional non-negative integer
        ``lag`` attribute, added to ``A``'s finish time before ``B`` starts.

    Returns
    -------
    tuple[dict[str, tuple[int, int]], int]
        A ``(task_times, makespan)`` tuple. ``task_times`` maps each node ID to
        its ``(start_time, end_time)``. ``makespan`` is the maximum end time, or
        zero for an empty graph.

    Raises
    ------
    ValueError
        If any node is missing a ``duration`` attribute or has a negative one,
        or if any edge has a negative or non-integer ``lag``.
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
    """Return the longest dependency path by total node duration.

    Parameters
    ----------
    graph : nx.DiGraph
        A directed graph in which each node has a ``duration`` attribute, a
        non-negative integer. An edge ``A -> B`` means ``B`` cannot start until
        ``A`` finishes.

    Returns
    -------
    list[str]
        The task IDs along the path with the greatest summed duration, ordered
        from the first task to the last. Returns an empty list for an empty
        graph. When several paths tie for the longest, any one may be returned.

    Raises
    ------
    ValueError
        If any node is missing a ``duration`` attribute or has a negative one.
    """
    _validate_durations(graph)

    earliest_finish = {}
    best_predecessor = {}

    for node in nx.topological_sort(graph):
        duration = graph.nodes[node]["duration"]
        latest = None
        for predecessor in graph.predecessors(node):
            if earliest_finish[predecessor] > earliest_finish.get(latest, -1):
                latest = predecessor
        best_predecessor[node] = latest
        earliest_finish[node] = duration + (
            earliest_finish[latest] if latest is not None else 0
        )

    tail = max(earliest_finish, key=earliest_finish.get) if earliest_finish else None
    if tail is None:
        return []

    path = [tail]
    while best_predecessor[tail] is not None:
        tail = best_predecessor[tail]
        path.append(tail)
    path.reverse()
    return path
