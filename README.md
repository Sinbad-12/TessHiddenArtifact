# TESS: The Hidden Architect

Reconstruct a hidden planetary system from noisy starlight.

Scientific simulation, deterministic inference, and interactive astronomical investigation built with Python 3.12+.

---

## Quick Launch (Interactive Demo UI)

Run the demo web application locally:

```bash
python -m tess_hidden_architect.app
```

Or when installed in editable mode (`pip install -e .`):

```bash
tess-demo
```

### CLI Options

* `--port <PORT>`: Specify local port (default: `8000`).
* `--no-browser`: Start the HTTP mission server without opening the browser automatically.
* `--test`: Run verification smoke test on the simulation, inference, and server pipeline, then exit immediately.

---

## Mission Flow

1. **OBSERVE**: Inspect the observed stellar light curve across the training baseline ($t \le 6.21$ days), containing 2 noisy transits. The future observation window is isolated and withheld.
2. **INFER**: Click **RUN INFERENCE** to construct a baseline-aware period grid, recover the dominant transit period, and compute the transit ephemeris.
3. **PREDICT**: The pipeline automatically extrapolates the linear ephemeris to forecast the next unseen transit center time.
4. **REVEAL**: Click **REVEAL WITHHELD DATA** to unblind the withheld observation window, compare the predicted transit against the actual transit dip, compute the timing error ($\Delta t$), and inspect the revealed ground-truth parameters.

---

## Scientific Assumptions (MVP)

* **Single-planet Keplerian dynamics**: Host star and companion orbit under Newtonian 2-body gravity.
* **Uniform stellar brightness**: Stellar disk has uniform surface brightness across the visible face.
* **Geometric transit overlap**: Exact analytical circle-circle intersection area models partial ingress/egress and flat-bottom full transits.
* **Deterministic measurement noise**: Seeded Gaussian noise ($\sigma = 1.5 \times 10^{-4}$) added to normalized relative flux.

---

## Running Tests

Execute the full automated test suite:

```bash
pytest
```
