<template>
  <div :class="['flex', role === 'user' ? 'justify-end' : 'justify-start', 'mb-4']">
    <div :class="[
      'max-w-[80%] rounded-lg px-4 py-3',
      role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900'
    ]">
      <div v-for="(seg, i) in rendered" :key="i">
        <div v-if="seg.type === 'html'" v-html="seg.html" class="prose prose-sm max-w-none"></div>
        <div v-else-if="seg.type === 'svg'" v-html="seg.svg" class="my-3 overflow-x-auto"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { marked } from 'marked'
import mermaid from 'mermaid'

const props = defineProps({
  content: String,
  role: String
})

const rendered = ref([])

mermaid.initialize({ startOnLoad: false, theme: 'default' })

const FENCED_MERMAID = /```mermaid\s*\n([\s\S]*?)```/g
const MERMAID_KEYWORDS = /^(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitgraph|mindmap|timeline)\b/m

function extractRawMermaid(text) {
  const match = text.match(MERMAID_KEYWORDS)
  if (!match) return null

  const startIdx = match.index
  const before = text.slice(0, startIdx)
  const lines = text.slice(startIdx).split('\n')
  const mermaidLines = []
  const restLines = []
  let inDiagram = true

  for (const line of lines) {
    if (inDiagram) {
      const stripped = line.trim()
      if (
        stripped === '' ||
        line.startsWith('    ') ||
        line.startsWith('\t') ||
        MERMAID_KEYWORDS.test(line) ||
        stripped.startsWith('style ') ||
        stripped.startsWith('classDef ') ||
        stripped.startsWith('class ') ||
        stripped.includes('-->') ||
        stripped.includes('---') ||
        stripped.includes('-.->' ) ||
        stripped.startsWith('subgraph') ||
        stripped.startsWith('end') ||
        stripped.startsWith('direction ') ||
        /^\s*\w+[\[({]/.test(stripped)
      ) {
        mermaidLines.push(line)
      } else {
        inDiagram = false
        restLines.push(line)
      }
    } else {
      restLines.push(line)
    }
  }

  // Trim trailing empty lines from diagram
  while (mermaidLines.length && !mermaidLines[mermaidLines.length - 1].trim()) {
    mermaidLines.pop()
  }

  return {
    before: before.trim(),
    mermaid: mermaidLines.join('\n').trim(),
    after: restLines.join('\n').trim()
  }
}

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function sanitizeMermaid(text) {
  return text
    // Remove trailing semicolons from lines
    .replace(/;\s*$/gm, '')
    // Quote node labels containing special chars, handling existing quotes
    .replace(/\[([^\]]+)\]/g, (_, label) => {
      const t = label.trim()
      // Already properly quoted
      if (t.startsWith('"') && t.endsWith('"')) return `[${label}]`
      // Has special chars that need quoting — strip inner quotes to avoid nesting
      if (/[()/:"]/.test(t)) return `["${t.replace(/"/g, '')}"]`
      return `[${label}]`
    })
    // Escape parens inside pipe labels: |text (abc)| → |text &#40;abc&#41;|
    .replace(/\|([^|]*)\|/g, (_, label) =>
      '|' + label.replace(/\(/g, '#40;').replace(/\)/g, '#41;') + '|'
    )
    // Quote edge labels with special characters (-- label --> syntax)
    .replace(
      /(--|\.\.|-\.)\s+([^|>\n"]+?)\s+(-->|-.->|==>|\.\.>|\.->)/g,
      (_, start, label, end) => `${start} "${label.trim()}" ${end}`
    )
}

function cleanupMermaidElement(id) {
  const el = document.getElementById(id)
  if (el) el.remove()
}

function parseSegments(text) {
  // Try fenced mermaid first
  const segments = []
  let last = 0
  for (const match of text.matchAll(FENCED_MERMAID)) {
    if (match.index > last) segments.push({ type: 'md', text: text.slice(last, match.index) })
    segments.push({ type: 'mermaid', text: match[1].trim() })
    last = match.index + match[0].length
  }
  if (segments.length > 0) {
    if (last < text.length) segments.push({ type: 'md', text: text.slice(last) })
    return segments
  }

  // No fenced blocks — try raw mermaid detection
  const raw = extractRawMermaid(text)
  if (raw) {
    if (raw.before) segments.push({ type: 'md', text: raw.before })
    segments.push({ type: 'mermaid', text: raw.mermaid })
    if (raw.after) segments.push({ type: 'md', text: raw.after })
    return segments
  }

  return [{ type: 'md', text }]
}

async function render() {
  const segs = parseSegments(props.content || '')
  const result = []
  for (const seg of segs) {
    if (seg.type === 'md') {
      result.push({ type: 'html', html: marked.parse(seg.text) })
    } else {
      const id = `mermaid-${Date.now()}-${Math.random().toString(36).slice(2)}`
      const sanitized = sanitizeMermaid(seg.text)
      try {
        // Try sanitized version first (handles most LLM syntax issues)
        const { svg } = await mermaid.render(id, sanitized)
        result.push({ type: 'svg', svg })
      } catch (err) {
        cleanupMermaidElement(id)
        // Fall back to raw input in case sanitizer changed valid syntax
        try {
          const { svg } = await mermaid.render(id + 'r', seg.text)
          result.push({ type: 'svg', svg })
        } catch (err2) {
          cleanupMermaidElement(id + 'r')
          console.warn('Mermaid render failed:', err2)
          result.push({ type: 'html', html: `<pre class="bg-gray-200 p-2 rounded text-sm overflow-x-auto"><code>${escapeHtml(seg.text)}</code></pre>` })
        }
      }
    }
  }
  rendered.value = result
}

onMounted(render)
watch(() => props.content, render)
</script>