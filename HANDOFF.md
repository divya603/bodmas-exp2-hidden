# BODMAS Experiment 2 (hidden steps): Handoff

A complete, from-scratch orientation for a model picking this up cold. Read this instead of any
conversation history.

> **⚠️ STANDING INSTRUCTION TO EVERY AGENT: keep this file current.** As you complete work (new
> scripts, figures, findings, decisions, payments, deploys), update the relevant sections either as
> you go or at the latest before your session ends. This file is the single source of truth; the
> next session must be able to pick up cold from it alone.

---

## 0. What this repo is

**Repo:** `divya603/bodmas-exp2-hidden` (GitHub). **Experiment 2 of 3.** It asks whether people can
tell which order-of-operations misconception a student holds from the student's written work when
**one line of that work is hidden**, and whether it matters where the hidden line sits relative to
the student's error.

**Status (2026-09-14): design DECIDED, stimulus pool REBUILT (v6), frontend NOT yet rebuilt.**
- **All of this is on branch `hidden-difficulty`** (pushed to origin). `main` still holds the initial
  import (Experiment 1's v5 pool, errors at step 1 or 3). Merge to `main` only once the frontend is
  done and the user agrees: pushing `main` deploys the live experiment.
- Done on the branch: the v6 pool (720 items, §3), verified; the ideal observer run on it (§4, §5);
  the natural-error-position analysis (§5).
- Not done: the 24-trial sampler, the hidden-line rendering, practice items, instructions and quiz
  (§9). `src/user/data/stimulus_pool.json` is still Experiment 1's v5 pool and the frontend still
  shows every line. The Bayesian figures are stale (§6).
Nothing has been deployed from this repo, and no human or LLM data exist.

Provenance: seeded from `divya603/bodmas-exp1-position` at commit `862dea1` (its pool, model,
observer, figures and finished Experiment 1 frontend), plus the hidden-step code from the archive repo
`divya603/bodmas-model`, branch `pilot-v5-hidden` (commit `89dfe97`). The v6 pool is built here and
is no longer a copy of Experiment 1's, but the **model code** (parser, traces, learner, generator) still
is: a model change in Experiment 1 does not reach this repo automatically.

### The design (decided with the user, 2026-09-14)
- **Error position is NOT selected.** Each trace is drawn the way the learner would produce it (§3),
  so the error lands wherever that path puts it, restricted to steps 2 to 4 (below). Experiment 1
  forced it to step 1 or 3; §5 has the measurement that motivated dropping that.
- **Difficulty = which line is hidden, relative to the error step k** (the wrong move turns line
  s(k-1) into line s(k)). Exactly one line is hidden per trial:

  | difficulty | hides | what the participant loses |
  |---|---|---|
  | easy | s(k+1) | the line after the error; the wrong move stays fully visible |
  | medium | s(k-1) | the line before the error; the wrong result is visible, not the line it came from |
  | hard | s(k) | the error's own line |

  The expression s0 and the answer s6 always stay visible, so all three versions exist only when k
  is 2, 3 or 4. The easy < medium < hard ordering is the user's hypothesis about people; the ideal
  observer barely distinguishes them (§5).
- **Pool:** 240 traces x 3 hidden versions = 720 items, 360 agree / 360 disagree. Difficulty is
  WITHIN expression (the same work in all three versions). No no-hide control: the effect of hiding
  vs not hiding can only be measured against Experiment 1.
- **Per participant: 24 trials, every one on a different expression** (never two versions of one
  trace). 4 per misconception, 8 per difficulty, 12 agree / 12 disagree; within each misconception
  2 agree / 2 disagree; within each difficulty 4 / 4. 36 trials (one per cell) was rejected by the
  user as too long to keep concentration.
- Misconception x difficulty cannot be balanced inside 24 trials (4 trials per misconception do not
  split three ways). So each misconception gets one difficulty twice (once agree, once disagree) and
  the other two once:

  | row | easy | medium | hard |
  |---|---|---|---|
  | misconception 1 | agree + disagree | agree | disagree |
  | misconception 2 | agree + disagree | disagree | agree |
  | misconception 3 | agree | agree + disagree | disagree |
  | misconception 4 | disagree | agree + disagree | agree |
  | misconception 5 | agree | disagree | agree + disagree |
  | misconception 6 | disagree | agree | agree + disagree |

  The sampler rotates which misconception sits in which row (cyclically over 6), so over every 6
  participants each of the 36 misconception x difficulty x statement cells appears exactly 4 times.
- **Proposed by Claude, not yet explicitly confirmed by the user:** choose the named wrong rules so
  each rule is named in exactly 2 disagree trials per participant. Then every belief statement
  appears 4 times per participant (2 true, 2 false) and its wording never hints at the answer.
- **Still open:** how the hidden line is displayed (an ellipsis line, "a step is not shown", nothing)
  and whether participants are told a line is missing.

### The task (one trial)
A participant sees a **math expression**, a **student's step-by-step work** containing exactly one
order-of-operations misconception, with **one line hidden**, and a **belief statement** claiming the
student holds a particular misconception. They rate on a **6-point Likert scale** (1 = Strongly
Disagree, 6 = Strongly Agree) how well the statement explains the work, NOT whether the final answer
is right. Scoring collapses the rating at **>= 4 = agree**.

### The 6 misconceptions
| id | meaning |
|---|---|
| `add_before_mul` | does `+` before an adjacent `×` |
| `add_before_div` | does `+` before an adjacent `÷` |
| `sub_before_mul` | does `-` before an adjacent `×` |
| `sub_before_div` | does `-` before an adjacent `÷` |
| `same_priority_rtl` | evaluates equal-priority ops right-to-left instead of left-to-right |
| `outside_bracket_first` | must finish everything outside a bracket before resolving its contents |

`outside_bracket_first` is a **preference**, not a permission: a learner holding it may not enter a
bracket while literal-literal work remains outside. It is the only rule that REMOVES options rather
than adding them, and that asymmetry is behind almost every place hiding a step matters (§5).

---

## 1. First-time setup on a new machine or clone

Run these in order, once, right after cloning:
```bash
git clone https://github.com/divya603/bodmas-exp2-hidden.git
cd bodmas-exp2-hidden
git checkout hidden-difficulty   # the v6 work lives here until it is merged
npm run get_secrets          # fetch the 5 gitignored lab files from codec-lab/smile-secrets
npm run upload_config        # push the app + deploy config into THIS repo's GitHub secrets
npm run setup_project        # npm install + git hooks (post-commit / post-checkout)
pip install -r base-task/requirements.txt
(cd base-task && python3 verify.py)   # must print ALL CHECKS PASSED
npm run force_deploy         # first deployment (gh workflow run deploy.yml on the current branch)
```

What each secrets step does:
- **`npm run get_secrets`** (`scripts/get_secrets.sh`) downloads, via `gh api`, from the private
  lab repo `codec-lab/smile-secrets`: `env/.env.local` (Firebase app config), `env/.env.deploy.local`
  (lab-server SSH details), `env/.env.docs.local`, `firebase/.service-account-key.json` (needed by
  `npm run getdata`), and `scripts/get_recruitment_data.mjs` (needed by `npm run getrecruitment`).
  All five are gitignored and must never be committed. Needs `gh` logged in with access to that repo
  (divya603 has access, checked 2026-09-13; otherwise ask Mark).
- **`npm run upload_config`** (`scripts/update_config.sh`) pushes `env/.env.local` as
  `SECRET_APP_CONFIG` and every line of `env/.env.deploy.local` as its own secret
  (`EXP_DEPLOY_HOST`, `EXP_DEPLOY_KEY`, `EXP_DEPLOY_PATH`, `EXP_DEPLOY_PORT`, `EXP_DEPLOY_USER`,
  `SLACK_WEBHOOK_URL`, `SLACK_WEBHOOK_ERROR_URL`) to whatever repo `origin` points at. Only needed
  once per repo, not once per clone.

**Status as of 2026-09-14: secrets NOT yet uploaded to this repo, so nothing has been deployed.**
`deploy.yml` handles missing secrets gracefully: its `check-secrets` job SKIPS the `deploy` job and
the run still shows GREEN, with a "secrets are not configured, skipping deploy" notice. After
`force_deploy`, confirm with `gh run list` then `gh run view <id>` that the **`deploy` job itself
ran** (build and rsync, about a minute), and look for the lab Slack message. Update this status
line once done.

⚠️ Until the hidden-step frontend exists (§9), a deployment of this repo serves **Experiment 1's
task** (every step visible) under Experiment 2's URL. Do not share the URL with anyone.

Node: `.node_version` pins 20.18.1; Node 24 has been working locally. If `npm install` misbehaves,
switch with `nvm use 20`.

What changes automatically because this is a separate repo:
- **The deploy URL.** Path is `/<owner>/<repo>/<branch>/`, so main deploys to
  `https://www.codec-lab.org/divya603/bodmas-exp2-hidden/main/`, and the short codename URL is derived
  from the same path (printed in the deploy log). Any Prolific link must point here. Once secrets
  exist, pushing `hidden-difficulty` deploys a separate staging site at
  `.../bodmas-exp2-hidden/hidden-difficulty/`.
- **Where the data lands.** Firestore's `projectRef` (`src/core/config.js`) is derived from the
  deploy path, so this experiment's data is stored under its own key and cannot mix with
  Experiment 1's.

---

## 2. Repository map

```
base-task/         The model, the pool, the ideal observer, and the hidden-step inference. §3 to §5.
analysis-Bayesian/ Ideal-observer figures. §6 (stale on this branch).
src/               The Smile/Vue web experiment (inherited from Experiment 1). §7.
scripts/           Smile deploy/data scripts.
public/            consent-form.pdf, debrief.pdf served by the frontend.
env/, firebase/    Smile config. env/.env is tracked defaults; env/*.local are secrets (untracked).
data/              Pulled participant data lands here. Participant files are gitignored.
docs/ tests/ plugins/ analysis/ plans/   Smile framework infrastructure, not ours. Leave alone.
```

---

## 3. The model and the pool (`base-task/`)

### Model core
- **`dag.py`** FlatDAG representation of an expression (atoms + op nodes, shared references).
- **`parser.py`** `build_dag(expr)`. Folds signed-number literals so re-parsing intermediate trace
  strings matches `_eval`'s representation.
- **`pattern_matcher.py`** classifies 3-node "windows" into Tables 1 to 6.
- **`learner.py`** `MISCONCEPTION_FLIPS`: each misconception's bidirectional `to_true`/`to_false`
  validity flips. A learner is a list of misconception ids.
- **`valid_actions.py`**, **`traces.py`** `generate_traces(dag, misconceptions)` simulates a learner
  and returns ALL step-by-step traces it could produce. `_next_dags(dag, L)` is the set of states
  learner L may legally reach in one step. Includes the `is_zero_divide` guard.
- **`distance.py`** `correct_answer()`, `tree_edges()`, `diagnostic_traces()`.
- **`generator.py`** the original random expression generator (imported by the constrained one).
- **`inference.py`** `posterior_over_profiles(trace)` and `marginal_rule_probability()`; see §4.
- `Bodmas_Modeling.pdf` is the written description of the model.

### How the error position comes about
A misconception only changes which moves the learner thinks are legal in particular windows (e.g.
`add_before_mul` makes `+` fireable before an adjacent `×` and that `×` unfireable). At each step the
learner may take ANY of its legal moves, so the same learner on the same expression can make its one
error at any step from 1 to 5, depending on the order it works in. **Position is a property of the
path, not of the expression or the rule.** (Step 6 can never hold the error: one operation is left
and its only move is legal.) v5 selected paths with the error at step 1 or 3; v6 does not select.

### The constrained generator and helpers
- **`generator_constrained.py`** draws numbers constructively left to right with one step of
  operator lookahead: subtraction operands ordered, division exact with a proper divisor (no `÷ 1`,
  no `n ÷ n`), `×` operands <= 6, no run of more than 2 equal numbers. Also holds:
  - `validate_trace()`: non-negative integers only, nothing over 999, no zero anywhere. This check on
    the displayed trace is the real gate, since evaluation order is the learner's choice.
  - `error_steps(trace)`: **the correct expert-legality test**. For each step it asks whether an
    expert could produce that line FROM THE IMMEDIATELY PRECEDING LINE
    (`expert_next` -> `_next_dags(build_dag(prev), [])`).
    ⚠️ Do NOT reimplement this as expert trace-edge membership. Once the learner diverges, every
    later state is off the expert's trace tree, so edge membership marks all subsequent steps as
    errors.
- **`find_pairs.py`** (name historical) the trace finder. `learner_paths(dag, L)` lists every path
  with the learner's probability of taking it (product of 1/|legal moves|, the observer's pi_L).
  `usable_traces(expr, m)` keeps the usable ones (finishes, exactly one expert-illegal move, a
  different answer from the expert, passes `validate_trace`) with the error in `POSITIONS = (2, 3, 4)`.
  `sample_trace(expr, m, rng)` draws one of those with the learner's own probabilities.
- **`lookalike.py`** `error_step_rules(trace)`: the statements that plainly describe a trace's error
  step, read from the surface of the two lines, not from the model. Drives the look-alike guard.
- **`natural_position.py`** where the error lands with no position selection (§5). Run from
  `base-task/`, about 20 s at the default 3000 expressions per rule.

### The pool: `pool.py` -> `stimulus_pool.json` (v6)
**720 items = 240 traces x 3 hidden versions, each trace on its own expression, seed 2026.**

How a trace is chosen: for misconception m, draw an expression (`generate_expression`, 6 ops,
`bracket_prob` 1.0 for `outside_bracket_first` else 0.6); `sample_trace` draws one usable trace with
the error at step 2 to 4 by the learner's own path probabilities; keep it if it passes the checks for
some still-open cell (the scarcest cell wins, ties random). Builds in about 3 s.

Grid:
```
A: present(6)            =  6 cells x 20 traces = 120 traces -> 360 items
B: present(6) x named(5) = 30 cells x  4 traces = 120 traces -> 360 items
```
So: 120 items per category x difficulty; 20 per misconception x difficulty x category; 4 per
present x named x difficulty B cell; the present x named heatmap over traces has 20 on the diagonal
and 4 in every off-diagonal cell (none empty). Category **A** names the present misconception
(correct answer agree), **B** names an absent foil (disagree).

Checks (the builder applies them; `verify.py` re-derives them):
- **A trace:** no other single rule could have made the error step, and the named rule plainly
  describes it; in every hidden version the observer's marginal on the true rule is above
  `A_HIDDEN_MIN` = 0.5, so "agree" stays the ideal answer.
- **B trace naming foil f:** on the full trace f's marginal is at most `UNSUPPORTED_MAX` = 0.35 and f
  is not a look-alike; in every hidden version f's marginal is still at most 0.35.
- Every trace: 6 steps, exactly one expert-illegal move at step 2 to 4, learner answer differs from
  the correct one, numbers 1 to 918 shown, no negatives, decimals or zeros.

What came out (seed 2026): the builder refused 53 candidate foils as look-alikes and 6 because a
hidden version lifted the foil above 0.35; it never refused an A trace. Error step over the 240
traces: step 2: 80, step 3: 79, step 4: 81. That near-even split is chance (seeds 1 to 5 give e.g.
80/64/96, 70/83/87, 70/90/80). Per rule it is uneven, e.g. `outside_bracket_first` 13/21/6,
`same_priority_rtl` 11/11/18.

Item fields: `id` (e.g. `A000-E`), `base_id` (`A000`, shared by a trace's three versions),
`category, difficulty` (`easy`/`medium`/`hard`), `hidden_line` (index into `trace`),
`error_position, expression, n_ops, misconceptions, num_misconceptions, trace` (all 7 lines; the
frontend hides `trace[hidden_line]`), `probed_misconception, statement_correct, student_name,
belief_statement, io_marginal_full, io_marginal_hidden`, plus on B items `foil_status` (full trace).
v5's `io_foil_marginal` is gone (it equals `io_marginal_full` on B items). `student_name` and
`belief_statement` are placeholders the sampler reassigns.

**Answer-leak fields** (never show a solver or a participant): `statement_correct, misconceptions,
probed_misconception, category, num_misconceptions, foil_status, io_marginal_full,
io_marginal_hidden`. `id` and `base_id` start with A or B, so they encode the category too: never
display them.

### ⚠️ Things about the pool that will bite you
1. **6 operators.** At 4 ops `outside_bracket_first` never reaches step 3 at all; never go below 5.
   Hiding needs a line on both sides of the error, which is why the error is kept to steps 2 to 4.
2. **Position is not selected, but not controlled either.** It follows each rule's natural spread
   within steps 2 to 4, so it is tied to misconception. All three difficulties share the same traces,
   so it cannot confound difficulty. Record `error_position` as a covariate and include the trace
   (`base_id`) as a random effect.
3. **`foil_status` is RECORDED but NOT BALANCED** (v6: 60 refuted / 60 unsupported traces overall,
   lopsided per foil). **Never split a figure or analysis by it.**
4. **The pool excludes the hardest foils.** `foil_options()` drops any foil whose marginal exceeds
   0.35, so no B item names a rule the trace positively supports (§6).
5. **Correct steps carry little evidence.** Measured on the v5 pool: summed over its 240 traces, the
   number of the 22 hypotheses each step eliminates was step 1 2532, step 2 485, step 3 1143, step 4
   90, step 5 81, step 6 0, i.e. the error steps (1 and 3 there) carried 85%. This is why hiding a
   line away from the error changes nothing for the observer (§5).
6. **`outside_bracket_first` errors look like the operator rules** (e.g. `4 + 8 ÷ (4 - 1)` ->
   `12 ÷ (4 - 1)` reads as "addition before division" but the model says only outside() can make
   it). Guarded: `foil_options()` drops look-alike foils and `verify.py` asserts none are named.
7. **`src/user/data/stimulus_pool.json` is still the v5 pool on this branch.** Copy the v6 pool
   there only together with the new sampler; the current `sampleForm.js` expects positions 1/3.

### Verification: `verify.py`
Independent verifier; run after ANY regeneration (`cd base-task && python3 verify.py`, exits
non-zero on failure, about 2 s). Per trace: re-derives the trace from its expression, re-tests every
step for expert legality, checks the error is at step 2 to 4, re-runs the full-trace observer and the
A uniqueness / visibility checks, foil checks and look-alike guard. Per item: the hidden line matches
the difficulty (easy s(k+1), medium s(k-1), hard s(k)), the three versions of a trace agree on every
shared field, and the hidden-version observer is recomputed with `multi_hidden_posterior` (the
forward-DP route, not the builder's two-step route) to check the stored marginal, that the expert
stays eliminated, and that the key is still the observer's answer. Globally: every expression in one
trace, and every cell count above. Currently ALL CHECKS PASSED (2026-09-14, branch
`hidden-difficulty`).

---

## 4. The Bayesian ideal observer

### Fully observed: `base-task/bayes.py` -> `base-task/bayes_per_item.json`
One row per TRACE (240; `id` = `base_id`), since the three versions share the full trace. The
observer weighs **22 hypotheses** (expert + 6 singletons + 15 pairs) at epsilon 0
(`DEFAULT_EPSILON = 0.0`: every trace is generated deterministically, so a forbidden step eliminates
its hypothesis outright). No trace is generated by a pair; the pairs let the observer represent
"might ALSO hold rule f", which is what separates "no evidence either way" from "had a chance and
did not". Keep 22.

```
P(L | s0..s6) ∝ P(L) · prod_t pi_L(s_{t+1} | s_t)        pi_L uniform over L's legal moves
P(R ∈ L | trace) = sum_L P(L | trace) · [R ∈ L]
```
The observer sees only the trace; the belief statement is NOT an input and only picks which of the
six marginals is read off. Category A vs B is therefore not a difference in its computation.

**Result (v6): 240/240 = 100%.** A: marginal on the present rule exactly 1.000 in all 120. B:
P(agree) 0.000, marginal min 0.000 / mean 0.134 / max 0.333.

⚠️ Use `probed_marginal` as the observer's response, never `map_profile` (on 17 of 240 traces the MAP
pairs the true rule with `outside_bracket_first`; no correctness or marginal is affected).

### With a hidden line: `base-task/hidden.py`
Hiding line `s_k` means neither the observer nor the participant sees it. The two likelihood factors
that touch `s_k` collapse into a marginal over every value it could have taken:
```
P(observed | L, s0) = [prod_{t != k-1, k} pi_L(s_{t+1} | s_t)] · sum_{s_k} pi_L(s_k | s_{k-1}) pi_L(s_{k+1} | s_k)
```
`two_step_prob`, `hidden_log_likelihood`, `hidden_posterior(trace, k)` handle one hidden line;
`gap_prob` (forward DP over every intermediate path), `multi_hidden_log_likelihood` and
`multi_hidden_posterior(trace, hide_set)` handle ANY set of hidden lines. The two paths agree
exactly (`verify.py` uses one, the builder the other). `s0` and the final answer must stay visible.
`visible_trace(trace, k)` returns the lines a participant would see. Hiding can only flatten the
posterior, never sharpen it.

Why the expert is never revived by hiding one line: every trace's answer differs from the correct
one, and expert-legal moves always reach the correct answer, so no expert path can bridge a gap and
still end at the trace's answer. The visible work always contains an error. `verify.py` asserts it.

---

## 5. Hidden steps: findings

### v6 pool: `base-task/bayes_hidden.py` -> `base-task/bayes_per_item_hidden.json`
720 rows, one per item, each with that item's own line hidden: `id, base_id, category, difficulty,
error_position, hidden_line, n_lines_shown, true_misconception, probed_misconception,
statement_correct, marginal_full, probed_marginal, delta_vs_full, observer_agrees,
observer_correct`.

| difficulty | accuracy | category A marginal | category B marginal |
|---|---|---|---|
| (no hiding) | 240/240 | 1.000 flat | mean 0.134, max 0.333 |
| easy | 240/240 | 1.000 flat | mean 0.133, max 0.333 |
| medium | 240/240 | 1.000 flat | mean 0.133, max 0.333 |
| hard | 240/240 | mean 0.989, min 0.600 | mean 0.134, max 0.333 |

- Items whose marginal moves at all: easy A 0 / B 7, medium A 0 / B 4, hard A 5 / B 2 (of 120 each).
- **All 5 moved A items are `outside_bracket_first` in the hard version**: A114-H 0.600, A107-H
  0.714, A111-H 0.714, A110-H 0.789, A104-H 0.889. That rule's hard mean is 0.935; every other
  rule x difficulty cell is 1.000.
- The observer is correct on all 720 by construction (the pool requires it, §3).

**What it means.** The observer does not order easy < medium < hard. It is flat on easy and medium
and dips only in one rule's hard cell. The difficulty ordering is a hypothesis about people: any
effect is processing cost (people cannot marginalise over paths), not lost information. The Bayes
arm therefore contributes almost no gradient on difficulty, as it contributes none on position.

### Where the error lands without selection: `base-task/natural_position.py` (2026-09-14)
3000 expressions per rule from the pool's generator; the learner chooses uniformly among its legal
moves. Most learner paths are not usable: 52% never show the error at all, 17% show two or more
errors, 16% have one error but reach the correct answer or undisplayable numbers; about 15% are
usable. Among usable paths, a pool built with no position filter would put the error at (% of items):

| misconception | step 1 | step 2 | step 3 | step 4 | step 5 |
|---|---|---|---|---|---|
| add_before_mul | 11 | 15 | 19 | 20 | 36 |
| add_before_div | 9 | 11 | 20 | 30 | 30 |
| sub_before_mul | 20 | 21 | 22 | 27 | 10 |
| sub_before_div | 28 | 23 | 21 | 22 | 7 |
| same_priority_rtl | 12 | 15 | 16 | 19 | 38 |
| outside_bracket_first | 11 | 26 | 43 | 21 | 0 |
| **all** | **15** | **18** | **23** | **23** | **21** |

On the v5 pool's own expressions, the learner left to itself would have put the error at step 1 only
40% of the time on the step-1 items, and at step 3 only 45% of the time on the step-3 items.

### Earlier findings on the v5 pool (errors at step 1 or 3; superseded, still explanatory)
Conditions `none`, `s2`, `s4`, `error_line` on the 240 v5 items: 240/240 correct in every condition.
Hiding s2 or s4 moved 7 of 480 item-by-hide combinations, all category B. Hiding the error's own line
moved 10 items: 6 category A, all `outside_bracket_first` (min 0.556), plus 4 B. Hiding s1, s3 and s5
together: A 0.986; hiding all five intermediate lines (only expression and answer shown): A 0.933.
The work without the answer: still 1.000. Only the first line shown: error-at-step-3 items 0.333.

**Why hiding barely matters. Two reasons, for different cells; do not merge them.**
1. *Hiding a correct line away from the error: correct steps carry almost no evidence* (§3 item 5).
2. *Hiding a line next to the error, or the error's own line: the gap is pinned by its endpoints.*
   Marginalising over the hidden state keeps only profiles that can bridge `s_{k-1} -> s_{k+1}` in two
   steps, and usually only the true profile can, so the elimination still happens. The exception is
   `outside_bracket_first`: it is the only rule that removes options, so its evidence is the only kind
   a single hidden line can dilute.

### The design questions, resolved (2026-09-14)
1. Which line is hidden: relative to the error (easy / medium / hard, §0), not a fixed s2 or s4.
2. Items: 720 (240 traces x 3 versions), no no-hide control.
3. Trials: 24 per participant, one expression at most once, with the rotation in §0.
4. **Still open:** display of the hidden line, and whether participants are told a line is missing.

---

## 6. Figures (`analysis-Bayesian/`)

⚠️ **Stale on branch `hidden-difficulty`.** The scripts group by `POSITIONS = [1, 3]`
(`bayes_common.py`) and `plot_bayes_hidden_dist_A.py` reads the v5 conditions (`none/s2/s4/error_line`),
which `bayes_per_item_hidden.json` no longer has. The PNGs in the folder are from the v5 pool. They
need rewriting for v6 (difficulty instead of position) before use.

- **`bayes_common.py`** shared loader and styling; reads `base-task/bayes_per_item.json`.
- **`plot_bayes_1misc_heatmap.py`**, **`plot_bayes_1misc_by_rule.py`**, **`plot_bayes_1misc_profile.py`**
  -> the three fully observed figures (present x named heatmap; P(rule | trace) present vs absent per
  rule; all six marginals per trace).
- **`plot_bayes_hidden_dist_A.py`** -> `bayes_hidden_dist_A.png`. Category A, one panel per
  misconception, one stem series per hidden condition.

Finding carried over from the v5 pool: over the 1200 (trace, absent rule) combinations, 42 give an
ABSENT rule a marginal above 0.35 and 27 above 0.5 (max 0.871), all 27 `outside_bracket_first`, and
the pool excludes all of them from category B.

Rules for any new figure: category A is a point mass at 1.000 (except `outside_bracket_first` hard),
do not draw its "distribution"; marginals are discrete, use exact-value stems, not KDEs; never split
by `foil_status`; never group by one rule while plotting the marginal selected by a different rule.

---

## 7. The web experiment (`src/`), inherited from Experiment 1

A Smile (codec-lab / gureckislab) Vue-3 experiment. **User code in `src/user/`.** `npm run dev` runs
it locally. **Everything here was built for Experiment 1 and shows every line of the work.** It is a
working starting point, not Experiment 2's task.

- **`src/user/design.js`** the timeline: consent -> windowsizer -> instructions -> comprehension quiz
  -> practice -> experiment -> strategy question -> feedback survey -> demographics -> save ->
  debrief -> thanks. `estimated_time` is set for Experiment 1.
- **`src/user/components/trace_judgment/TraceJudgmentView.vue`** the 24-trial task (expression, work
  as `= step` lines, belief statement, 6-point Likert, 3-second lock, "X of 24" counter, mouse
  tracking, bonus scoring). **Needs to render `trace[hidden_line]` as hidden.**
- **`src/user/utils/sampleForm.js`** + Python twin **`base-task/sample_form.py`**: Experiment 1's
  sampler (four pools by category x position, one item per misconception from each, 24 trials, same
  seeded PRNG in both languages). **Knows nothing about v6; `sample_form.py`'s checks fail against
  the v6 pool.** Both must be rewritten for the §0 form.
- **`src/user/data/stimulus_pool.json`** = still the **v5** pool (see §3 item 7).
  **`src/user/data/practice_items.json`** = Experiment 1's 3 practice items, written by
  `base-task/practice.py`; they show every step.
- **`InstructionsView.vue`** / **`quizQuestions.js`**: Experiment 1's user-approved text and 4-question
  quiz. They say nothing about hidden lines.
- **`PracticeView.vue`** feedback highlights the error step amber; with hidden lines it needs
  deciding what to highlight when the error's line is the hidden one (hard).
- **`src/builtins/thanks/ThanksView.vue`** Prolific completion code **`CNIEB9GV`** (old study). A new
  Prolific study issues a new code; replace it in both the `prolific` and `web` blocks before launch.
- **`public/consent-form.pdf`** NYU IRB form (IRB-FY2026-11440, PI Mark Ho).

### Bonus
Binary direction only: rating >= 4 counts as agree, correct if that matches `statement_correct`.
`bonus = max(0, (accuracy - 0.5) / 0.5) x $2`, rounded to cents, recorded per trial (`is_correct`)
and as a `traceJudgmentBonus` block in `pageData_exp`. Confidence is deliberately NOT rewarded,
because the Likert distribution is the dependent variable. Base pay is separate.

### ⚠️ Prolific URL (a missing-params bug cost a whole batch once)
Participants MUST arrive on `#/welcome/prolific/` with the ID params, or they are recorded
`recruitmentService: "web"` with no `prolific_id` and cannot be bonused. Params BEFORE and AFTER the
hash:
```
https://www.codec-lab.org/divya603/bodmas-exp2-hidden/main/?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}#/welcome/prolific/?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}
```

### Checklist before running any participant
- [ ] Hidden-line frontend, sampler, practice items, instructions and quiz built for the §0 design
      (§9), merged, deployed, and the LIVE bundle verified to contain them.
- [ ] Deploy secrets uploaded and a real deploy confirmed (§1).
- [ ] Prolific completion code replaced; `estimated_time` in `design.js` checked with the PI.
- [ ] Consent and debrief: `design.js` points at `public/consent-form.pdf` and `public/debrief.pdf`,
      both present. Confirm with the PI that the IRB protocol covers Experiment 2.
- [ ] Prolific URL tested end to end with a fake PID (a `prolific_id` must appear in
      `npm run getrecruitment`, type `testing`).
- [ ] Fresh bonus ledger for this experiment.

### Running participants and paying them
- `npm run getdata` prompts for data type (`testing` or `real`), complete-only or all, branch
  (`main`), filename; saves JSON under `data/`. `npm run getrecruitment` -> `data/private/...` (maps
  `session_id` -> `prolific_id`). **Join key: data `seedID` == recruitment `session_id`.**
- Bonus list: `scripts/make_bonus_list.py` from the old study was never committed; it is at
  `~/Desktop/NYU/Darpa/Bodmas_model/scripts/make_bonus_list.py`. It recomputes each bonus from raw
  responses against `statement_correct` and emits `prolific_id,amount` lines for Prolific.
- Keep a FRESH payment ledger (`data/private/bonus_paid.csv`, gitignored): run the script, pay,
  re-run with `--mark-paid`. It is the only guard against double-paying across batches.

### Deploys
`.github/workflows/deploy.yml` deploys on push to ANY branch except `feat-* fix-* refactor-* test-*
chore-* style-* docs-* ci-*`, each to its own path `/<owner>/<repo>/<branch>/`. So **pushing `main`
deploys the live experiment**; other branches (including `hidden-difficulty`) get separate staging
sites. Commits touching only `*.md` files or `docs/` do NOT deploy (`paths-ignore`). Monitor with
`gh run list` / `gh run watch`. A transient "SSH i/o timeout" at "create the remote folders" has
happened; `gh run rerun <id> --failed` fixed it.

---

## 8. Commands cheat-sheet

```bash
# Pool (v6) and its checks
cd base-task && python3 pool.py            # rebuild the pool (seed 2026, ~3 s); only if deliberately changing it
cd base-task && python3 verify.py          # independent checks, incl. every hidden version (~2 s)

# Observer
cd base-task && python3 bayes.py           # full traces -> bayes_per_item.json (240 rows, expect 240/240)
cd base-task && python3 bayes_hidden.py    # each item's own hidden line -> bayes_per_item_hidden.json (720 rows)
cd base-task && python3 natural_position.py   # error position with no selection (~20 s)

# Frontend helpers (Experiment 1 versions; NOT yet updated for v6)
cd base-task && python3 sample_form.py     # sampler checks over 500 seeds (twin of sampleForm.js)
cd base-task && python3 practice.py        # check + write practice items to src/user/data/

# Figures (from repo root; stale for v6, §6)
python3 analysis-Bayesian/plot_bayes_hidden_dist_A.py
python3 analysis-Bayesian/plot_bayes_1misc_heatmap.py
python3 analysis-Bayesian/plot_bayes_1misc_by_rule.py
python3 analysis-Bayesian/plot_bayes_1misc_profile.py

# Experiment
npm run dev ; npm run build
git push origin main                       # DEPLOYS THE LIVE EXPERIMENT (ask first)
npm run getdata ; npm run getrecruitment
npm run upload_config                      # (re)push deploy secrets from env/*.local
```

---

## 9. What is next (all on branch `hidden-difficulty`)

1. **Sampler**, `sampleForm.js` and its twin `sample_form.py`, for the §0 form: 24 trials, the
   2-1-1 difficulty table with the cyclic misconception rotation, at most one version per trace
   (`base_id`), and (if the user confirms) each rule named in exactly 2 disagree trials. Same seeded
   PRNG in both languages, checked over 500 seeds in both.
2. **Copy the v6 pool** into `src/user/data/stimulus_pool.json` in the same commit as the sampler.
3. **Decide the hidden-line display** with the user (§5 question 4), then render it in
   `TraceJudgmentView.vue` and `PracticeView.vue` (and decide what practice feedback highlights when
   the error's line is hidden).
4. **Practice items with a hidden line** (`practice.py`), and instructions and quiz that explain it.
5. **Figures** rewritten for v6 (§6).
6. **Deploy**: secrets (§1), staging deploy of the branch, verify the live bundle; merge to `main`
   only with the user's go-ahead.
7. The §7 checklist.

---

## 10. Gotchas and working rules

- **An experiment change is only done when it is committed, pushed, verified in the deployed bundle,
  and recorded here.** The live site is built by CI from the git remote; local files do nothing for
  participants. A previous study lost 19 paid participants to a pool that was regenerated locally but
  never pushed.
- **Pushing `main` deploys the live experiment.** Ask the user before pushing experiment-material
  changes to `main`.
- **A green deploy run does not mean it deployed.** With secrets missing, the `deploy` job is skipped
  and the workflow still passes. Check the `deploy` job's steps (`gh run view <id>`).
- **Two pool copies can drift.** `base-task/stimulus_pool.json` is the source; the frontend reads
  `src/user/data/stimulus_pool.json`. On this branch they currently differ on purpose (§3 item 7).
- **The model code is a copy of Experiment 1's** (§0). Do not assume a change in one repo reaches the
  other.
- **`sampleForm.js` and `sample_form.py` must stay in sync.** The live experiment uses the JS one.
- **Never commit** `data/real-all-main-data.json`, anything under `data/private/`, `env/*.local`,
  `firebase/.service-account-key.json`, or any API key.
- **User preferences:** finish a design discussion before writing code. On a surprising result, audit
  our own stimuli and task before blaming participants. The user often runs commands themselves via
  `! <cmd>` and likes work pushed rather than left local. **No em dashes in any writing** (docs,
  reports, chat). **LaTeX compiles on Overleaf only**: self-contained folders, figures referenced as
  `figs/<exact-name>`, never install a local TeX toolchain.
- If a commit prints `Cannot find module '@codenamize/codenamize'`, run `npm run setup_project`. The
  commit itself still lands.
- Commit messages end with the current model's co-author line.
