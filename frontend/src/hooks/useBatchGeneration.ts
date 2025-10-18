/**
 * @fileoverview Custom hook for managing batch generation state
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import api, { BatchHistory, GenerationConfig } from '../services/api'

type NotificationSeverity = 'success' | 'error' | 'info' | 'warning'
type NotificationFunction = (message: string, severity: NotificationSeverity) => void

/**
 * Hook for managing batch generation with SSE updates
 */
export function useBatchGeneration(onNotification: NotificationFunction | null = null) {
  const [batchHistory, setBatchHistory] = useState<BatchHistory[]>([])
  const [batchStatus, setBatchStatus] = useState<any>(null)
  const [stuckBatches, setStuckBatches] = useState<any[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [previousStuckCount, setPreviousStuckCount] = useState<number>(0)

  const eventSourceRef = useRef<EventSource | null>(null)

  // Load batch history
  const loadBatchHistory = useCallback(async () => {
    try {
      const data = await api.generation.getHistory()

      if (data.success && data.data) {
        setBatchHistory(data.data.batches)
      }
    } catch (error) {
      console.error('Error loading batch history:', error)
    }
  }, [])

  // Check for stuck batches
  const checkStuckBatches = useCallback(async () => {
    try {
      const data = await api.generation.getStuckBatches()

      if (data.success && data.data) {
        setStuckBatches(data.data.stuck_batches || [])
      }
    } catch (error) {
      console.error('Error checking stuck batches:', error)
    }
  }, [])

  // Connect to SSE for real-time updates
  const connectSSE = useCallback(() => {
    const eventSource = api.generation.connectSSE()

    eventSource.onmessage = (event: MessageEvent) => {
      if (event.data && event.data !== ': heartbeat') {
        try {
          const message = JSON.parse(event.data)

          let batchData = null
          if (message.type === 'batch_update' && message.batch) {
            batchData = message.batch
          } else if (message.type === 'all_batches' && message.batches) {
            const batches = Object.values(message.batches)
            const runningBatch = batches.find((b: any) => b.running)
            batchData = runningBatch || batches[0]
          } else if (!message.type) {
            batchData = message
          }

          if (batchData) {
            setBatchStatus(batchData)

            if (!batchData.running && batchData.samples_generated > 0) {
              loadBatchHistory()
            }
          }
        } catch (error) {
          console.error('Error parsing SSE data:', error)
        }
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error)
      eventSource.close()
      setTimeout(() => connectSSE(), 5000) // Retry after 5 seconds
    }

    eventSourceRef.current = eventSource
  }, [loadBatchHistory])

  // Start batch generation
  const startBatch = useCallback(async (config: GenerationConfig) => {
    setLoading(true)
    try {
      const data = await api.generation.start(config)
      if (data.success) {
        if (onNotification) {
          onNotification('✅ Batch generation started!', 'success')
        }
        return { success: true }
      } else {
        if (onNotification) {
          onNotification(`Error: ${data.error}`, 'error')
        }
        return { success: false, error: data.error }
      }
    } catch (error) {
      console.error('Error starting batch:', error)
      const message = error instanceof Error ? error.message : 'Unknown error'
      if (onNotification) {
        onNotification(`Failed to start: ${message}`, 'error')
      }
      return { success: false, error: message }
    } finally {
      setLoading(false)
    }
  }, [onNotification])

  // Stop batch generation
  const stopBatch = useCallback(async (batchId?: string) => {
    try {
      await api.generation.stop(batchId)
      loadBatchHistory()
      if (onNotification) {
        onNotification(
          batchId ? `Stopped batch ${batchId}` : 'Stopped all running batches',
          'info'
        )
      }
    } catch (error) {
      console.error('Error stopping batch:', error)
      if (onNotification) {
        onNotification('Failed to stop batch', 'error')
      }
    }
  }, [loadBatchHistory, onNotification])

  // Initialize on mount
  useEffect(() => {
    loadBatchHistory()
    checkStuckBatches()
    connectSSE()

    // Poll for updates every 5 seconds
    const interval = setInterval(() => {
      loadBatchHistory()
      checkStuckBatches()
    }, 5000)

    return () => {
      clearInterval(interval)
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [loadBatchHistory, checkStuckBatches, connectSSE])

  // Notify when stuck batches increase
  useEffect(() => {
    if (stuckBatches.length > previousStuckCount && stuckBatches.length > 0 && onNotification) {
      const newStuckCount = stuckBatches.length - previousStuckCount
      onNotification(
        `⚠️ ${newStuckCount} stuck batch${newStuckCount > 1 ? 'es' : ''} detected!`,
        'warning'
      )
    }
    setPreviousStuckCount(stuckBatches.length)
  }, [stuckBatches, previousStuckCount, onNotification])

  const runningBatches = batchHistory.filter(b => b.status === 'running')

  return {
    batchHistory,
    batchStatus,
    stuckBatches,
    runningBatches,
    loading,
    startBatch,
    stopBatch,
    refresh: loadBatchHistory,
  }
}

export default useBatchGeneration
