"""
pool.py

Builds the v6 stimulus pool for Experiment 2 (hidden steps): 240 traces, each
on its own expression, each shown in three hidden-line versions = 720 items.

v6 vs v5 (changed 2026-09-14)
-----------------------------
  * Error position is no longer selected. v5 kept only traces whose error was at
    step 1 or 3. v6 picks, among a learner's usable traces on an expression, one
    with the probability the learner's own policy gives it (uniform over its
    legal moves at each step), so the position is wherever that path puts it.
    The one restriction is that the error lands at step 2, 3 or 4 (below).
  * Difficulty is which line is hidden, relative to the error step k (the
    wrong move turns line s(k-1) into line s(k)):
        easy    hide s(k+1)   the wrong move stays fully visible
        medium  hide s(k-1)   the wrong result is visible, the line before it is not
        hard    hide s(k)     the error's own line
    The expression s0 and the answer s6 always stay visible, so all three
    versions exist only when k is 2, 3 or 4.
  * Every trace appears in all three versions, so difficulty is manipulated
    WITHIN expression. A participant must see at most one version of any
    expression; that is the sampler's job (base_id groups the versions).
  * The observer checks run on every hidden version, not just the full trace.

Design
------
Two categories, one misconception per trace:
  A - the statement NAMES the misconception in the trace   -> agree
  B - the statement names a FOIL                           -> disagree

Grid, 240 traces on 240 distinct expressions, x 3 versions = 720 items:
  A: present(6)            =  6 cells x 20 traces = 120 traces -> 360 items
  B: present(6) x named(5) = 30 cells x  4 traces = 120 traces -> 360 items

So every (misconception, difficulty) cell holds 20 agree and 20 disagree items,
every (present, named, difficulty) B cell holds 4, and the present x named
heatmap (over traces) has 20 on each diagonal cell and 4 off it.

Checks
------
A trace can be an A item when
  * no other single rule could have made its error step, and the named rule's
    statement plainly describes that step (lookalike.py);
  * in every hidden version the observer's marginal on the true rule is above
    A_HIDDEN_MIN (0.5), so "agree" stays the ideal answer.
A trace can be a B item naming foil f when
  * on the full trace f's marginal is at most UNSUPPORTED_MAX (0.35) and f is
    not a look-alike (both as in v5);
  * in every hidden version f's marginal is still at most UNSUPPORTED_MAX, so
    hiding a line never makes the foil plausible.

student_name and belief_statement are placeholders: the frontend reassigns them
per participant.
"""

import json
import random
from collections import Counter
from itertools import combinations

from parser import build_dag
from traces import _next_dags
from misconceptions import dag_to_str
from learner import MISCONCEPTION_FLIPS
from inference import posterior_over_profiles, marginal_rule_probability
from hidden import hidden_posterior
from generator_constrained import generate_expression, error_steps
from find_pairs import sample_trace, N_OPS, POSITIONS
from lookalike import error_step_rules

IDS        = list(MISCONCEPTION_FLIPS.keys())
HYPOTHESES = [()] + [(m,) for m in IDS] + list(combinations(IDS, 2))

A_PER_CELL = 20   # traces per present rule           -> 120 A traces
B_PER_CELL = 4    # traces per (present, named) pair  -> 120 B traces

# the line each difficulty hides, as an offset from the error step k
HIDE_OFFSET  = {'easy': +1, 'medium': -1, 'hard': 0}
DIFFICULTIES = tuple(HIDE_OFFSET)

REFUTED_MAX     = 0.15
UNSUPPORTED_MAX = 0.35
A_HIDDEN_MIN    = 0.5

# a cell that cannot be filled stops the build after this many fruitless draws
MAX_DRY_DRAWS = 300_000

STATEMENT_TEMPLATES = {
    'add_before_mul':        "{name} believes addition should be done before multiplication.",
    'add_before_div':        "{name} believes addition should be done before division.",
    'sub_before_mul':        "{name} believes subtraction should be done before multiplication.",
    'sub_before_div':        "{name} believes subtraction should be done before division.",
    'same_priority_rtl':     "{name} believes operations of the same priority should be worked right to left.",
    'outside_bracket_first': "{name} believes you should calculate outside the brackets before what's inside them.",
}

STUDENT_NAMES = [
    'Noah', 'Maya', 'Liam', 'Ava', 'Ethan', 'Zoe',
    'Mia', 'Lucas', 'Emma', 'Owen', 'Sofia', 'Caleb',
    'Ruby', 'Jonah', 'Isla', 'Felix', 'Nora', 'Dylan',
    'Priya', 'Marcus', 'Elena', 'Theo', 'Jasmine', 'Omar',
]


def hidden_line(k, difficulty):
    """Index of the line a difficulty hides, for an error at step k."""
    return k + HIDE_OFFSET[difficulty]


def _status(marginal):
    if marginal < REFUTED_MAX:
        return 'refuted'
    if marginal <= UNSUPPORTED_MAX:
        return 'unsupported'
    return 'high'


def marginals(trace, hide=None):
    """{rule: observer marginal} with line `hide` hidden (None = every line shown)."""
    if hide is None:
        post = posterior_over_profiles(trace, profiles=HYPOTHESES)
    else:
        post = hidden_posterior(trace, hide, profiles=HYPOTHESES)
    return {r: marginal_rule_probability(post, r) for r in IDS}


def foil_options(trace, true_m):
    """
    ({foil_rule: (status, marginal)}, [look-alikes dropped]) for the rules
    other than true_m, on the FULL trace. A rule is an option when the trace
    does not support it (status is not 'high') and its statement does not
    plainly describe the error step (lookalike.py).
    """
    post = posterior_over_profiles(trace, profiles=HYPOTHESES)
    visible = error_step_rules(trace)
    out, dropped = {}, []
    for f in IDS:
        if f == true_m:
            continue
        marg = marginal_rule_probability(post, f)
        st = _status(marg)
        if st == 'high':
            continue
        if f in visible:
            dropped.append(f)
            continue
        out[f] = (st, marg)
    return out, dropped


def _one_step(line, rules):
    return {dag_to_str(d) for d in _next_dags(build_dag(line), list(rules))}


def a_item_ok(trace, m, k):
    """The error step could be made by m alone, and m's statement plainly describes it."""
    if any(trace[k] in _one_step(trace[k - 1], [r]) for r in IDS if r != m):
        return False
    return m in error_step_rules(trace)


def build(seed=2026, verbose=True):
    rng = random.Random(seed)

    a_need = {m: A_PER_CELL for m in IDS}
    b_need = {(m, f): B_PER_CELL for m in IDS for f in IDS if f != m}
    chosen = []                 # (category, present, named, expression, trace, foil_status, hidden marginals)
    seen_expressions = set()
    draws = Counter()
    drops = Counter()           # why a candidate slot was refused
    dry = 0

    while any(a_need.values()) or any(b_need.values()):
        for m in IDS:
            foils = [f for f in IDS if b_need.get((m, f), 0) > 0]
            if not a_need[m] and not foils:
                continue

            bp = 1.0 if m == 'outside_bracket_first' else 0.6
            expr = generate_expression(n_ops=N_OPS, bracket_prob=bp, rng=rng)
            draws[m] += 1
            dry += 1
            # An expression is used by exactly ONE trace, so a participant who
            # sees one version of each trace never meets an expression twice.
            if expr is None or expr in seen_expressions:
                continue
            trace = sample_trace(expr, m, rng)
            if trace is None:
                continue
            k = error_steps(trace)[0]

            # full-trace checks first; they are cheap
            want_a = a_need[m] > 0
            if want_a and not a_item_ok(trace, m, k):
                drops['A: error step not unique to the rule, or not visibly it'] += 1
                want_a = False
            want_f = {}
            if foils:
                opts, dropped = foil_options(trace, m)
                for f in foils:
                    if f in dropped:
                        drops['B: foil is a look-alike'] += 1
                    elif f in opts:
                        want_f[f] = opts[f][0]
            if not want_a and not want_f:
                continue

            # then every hidden version
            hid = {d: marginals(trace, hidden_line(k, d)) for d in DIFFICULTIES}
            slots = []
            if want_a:
                if all(hid[d][m] > A_HIDDEN_MIN for d in DIFFICULTIES):
                    slots.append((a_need[m] / A_PER_CELL, rng.random(), 'A', m, None))
                else:
                    drops[f'A: a hidden version leaves the true rule at or below {A_HIDDEN_MIN}'] += 1
            for f, st in want_f.items():
                if all(hid[d][f] <= UNSUPPORTED_MAX for d in DIFFICULTIES):
                    slots.append((b_need[(m, f)] / B_PER_CELL, rng.random(), 'B', f, st))
                else:
                    drops[f'B: a hidden version lifts the foil above {UNSUPPORTED_MAX}'] += 1
            if not slots:
                continue

            # the scarcest cell wins (ties random)
            _, _, cat, named, st = max(slots, key=lambda s: s[:2])
            if cat == 'A':
                a_need[m] -= 1
            else:
                b_need[(m, named)] -= 1
            seen_expressions.add(expr)
            chosen.append((cat, m, named, expr, trace, st, hid))
            dry = 0

        if verbose:
            print(f"  remaining traces: A={sum(a_need.values()):3d}  "
                  f"B={sum(b_need.values()):3d}", end='\r')
        if dry > MAX_DRY_DRAWS:
            missing = {k: v for k, v in b_need.items() if v} | \
                      {k: v for k, v in a_need.items() if v}
            raise SystemExit(f"\nstalled with cells unfilled: {missing}")

    if verbose:
        print(f"  generated {len(seen_expressions)} traces "
              f"({sum(draws.values())} expression draws)              ")
        print("  candidate slots refused:")
        for why, n in sorted(drops.items()):
            print(f"    {n:6d}  {why}")

    # emit: A then B, each ordered by present rule then named rule; one item per difficulty
    order = {m: i for i, m in enumerate(IDS)}
    chosen.sort(key=lambda c: (c[0], order[c[1]], order[c[2]]))
    items, n_cat = [], Counter()
    for idx, (cat, m, named, expr, trace, st, hid) in enumerate(chosen):
        base_id = f"{cat}{n_cat[cat]:03d}"
        n_cat[cat] += 1
        name = STUDENT_NAMES[idx % len(STUDENT_NAMES)]
        k = error_steps(trace)[0]
        full = marginals(trace)
        for d in DIFFICULTIES:
            it = {
                'id':                   f"{base_id}-{d[0].upper()}",
                'base_id':              base_id,
                'category':             cat,
                'difficulty':           d,
                'hidden_line':          hidden_line(k, d),
                'error_position':       k,
                'expression':           expr,
                'n_ops':                N_OPS,
                'misconceptions':       [m],
                'num_misconceptions':   1,
                'trace':                trace,
                'probed_misconception': named,
                'statement_correct':    cat == 'A',
                'student_name':         name,
                'belief_statement':     STATEMENT_TEMPLATES[named].format(name=name),
                'io_marginal_full':     round(full[named], 4),
                'io_marginal_hidden':   round(hid[d][named], 4),
            }
            if cat == 'B':
                # recorded, NOT balanced (full trace)
                it['foil_status'] = st
            items.append(it)
    return items


def summarise(items):
    bases = {i['base_id']: i for i in items}
    print(f"\n{len(items)} items, {len(bases)} traces, "
          f"{len({i['expression'] for i in items})} distinct expressions")
    print("  items per category x difficulty, want 120 each:",
          dict(Counter((i['category'], i['difficulty']) for i in items)))
    print("  hidden line per difficulty:",
          {d: dict(sorted(Counter(i['hidden_line'] for i in items if i['difficulty'] == d).items()))
           for d in DIFFICULTIES})

    print(f"\n  error step per present rule (traces; not selected, only kept in {POSITIONS}):")
    for m in IDS:
        c = Counter(b['error_position'] for b in bases.values() if b['misconceptions'][0] == m)
        n = sum(c.values())
        print(f"    {m:24s} n={n:3d}  " +
              "  ".join(f"step {p}: {c[p]:2d} ({c[p]/n:.0%})" for p in POSITIONS))
    c = Counter(b['error_position'] for b in bases.values())
    print(f"    {'all':24s} n={len(bases):3d}  " +
          "  ".join(f"step {p}: {c[p]:2d} ({c[p]/len(bases):.0%})" for p in POSITIONS))

    print(f"\n  present x named heatmap over traces (diagonal = A, want 20; off-diagonal = B, want 4):")
    grid = Counter((b['misconceptions'][0], b['probed_misconception']) for b in bases.values())
    header = "".join(f"{n[:9]:>11s}" for n in IDS)
    print(f"    {'present \\ named':>24s}{header}")
    for p in IDS:
        print(f"    {p:>24s}" + "".join(f"{grid[(p, n)]:>11d}" for n in IDS))

    def stats(v):
        return f"min {min(v):.3f}  mean {sum(v)/len(v):.3f}  max {max(v):.3f}"
    print("\n  observer marginal on the named rule:")
    for cat in 'AB':
        full = [b['io_marginal_full'] for b in bases.values() if b['category'] == cat]
        print(f"    {cat} full trace     {stats(full)}")
        for d in DIFFICULTIES:
            v = [i['io_marginal_hidden'] for i in items if i['category'] == cat and i['difficulty'] == d]
            print(f"    {cat} {d:14s} {stats(v)}")

    print("\n  refutation status, RECORDED not balanced (traces):",
          dict(Counter(b['foil_status'] for b in bases.values() if b['category'] == 'B')))
    look = [b['base_id'] for b in bases.values() if b['category'] == 'B'
            and b['probed_misconception'] in error_step_rules(b['trace'])]
    print(f"  B traces naming a look-alike foil (want 0): {len(look)}")


if __name__ == '__main__':
    print("Building v6 pool...")
    items = build()
    summarise(items)
    with open('stimulus_pool.json', 'w', encoding='utf-8') as fh:
        json.dump(items, fh, ensure_ascii=False, indent=1)
    print("\nwrote stimulus_pool.json")
