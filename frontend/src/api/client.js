export async function postQuery(query, filters = {}) {
  const res = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, ...filters })
  })
  if (!res.ok) throw new Error(`Query failed: ${res.status}`)
  return res.json()
}

export async function getOwners() {
  const res = await fetch('/api/metadata/owners')
  return res.json()
}

export async function getCompanies() {
  const res = await fetch('/api/metadata/companies')
  return res.json()
}

export async function getCategories() {
  const res = await fetch('/api/metadata/categories')
  return res.json()
}

export async function getStats() {
  const res = await fetch('/api/metadata/stats')
  return res.json()
}

export async function getGraphData() {
  const res = await fetch('/api/graph/data')
  return res.json()
}