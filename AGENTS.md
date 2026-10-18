# Project Rules

- All functions and classes must have a docstring. Docstrings must be NumPy-style.
- All function/method arguments must be typehint-ed.
- Before a commit is made, all existing tests must pass.

# Tests and Verification

## Draw ASCII diagram graphs
All tests revolve around sample graphs. These must be drawn so that the reader will easily be able to interpret the intended graph and its connections between nodes.

For example, for nodes A->B and B->C, the following could be present in the docstring:

```
Graph (node values are durations):

A [10] ──┐
         ├──> C [5]
B [20] ──┘

C starts when both A and B have finished.
```

## Comment what is changed

In many tests, we assert values expected after changing some nodes or edges.
Comment what this change should be before making the change, so the reader is able to understand by just scanning the comments.

Alternatively, re-draw the ASCII diagram with the changed graph.
