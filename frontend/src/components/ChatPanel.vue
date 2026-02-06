<template>
  <div class="flex flex-col h-full">
    <!-- Messages -->
    <div ref="messagesEl" class="flex-1 overflow-y-auto p-4 space-y-2">
      <div v-for="(msg, i) in messages" :key="i">
        <ChatMessage :content="msg.content" :role="msg.role" />
        <div :class="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'">
          <div class="max-w-[80%]">
            <SourceCitations v-if="msg.role === 'assistant'" :sources="msg.sources || []" />
          </div>
        </div>
      </div>
      <div v-if="loading" class="flex justify-start mb-4">
        <div class="bg-gray-100 rounded-lg px-4 py-3 text-gray-500 animate-pulse">
          Thinking...
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="border-t border-gray-200 p-4">
      <form @submit.prevent="handleSubmit" class="flex gap-2">
        <input
          v-model="input"
          type="text"
          placeholder="Ask a question..."
          class="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          :disabled="loading"
        />
        <button
          type="submit"
          :disabled="!input.trim() || loading"
          class="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import ChatMessage from './ChatMessage.vue'
import SourceCitations from './SourceCitations.vue'
import { useChat } from '../composables/useChat'
import { useFilters } from '../composables/useFilters'

const { messages, loading, sendMessage } = useChat()
const { getActiveFilters } = useFilters()

const input = ref('')
const messagesEl = ref(null)

async function handleSubmit() {
  const query = input.value.trim()
  if (!query) return
  input.value = ''
  await sendMessage(query, getActiveFilters())
}

watch(messages, async () => {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}, { deep: true })
</script>