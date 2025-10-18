/**
 * @fileoverview Custom hook for managing dataset operations
 */

import { useState, useEffect, useCallback } from 'react'
import api, { Sample } from '../services/api'

type NotificationSeverity = 'success' | 'error' | 'info' | 'warning'
type NotificationFunction = (message: string, severity: NotificationSeverity) => void

export interface SampleWithNumericId extends Sample {
  numericId: number
}

/**
 * Hook for managing dataset with search and CRUD operations
 */
export function useData(onNotification: NotificationFunction | null = null) {
  const [data, setData] = useState<SampleWithNumericId[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const rows = await api.data.getAll()

      // Add numeric IDs for DataGrid
      const rowsWithIds: SampleWithNumericId[] = rows.map((row, idx) => ({
        ...row,
        numericId: idx + 1
      }))

      setData(rowsWithIds)
      setLoading(false)
    } catch (err) {
      console.error('Error loading data:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  // Update sample
  const updateSample = useCallback(async (id: string, updates: Partial<Sample>) => {
    try {
      const result = await api.data.updateSample(id, updates)

      if (result.success) {
        if (onNotification) {
          onNotification(result.message || 'Sample updated successfully', 'success')
        }
        await loadData()
        return { success: true }
      } else {
        if (onNotification) {
          onNotification(result.error || 'Update failed', 'error')
        }
        return { success: false, error: result.error }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      if (onNotification) {
        onNotification(`Update failed: ${message}`, 'error')
      }
      return { success: false, error: message }
    }
  }, [loadData, onNotification])

  // Delete sample
  const deleteSample = useCallback(async (id: string) => {
    try {
      const result = await api.data.deleteSample(id)

      if (result.success) {
        if (onNotification) {
          onNotification(result.message || 'Sample deleted successfully', 'success')
        }
        await loadData()
        return { success: true }
      } else {
        if (onNotification) {
          onNotification(result.error || 'Delete failed', 'error')
        }
        return { success: false, error: result.error }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      if (onNotification) {
        onNotification(`Delete failed: ${message}`, 'error')
      }
      return { success: false, error: message }
    }
  }, [loadData, onNotification])

  // Import from JSONL
  const importJsonl = useCallback(async (content: string) => {
    try {
      const result = await api.data.importJsonl(content)

      if (result.success && result.data) {
        if (onNotification) {
          onNotification(result.message || 'Import successful', 'success')
        }
        await loadData()
        return { success: true, total: result.data.total_samples }
      } else {
        if (onNotification) {
          onNotification(result.error || 'Import failed', 'error')
        }
        return { success: false, error: result.error }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      if (onNotification) {
        onNotification(`Import failed: ${message}`, 'error')
      }
      return { success: false, error: message }
    }
  }, [loadData, onNotification])

  return {
    data,
    loading,
    error,
    loadData,
    updateSample,
    deleteSample,
    importJsonl,
  }
}

export default useData
