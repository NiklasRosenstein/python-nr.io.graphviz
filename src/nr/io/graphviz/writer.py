from __future__ import annotations

import typing as t


class GraphvizWriter:
    """A helper class to write Dotviz files."""

    def __init__(self, out: t.TextIO, indent: str = "\t") -> None:
        """
        :param out: The output file to write to.
        :param indent: The string to use for every level of indendation.
        """

        self._out = out
        self._indent = indent
        self._level = 0
        self._edge_type: list[str] = []

    @property
    def _line_prefix(self) -> str:
        return self._level * self._indent

    def _escape(self, name: str) -> str:
        # TODO (@NiklasRosenstein): Improve escaping logic.
        if "\n" in name:
            raise ValueError("Cannot have newline (contained in {name!r})")
        if " " in name or "," in name or "." in name or ":" in name:
            name = f'"{name}"'
        return name

    def _write_attrs(self, attrs: dict[str, str | None]) -> None:
        safe_attrs = {key: value for key, value in attrs.items() if value is not None}
        if safe_attrs:
            self._out.write("[")
            self._out.write(" ".join(f"{self._escape(key)}={self._escape(value)}" for key, value in safe_attrs.items()))
            self._out.write("]")

    def _write_scope(self, keyword: str, name: str | None, attrs: dict[str, str | None]) -> None:
        self._out.write(f"{self._line_prefix}{keyword} ")
        if name is not None:
            self._out.write(self._escape(name) + " ")
        self._out.write("{\n")
        self._level += 1
        for key, value in attrs.items():
            if value is not None:
                self._out.write(f"{self._line_prefix}{self._escape(key)}={self._escape(value)};\n")

    def graph(self, name: str | None = None, **attrs: str | None) -> None:
        """Open a `graph{}` block. Close it by calling :meth:`end`."""
        self._write_scope("graph", name, attrs)
        self._edge_type.append("--")

    def digraph(self, name: str | None = None, **attrs: str | None) -> None:
        """Open a `digraph{}` block. Close it by calling :meth:`end`."""
        self._write_scope("digraph", name, attrs)
        self._edge_type.append("->")

    def subgraph(self, name: str | None = None, **attrs: str | None) -> None:
        """Open a `subgraph{}` block. Close it by calling :meth:`end`."""
        self._write_scope("subgraph", name, attrs)
        self._edge_type.append(self._edge_type[-1])

    def end(self) -> None:
        """Close a previouly opened block. Raises an :class:`AssertionError` if called too many times."""
        assert self._level >= 1, "called end() too many times"
        self._level -= 1
        self._edge_type.pop()
        self._out.write(self._line_prefix + "}\n")

    def set_node_style(self, **attrs: str | None) -> None:
        """Sets the node style in the current block."""
        self._out.write(self._line_prefix + "node ")
        self._write_attrs(attrs)
        self._out.write(";\n")

    def node(self, node_id: str, **attrs: str | None) -> None:
        """Draw a node in the current context."""
        self._out.write(self._line_prefix + self._escape(node_id))
        if attrs:
            self._write_attrs(attrs)
        self._out.write(";\n")

    def edge(self, source: str | t.Sequence[str], target: str | t.Sequence[str], **attrs: str | None) -> None:
        """Draw one or multiple edges in the current contect from source to target. Specifying multiple
        nodes on either side will generate the cross product of edges between all nodes."""
        if isinstance(source, str):
            source = [source]
        if isinstance(target, str):
            target = [target]

        if not source or not target:
            raise ValueError("edge needs at least one source and at least one target")

        def _write_nodes(nodes: t.Sequence[str]) -> None:
            if len(nodes) == 1:
                self._out.write(self._escape(nodes[0]))
            else:
                self._out.write("{")
                self._out.write(" ".join(self._escape(node_id) for node_id in nodes))
                self._out.write("}")

        # TODO (@NiklasRosenstein): Does GraphViz support a syntax for multiple nodes on the left?
        for node_id in source:
            self._out.write(self._line_prefix)
            _write_nodes([node_id])
            self._out.write(f" {self._edge_type[-1]} ")
            _write_nodes(target)
            self._write_attrs(attrs)
            self._out.write(";\n")
