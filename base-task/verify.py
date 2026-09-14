"""
verify.py

Independent checks on stimulus_pool.json (v6: 240 traces x 3 hidden-line
versions = 720 items). Recomputes everything from the model rather than trusting
the builder: traces are re-derived from the expression, error positions
re-tested for expert legality, the observer re-run on the full trace and on
every hidden version, and the look-alike guard re-applied.

The hidden-version observer is recomputed with hidden.multi_hidden_posterior
(forward DP over every intermediate path), NOT the two-step route the builder
uses, so the two implementations check each other.

Design checks: every expression belongs to exactly one trace; every trace has
exactly the three versions easy/medium/hard hiding s(k+1)/s(k-1)/s(k); 120
items per category x difficulty; 20 per (misconception, difficulty, category);
4 per (present, named, difficulty) B cell; the present x named heatmap over
traces is full (20 diagonal, 4 off-diagonal).

For every A trace it also checks the error step itself: no other single rule
could have made it, and the named rule plainly describes it. In every hidden
version the expert must stay eliminated (the visible work still contains an
error) and the key must stay the ideal answer: A marginal above A_HIDDEN_MIN,
B marginal at most UNSUPPORTED_MAX.

It deliberately does NOT check refutation balance: foil_status is recorded but
not a factor. What IS checked is that the stored status matches a fresh
recomputation.

Run after any pool regeneration. Exits non-zero on any failure.
"""

import json
import sys
from collections import Counter, defaultdict

from parser import build_dag
from traces import generate_traces, _next_dags
from misconceptions import dag_to_str
from distance import correct_answer
from learner import MISCONCEPTION_FLIPS
from inference import posterior_over_profiles, marginal_rule_probability
from hidden import multi_hidden_posterior
from generator_constrained import validate_trace, error_steps
from lookalike import error_step_rules
from find_pairs import POSITIONS
from pool import (HYPOTHESES, STATEMENT_TEMPLATES, N_OPS, UNSUPPORTED_MAX, A_HIDDEN_MIN,
                  HIDE_OFFSET, DIFFICULTIES, _status, A_PER_CELL, B_PER_CELL)

IDS = list(MISCONCEPTION_FLIPS.keys())
N_TRACES = {'A': A_PER_CELL * len(IDS), 'B': B_PER_CELL * len(IDS) * (len(IDS) - 1)}
SHARED = ('category', 'expression', 'n_ops', 'misconceptions', 'num_misconceptions', 'trace',
          'error_position', 'probed_misconception', 'statement_correct', 'student_name',
          'belief_statement', 'io_marginal_full', 'foil_status')
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def one_step(line, rules):
    """Every line a learner holding `rules` could write next."""
    return {dag_to_str(d) for d in _next_dags(build_dag(line), list(rules))}


def check_trace(it):
    """The v5 checks, on the full trace of one base trace."""
    tag = it['base_id']
    trace, expr = it['trace'], it['expression']
    true_m = it['misconceptions'][0]

    check(it['num_misconceptions'] == 1 and len(it['misconceptions']) == 1,
          f"{tag}: not exactly one misconception")
    check(len(trace) == N_OPS + 1, f"{tag}: trace has {len(trace)} lines, want {N_OPS+1}")
    check(trace[0] == expr, f"{tag}: trace does not start at the expression")
    check(len(trace[-1].split()) == 1, f"{tag}: trace does not reduce to a number")
    check(validate_trace(trace), f"{tag}: trace fails validate_trace ({trace})")

    legal = generate_traces(build_dag(expr), [true_m])
    check(trace in legal, f"{tag}: trace is not generable by {true_m}")

    errs = error_steps(trace)
    check(errs == [it['error_position']],
          f"{tag}: error steps {errs}, declared position {it['error_position']}")
    check(it['error_position'] in POSITIONS,
          f"{tag}: error at step {it['error_position']}, outside {POSITIONS}")

    expert = generate_traces(build_dag(expr), [])
    check(trace[-1] != correct_answer(expert), f"{tag}: learner answer equals the expert answer")

    probed = it['probed_misconception']
    check(it['belief_statement'] == STATEMENT_TEMPLATES[probed].format(name=it['student_name']),
          f"{tag}: belief statement does not match probed rule / name")

    post = posterior_over_profiles(trace, profiles=HYPOTHESES)
    marg = marginal_rule_probability(post, probed)
    check(abs(marg - it['io_marginal_full']) < 1e-3,
          f"{tag}: stored full marginal {it['io_marginal_full']} != recomputed {marg:.4f}")
    visible = error_step_rules(trace)
    if it['category'] == 'A':
        check(probed == true_m and it['statement_correct'] is True,
              f"{tag}: A trace probed {probed} but holds {true_m}")
        check(marg > 0.99, f"{tag}: A trace true-rule marginal {marg:.3f} too low")
        check('foil_status' not in it, f"{tag}: A trace carries a foil_status")
        for k in errs:
            others = [r for r in IDS if r != true_m and trace[k] in one_step(trace[k - 1], [r])]
            check(not others, f"{tag}: error step {k} could also be made by {others}")
        check(probed in visible,
              f"{tag}: error step does not visibly show {probed} (reads as {sorted(visible)})")
    else:
        check(probed != true_m and it['statement_correct'] is False,
              f"{tag}: B trace probes its own true rule")
        check(marg <= UNSUPPORTED_MAX,
              f"{tag}: foil marginal {marg:.3f} above {UNSUPPORTED_MAX}, not a clean foil")
        check(_status(marg) == it['foil_status'],
              f"{tag}: foil_status {it['foil_status']} but marginal {marg:.3f} says {_status(marg)}")
        check(probed not in visible,
              f"{tag}: foil {probed} plainly describes the error step (look-alike)")


def check_version(it):
    """One hidden version: which line, and what the observer makes of it."""
    tag = it['id']
    k, h, d = it['error_position'], it['hidden_line'], it['difficulty']
    check(d in HIDE_OFFSET, f"{tag}: unknown difficulty {d}")
    check(h == k + HIDE_OFFSET.get(d, 99), f"{tag}: {d} hides s{h}, error at step {k}")
    check(1 <= h <= N_OPS - 1, f"{tag}: hides s{h}; s0 and the answer must stay visible")
    check(it['id'] == f"{it['base_id']}-{d[0].upper()}", f"{tag}: id does not match base_id/difficulty")

    post = multi_hidden_posterior(it['trace'], {h}, profiles=HYPOTHESES)
    check(post[()] == 0.0, f"{tag}: with s{h} hidden an expert could have written the visible work")
    marg = marginal_rule_probability(post, it['probed_misconception'])
    check(abs(marg - it['io_marginal_hidden']) < 1e-3,
          f"{tag}: stored hidden marginal {it['io_marginal_hidden']} != recomputed {marg:.4f}")
    if it['category'] == 'A':
        check(marg > A_HIDDEN_MIN, f"{tag}: true-rule marginal {marg:.3f} with s{h} hidden, "
                                   f"not above {A_HIDDEN_MIN}")
    else:
        check(marg <= UNSUPPORTED_MAX, f"{tag}: foil marginal {marg:.3f} with s{h} hidden, "
                                       f"above {UNSUPPORTED_MAX}")
    return marg


def main(path='stimulus_pool.json'):
    items = json.load(open(path, encoding='utf-8'))
    print(f"verifying {len(items)} items from {path}\n")

    check(len({i['id'] for i in items}) == len(items), "duplicate item ids")
    groups = defaultdict(list)
    for it in items:
        groups[it['base_id']].append(it)

    hidden_marg = defaultdict(list)
    for base_id, grp in groups.items():
        check(sorted(i['difficulty'] for i in grp) == sorted(DIFFICULTIES),
              f"{base_id}: versions {[i['difficulty'] for i in grp]}, want one of each {DIFFICULTIES}")
        for f in SHARED:
            check(len({json.dumps(i.get(f)) for i in grp}) == 1,
                  f"{base_id}: field {f} differs between its versions")
        check_trace(grp[0])
        for it in grp:
            hidden_marg[(it['category'], it['difficulty'])].append(check_version(it))

    # every expression belongs to exactly one trace, so no one can meet it twice
    per_expr = defaultdict(set)
    for it in items:
        per_expr[it['expression']].add(it['base_id'])
    check(all(len(v) == 1 for v in per_expr.values()),
          f"expressions shared between traces: {[e for e, v in per_expr.items() if len(v) > 1][:3]}")

    bases = [g[0] for g in groups.values()]
    nt = Counter(b['category'] for b in bases)
    check(nt == Counter(N_TRACES), f"traces per category {dict(nt)}, want {N_TRACES}")

    cd = Counter((i['category'], i['difficulty']) for i in items)
    want = Counter({(c, d): N_TRACES[c] for c in 'AB' for d in DIFFICULTIES})
    check(cd == want, f"category x difficulty {dict(cd)}, want {dict(want)}")

    mdc = Counter((i['misconceptions'][0], i['difficulty'], i['category']) for i in items)
    check(len(mdc) == 36 and set(mdc.values()) == {A_PER_CELL},
          f"misconception x difficulty x category cells: {len(mdc)} cells, "
          f"sizes {sorted(set(mdc.values()))}, want 36 x {A_PER_CELL}")

    cb = Counter((i['misconceptions'][0], i['probed_misconception'], i['difficulty'])
                 for i in items if i['category'] == 'B')
    check(len(cb) == 90 and set(cb.values()) == {B_PER_CELL},
          f"B cells (present x named x difficulty): {len(cb)} cells, sizes {sorted(set(cb.values()))}")

    grid = Counter((b['misconceptions'][0], b['probed_misconception']) for b in bases)
    empty = [(p, n) for p in IDS for n in IDS if grid[(p, n)] == 0]
    check(not empty, f"heatmap has {len(empty)} empty cells: {empty[:5]}")
    check({grid[(m, m)] for m in IDS} == {A_PER_CELL}, "diagonal cells not all 20")
    check({grid[(p, n)] for p in IDS for n in IDS if p != n} == {B_PER_CELL},
          "off-diagonal cells not all 4")

    if fails:
        print(f"FAILED - {len(fails)} problem(s):")
        for f in fails[:25]:
            print("  -", f)
        if len(fails) > 25:
            print(f"  ... and {len(fails)-25} more")
        sys.exit(1)

    def stats(v):
        return f"min {min(v):.3f}  mean {sum(v)/len(v):.3f}  max {max(v):.3f}"
    nums = [int(n) for b in bases for line in b['trace']
            for n in line.replace('(', ' ').replace(')', ' ').split()
            if n.lstrip('-').isdigit()]
    pos = Counter(b['error_position'] for b in bases)
    print("ALL CHECKS PASSED")
    print(f"  {len(items)} items = {len(bases)} traces x 3 versions; "
          f"{len(per_expr)} expressions, each in one trace")
    print(f"  every trace: {N_OPS} steps, exactly 1 expert-illegal move; error step "
          + ", ".join(f"{p}: {pos[p]}" for p in POSITIONS))
    print(f"  versions: easy hides s(k+1), medium s(k-1), hard s(k); s0 and the answer always shown")
    print(f"  cells: 120 per category x difficulty, 20 per misconception x difficulty x category, "
          f"4 per B present x named x difficulty")
    print(f"  A error steps: only the named rule could make them, and it visibly shows")
    print(f"  B foils: none plainly describes the error step (look-alike guard)")
    print(f"  every hidden version: expert eliminated, key still the observer's answer")
    for c in 'AB':
        for d in DIFFICULTIES:
            print(f"    {c} {d:7s} named-rule marginal {stats(hidden_marg[(c, d)])}")
    print(f"  numbers shown: min {min(nums)}  max {max(nums)}  (no negatives, no decimals, no zero)")


if __name__ == '__main__':
    main()
