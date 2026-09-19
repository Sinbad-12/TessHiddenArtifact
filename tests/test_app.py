"""Focused tests for the demo UI application and state coordinator."""

from http import HTTPStatus
import json
import threading
import urllib.request

import pytest

from tess_hidden_architect.app.demo import DemoSession
from tess_hidden_architect.app.main import main
from tess_hidden_architect.app.server import create_demo_server


def test_demo_session_lifecycle() -> None:
    """Verify the OBSERVE -> INFER -> PREDICT -> REVEAL lifecycle."""
    session = DemoSession(seed=42)

    # 1. OBSERVE stage
    state0 = session.get_state()
    assert state0["stage"] == "OBSERVED"
    assert not state0["inferred"]
    assert not state0["revealed"]
    assert "observed_data" in state0
    assert state0["observed_data"]["count"] > 1000

    # Withheld data and true system parameters must NOT be present
    assert "withheld_data" not in state0
    assert "hidden_ground_truth" not in state0
    assert "inference" not in state0
    assert "evaluation" not in state0

    # Cannot reveal before inference
    with pytest.raises(RuntimeError):
        session.reveal_withheld()

    # 2. INFER & PREDICT stage
    state1 = session.run_inference()
    assert state1["stage"] == "INFERRED"
    assert state1["inferred"]
    assert not state1["revealed"]
    assert "inference" in state1

    # Inferred parameters present, but withheld data and ground truth still hidden
    assert state1["inference"]["inferred_period_days"] > 0
    assert state1["inference"]["predicted_next_transit_days"] > state1["split_time_days"]
    assert "withheld_data" not in state1
    assert "hidden_ground_truth" not in state1
    assert "evaluation" not in state1

    # 3. REVEAL stage
    state2 = session.reveal_withheld()
    assert state2["stage"] == "REVEALED"
    assert state2["revealed"]
    assert "withheld_data" in state2
    assert "evaluation" in state2
    assert "hidden_ground_truth" in state2

    # Verification of timing error
    timing_err = state2["evaluation"]["timing_error_seconds"]
    assert timing_err >= 0.0
    assert timing_err < 60.0  # Timing error must be less than 1 minute

    # 4. RESET stage
    state3 = session.reset()
    assert state3["stage"] == "OBSERVED"
    assert not state3["inferred"]
    assert not state3["revealed"]
    assert "withheld_data" not in state3
    assert "hidden_ground_truth" not in state3


def test_demo_server_endpoints() -> None:
    """Verify HTTP server responds with correct status codes and JSON payloads."""
    session = DemoSession(seed=42)
    # Pick port 8089 to avoid conflict
    server = create_demo_server(host="127.0.0.1", port=8089, session=session)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    base_url = "http://127.0.0.1:8089"

    try:
        # GET / (HTML frontend)
        with urllib.request.urlopen(f"{base_url}/") as resp:
            assert resp.status == HTTPStatus.OK
            body = resp.read().decode("utf-8")
            assert "TESS: THE HIDDEN ARCHITECT" in body
            assert "Scientific Assumptions" in body

        # GET /api/state
        with urllib.request.urlopen(f"{base_url}/api/state") as resp:
            assert resp.status == HTTPStatus.OK
            data = json.loads(resp.read().decode("utf-8"))
            assert data["stage"] == "OBSERVED"

        # POST /api/infer
        req = urllib.request.Request(f"{base_url}/api/infer", data=b"", method="POST")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == HTTPStatus.OK
            data = json.loads(resp.read().decode("utf-8"))
            assert data["stage"] == "INFERRED"
            assert "inference" in data

        # POST /api/reveal
        req = urllib.request.Request(f"{base_url}/api/reveal", data=b"", method="POST")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == HTTPStatus.OK
            data = json.loads(resp.read().decode("utf-8"))
            assert data["stage"] == "REVEALED"
            assert "evaluation" in data
            assert "hidden_ground_truth" in data

        # POST /api/reset
        req = urllib.request.Request(f"{base_url}/api/reset", data=b"", method="POST")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == HTTPStatus.OK
            data = json.loads(resp.read().decode("utf-8"))
            assert data["stage"] == "OBSERVED"

    finally:
        server.shutdown()
        server.server_close()


def test_app_main_smoke_test() -> None:
    """Verify application main() entry point can start and pass automated smoke test."""
    exit_code = main(["--test", "--port", "8090"])
    assert exit_code == 0
