import { reactive } from 'vue'

export interface ToastItem {
  id: number
  message: string
  type: 'success' | 'error'
}

const state = reactive<{
  toasts: ToastItem[]
}>({
  toasts: []
})

let nextId = 1

function showToast(message: string, type: 'success' | 'error' = 'error'): void {
  const id = nextId++
  state.toasts.push({ id, message, type })
  window.setTimeout(() => {
    dismiss(id)
  }, 2600)
}

function dismiss(id: number): void {
  const index = state.toasts.findIndex((t) => t.id === id)
  if (index !== -1) {
    state.toasts.splice(index, 1)
  }
}

export function useToast() {
  return {
    state,
    showToast,
    dismiss
  }
}