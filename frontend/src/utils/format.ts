export function formatBytes(n: number | undefined | null): string {
  if (n == null || Number.isNaN(n)) return '—'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

export function formatRatio(n: number | undefined | null, digits = 4): string {
  if (n == null || Number.isNaN(n)) return '—'
  return (n * 100).toFixed(digits) + '%'
}

export function formatNumber(n: unknown, digits = 4): string {
  if (n == null || (typeof n === 'number' && Number.isNaN(n))) return '—'
  if (typeof n === 'number') return Number.isInteger(n) ? String(n) : n.toFixed(digits)
  return String(n)
}
