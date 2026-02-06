<template>
  <div class="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-2">
    <h1 class="text-lg font-semibold text-gray-800">Knowledge Bot</h1>

    <div v-if="stats" class="flex gap-4 text-xs text-gray-500">
      <span>{{ stats.documents }} docs</span>
      <span>{{ stats.owners }} owners</span>
      <span>{{ stats.companies }} companies</span>
      <span>{{ stats.categories }} categories</span>
    </div>

    <div class="flex gap-1">
      <button
        v-for="v in ['chat', 'graph']"
        :key="v"
        @click="$emit('update:view', v)"
        :class="[
          'rounded px-3 py-1 text-xs font-medium',
          view === v ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        ]"
      >
        {{ v === 'chat' ? 'Chat' : 'Graph' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStats } from '../api/client'

defineProps({
  view: String
})
defineEmits(['update:view'])

const stats = ref(null)

onMounted(async () => {
  try {
    stats.value = await getStats()
  } catch {
    // Stats are non-critical
  }
})
</script>