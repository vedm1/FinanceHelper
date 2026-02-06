<template>
  <div class="h-full flex flex-col">
    <div v-if="graphLoading" class="flex-1 flex items-center justify-center text-gray-500">
      Loading graph...
    </div>
    <div v-else ref="container" class="flex-1"></div>
    <!-- Legend -->
    <div class="flex gap-4 p-3 border-t border-gray-200 text-xs text-gray-600">
      <span v-for="(color, type) in TYPE_COLORS" :key="type" class="flex items-center gap-1">
        <span class="inline-block w-3 h-3 rounded-full" :style="{ backgroundColor: color }"></span>
        {{ type }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Network } from 'vis-network'
import { DataSet } from 'vis-data'
import { useGraph } from '../composables/useGraph'

const { graphData, graphLoading, loadGraph } = useGraph()
const container = ref(null)

const TYPE_COLORS = {
  Document: '#60a5fa',
  Owner: '#f472b6',
  Company: '#34d399',
  Category: '#fbbf24',
  Year: '#a78bfa',
}

onMounted(async () => {
  await loadGraph()
  if (!graphData.value || !container.value) return

  const nodes = new DataSet(graphData.value.nodes.map(n => ({
    id: n.id,
    label: n.label,
    color: TYPE_COLORS[n.type] || '#9ca3af',
    shape: n.type === 'Document' ? 'dot' : 'diamond',
    size: n.type === 'Document' ? 12 : 18,
    title: `${n.type}: ${n.label}`,
    font: { size: 10 }
  })))

  const edges = new DataSet(graphData.value.edges.map((e, i) => ({
    id: i,
    from: e.source,
    to: e.target,
    label: e.relationship,
    arrows: 'to',
    font: { size: 8, align: 'middle' },
    color: { color: '#9ca3af' }
  })))

  new Network(container.value, { nodes, edges }, {
    physics: {
      stabilization: { iterations: 150 },
      barnesHut: { gravitationalConstant: -3000 }
    },
    interaction: { hover: true, tooltipDelay: 200 },
  })
})
</script>