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
**one step of that work is hidden**, and whether it matters which step is hidden.

**Status (2026-09-13): the design is NOT decided yet.** What exists:
- the stimulus pool Experiment 2 is built on (240 items, identical to Experiment 1's, §3);
- the ideal-observer machinery for hidden steps, already run over that pool (§4, §5);
- a web experiment inherited from Experiment 1, which still shows EVERY step (§7).
Nothing has been deployed from this repo, and no human or LLM data exist.

Provenance: seeded from `divya603/bodmas-exp1-position` at commit `862dea1` (its pool, model,
observer, figures and finished Experiment 1 frontend), plus the hidden-step code from the archive repo
`divya603/bodmas-model`, branch `pilot-v5-hidden` (commit `89dfe97`). ⚠️ **The pool here is a COPY of
Experiment 1's.** If Experiment 1 ever rebuilds its pool, this repo does not follow automatically;
decide then whether it should, and rerun everything in §4 and §5.

### The user's proposed design (2026-09-09, not yet final)
The same stimuli as Experiment 1, but with one step of the student's work hidden, **either step 2 or
step 4**. Factors, meant to be fully crossed: misconception present (6) x error position (step 1 or
3) x what the statement names (the present rule or a foil) x which step is hidden (2 or 4). §5 has
the measured consequences and the open questions; read it before building anything.

### The task (one trial)
A participant sees a **math expression**, a **student's step-by-step work** containing exactly one
order-of-operations misconception, and a **belief statement** claiming the student holds a
particular misconception. They rate on a **6-point Likert scale** (1 = Strongly Disagree, 6 =
Strongly Agree) how well the statement explains the work, NOT whether the final answer is right.
Scoring collapses the rating at **>= 4 = agree**. In Experiment 2, one line of the work is hidden.

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

**Status as of 2026-09-13: secrets NOT yet uploaded to this repo, so nothing has been deployed.**
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
  from the same path (printed in the deploy log). Any Prolific link must point here.
- **Where the data lands.** Firestore's `projectRef` (`src/core/config.js`) is derived from the
  deploy path, so this experiment's data is stored under its own key and cannot mix with
  Experiment 1's.

---

## 2. Repository map

```
base-task/         The model, the pool, the ideal observer, and the hidden-step inference. §3 to §5.
analysis-Bayesian/ Ideal-observer figures. §6.
src/               The Smile/Vue web experiment (inherited from Experiment 1). §7.
scripts/           Smile deploy/data scripts.
public/            consent-form.pdf, debrief.pdf served by the frontend.
env/, firebase/    Smile config. env/.env is tracked defaults; env/*.local are secrets (untracked).
data/              Pulled participant data lands here. Participant files are gitignored.
docs/ tests/ plugins/ analysis/ plans/   Smile framework infrastructure, not ours. Leave alone.
```

---

## 3. The model and the base pool (`base-task/`)

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
- **`find_pairs.py`** `pairs_for_expression(expr, misconception)` returns `{position: trace}` for
  the requested error positions an expression supports (exactly one expert-illegal move, at that
  step, a different answer from the expert, passes `validate_trace`). `POSITIONS = (1, 3)`.
- **`lookalike.py`** `error_step_rules(trace)`: the statements that plainly describe a trace's error
  step, read from the surface of the two lines, not from the model. Drives the look-alike guard.

### The base pool: `pool.py` -> `stimulus_pool.json`
**240 items, each on its own expression**, seed 2026, byte-identical to Experiment 1's pool
(Experiment 1 calls it "v5"). Every item shows all 7 lines (`s0` expression through `s6` answer);
hiding is applied on top of it, in inference now (§5) and in the frontend later (§9).

Grid:
```
A: present(6) x position(2)            = 12 cells x 10 items = 120
B: present(6) x named(5) x position(2) = 60 cells x  2 items = 120
```
Category **A** names the present misconception (correct answer agree), **B** names an absent foil
(disagree). Each rule is present in 40 items: 10 each of (A, step 1), (A, step 3), (B, step 1),
(B, step 3), and within its 20 B items the named foil is balanced 5 foils x 2 positions x 2 items, so
the present x named heatmap has no empty cells. Error position is BETWEEN expressions (no expression
appears twice). 240 distinct expressions; every trace is 6 steps with exactly one expert-illegal
move; every learner answer differs from the correct one; numbers 1 to 930, no negatives, decimals
or zeros. In every A item only the named rule could make the error step and it visibly shows it; no
B item names a look-alike foil.

Item fields: `id, category, error_position, expression, n_ops, misconceptions, num_misconceptions,
trace, probed_misconception, statement_correct, student_name, belief_statement`, plus on B items
only `foil_status` and `io_foil_marginal`. `student_name` and `belief_statement` are placeholders
that the frontend sampler reassigns. There is no `pair_id` in this pool.

**Answer-leak fields** (never show a solver or a participant): `statement_correct, misconceptions,
probed_misconception, category, num_misconceptions, foil_status, io_foil_marginal`.

### ⚠️ Things about the base pool that will bite you
1. **6 operators.** At 4 ops `outside_bracket_first` never reaches step 3 at all; never go below 5.
   Hiding a line needs an interior line to hide, which 6-step traces have plenty of.
2. **Position is SELECTED, not constructed.** A misconception decides what happens when the learner
   touches its window, not when; one expression yields traces with the error anywhere from step 1 to
   5, and the builder keeps step 1 and step 3. Position is also between expressions, so a position
   effect in people partly reflects which expressions support each position. Include item as a random
   effect in analyses.
3. **`foil_status` is RECORDED but NOT BALANCED.** Pool-wide 58 refuted / 62 unsupported, lopsided
   per foil. **Never split a figure or analysis by it.**
4. **The pool excludes the hardest foils.** `pool.py: foil_options()` drops any foil whose marginal
   exceeds 0.35, so no B item names a rule the trace positively supports (§6).
5. **Most of the evidence sits in two or three of the 6 steps.** Summed over all 240 traces, the
   number of the 22 hypotheses each step eliminates is: step 1 2532, step 2 485, step 3 1143, step 4
   90, step 5 81, step 6 0. Steps 1 and 3 (the error positions) carry 85%; the forced last step
   carries none. **This one fact explains most of §5.**
6. **`outside_bracket_first` errors look like the operator rules** (e.g. `4 + 8 ÷ (4 - 1)` ->
   `12 ÷ (4 - 1)` reads as "addition before division" but the model says only outside() can make
   it). Guarded: `foil_options()` drops look-alike foils and `verify.py` asserts none are named.

### Verification: `verify.py`
Independent verifier; run after ANY regeneration (`cd base-task && python3 verify.py`, exits
non-zero on failure). Re-derives every trace from its expression, re-tests every step for expert
legality, re-runs the observer, and re-checks statement wiring, expression uniqueness, the four
60-item sampling pools, the exact cell counts, the A-item uniqueness check and the look-alike guard.
Currently ALL CHECKS PASSED (checked in this repo 2026-09-13). It checks the base pool only; it knows
nothing about hidden steps.

---

## 4. The Bayesian ideal observer

### Fully observed (the base pool as shown in Experiment 1)
`base-task/bayes.py` -> `base-task/bayes_per_item.json`. The observer weighs **22 hypotheses**
(expert + 6 singletons + 15 pairs) at epsilon 0 (`DEFAULT_EPSILON = 0.0`: every trace is generated
deterministically, so a forbidden step eliminates its hypothesis outright). No item is generated by a
pair; the pairs let the observer represent "might ALSO hold rule f", which is what separates "no
evidence either way" from "had a chance and did not". Keep 22.

```
P(L | s0..s6) ∝ P(L) · prod_t pi_L(s_{t+1} | s_t)        pi_L uniform over L's legal moves
P(R ∈ L | trace) = sum_L P(L | trace) · [R ∈ L]
```
The observer sees only the trace; the belief statement is NOT an input and only picks which of the
six marginals is read off. Category A vs B is therefore not a difference in its computation.

**Result: 240/240 = 100%.** A: marginal on the present rule exactly 1.000 in all 120. B: P(agree)
0.000, marginal min 0.000 / mean 0.138 / max 0.333.

⚠️ Use `probed_marginal` as the observer's response, never `map_profile` (on 35 of 240 items the MAP
pairs the true rule with `outside_bracket_first`; no correctness or marginal is affected).

### With a hidden step: `base-task/hidden.py`
Hiding line `s_k` means neither the observer nor the participant sees it. The two likelihood factors
that touch `s_k` collapse into a marginal over every value it could have taken:
```
P(observed | L, s0) = [prod_{t != k-1, k} pi_L(s_{t+1} | s_t)] · sum_{s_k} pi_L(s_k | s_{k-1}) pi_L(s_{k+1} | s_k)
```
`two_step_prob`, `hidden_log_likelihood`, `hidden_posterior(trace, k)` handle one hidden line;
`gap_prob` (forward DP over every intermediate path), `multi_hidden_log_likelihood` and
`multi_hidden_posterior(trace, hide_set)` handle ANY set of hidden lines. The two paths agree
exactly. `s0` and the final answer must stay visible. `visible_trace(trace, k)` returns the lines a
participant would see. Hiding can only flatten the posterior, never sharpen it.

---

## 5. Hidden steps: what the observer does, and what it means for the design

All numbers below are on this repo's 240-item pool (recomputed 2026-09-13; an earlier version of
these findings was measured on an older pool and is superseded).

### Per-item marginals: `base-task/bayes_hidden.py` -> `base-task/bayes_per_item_hidden.json`
960 rows (240 items x 4 conditions) with `probed_marginal`, `delta_vs_full`, `observer_agrees`,
`observer_correct`, `hidden_line`, `n_lines_shown`. Conditions: `none` (every line shown), `s2`, `s4`,
and `error_line` (hide the line PRODUCED by the error: `s1` when the error is at step 1, `s3` when at
step 3).

| condition | accuracy | category A marginal | category B marginal |
|---|---|---|---|
| none | 240/240 | 1.000 flat | mean 0.138 |
| **s2** | 240/240 | **1.000 flat** | mean 0.137 |
| **s4** | 240/240 | **1.000 flat** | mean 0.140 |
| error_line | 240/240 | mean 0.985, min 0.556 | mean 0.138 |

**The observer is 240/240 correct in every condition: no hidden line ever flips a judgement.**

### ⚠️ MEASURED: hiding steps removes almost no information from the ideal observer
- **Hiding s2 or s4 (the proposed manipulation) changes the marginal on 7 of 480 item-by-hide
  combinations, all in category B. Category A stays at exactly 1.000.**
- Sweeping every hideable line, the only category-A items that ever move are 1 (hide `s1`, error at
  step 1) and 5 (hide `s3`, error at step 3), i.e. only when the hidden line is the one the error
  produced.
- Hiding the error's own line moves 10 items in all: 6 in category A, **all six
  `outside_bracket_first`** (A110 1.000 -> 0.556, A111 0.667, A114 0.706, A115 0.714, A106 0.727, A112
  0.857), plus 4 B items (2 `sub_before_mul`, 2 `sub_before_div` traces).
- Category A with more hidden: hide s2 and s4 together, still 1.000; hide s1, s3 and s5, 0.986; hide
  ALL FIVE intermediate lines (only the expression and the answer shown), 0.933, with 18 of 120 below
  1.000 and 3 below 0.5.
- The work without the final answer: still 1.000. **Only the first step shown**: error-at-step-1
  items 1.000, error-at-step-3 items **0.333**. The one thing that really degrades the observer is not
  having reached the error yet.

**Why. Two reasons, for different cells; do not merge them.**
1. *Hiding a correct step (s2 or s4 with the error elsewhere): correct steps carry almost no
   evidence.* Steps 1 and 3 carry 85% of all hypothesis eliminations and step 6 none (§3 item 5).
   When the error is at step 1, the observer still sees the illegal move `s0 -> s1` directly and
   infers nothing about the hidden correct step.
2. *Hiding a line next to the error (error at step 3 with s2 hidden, or the error's own line): the
   gap is pinned by its endpoints.* Marginalising over the hidden state keeps only profiles that can
   bridge `s_{k-1} -> s_{k+1}` in two steps, and usually only the true profile can, so the elimination
   still happens. The exception is `outside_bracket_first`: it is the only rule that removes options,
   so its evidence is the only kind a single hidden line can dilute.
The information is also redundant across routes: the work alone identifies the rule (1.000 without
the answer) and the expression plus the answer nearly does (0.933).

### What this means for the design
Hiding is **normatively almost free**. That is a legitimate framing for the human arm: people cannot
marginalise over paths, so any effect of hiding is pure processing cost, just like error position in
Experiment 1. But it means **the Bayes arm is a flat line on this factor**, as it is on position, so
the ideal observer contributes no gradient to a human-vs-observer comparison. Decide deliberately
whether that is acceptable. If observer-side variance is wanted, hiding is the wrong lever; it would
need genuine ambiguity (traces that several profiles produce identically).

### Open design questions (the user's to decide; discuss before building)
1. **Which step is hidden, absolute or relative?** The proposal is "step 2 or step 4". But hiding `s2`
   sits next to a step-3 error and not a step-1 error, so it is a different manipulation at the two
   error positions. A relative definition (hide the error's own line vs a line far from it) crosses
   cleanly with position, and is the only version where the observer moves at all.
2. **How many items, and is there a no-hide control?** The pool is already balanced on
   misconception x position x statement, so crossing in the hidden factor is automatic; no rebuild
   needed.
   - **480 items**: both hidden versions of all 240 (A = 6 x 2 x 2 = 24 cells x 10; B = 6 x 5 x 2 x 2
     = 120 cells x 2). Hiding becomes within-expression, but each expression then backs 2 items, so a
     participant must see at most one of them.
   - **240 items**: one hidden version per item (A 5 per cell, B 1 per cell; B gets thin).
   - A **no-hide control** as a third level gives 360 or 720. Without it, the effect of hiding can only
     be measured against Experiment 1 as a separate study.
3. **How many trials per participant?** Experiment 1's form is exactly 24 = 6 misconceptions x 2
   positions x 2 statement types, one trial per cell. A fourth, 2-level factor does not fit at one trial
   per cell: it needs 48 trials, or a 24-trial form that covers only half the cells per person.
4. **How the hidden line is displayed** (an ellipsis line, "a step is not shown", nothing at all), and
   whether participants are told a step is missing.

---

## 6. Figures (`analysis-Bayesian/`)

- **`bayes_common.py`** shared loader and styling; reads `base-task/bayes_per_item.json`.
- **`plot_bayes_1misc_heatmap.py`**, **`plot_bayes_1misc_by_rule.py`**, **`plot_bayes_1misc_profile.py`**
  -> the three fully observed figures, identical to Experiment 1's (present x named heatmap with 0
  empty cells; P(rule | trace) present vs absent per rule; all six marginals per trace).
- **`plot_bayes_hidden_dist_A.py`** -> `bayes_hidden_dist_A.png`. Category A, one panel per
  misconception, one stem series per hidden condition, from `bayes_per_item_hidden.json`. `none`,
  `s2` and `s4` are exactly equal on all 120 A items, so three series coincide at 1.000 in every panel
  (offset only to be visible). **All movement is in the `outside_bracket_first` panel**, where hiding
  the error's own line takes 6 of its 20 items below 1.000 (panel mean 1.000 -> 0.911).

Finding carried over from the base pool: over the 1200 (trace, absent rule) combinations, 42 give an
ABSENT rule a marginal above 0.35 and 27 above 0.5 (max 0.871), all 27 `outside_bracket_first`, and
the pool excludes all of them from category B.

Rules for any new figure: category A is a point mass at 1.000, do not draw its "distribution";
marginals are discrete, use exact-value stems, not KDEs; never split by `foil_status`; never group by
one rule while plotting the marginal selected by a different rule.

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
  tracking, bonus scoring). **Needs a way to render a hidden line.**
- **`src/user/utils/sampleForm.js`** + Python twin **`base-task/sample_form.py`**: Experiment 1's
  sampler (four pools by category x position, one item per misconception from each, 24 trials, same
  seeded PRNG in both languages; `python3 sample_form.py` runs its 500-seed checks). **Knows nothing
  about hidden steps.**
- **`src/user/data/stimulus_pool.json`** = the base pool (identical to `base-task/`).
  **`src/user/data/practice_items.json`** = Experiment 1's 3 practice items, written by
  `base-task/practice.py`; they show every step.
- **`InstructionsView.vue`** / **`quizQuestions.js`**: Experiment 1's user-approved text and 4-question
  quiz. They say nothing about hidden steps.
- **`PracticeView.vue`** feedback highlights the error step amber; with hidden steps it needs
  deciding what to highlight if the error's line is the hidden one.
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
- [ ] Design decided (§5) and the hidden-step frontend, sampler, practice items, instructions and quiz
      built for it (§9), deployed, and the LIVE bundle verified to contain them.
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
deploys the live experiment**; other branches get separate staging sites. Commits touching only
`*.md` files or `docs/` do NOT deploy (`paths-ignore`). Monitor with `gh run list` / `gh run watch`.
A transient "SSH i/o timeout" at "create the remote folders" has happened; `gh run rerun <id>
--failed` fixed it.

---

## 8. Commands cheat-sheet

```bash
# Base pool and fully observed observer
cd base-task && python3 verify.py          # independent checks on the base pool
cd base-task && python3 bayes.py           # -> bayes_per_item.json (expect 240/240)
cd base-task && python3 pool.py            # rebuild the base pool (seed 2026); only if deliberately changing it

# Hidden steps
cd base-task && python3 bayes_hidden.py    # -> bayes_per_item_hidden.json (960 rows) + summary

# Frontend helpers (Experiment 1 versions)
cd base-task && python3 sample_form.py     # sampler checks over 500 seeds (twin of sampleForm.js)
cd base-task && python3 practice.py        # check + write practice items to src/user/data/

# Figures (from repo root)
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

## 9. What is next

1. **Decide the design** with the user (§5 open questions 1 to 4). Finish that discussion before
   writing code.
2. **Build the hidden-step stimuli**: which line each item hides, stored per item (e.g. a
   `hidden_line` field) or as a separate derived pool; extend `verify.py` to check it; rerun
   `bayes_hidden.py` for exactly the chosen conditions.
3. **Frontend**: render the hidden line in `TraceJudgmentView.vue` and `PracticeView.vue`; new
   sampler in `sampleForm.js` and `sample_form.py` for the decided form, checked over 500 seeds in
   both languages; new practice items with a hidden line; instructions and quiz that explain it.
4. **Deploy**: secrets (§1), then deploy and verify the live bundle before any participant.
5. The §7 checklist.

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
- **The base pool is a copy of Experiment 1's** (§0). Do not assume a change in one repo reaches the
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
