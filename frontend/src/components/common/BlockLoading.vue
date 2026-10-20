<script setup lang="ts">
defineProps<{
  text?: string
}>()
</script>

<template>
  <div class="block-loading" role="status">
    <span class="spinner"></span>
    <span class="loading-text">{{ text ?? '加载中，请稍候…' }}</span>
  </div>
</template>

<style scoped>
.block-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8) var(--space-4);
  color: var(--color-muted-foreground);
}

.spinner {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 3px solid rgba(0, 82, 255, 0.15);
  border-top-color: var(--color-accent);
  animation: spin 0.8s linear infinite;
}

.loading-text {
  font-size: 13px;
  letter-spacing: 0.02em;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>