<template>
  <aside class="bg-white border-r border-gray-200 p-4 flex flex-col gap-4">
    <h2 class="font-semibold text-gray-800 text-sm">Filters</h2>

    <div>
      <label class="block text-xs text-gray-500 mb-1">Owner</label>
      <select v-model="selectedOwner" class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm">
        <option :value="null">All</option>
        <option v-for="o in owners" :key="o" :value="o">{{ o }}</option>
      </select>
    </div>

    <div>
      <label class="block text-xs text-gray-500 mb-1">Company</label>
      <select v-model="selectedCompany" class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm">
        <option :value="null">All</option>
        <option v-for="c in companies" :key="c" :value="c">{{ c }}</option>
      </select>
    </div>

    <div>
      <label class="block text-xs text-gray-500 mb-1">Category</label>
      <select v-model="selectedCategory" class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm">
        <option :value="null">All</option>
        <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
      </select>
    </div>

    <div>
      <label class="block text-xs text-gray-500 mb-1">Year</label>
      <input
        v-model="selectedYear"
        type="number"
        placeholder="e.g. 2024"
        class="w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
      />
    </div>

    <button
      @click="clearFilters"
      class="mt-2 text-xs text-blue-600 hover:text-blue-800"
    >
      Clear filters
    </button>

    <button
      @click="$emit('clear-chat')"
      class="mt-auto rounded bg-gray-100 px-3 py-2 text-xs text-gray-600 hover:bg-gray-200"
    >
      Clear Chat
    </button>
  </aside>
</template>

<script setup>
import { onMounted } from 'vue'
import { useFilters } from '../composables/useFilters'

defineEmits(['clear-chat'])

const {
  owners, companies, categories,
  selectedOwner, selectedCompany, selectedCategory, selectedYear,
  loadFilters, clearFilters
} = useFilters()

onMounted(loadFilters)
</script>