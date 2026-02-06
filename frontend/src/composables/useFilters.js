import { ref } from 'vue'
import { getOwners, getCompanies, getCategories } from '../api/client'

const owners = ref([])
const companies = ref([])
const categories = ref([])
const selectedOwner = ref(null)
const selectedCompany = ref(null)
const selectedCategory = ref(null)
const selectedYear = ref(null)

export function useFilters() {
  async function loadFilters() {
    const [o, co, ca] = await Promise.all([getOwners(), getCompanies(), getCategories()])
    owners.value = o
    companies.value = co
    categories.value = ca
  }

  function getActiveFilters() {
    const f = {}
    if (selectedOwner.value) f.owner = selectedOwner.value
    if (selectedCompany.value) f.company = selectedCompany.value
    if (selectedCategory.value) f.category = selectedCategory.value
    if (selectedYear.value) f.year = parseInt(selectedYear.value)
    return f
  }

  function clearFilters() {
    selectedOwner.value = null
    selectedCompany.value = null
    selectedCategory.value = null
    selectedYear.value = null
  }

  return {
    owners, companies, categories,
    selectedOwner, selectedCompany, selectedCategory, selectedYear,
    loadFilters, getActiveFilters, clearFilters
  }
}