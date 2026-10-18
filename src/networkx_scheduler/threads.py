import networkx as nx


class ExecutionThread:
    """Add a sequence of tasks to a shared graph as one execution thread.

    Parameters
    ----------
    graph : nx.DiGraph
        The graph tasks are added to. Tasks are stored directly as nodes.
    thread_id : str
        The identifier recorded on every task added by this thread.
    """

    def __init__(self, graph: nx.DiGraph, thread_id: str) -> None:
        self.graph = graph
        self.thread_id = thread_id
        self._last_task = None

    def add_task(self, task_id: str, duration: int) -> str:
        """Add a task node to the thread and return its ID.

        When a previous task exists on this thread, a dependency edge is added
        from that task to the new one. Duplicate task IDs are rejected.

        Parameters
        ----------
        task_id : str
            The unique identifier of the task.
        duration : int
            The duration of the task, stored as a node attribute.

        Returns
        -------
        str
            The ``task_id`` that was added.

        Raises
        ------
        ValueError
            If ``task_id`` already exists as a node in the graph.
        """
        if task_id in self.graph:
            raise ValueError(f"task {task_id!r} already exists in the graph")
        self.graph.add_node(task_id, duration=duration, thread_id=self.thread_id)
        if self._last_task is not None:
            self.graph.add_edge(self._last_task, task_id)
        self._last_task = task_id
        return task_id
