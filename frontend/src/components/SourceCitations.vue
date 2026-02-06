<template>
  <div v-if="sources.length" class="mt-2">
    <button
      @click="open = !open"
      class="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
    >
      <span>{{ open ? '▾' : '▸' }}</span>
      <span>{{ sources.length }} source{{ sources.length > 1 ? 's' : '' }}</span>
    </button>
    <ul v-if="open" class="mt-1 text-xs text-gray-600 list-disc list-inside">
      <li v-for="(src, i) in sources" :key="i" class="truncate" :title="src.source">
        {{ src.source }}
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  sources: { type: Array, default: () => [] }
})

const open = ref(false)
</script>