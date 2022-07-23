from __future__ import annotations

import http.server
import logging
import subprocess as sp
import tempfile
import webbrowser
from pathlib import Path
from typing import overload

logger = logging.getLogger(__name__)


@overload
def render(graphviz_code: str, format: str, algorithm: str = ...) -> bytes:
    """Renders the *graphviz_code* to an image file of the specified *format*. The default format is `"dot"`."""


@overload
def render(graphviz_code: str, format: str, algorithm: str = ..., *, output_file: Path) -> None:
    """Renders the *graphviz_code* to a file."""


def render(graphviz_code: str, format: str, algorithm: str = "dot", *, output_file: Path | None = None) -> None | bytes:
    command = [algorithm, f"-T{format}"]
    if output_file is not None:
        command += ["-o", str(output_file)]
    try:
        process = sp.run(command, input=graphviz_code.encode(), check=True, capture_output=True)
    except sp.CalledProcessError as exc:
        logger.error("%s: %s", exc, exc.stderr.decode())
        raise
    return process.stdout


def render_to_browser(graphviz_code: str, algorithm: str = "dot") -> None:
    """Renders the *graphviz_code* to an SVG file and opens it in the webbrowser. Blocks until the
    browser opened the page."""

    with tempfile.TemporaryDirectory() as tempdir:
        svg_file = Path(tempdir) / "graph.svg"
        render(graphviz_code, "svg", algorithm, output_file=svg_file)
        server = http.server.HTTPServer(
            ("", 0),
            lambda *args: http.server.SimpleHTTPRequestHandler(*args, directory=tempdir),  # type: ignore[misc]
        )
        webbrowser.open(f"http://localhost:{server.server_port}/graph.svg")
        server.handle_request()
