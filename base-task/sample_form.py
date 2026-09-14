"""
sample_form.py

Python twin of src/user/utils/sampleForm.js, which is what the live experiment
runs. Both draw one participant's 24 trials the same way with the same PRNG
(mulberry32), so a given seed yields the identical form in both languages.
Change one, change the other, then rerun the checks here.

The form (Experiment 2, v6 pool, decided 2026-09-14):
  * 4 trials per misconception (the rule present in the trace), 8 per
    difficulty, 12 agree / 12 disagree; 2 agree / 2 disagree within each
    misconception and 4 / 4 within each difficulty
  * 4 trials per misconception cannot split evenly over 3 difficulties, so each
    misconception fills one row of ROWS: one difficulty twice (once agree, once
    disagree), the other two once. Which misconception gets which row is a
    random permutation per participant. Smile has no cross-participant counter,
    so the 36 misconception x difficulty x statement cells balance in
    expectation, not exactly every 6 participants.
  * each cell is a random pool item of that (misconception, difficulty,
    category); a disagree item brings the foil it was built with, so which
    wrong statement a trial names is left to the draw (as in Experiment 1)
  * no trace (base_id) twice, so no expression twice
  * trial order shuffled; the 24 STUDENT_NAMES shuffled, one per trial; the
    belief statement is rewritten to match

    python3 sample_form.py            # checks over 500 seeds
    python3 sample_form.py --dump N   # [id, name] per trial for seeds 0..N-1, as JSON
"""

import json
import sys
from collections import Counter

from learner import MISCONCEPTION_FLIPS
from pool import STATEMENT_TEMPLATES, STUDENT_NAMES, DIFFICULTIES

IDS = list(MISCONCEPTION_FLIPS.keys())
# (difficulty, category) cells per row; A = agree, B = disagree
ROWS = [
    [('easy', 'A'), ('easy', 'B'), ('medium', 'A'), ('hard', 'B')],
    [('easy', 'A'), ('easy', 'B'), ('medium', 'B'), ('hard', 'A')],
    [('easy', 'A'), ('medium', 'A'), ('medium', 'B'), ('hard', 'B')],
    [('easy', 'B'), ('medium', 'A'), ('medium', 'B'), ('hard', 'A')],
    [('easy', 'A'), ('medium', 'B'), ('hard', 'A'), ('hard', 'B')],
    [('easy', 'B'), ('medium', 'A'), ('hard', 'A'), ('hard', 'B')],
]
_M = 0xFFFFFFFF


class Mulberry32:
    """Bit-exact port of makeRng in sampleForm.js (32-bit unsigned arithmetic)."""

    def __init__(self, seed):
        self.s = seed & _M

    def next(self):
        self.s = (self.s + 0x6D2B79F5) & _M
        s = self.s
        t = ((s ^ (s >> 15)) * (1 | s)) & _M
        t = ((t + (((t ^ (t >> 7)) * (61 | t)) & _M)) & _M) ^ t
        return ((t ^ (t >> 14)) & _M) / 4294967296

    def choice(self, arr):
        return arr[int(self.next() * len(arr))]

    def shuffle(self, arr):
        for i in range(len(arr) - 1, 0, -1):
            j = int(self.next() * (i + 1))
            arr[i], arr[j] = arr[j], arr[i]
        return arr


def sample_form(pool, seed):
    rng = Mulberry32(seed)
    rows = rng.shuffle(list(IDS))          # rows[r] = the misconception filling ROWS[r]
    form, used = [], set()
    for r, m in enumerate(rows):
        for d, cat in ROWS[r]:
            members = [it for it in pool if it['misconceptions'][0] == m and it['difficulty'] == d
                       and it['category'] == cat and it['base_id'] not in used]
            it = rng.choice(members)
            used.add(it['base_id'])
            form.append(it)
    rng.shuffle(form)
    names = rng.shuffle(list(STUDENT_NAMES))
    return [dict(it, student_name=names[i],
                 belief_statement=names[i] + it['belief_statement'][len(it['student_name']):])
            for i, it in enumerate(form)]


def check(pool, n_seeds=500):
    by_id = {it['id']: it for it in pool}
    row_cells = [Counter(r) for r in ROWS]
    cells, uses, named_foil, doubled = Counter(), Counter(), Counter(), Counter()
    for seed in range(n_seeds):
        form = sample_form(pool, seed)
        assert len(form) == 24, (seed, len(form))
        assert len({it['id'] for it in form}) == 24, seed
        assert len({it['base_id'] for it in form}) == 24, seed
        assert len({it['expression'] for it in form}) == 24, seed
        assert sorted(it['student_name'] for it in form) == sorted(STUDENT_NAMES), seed

        assert Counter(it['misconceptions'][0] for it in form) == Counter({m: 4 for m in IDS}), seed
        assert Counter(it['difficulty'] for it in form) == Counter({d: 8 for d in DIFFICULTIES}), seed
        assert sum(it['statement_correct'] for it in form) == 12, seed
        assert Counter((it['misconceptions'][0], it['category']) for it in form) == \
            Counter({(m, c): 2 for m in IDS for c in 'AB'}), seed
        assert Counter((it['difficulty'], it['category']) for it in form) == \
            Counter({(d, c): 4 for d in DIFFICULTIES for c in 'AB'}), seed
        # every misconception fills a different row of the table
        used_rows = []
        for m in IDS:
            pattern = Counter((it['difficulty'], it['category'])
                              for it in form if it['misconceptions'][0] == m)
            assert pattern in row_cells, (seed, m, pattern)
            used_rows.append(row_cells.index(pattern))
            doubled[(m, next(d for d in DIFFICULTIES if pattern[(d, 'A')] and pattern[(d, 'B')]))] += 1
        assert sorted(used_rows) == list(range(6)), seed
        # every statement named exactly twice as the CORRECT one
        assert Counter(it['probed_misconception'] for it in form
                       if it['category'] == 'A') == Counter({m: 2 for m in IDS}), seed

        for it in form:
            assert it['belief_statement'] == STATEMENT_TEMPLATES[it['probed_misconception']].format(
                name=it['student_name']), (seed, it['id'])
            src = by_id[it['id']]
            assert all(it[k] == src[k] for k in src if k not in ('student_name', 'belief_statement'))
        cells.update((it['misconceptions'][0], it['difficulty'], it['category']) for it in form)
        uses.update(it['id'] for it in form)
        foil = Counter(it['probed_misconception'] for it in form if it['category'] == 'B')
        named_foil[max(foil.values())] += 1

    print(f"ALL CHECKS PASSED over {n_seeds} seeds")
    print("  every form: 24 trials, 24 distinct traces and expressions, each of the 24 names once;")
    print("  4 per misconception, 8 per difficulty, 12 agree / 12 disagree, 2/2 within each")
    print("  misconception, 4/4 within each difficulty; each misconception fills a different row;")
    print("  each statement named exactly twice as the correct one; statements rewritten")
    exp = n_seeds * 24 / 36
    print(f"  36 misconception x difficulty x statement cells over all forms: "
          f"min {min(cells.values())}  max {max(cells.values())}  (expect about {exp:.0f} each)")
    print(f"  times each misconception got each difficulty doubled: "
          f"min {min(doubled.values())}  max {max(doubled.values())}  (expect about {n_seeds / 3:.0f})")
    exp = n_seeds * 24 / len(pool)
    print(f"  item usage: min {min(uses[i] for i in by_id)}  max {max(uses.values())}  "
          f"(expect about {exp:.0f} each; {sum(1 for i in by_id if uses[i] == 0)} items never drawn)")
    print(f"  most times one statement is named as a WRONG statement, per form: "
          f"{dict(sorted(named_foil.items()))}")


if __name__ == '__main__':
    pool = json.load(open('stimulus_pool.json', encoding='utf-8'))
    if len(sys.argv) > 2 and sys.argv[1] == '--dump':
        print(json.dumps([[[it['id'], it['student_name']] for it in sample_form(pool, s)]
                          for s in range(int(sys.argv[2]))]))
    else:
        check(pool)
