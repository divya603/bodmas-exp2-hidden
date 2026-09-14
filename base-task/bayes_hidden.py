"""
bayes_hidden.py

Runs the ideal observer over every pool item (v6: 720 = 240 traces x 3 hidden
versions) with that item's line hidden, and saves its response next to the
fully observed one. The hidden-step counterpart of bayes.py.

Each item's difficulty fixes the hidden line relative to its error step k:
  easy    s(k+1)   the wrong move stays fully visible
  medium  s(k-1)   the wrong result is visible, the line before it is not
  hard    s(k)     the error's own line

The observer sees only what a participant would see. With line s_h hidden the
two likelihood factors touching it collapse into a marginal over every value
the hidden state could have taken (see hidden.py).

Use `probed_marginal` as the observer's response, not a MAP profile, for the
same reason as in the fully observed case.
"""

import json
from collections import defaultdict

from hidden import hidden_posterior, visible_trace
from inference import posterior_over_profiles, marginal_rule_probability
from pool import HYPOTHESES, IDS, DIFFICULTIES

POOL = 'stimulus_pool.json'
OUT = 'bayes_per_item_hidden.json'


def run(pool_path=POOL, out_path=OUT):
    items = json.load(open(pool_path, encoding='utf-8'))
    full = {}
    rows = []
    for it in items:
        probed = it['probed_misconception']
        if it['base_id'] not in full:
            post = posterior_over_profiles(it['trace'], profiles=HYPOTHESES)
            full[it['base_id']] = marginal_rule_probability(post, probed)
        base = full[it['base_id']]
        h = it['hidden_line']
        post = hidden_posterior(it['trace'], h, profiles=HYPOTHESES)
        marg = marginal_rule_probability(post, probed)
        rows.append({
            'id': it['id'],
            'base_id': it['base_id'],
            'category': it['category'],
            'difficulty': it['difficulty'],
            'error_position': it['error_position'],
            'hidden_line': h,
            'n_lines_shown': len(visible_trace(it['trace'], h)),
            'true_misconception': it['misconceptions'][0],
            'probed_misconception': probed,
            'statement_correct': it['statement_correct'],
            'marginal_full': round(base, 6),
            'probed_marginal': round(marg, 6),
            'delta_vs_full': round(marg - base, 6),
            'observer_agrees': bool(marg > 0.5),
            'observer_correct': bool((marg > 0.5) == it['statement_correct']),
        })
    json.dump(rows, open(out_path, 'w', encoding='utf-8'), indent=1)
    return rows


def _stats(v):
    v = sorted(v)
    return f"min {v[0]:.3f}  mean {sum(v)/len(v):.3f}  max {v[-1]:.3f}"


def summarise(rows):
    by = defaultdict(list)
    for r in rows:
        by[(r['difficulty'], r['category'])].append(r)

    print(f"ideal observer on {len(rows)} items, each with its own line hidden "
          f"(22 hypotheses, epsilon=0)\n")
    print(f"{'difficulty':>12s} {'acc':>9s}   {'category A marginal':>34s}   {'category B marginal':>34s}")
    a0 = [r['marginal_full'] for r in rows if r['category'] == 'A' and r['difficulty'] == 'easy']
    b0 = [r['marginal_full'] for r in rows if r['category'] == 'B' and r['difficulty'] == 'easy']
    print(f"  {'(no hiding)':>10s} {'':>9s}   {_stats(a0):>34s}   {_stats(b0):>34s}")
    for d in DIFFICULTIES:
        a, b = by[(d, 'A')], by[(d, 'B')]
        acc = sum(r['observer_correct'] for r in a + b)
        print(f"  {d:>10s} {acc:>4d}/{len(a)+len(b):<4d}   "
              f"{_stats([r['probed_marginal'] for r in a]):>34s}   "
              f"{_stats([r['probed_marginal'] for r in b]):>34s}")

    print("\nitems the hiding actually MOVES (|delta| > 1e-6)")
    for d in DIFFICULTIES:
        cells = []
        for cat in 'AB':
            grp = by[(d, cat)]
            cells.append(f"{cat} {sum(1 for r in grp if abs(r['delta_vs_full']) > 1e-6):3d}/{len(grp)}")
        print(f"  {d:>10s}   " + "   ".join(cells))

    print("\ncategory A, mean marginal on the PRESENT rule by misconception x difficulty")
    print(f"  {'':24s}" + "".join(f"{d:>9s}" for d in DIFFICULTIES))
    for m in IDS:
        row = []
        for d in DIFFICULTIES:
            v = [r['probed_marginal'] for r in by[(d, 'A')] if r['true_misconception'] == m]
            row.append(f"{sum(v)/len(v):9.3f}")
        print(f"  {m:24s}" + "".join(row))

    worst = sorted((r for r in rows if r['category'] == 'A'), key=lambda r: r['probed_marginal'])[:8]
    print("\nlowest category-A marginals (where hiding bites):")
    for r in worst:
        print(f"  {r['id']} {r['true_misconception']:>22s} err@{r['error_position']} "
              f"{r['difficulty']:>6s} hides s{r['hidden_line']} -> {r['probed_marginal']:.3f}")


if __name__ == '__main__':
    rows = run()
    summarise(rows)
    print(f"\nwrote {OUT}")
