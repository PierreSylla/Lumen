<script setup>
defineProps({ modelValue: { type: String, default: '' }, placeholder: { type: String, default: '' } })
defineEmits(['update:modelValue'])
</script>

<template>
  <input
    class="field"
    type="text"
    :value="modelValue"
    :placeholder="placeholder"
    @input="$emit('update:modelValue', $event.target.value)"
  />
</template>

<style scoped>
.field {
  background: var(--inset);
  border: 1px solid var(--panel-line);
  border-radius: 9px;
  padding: 9px 11px;
  font-size: 14px;
  font-family: inherit;
  color: var(--ink);
  width: 100%;
}
.field::placeholder {
  color: var(--field-ph);
}
.field:focus {
  outline: 1px solid var(--accent);
  outline-offset: -1px;
}
</style>
