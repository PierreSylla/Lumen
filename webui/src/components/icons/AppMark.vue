<script setup>
defineProps({ size: { type: [String, Number], default: 26 } })
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 26 26">
    <circle cx="13" cy="10" r="7" fill="var(--accent)" />
    <rect x="10" y="17" width="6" height="5" rx="1.5" fill="var(--ink-4)" />
  </svg>
</template>
