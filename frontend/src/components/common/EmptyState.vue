<script setup lang="ts">
defineProps<{
  text?: string
}>()
</script>

<template>
  <div class="empty-state">
    <div class="empty-icon" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
        <circle cx="11" cy="11" r="7" />
        <path d="M21 21l-4.3-4.3" stroke-linecap="round" />
      </svg>
    </div>
    <p class="empty-text">{{ text ?? '暂无数据' }}</p>
    <slot />
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8) var(--space-4);
  color: var(--color-muted-foreground);
}

.empty-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--color-muted);
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon svg {
  width: 22px;
  height: 22px;
}

.empty-text {
  font-size: 13px;
  text-align: center;
  line-height: 1.6;
}
</style>