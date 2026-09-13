# BODMAS Experiment 2: hidden steps

Can people tell which order-of-operations misconception a student holds from the student's written
work when one step of that work is hidden, and does it matter which step?

This repo contains:

- `base-task/`: the learner model, the 240-item base stimulus pool (shared with Experiment 1), its
  builder and verifier, a Bayesian ideal observer, and `hidden.py`, which extends the observer to
  work with hidden steps.
- `analysis-Bayesian/`: ideal-observer figures, including the hidden-step comparison.
- `src/`: the web experiment, built on [Smile](https://smile.gureckislab.org/) (codec-lab fork),
  inherited from Experiment 1 and not yet adapted to hidden steps.

**Start with [`HANDOFF.md`](HANDOFF.md)**, the full orientation: setup, design status, results so
far, and what is next.
