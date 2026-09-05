<script setup>
defineEmits(['close'])
</script>

<template>
  <div class="overlay" @click="$emit('close')">
    <div class="panel" @click.stop>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: absolute;
  inset: 0;
  background: var(--overlay);
  display: flex;
  align-items: flex-end;
}
.panel {
  width: 100%;
  border-radius: 16px 16px 0 0;
  border-top: 1px solid var(--sheet-line);
  background: var(--sheet);
  padding: 16px 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 90%;
  overflow-y: auto;
}
</style>
