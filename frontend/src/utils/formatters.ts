/**
 * @fileoverview Utility functions for formatting data
 */

/**
 * Format a number with thousand separators
 */
export function formatNumber(num: number | null | undefined): string {
  if (num == null) return '0'
  return num.toLocaleString()
}

/**
 * Format a date/timestamp to localized string
 */
export function formatDate(timestamp: string | Date | null | undefined): string {
  if (!timestamp) return 'N/A'

  try {
    return new Date(timestamp).toLocaleString()
  } catch (e) {
    return 'Invalid Date'
  }
}

/**
 * Format a timestamp to relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(timestamp: string | Date | null | undefined): string {
  if (!timestamp) return 'Unknown'

  try {
    const now = new Date()
    const date = new Date(timestamp)
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`

    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return 'Unknown'
  }
}

/**
 * Format duration in seconds to human-readable string
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null || seconds < 0) return 'N/A'

  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60

  if (mins > 0) {
    return `${mins}m ${secs}s`
  }
  return `${secs}s`
}

/**
 * Format duration between two timestamps
 */
export function formatDurationBetween(
  startTime: string | Date | null | undefined,
  endTime: string | Date | null | undefined = null
): string {
  if (!startTime) return 'N/A'

  try {
    const start = new Date(startTime)
    const end = endTime ? new Date(endTime) : new Date()
    const seconds = Math.round((end.getTime() - start.getTime()) / 1000)

    return formatDuration(seconds)
  } catch (e) {
    return 'N/A'
  }
}

/**
 * Truncate text to a maximum length with ellipsis
 */
export function truncateText(text: string | null | undefined, maxLength: number = 100): string {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

/**
 * Capitalize first letter of a string
 */
export function capitalize(str: string | null | undefined): string {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

/**
 * Format bytes to human-readable size
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

/**
 * Format percentage value
 */
export function formatPercentage(
  value: number | null | undefined,
  decimals: number = 1,
  isDecimal: boolean = false
): string {
  if (value == null) return '0%'

  const percentage = isDecimal ? value * 100 : value
  return `${percentage.toFixed(decimals)}%`
}

export default {
  formatNumber,
  formatDate,
  formatRelativeTime,
  formatDuration,
  formatDurationBetween,
  truncateText,
  capitalize,
  formatBytes,
  formatPercentage,
}
