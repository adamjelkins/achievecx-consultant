import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000)     return `$${Math.round(value / 1_000)}K`
  return `$${value.toLocaleString()}`
}

export function formatPct(value: number): string {
  return `${Math.round(value * 100)}%`
}
