// Checks that the live JS sampler (src/user/utils/sampleForm.js) draws exactly
// the forms its Python twin does. Reads the twin's dump on stdin:
//
//   cd base-task && python3 sample_form.py --dump 500 | node sample_form_parity.mjs
//
// Exits non-zero on any mismatch.
import { readFileSync } from 'fs'
import { sampleForm } from '../src/user/utils/sampleForm.js'

const pool = JSON.parse(readFileSync(new URL('../src/user/data/stimulus_pool.json', import.meta.url), 'utf8'))
const py = JSON.parse(readFileSync(0, 'utf8'))

let same = 0
py.forEach((form, seed) => {
  const js = sampleForm(pool, seed).map((it) => [it.id, it.student_name])
  if (JSON.stringify(js) === JSON.stringify(form)) same++
  else console.log(`seed ${seed} differs`)
})
console.log(`${same}/${py.length} seeds: JS form identical to Python`)
process.exit(same === py.length ? 0 : 1)
