"""
natural_position.py

Where does the error land when error position is NOT selected?

For each misconception, draw expressions exactly as pool.py does (n_ops=6,
bracket_prob 1.0 for outside_bracket_first else 0.6), let the learner walk every
path it could take, each move chosen uniformly among its legal moves (the
observer's pi_L), and classify every path by its expert-illegal steps. Also runs
the same analysis on the expressions of the current stimulus_pool.json.

This is the measurement behind v6's decision to stop selecting step 1 or 3
(HANDOFF.md §5). Run from base-task/:  python3 natural_position.py [N per misconception]
"""

import json
import random
import sys
from collections import Counter, defaultdict

from parser import build_dag
from traces import generate_traces
from distance import correct_answer
from generator_constrained import generate_expression, validate_trace, error_steps
from learner import MISCONCEPTION_FLIPS
from find_pairs import learner_paths, N_OPS

IDS = list(MISCONCEPTION_FLIPS)
POS = range(1, N_OPS + 1)


def classify(expr, m):
    """
    ({outcome: prob mass}, {positions with a usable trace}) for one expression.
    Outcomes: 'no_error', 'multi_error', 'stuck', or ('one', k, usable) for exactly
    one error at step k; usable = wrong answer and displayable.
    """
    try:
        dag = build_dag(expr)
        right = correct_answer(generate_traces(dag, []))
        paths = learner_paths(dag, [m])
    except Exception:
        return None, None
    mass, support = Counter(), set()
    for t, p in paths:
        if len(t) != N_OPS + 1 or len(t[-1].split()) != 1:
            mass['stuck'] += p
            continue
        errs = error_steps(t)
        if not errs:
            mass['no_error'] += p
        elif len(errs) > 1:
            mass['multi_error'] += p
        else:
            ok = t[-1] != right and validate_trace(t)
            mass[('one', errs[0], ok)] += p
            if ok:
                support.add(errs[0])
    return mass, support


def summarise(label, masses, supports):
    n = len(masses)
    tot = Counter()
    for ms in masses:
        tot.update(ms)
    avg = {k: v / n for k, v in tot.items()}
    one_ok = {k: avg.get(('one', k, True), 0) for k in POS}
    q = sum(one_ok.values())
    # a pool built with no position filter: draw an expression, keep it if it has
    # any usable trace, then pick one of those by the learner's own move probabilities
    per = []
    for ms in masses:
        qe = sum(ms.get(('one', k, True), 0) for k in POS)
        if qe > 0:
            per.append({k: ms.get(('one', k, True), 0) / qe for k in POS})
    return dict(
        label=label, n=n,
        no_error=avg.get('no_error', 0), multi_error=avg.get('multi_error', 0),
        stuck=avg.get('stuck', 0),
        one_error_unusable=sum(avg.get(('one', k, False), 0) for k in POS),
        qualifying=q,
        support={k: sum(k in s for s in supports) / n for k in POS},
        build={k: (sum(d[k] for d in per) / len(per) if per else 0) for k in POS},
        n_usable_expr=len(per))


def fmt(r):
    return "\n".join([
        f"{r['label']}  (n={r['n']} expressions)",
        f"  learner paths: no error {r['no_error']:.1%} | 2+ errors {r['multi_error']:.1%} | "
        f"1 error but same answer/undisplayable {r['one_error_unusable']:.1%} | "
        f"stuck {r['stuck']:.1%} | usable single error {r['qualifying']:.1%}",
        "  share of expressions that CAN yield a usable error at step k: " +
        "  ".join(f"s{k}={r['support'][k]:.1%}" for k in POS),
        f"  pool without position filter ({r['n_usable_expr']} usable expressions): " +
        "  ".join(f"s{k}={r['build'][k]:.1%}" for k in POS)])


if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    rng = random.Random(2026)
    all_m, all_s = [], []
    for m in IDS:
        bp = 1.0 if m == 'outside_bracket_first' else 0.6
        ms_list, sp_list, seen = [], [], set()
        while len(ms_list) < N:
            expr = generate_expression(n_ops=N_OPS, bracket_prob=bp, rng=rng)
            if expr is None or expr in seen:
                continue
            seen.add(expr)
            ms, sp = classify(expr, m)
            if ms is None:
                continue
            ms_list.append(ms)
            sp_list.append(sp)
        print(fmt(summarise(m, ms_list, sp_list)), "\n", flush=True)
        all_m += ms_list
        all_s += sp_list
    print(fmt(summarise('ALL misconceptions pooled', all_m, all_s)), "\n")

    pool = json.load(open('stimulus_pool.json', encoding='utf-8'))
    traces = {}
    for it in pool:
        traces.setdefault(it.get('base_id', it['id']), it)
    by_pos = defaultdict(lambda: ([], []))
    for it in traces.values():
        ms, sp = classify(it['expression'], it['misconceptions'][0])
        by_pos[it['error_position']][0].append(ms)
        by_pos[it['error_position']][1].append(sp)
    print("=== current pool traces: the learner on the SAME expression, left to itself ===")
    for p in sorted(by_pos):
        print(fmt(summarise(f"pool traces with the error at step {p}", *by_pos[p])), "\n")
