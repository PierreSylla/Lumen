<script setup>
defineProps({
  variant: { type: String, default: 'pill' }, // pill | accent | danger
})
</script>

<template>
  <button type="button" class="btn" :class="variant">
    <slot />
  </button>
</template>

<style scoped>
.btn {
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  border-radius: 9px;
  padding: 8px 16px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
}
.btn.pill {
  background: var(--pill);
  border: 1px solid var(--pill-line);
  color: var(--ink-2);
  font-weight: 500;
}
.btn.accent {
  background: var(--accent);
  border: 1px solid var(--accent);
  color: var(--on-accent);
}
.btn.danger {
  background: var(--danger-bg);
  border: 1px solid var(--danger-line);
  color: var(--danger);
  font-weight: 500;
}
</style>
