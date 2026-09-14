// Draws one participant's 24-trial form from the Experiment 2 (v6) pool.
// Python twin: base-task/sample_form.py. Both use the same PRNG (mulberry32)
// and the same sequence of draws, so one seed gives the identical form in both
// languages. Change one, change the other, then rerun its checks.
//
// Design (decided 2026-09-14): 4 trials per misconception (the rule present in
// the trace), 8 per difficulty, 12 agree / 12 disagree; 2 agree / 2 disagree
// within each misconception and 4 / 4 within each difficulty. Four trials per
// misconception cannot split evenly over three difficulties, so each
// misconception fills one row of ROWS: one difficulty twice (once agree, once
// disagree), the other two once. Which misconception gets which row is a random
// permutation per participant, so the 36 misconception x difficulty x statement
// cells balance in expectation (Smile has no cross-participant counter for an
// exact rotation). Each cell is a random pool item of that (misconception,
// difficulty, category); a disagree item brings the foil it was built with, so
// which wrong statement a trial names is left to the draw, as in Experiment 1.
// No trace (base_id) is drawn twice, so no expression repeats. Trial order is
// shuffled, and the 24 names are shuffled so each appears exactly once.

const IDS = [
  'add_before_mul',
  'add_before_div',
  'sub_before_mul',
  'sub_before_div',
  'same_priority_rtl',
  'outside_bracket_first',
]

// [difficulty, category] cells per row; A = the statement names the present
// rule (agree), B = it names a foil (disagree). Each difficulty column holds
// 4 A and 4 B over the six rows.
const ROWS = [
  [['easy', 'A'], ['easy', 'B'], ['medium', 'A'], ['hard', 'B']],
  [['easy', 'A'], ['easy', 'B'], ['medium', 'B'], ['hard', 'A']],
  [['easy', 'A'], ['medium', 'A'], ['medium', 'B'], ['hard', 'B']],
  [['easy', 'B'], ['medium', 'A'], ['medium', 'B'], ['hard', 'A']],
  [['easy', 'A'], ['medium', 'B'], ['hard', 'A'], ['hard', 'B']],
  [['easy', 'B'], ['medium', 'A'], ['hard', 'A'], ['hard', 'B']],
]

// One name per trial (24), so no participant ever sees the same student twice.
// Names baked into the pool JSON are placeholders, replaced here at sampling
// time. Keep in sync with STUDENT_NAMES in base-task/pool.py.
const STUDENT_NAMES = [
  'Noah', 'Maya', 'Liam', 'Ava', 'Ethan', 'Zoe',
  'Mia', 'Lucas', 'Emma', 'Owen', 'Sofia', 'Caleb',
  'Ruby', 'Jonah', 'Isla', 'Felix', 'Nora', 'Dylan',
  'Priya', 'Marcus', 'Elena', 'Theo', 'Jasmine', 'Omar',
]

// Small seeded PRNG (mulberry32) so a given seed always reproduces the same form.
function makeRng(seed) {
  let s = seed >>> 0
  function next() {
    s = (s + 0x6d2b79f5) | 0
    let t = Math.imul(s ^ (s >>> 15), 1 | s)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
  return {
    choice(arr) {
      return arr[Math.floor(next() * arr.length)]
    },
    shuffle(arr) {
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(next() * (i + 1))
        ;[arr[i], arr[j]] = [arr[j], arr[i]]
      }
      return arr
    },
  }
}

export function sampleForm(pool, seed) {
  const rng = makeRng(seed)
  const rows = rng.shuffle(IDS.slice()) // rows[r] = the misconception filling ROWS[r]
  const form = []
  const used = new Set()
  rows.forEach((mid, r) => {
    for (const [difficulty, category] of ROWS[r]) {
      const members = pool.filter(
        (it) =>
          it.misconceptions[0] === mid &&
          it.difficulty === difficulty &&
          it.category === category &&
          !used.has(it.base_id)
      )
      const item = rng.choice(members)
      used.add(item.base_id)
      form.push(item)
    }
  })
  rng.shuffle(form)

  // Assign each trial a distinct student name (copies, so the shared pool
  // objects are never mutated), rewriting the belief statement to match. Every
  // pool statement begins with its placeholder name.
  const names = rng.shuffle(STUDENT_NAMES.slice())
  return form.map((it, i) => ({
    ...it,
    student_name: names[i],
    belief_statement: names[i] + it.belief_statement.slice(it.student_name.length),
  }))
}

export function randomSeed() {
  return Math.floor(Math.random() * 2 ** 31)
}
