"""Application entry point for TESS: The Hidden Architect demo."""

from __future__ import annotations

import argparse
import sys
import threading
import time
import webbrowser

from tess_hidden_architect.app.demo import DemoSession
from tess_hidden_architect.app.server import create_demo_server


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="TESS: The Hidden Architect — Interactive Demo"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to serve the local demo on (default: 8000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to bind the server to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the browser upon launch",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run startup and smoke validation test, then terminate immediately",
    )
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> int:
    """Run the local demo application server."""
    args = parse_args(argv)

    session = DemoSession()
    server = create_demo_server(host=args.host, port=args.port, session=session)
    url = f"http://{args.host}:{args.port}/"

    if args.test:
        # Run automated smoke test
        print("TESS Hidden Architect: verifying simulation & inference pipeline...")
        state0 = session.get_state()
        assert state0["stage"] == "OBSERVED"
        assert not state0["inferred"]
        assert "withheld_data" not in state0
        assert "hidden_ground_truth" not in state0

        state1 = session.run_inference()
        assert state1["stage"] == "INFERRED"
        assert state1["inferred"]
        assert "inference" in state1
        assert "withheld_data" not in state1
        assert "hidden_ground_truth" not in state1

        state2 = session.reveal_withheld()
        assert state2["stage"] == "REVEALED"
        assert state2["revealed"]
        assert "withheld_data" in state2
        assert "evaluation" in state2
        assert "hidden_ground_truth" in state2
        timing_error = state2["evaluation"]["timing_error_seconds"]
        print(f"Pipeline verification PASSED: timing error = {timing_error:.2f} s")
        server.server_close()
        return 0

    print("=" * 65)
    print("       TESS: THE HIDDEN ARCHITECT — MISSION DEMO")
    print("=" * 65)
    print("Reconstruct a hidden planetary system from noisy starlight.")
    print(f"Local Mission Server running at: {url}")
    print("Story Flow: OBSERVE -> INFER -> PREDICT -> REVEAL")
    print("Press Ctrl+C to terminate.")
    print("=" * 65)

    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down mission server...")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
