import { ref } from 'vue'
import { getGraphData } from '../api/client'

const graphData = ref(null)
const graphLoading = ref(false)

export function useGraph() {
  async function loadGraph() {
    graphLoading.value = true
    try {
      graphData.value = await getGraphData()
    } finally {
      graphLoading.value = false
    }
  }

  return { graphData, graphLoading, loadGraph }
}
