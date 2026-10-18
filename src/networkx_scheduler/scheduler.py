import networkx as nx


def schedule(graph):
    for node in graph.nodes:
        duration = graph.nodes[node].get("duration")
        if duration is None:
            raise ValueError(f"node {node!r} is missing a 'duration' attribute")
        if duration < 0:
            raise ValueError(f"node {node!r} has a negative duration")

    order = list(nx.topological_sort(graph))

    task_times = {}
    for node in order:
        duration = graph.nodes[node]["duration"]
        start_time = max(
            (task_times[predecessor][1] for predecessor in graph.predecessors(node)),
            default=0,
        )
        task_times[node] = (start_time, start_time + duration)

    makespan = max((end for _, end in task_times.values()), default=0)
    return task_times, makespan
