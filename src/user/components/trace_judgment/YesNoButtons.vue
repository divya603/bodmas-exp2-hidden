<script setup>
// The YES / NO answer for a trial (user's design, 2026-09-16): two buttons plus
// the D (YES) and F (NO) keys. Emits 'answer' with { response: 'yes' | 'no',
// method: 'key' | 'click' }. Keys and clicks are ignored while `disabled`.
// `chosen` keeps the given answer highlighted (practice shows it next to the
// feedback). The key listener lives as long as this component is mounted.
import { onKeyDown } from '@vueuse/core'

const props = defineProps({
  disabled: { type: Boolean, default: false },
  chosen: { type: String, default: null },
})
const emit = defineEmits(['answer'])

const KEY_TO_RESPONSE = { d: 'yes', f: 'no' }

function answer(response, method) {
  if (props.disabled) return
  emit('answer', { response, method })
}

onKeyDown(
  ['d', 'D', 'f', 'F'],
  (e) => {
    if (props.disabled || e.metaKey || e.ctrlKey || e.altKey) return
    e.preventDefault()
    answer(KEY_TO_RESPONSE[e.key.toLowerCase()], 'key')
  },
  { dedupe: true }
)

function dim(response) {
  return props.disabled && props.chosen !== response ? 'opacity-40' : ''
}
</script>

<template>
  <div class="mb-6">
    <div class="flex justify-center gap-8">
      <button
        type="button"
        :disabled="disabled"
        @click="answer('yes', 'click')"
        class="w-56 py-4 rounded-xl text-2xl font-bold text-white bg-emerald-600 transition"
        :class="[
          dim('yes'),
          chosen === 'yes' ? 'ring-4 ring-emerald-300' : '',
          disabled ? 'cursor-not-allowed' : 'hover:bg-emerald-700',
        ]"
      >
        YES <span class="ml-2 text-lg font-semibold text-white/60">(D)</span>
      </button>
      <button
        type="button"
        :disabled="disabled"
        @click="answer('no', 'click')"
        class="w-56 py-4 rounded-xl text-2xl font-bold text-white bg-rose-600 transition"
        :class="[
          dim('no'),
          chosen === 'no' ? 'ring-4 ring-rose-300' : '',
          disabled ? 'cursor-not-allowed' : 'hover:bg-rose-700',
        ]"
      >
        NO <span class="ml-2 text-lg font-semibold text-white/60">(F)</span>
      </button>
    </div>
    <p class="mt-3 text-center text-muted-foreground">
      Press
      <kbd class="px-1.5 py-0.5 mx-0.5 rounded border border-gray-300 bg-white font-mono text-sm">D</kbd>
      for <strong>YES</strong> or
      <kbd class="px-1.5 py-0.5 mx-0.5 rounded border border-gray-300 bg-white font-mono text-sm">F</kbd>
      for <strong>NO</strong>
    </p>
  </div>
</template>
