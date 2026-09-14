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

**Status (2026-09-14): design DECIDED; v6 pool, 24-trial sampler and hidden-line display DONE and
live on `main`; instructions and quiz revised; practice items NOT yet adapted.**
- **Work on `main` only** (the user's preference: one branch). The `hidden-difficulty` branch was
  merged into `main` by fast-forward and deleted on 2026-09-14. Pushing `main` deploys the live
  experiment, so keep `main` in a runnable state.
- Done: the v6 pool (720 items, §3), verified; the ideal observer run on it (§4, §5); the
  natural-error-position analysis (§5); the sampler in JS and Python, identical on 503 seeds (§7);
  the trial view hides the line (§7); `src/user/data/stimulus_pool.json` is the v6 pool.
- Not done: practice items (still Experiment 1's 3 full traces), instructions and quiz review for
  Experiment 2, the Bayesian figures (stale, §6). See §9.
No human or LLM data exist yet.

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
- **Display: the hidden line is simply not shown.** No ellipsis, no "step not shown" note; the work
  goes straight from the line before to the line after. **Participants ARE told, in the
  instructions only**, that the student's work has "one step skipped" (user's decision 2026-09-14,
  reversing the earlier "do not tell them"). Nothing on the trial screen marks where.
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
  | 1 | agree + disagree | agree | disagree |
  | 2 | agree + disagree | disagree | agree |
  | 3 | agree | agree + disagree | disagree |
  | 4 | disagree | agree + disagree | agree |
  | 5 | agree | disagree | agree + disagree |
  | 6 | disagree | agree | agree + disagree |

  **Which misconception fills which row is a random permutation per participant**, drawn from the
  form seed. An exact rotation (every cell exactly 4 times per 6 participants) is not possible: Smile's
  `randomAssignCondition` samples with replacement and there is no cross-participant counter. The 36
  misconception x difficulty x statement cells balance in expectation; over 500 simulated forms each
  got 310 to 350 trials (expected 333).
- **Wrong statements are left to the draw, as in Experiment 1** (user's decision, 2026-09-14). Each
  disagree cell is a random pool item of that (misconception, difficulty), and it brings the foil it
  was built with. Within one participant a wrong statement can therefore repeat: over 500 forms the
  most-named wrong statement appears 3 to 5 times out of the 12 disagree trials in most forms (max 7).
  Each statement is named as the CORRECT one exactly twice per form.

### The task (one trial)
A participant sees a **math expression**, a **student's step-by-step work** containing exactly one
order-of-operations misconception, with **one step skipped** (unmarked), and a **belief statement**
claiming the student holds a particular misconception. They rate on a **6-point Likert scale** (1 =
Strongly Disagree, 6 = Strongly Agree) how well the statement explains the work, NOT whether the
final answer is right. Scoring collapses the rating at **>= 4 = agree**.

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

**Status as of 2026-09-14: secrets uploaded (by the user) and real deploys confirmed.** `main`:
first `workflow_dispatch` on 2026-09-13 (`deploy` job ran, 1m20s; that build was Experiment 1's task).
After the merge, the push of `6be93c0` (2026-09-14) deployed (`deploy` job 1m30s) and the LIVE `main`
bundle was checked: it contains the v6 items (`A000-E` ... `B119-H`) and `hidden_line`.
Remember `deploy.yml` SKIPS the `deploy` job and still shows GREEN when secrets are missing, so always
check with `gh run view <id>` that the **`deploy` job itself ran** (build and rsync, about a minute).

⚠️ The live `main` URL now serves the Experiment 2 trials, but still Experiment 1's practice items
(§9). Do not send participants there until the §7 checklist is done. A stale staging copy from the
deleted `hidden-difficulty` branch remains on the server at `.../bodmas-exp2-hidden/hidden-difficulty/`
(deploys never remove old paths); ignore it and never share it. Its test data, if any, sits under its
own Firestore key.

Node: `.node_version` pins 20.18.1; Node 24 has been working locally. If `npm install` misbehaves,
switch with `nvm use 20`.

What changes automatically because this is a separate repo:
- **The deploy URL.** Path is `/<owner>/<repo>/<branch>/`, so main deploys to
  `https://www.codec-lab.org/divya603/bodmas-exp2-hidden/main/`, and the short codename URL is derived
  from the same path (printed in the deploy log). Any Prolific link must point here.
- **Where the data lands.** Firestore's `projectRef` (`src/core/config.js`) is derived from the
  deploy path, so this experiment's data is stored under its own key and cannot mix with
  Experiment 1's.

---

## 2. Repository map

```
base-task/         The model, the pool, the ideal observer, the hidden-step inference, the sampler's
                   Python twin. §3 to §5, §7.
analysis-Bayesian/ Ideal-observer figures. §6 (stale).
src/               The Smile/Vue web experiment. §7.
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
frontend leaves out `trace[hidden_line]`), `probed_misconception, statement_correct, student_name,
belief_statement, io_marginal_full, io_marginal_hidden`, plus on B items `foil_status` (full trace).
v5's `io_foil_marginal` is gone (it equals `io_marginal_full` on B items). `student_name` and
`belief_statement` are placeholders the sampler reassigns.

**Answer-leak fields** (never show a solver or a participant): `statement_correct, misconceptions,
probed_misconception, category, num_misconceptions, foil_status, io_marginal_full,
io_marginal_hidden`. `id` and `base_id` start with A or B, so they encode the category too: never
display them. (They are Smile step ids in the task, but Smile's router only pushes named views, so
step ids never reach the URL.)

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
7. **Two pool copies.** `base-task/stimulus_pool.json` is the source; the frontend bundles
   `src/user/data/stimulus_pool.json`. They are identical (v6) since 2026-09-14. After any rebuild,
   copy it over and check with `cmp`, then rerun the sampler checks (§7).

### Verification: `verify.py`
Independent verifier; run after ANY regeneration (`cd base-task && python3 verify.py`, exits
non-zero on failure, about 2 s). Per trace: re-derives the trace from its expression, re-tests every
step for expert legality, checks the error is at step 2 to 4, re-runs the full-trace observer and the
A uniqueness / visibility checks, foil checks and look-alike guard. Per item: the hidden line matches
the difficulty (easy s(k+1), medium s(k-1), hard s(k)), the three versions of a trace agree on every
shared field, and the hidden-version observer is recomputed with `multi_hidden_posterior` (the
forward-DP route, not the builder's two-step route) to check the stored marginal, that the expert
stays eliminated, and that the key is still the observer's answer. Globally: every expression in one
trace, and every cell count above. Currently ALL CHECKS PASSED (2026-09-14).

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
3. Trials: 24 per participant, one expression at most once, rows assigned by random permutation.
4. Display: the line is left out with nothing in its place; the instructions say one step is skipped.

---

## 6. Figures (`analysis-Bayesian/`)

⚠️ **Stale for v6.** The scripts group by `POSITIONS = [1, 3]` (`bayes_common.py`) and
`plot_bayes_hidden_dist_A.py` reads the v5 conditions (`none/s2/s4/error_line`), which
`bayes_per_item_hidden.json` no longer has. The PNGs in the folder are from the v5 pool. They need
rewriting for v6 (difficulty instead of position) before use.

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

## 7. The web experiment (`src/`)

A Smile (codec-lab / gureckislab) Vue-3 experiment. **User code in `src/user/`.** `npm run dev` runs
it locally; `npm run build` must succeed before pushing. Inherited from Experiment 1; the main task is
now Experiment 2's, the practice is still Experiment 1's.

- **`src/user/design.js`** the timeline: consent -> windowsizer -> instructions -> comprehension quiz
  -> practice -> experiment -> strategy question -> feedback survey -> demographics -> save ->
  debrief -> thanks. `estimated_time` is set for Experiment 1.
- **`src/user/components/trace_judgment/TraceJudgmentView.vue`** the 24-trial task. Shows the
  expression, then the work as `= line` for every line except `trace[hidden_line]` (`shownWork()`;
  nothing in its place), the belief statement, 6-point Likert, 3-second lock, "X of 24" counter, mouse
  tracking, bonus scoring. Every item field (incl. `difficulty`, `hidden_line`, `base_id`) is recorded
  with the trial. The form seed is persisted, so a reload redraws the same form.
- **`src/user/utils/sampleForm.js`** + Python twin **`base-task/sample_form.py`**: the v6 sampler
  (§0): a random permutation assigns the 6 misconceptions to the 6 `ROWS`; each (difficulty,
  category) cell of a row is one random pool item of that misconception, skipping traces already
  used; then the trial order and the 24 names are shuffled. Same mulberry32 PRNG and draw order in
  both. `python3 sample_form.py` runs the 500-seed checks (every balance in §0, distinct traces and
  expressions, names, statement wiring); `python3 sample_form.py --dump 500 | node
  sample_form_parity.mjs` (from `base-task/`) confirms the JS draws identical forms (503/503 incl.
  large seeds on 2026-09-14). **Change both together.**
- **`src/user/data/stimulus_pool.json`** = the v6 pool (§3 item 7).
  **`src/user/data/practice_items.json`** = still Experiment 1's 3 practice items, written by
  `base-task/practice.py`; they show every line and have no `hidden_line`.
- **`InstructionsView.vue`**: Experiment 1's user-approved text with two changes the user asked for
  on 2026-09-14: the first paragraph says the work is shown "with one step skipped", and the bonus
  paragraph is one line ("You can earn a bonus of up to $2."; the scoring rule is no longer
  explained to participants, though the bonus is computed exactly as before, §7 Bonus). The user
  wants the text short: do not over-explain.
- **`quizQuestions.js`**: the quiz is down to 3 questions (what to base the rating on; one
  mistake per student; a different-mistake statement means disagree): Experiment 1's brackets
  question was removed on 2026-09-14 at the user's request (commit `9eeb981`; deploy ran and the
  LIVE bundle was checked: the brackets question is gone, the other three are there). The text says "the step-by-step work a
  student wrote" and "every student makes exactly one mistake, at one step of their work"; it never
  claims every line is shown.
- **`PracticeView.vue`** feedback highlights the error step amber. If practice items get a hidden
  line, decide what the feedback highlights when the error's own line is the hidden one (hard).
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
- [ ] Practice items, instructions and quiz settled for the §0 design (§9), deployed, and the LIVE
      bundle verified to contain them.
- [x] Deploy secrets uploaded and a real deploy confirmed (§1).
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
chore-* style-* docs-* ci-*`, each to its own path `/<owner>/<repo>/<branch>/`. **Pushing `main`
deploys the live experiment.** Commits touching only `*.md` files or `docs/` do NOT deploy
(`paths-ignore`). Monitor with `gh run list` / `gh run watch`. A transient "SSH i/o timeout" at
"create the remote folders" has happened; `gh run rerun <id> --failed` fixed it.

---

## 8. Commands cheat-sheet

```bash
# Pool (v6) and its checks
cd base-task && python3 pool.py            # rebuild the pool (seed 2026, ~3 s); only if deliberately changing it
cd base-task && python3 verify.py          # independent checks, incl. every hidden version (~2 s)
cp base-task/stimulus_pool.json src/user/data/stimulus_pool.json   # after any rebuild (then cmp)

# Observer
cd base-task && python3 bayes.py           # full traces -> bayes_per_item.json (240 rows, expect 240/240)
cd base-task && python3 bayes_hidden.py    # each item's own hidden line -> bayes_per_item_hidden.json (720 rows)
cd base-task && python3 natural_position.py   # error position with no selection (~20 s)

# Sampler (v6)
cd base-task && python3 sample_form.py     # 500-seed checks of the Python twin
cd base-task && python3 sample_form.py --dump 500 | node sample_form_parity.mjs   # JS == Python?

# Practice (Experiment 1 version; NOT yet updated)
cd base-task && python3 practice.py        # check + write practice items to src/user/data/

# Figures (from repo root; stale for v6, §6)
python3 analysis-Bayesian/plot_bayes_hidden_dist_A.py
python3 analysis-Bayesian/plot_bayes_1misc_heatmap.py
python3 analysis-Bayesian/plot_bayes_1misc_by_rule.py
python3 analysis-Bayesian/plot_bayes_1misc_profile.py

# Experiment
npm run dev ; npm run build
git push origin main                       # DEPLOYS THE LIVE EXPERIMENT
npm run getdata ; npm run getrecruitment
npm run upload_config                      # (re)push deploy secrets from env/*.local
```

---

## 9. What is next

1. **Instructions and quiz**: revised 2026-09-14 (one step skipped; one-line bonus; 3-question
   quiz). Further changes only if the user asks.
2. **Debrief**: the generic lab PDF (`public/debrief.pdf`) does not mention the skipped step; the
   user may check with the PI whether it should.
3. **Practice items.** They are Experiment 1's 3 items with every line shown. Decide with the user
   whether practice should also leave a line out (and, for a hard-style item, what the feedback
   highlights when the error's own line is missing); then `practice.py` and `PracticeView.vue`.
4. **Click through the live site** end to end: a line really is missing on every trial, 24 trials,
   and `difficulty` / `hidden_line` / `base_id` are in the saved trial data.
5. **Figures** rewritten for v6 (§6).
6. `estimated_time`, Prolific code, IRB coverage (§7 checklist), then verify the live bundle.

---

## 10. Gotchas and working rules

- **An experiment change is only done when it is committed, pushed, verified in the deployed bundle,
  and recorded here.** The live site is built by CI from the git remote; local files do nothing for
  participants. A previous study lost 19 paid participants to a pool that was regenerated locally but
  never pushed.
- **Work on `main` only; no second branch** (user's preference, 2026-09-14). Pushing `main` deploys
  the live experiment, so run the checks (`verify.py`, `sample_form.py`, the parity check, `npm run
  build`) before every push, and ask the user before pushing experiment-material changes.
- **A green deploy run does not mean it deployed.** With secrets missing, the `deploy` job is skipped
  and the workflow still passes. Check the `deploy` job's steps (`gh run view <id>`).
- **Two pool copies can drift.** `base-task/stimulus_pool.json` is the source; the frontend reads
  `src/user/data/stimulus_pool.json`. Keep them identical (§3 item 7).
- **The model code is a copy of Experiment 1's** (§0). Do not assume a change in one repo reaches the
  other.
- **`sampleForm.js` and `sample_form.py` must stay in sync.** The live experiment uses the JS one;
  check with the parity command in §8.
- **Never commit** `data/real-all-main-data.json`, anything under `data/private/`, `env/*.local`,
  `firebase/.service-account-key.json`, or any API key.
- **User preferences:** finish a design discussion before writing code. On a surprising result, audit
  our own stimuli and task before blaming participants. The user often runs commands themselves via
  `! <cmd>` and likes work pushed rather than left local. One branch (`main`). **No em dashes in any
  writing** (docs, reports, chat). **LaTeX compiles on Overleaf only**: self-contained folders,
  figures referenced as `figs/<exact-name>`, never install a local TeX toolchain.
- If a commit prints `Cannot find module '@codenamize/codenamize'`, run `npm run setup_project`. The
  commit itself still lands.
- Commit messages end with the current model's co-author line.
