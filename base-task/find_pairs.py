"""
find_pairs.py

The trace finder the pool builder calls. For one expression and misconception it
lists the learner's USABLE traces: the trace finishes, has exactly one
expert-illegal move, reaches a different answer from the expert, and passes
validate_trace(). Each trace comes with the probability the learner's own
policy gives it (uniform over its legal moves at every step, the observer's
pi_L), so the builder can pick one the way the learner would produce it.

v6 (2026-09-14): error position is no longer SELECTED to be step 1 or 3.
POSITIONS is now the range the error may fall in, (2, 3, 4): the steps where all
three hidden-line versions exist (see pool.py). Within that range the position
is whatever path the learner takes. natural_position.py measures the spread.

(The file name is historical: v3/v4 searched for matched step-1/step-3 pairs.)
"""

from parser import build_dag
from traces import generate_traces, _next_dags, _is_done
from misconceptions import dag_to_str
from distance import correct_answer
from generator_constrained import validate_trace, error_steps

N_OPS     = 6
POSITIONS = (2, 3, 4)


def learner_paths(dag, misconceptions, _memo=None):
    """
    [(trace, prob)] for every path the learner can take from dag, where prob is
    the product of 1/|legal moves| over its steps. Same enumeration, and the
    same order, as traces.generate_traces.
    """
    memo = {} if _memo is None else _memo
    cur = dag_to_str(dag)
    if cur in memo:
        return memo[cur]
    if _is_done(dag):
        out = [([cur], 1.0)]
    else:
        nexts = _next_dags(dag, misconceptions)
        if not nexts:
            out = [([cur], 1.0)]   # stuck: partial trace
        else:
            w = 1.0 / len(nexts)
            out = [([cur] + sub, w * p)
                   for nd in nexts for sub, p in learner_paths(nd, misconceptions, memo)]
    memo[cur] = out
    return out


def usable_traces(expr, misconception, positions=POSITIONS, n_ops=N_OPS):
    """
    [(prob, trace)] for every usable trace whose single error is at a step in
    `positions`. prob is the learner's probability of taking that path, not
    renormalised.
    """
    try:
        dag = build_dag(expr)
        right = correct_answer(generate_traces(dag, []))
        paths = learner_paths(dag, [misconception])
    except Exception:
        return []
    out = []
    for t, p in paths:
        if len(t) != n_ops + 1 or len(t[-1].split()) != 1:
            continue
        if t[-1] == right or not validate_trace(t):
            continue
        errs = error_steps(t)
        if len(errs) == 1 and errs[0] in positions:
            out.append((p, t))
    return out


def sample_trace(expr, misconception, rng, positions=POSITIONS):
    """
    One usable trace, drawn with the learner's own path probabilities
    (renormalised over the usable ones), or None if the expression has none.
    """
    cands = usable_traces(expr, misconception, positions)
    if not cands:
        return None
    r = rng.random() * sum(p for p, _ in cands)
    for p, t in cands:
        r -= p
        if r <= 0:
            return t
    return cands[-1][1]
