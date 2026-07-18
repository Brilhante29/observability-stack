"""Container entry point for the API and benchmark commands."""

from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        from .benchmark import main as benchmark_main

        sys.argv = [sys.argv[0], *sys.argv[2:]]
        benchmark_main()
        return

    import uvicorn

    uvicorn.run("observability_stack.api:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
