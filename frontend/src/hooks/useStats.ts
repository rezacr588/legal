/**
 * @fileoverview Custom hook for fetching and managing statistics
 */

import { useState, useEffect, useCallback } from 'react'
import api, { Stats, DetailedStats, TokenStats } from '../services/api'

/**
 * Hook for managing basic statistics with auto-refresh
 */
export function useStats(autoRefresh: boolean = true) {
  const [stats, setStats] = useState<Stats>({} as Stats)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const loadStats = useCallback(async () => {
    try {
      setError(null)
      const data = await api.stats.get()
      setStats(data)
      setLoading(false)
    } catch (err) {
      console.error('Error loading stats:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadStats()

    if (autoRefresh) {
      const interval = setInterval(loadStats, 10000) // Refresh every 10 seconds
      return () => clearInterval(interval)
    }
  }, [loadStats, autoRefresh])

  return { stats, loading, error, refresh: loadStats }
}

/**
 * Hook for managing detailed statistics
 */
export function useDetailedStats() {
  const [detailedStats, setDetailedStats] = useState<DetailedStats | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const loadDetailedStats = useCallback(async () => {
    try {
      setError(null)
      const data = await api.stats.getDetailed()
      if (data.success && data.data) {
        setDetailedStats(data.data)
      }
      setLoading(false)
    } catch (err) {
      console.error('Error loading detailed stats:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDetailedStats()
  }, [loadDetailedStats])

  return { detailedStats, loading, error, refresh: loadDetailedStats }
}

/**
 * Hook for managing token statistics
 */
export function useTokenStats() {
  const [tokenStats, setTokenStats] = useState<TokenStats | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const loadTokenStats = useCallback(async () => {
    try {
      setError(null)
      const data = await api.stats.getTokens()
      if (data.success && data.data) {
        setTokenStats(data.data)
      }
      setLoading(false)
    } catch (err) {
      console.error('Error loading token stats:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadTokenStats()
  }, [loadTokenStats])

  return { tokenStats, loading, error, refresh: loadTokenStats }
}

export default { useStats, useDetailedStats, useTokenStats }
