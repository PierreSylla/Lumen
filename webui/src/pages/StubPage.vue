<script setup>
defineProps({ note: { type: String, required: true } })
</script>

<template>
  <div class="stub">{{ note }}</div>
</template>

<style scoped>
.stub {
  font-size: 13px;
  color: var(--ink-4);
  padding: 20px 4px;
}
</style>
