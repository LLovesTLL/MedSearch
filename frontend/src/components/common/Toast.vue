<script setup lang="ts">
import { useToast } from '../../composables/useToast'

const { state, dismiss } = useToast()
</script>

<template>
  <div class="toast-container" aria-live="polite">
    <transition-group name="toast">
      <div
        v-for="toast in state.toasts"
        :key="toast.id"
        class="toast-item"
        :class="`toast-${toast.type}`"
        @click="dismiss(toast.id)"
      >
        <span class="toast-icon" aria-hidden="true">
          <svg
            v-if="toast.type === 'success'"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.4"
          >
            <path d="M20 6L9 17l-5-5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <svg
            v-else
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.4"
          >
            <path d="M12 8v5" stroke-linecap="round" />
            <path d="M12 16.5h.01" stroke-linecap="round" />
            <circle cx="12" cy="12" r="9" />
          </svg>
        </span>
        <span class="toast-message">{{ toast.message }}</span>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: calc(16px + env(safe-area-inset-top));
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  width: max-content;
  max-width: calc(100vw - 32px);
  pointer-events: none;
}

.toast-item {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 10px 16px;
  border-radius: var(--radius-full);
  font-size: 13px;
  font-weight: 500;
  color: #ffffff;
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(8px);
  cursor: pointer;
  max-width: 100%;
}

.toast-success {
  background: rgba(22, 163, 74, 0.94);
}

.toast-error {
  background: rgba(220, 38, 38, 0.94);
}

.toast-icon {
  display: inline-flex;
  flex-shrink: 0;
}

.toast-icon svg {
  width: 15px;
  height: 15px;
}

.toast-message {
  overflow-wrap: anywhere;
}

.toast-enter-active,
.toast-leave-active {
  transition: all var(--duration-normal) var(--ease-out);
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(-14px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>