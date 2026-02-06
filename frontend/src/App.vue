<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Sidebar -->
    <FilterSidebar class="w-56 flex-shrink-0" @clear-chat="clearChat" />

    <!-- Main -->
    <div class="flex-1 flex flex-col min-w-0">
      <StatsBar v-model:view="view" />
      <ChatPanel v-if="view === 'chat'" class="flex-1 min-h-0" />
      <GraphExplorer v-else class="flex-1 min-h-0" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FilterSidebar from './components/FilterSidebar.vue'
import StatsBar from './components/StatsBar.vue'
import ChatPanel from './components/ChatPanel.vue'
import GraphExplorer from './components/GraphExplorer.vue'
import { useChat } from './composables/useChat'

const view = ref('chat')
const { clearChat } = useChat()
</script>
