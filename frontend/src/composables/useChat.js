import { ref } from 'vue'
import { postQuery } from '../api/client'

const messages = ref([
  { role: 'assistant', content: 'Ask me anything and I\'ll retrieve the docs and cite relevant sources.', sources: [] }
])
const loading = ref(false)

export function useChat() {
  async function sendMessage(query, filters) {
    messages.value.push({ role: 'user', content: query, sources: [] })
    loading.value = true
    try {
      const data = await postQuery(query, filters)
      messages.value.push({
        role: 'assistant',
        content: data.answer,
        sources: data.sources
      })
    } catch (e) {
      messages.value.push({
        role: 'assistant',
        content: 'Error: ' + e.message,
        sources: []
      })
    } finally {
      loading.value = false
    }
  }

  function clearChat() {
    messages.value = [messages.value[0]]
  }

  return { messages, loading, sendMessage, clearChat }
}
