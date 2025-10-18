import { useState, useEffect, useRef } from 'react'
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  Button,
  LinearProgress,
  Box,
  Chip,
  Alert,
  CircularProgress,
  Fade,
  Grow,
  Zoom,
  Tooltip,
  Divider,
  Paper,
  Grid,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stack,
  Switch,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'
import {
  PlayArrow,
  Stop,
  CheckCircle,
  Cancel,
  Rocket,
  Speed,
  TrendingUp,
  Psychology as AIIcon,
  Topic as TopicIcon,
  BarChart as DifficultyIcon,
  Category as SampleTypeIcon,
  Numbers as CountIcon,
  Create as CustomIcon,
  Cloud as CloudIcon,
  ExpandMore,
  ExpandLess,
  FilterAlt,
  Settings,
  Bolt,
  Visibility,
  Schedule,
  Timer,
  Assessment as QualityIcon,
  Search
} from '@mui/icons-material'

export default function GenerationHub({ onStatsUpdate, onNotification }) {
  // Generation state
  const [providers, setProviders] = useState([])
  const [smartMode, setSmartMode] = useState(true)  // Smart Mode enabled by default
  const [selectedProvider, setSelectedProvider] = useState('auto')
  const [models, setModels] = useState([])
  const [filteredModels, setFilteredModels] = useState([])
  const [topics, setTopics] = useState([])
  const [sampleTypes, setSampleTypes] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [selectedTopic, setSelectedTopic] = useState('all')
  const [selectedDifficulty, setSelectedDifficulty] = useState('balanced')
  const [selectedSampleType, setSelectedSampleType] = useState('balance')
  const [targetCount, setTargetCount] = useState(2500)
  const [currentSamples, setCurrentSamples] = useState(0)
  const [reasoningInstruction, setReasoningInstruction] = useState('')
  const [loading, setLoading] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Batch status state
  const [batchStatus, setBatchStatus] = useState(null)
  const [batchHistory, setBatchHistory] = useState([])
  const [selectedBatch, setSelectedBatch] = useState(null)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [qualityDialogOpen, setQualityDialogOpen] = useState(false)
  const [batchQuality, setBatchQuality] = useState(null)
  const [loadingQuality, setLoadingQuality] = useState(false)
  const [generationModalOpen, setGenerationModalOpen] = useState(false)
  const [stuckBatches, setStuckBatches] = useState([])
  const [previousStuckCount, setPreviousStuckCount] = useState(0)
  const eventSourceRef = useRef(null)

  // Samples viewer state
  const [batchSamples, setBatchSamples] = useState([])
  const [loadingSamples, setLoadingSamples] = useState(false)
  const [detailsTab, setDetailsTab] = useState(0)
  const [sampleSearch, setSampleSearch] = useState('')

  useEffect(() => {
    loadProviders()
    loadModels()
    loadTopics()
    loadSampleTypes()
    loadCurrentCount()
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
  }, [])

  // Filter models when provider changes
  useEffect(() => {
    const filtered = models.filter(m => m.provider === selectedProvider)
    setFilteredModels(filtered)

    if (filtered.length > 0) {
      const currentModelValid = filtered.find(m => m.id === selectedModel)
      if (!currentModelValid) {
        const defaultModel = filtered.find(m =>
          m.id.includes('versatile') || m.id.includes('thinking') || m.id.includes('235b')
        ) || filtered[0]
        setSelectedModel(defaultModel.id)
      }
    }
  }, [selectedProvider, models])

  useEffect(() => {
    if (stuckBatches.length > previousStuckCount && stuckBatches.length > 0 && onNotification) {
      const newStuckCount = stuckBatches.length - previousStuckCount
      onNotification(
        `⚠️ ${newStuckCount} stuck batch${newStuckCount > 1 ? 'es' : ''} detected!`,
        'warning'
      )
    }
    setPreviousStuckCount(stuckBatches.length)
  }, [stuckBatches])

  const loadProviders = async () => {
    try {
      const response = await fetch('/api/providers')
      const data = await response.json()
      if (data.success && data.providers.length > 0) {
        setProviders(data.providers)
        setSelectedProvider(data.default_provider || data.providers[0].id)
      }
    } catch (error) {
      console.error('Error loading providers:', error)
    }
  }

  const loadModels = async () => {
    try {
      const response = await fetch('/api/models')
      const data = await response.json()
      if (data.success) {
        setModels(data.models)
      }
    } catch (error) {
      console.error('Error loading models:', error)
    }
  }

  const loadTopics = async () => {
    try {
      const response = await fetch('/api/topics')
      const data = await response.json()
      setTopics(data.topics || [])
    } catch (error) {
      console.error('Error loading topics:', error)
    }
  }

  const loadSampleTypes = async () => {
    try {
      const response = await fetch('/api/sample-types')
      const data = await response.json()
      if (data.success) {
        setSampleTypes(data.sample_types || [])
        setSelectedSampleType(data.default || 'case_analysis')
      }
    } catch (error) {
      console.error('Error loading sample types:', error)
    }
  }

  const loadCurrentCount = async () => {
    try {
      const response = await fetch('/api/stats')
      const data = await response.json()
      setCurrentSamples(data.total || 0)
    } catch (error) {
      console.error('Error loading stats:', error)
    }
  }

  const loadBatchHistory = async () => {
    try {
      const response = await fetch('/api/generate/batch/history')
      const data = await response.json()

      if (data.success) {
        const batches = data.batches.map(batch => ({
          id: batch.id,
          started_at: batch.started_at,
          completed_at: batch.completed_at,
          model: batch.model || 'Unknown',
          provider: batch.provider,
          topic_filter: batch.topic_filter,
          difficulty_filter: batch.difficulty_filter,
          target: batch.target || 0,
          samples_generated: batch.samples_generated || 0,
          tokens_used: batch.tokens_used || 0,
          status: batch.status,
          errors: batch.errors || []
        }))

        setBatchHistory(batches)
      }
    } catch (error) {
      console.error('Error loading batch history:', error)
    }
  }

  const checkStuckBatches = async () => {
    try {
      const response = await fetch('/api/batches/stuck')
      const data = await response.json()

      if (data.success) {
        setStuckBatches(data.stuck_batches || [])
      }
    } catch (error) {
      console.error('Error checking stuck batches:', error)
    }
  }

  const connectSSE = () => {
    const eventSource = new EventSource('/api/generate/batch/stream')

    eventSource.onmessage = (event) => {
      if (event.data && event.data !== ': heartbeat') {
        try {
          const message = JSON.parse(event.data)

          let batchData = null
          if (message.type === 'batch_update' && message.batch) {
            batchData = message.batch
          } else if (message.type === 'all_batches' && message.batches) {
            const batches = Object.values(message.batches)
            const runningBatch = batches.find(b => b.running)
            batchData = runningBatch || batches[0]
          } else if (!message.type) {
            batchData = message
          }

          if (batchData) {
            setBatchStatus(batchData)

            if (!batchData.running && batchData.samples_generated > 0) {
              onStatsUpdate()
              loadCurrentCount()
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
      setTimeout(() => connectSSE(), 5000)
    }

    eventSourceRef.current = eventSource
  }

  const startBatchGeneration = async () => {
    const payload = {
      target_count: targetCount,
      provider: smartMode ? 'auto' : selectedProvider,
      model: smartMode ? null : selectedModel,
      sample_type: smartMode ? 'balance' : selectedSampleType,
      smart_mode: smartMode
    }

    // Only apply filters if NOT in smart mode (smart mode auto-balances)
    if (!smartMode) {
      if (selectedTopic !== 'all') {
        payload.topic = selectedTopic
      }
      if (selectedDifficulty !== 'balanced') {
        payload.difficulty = selectedDifficulty
      }
    }

    if (reasoningInstruction.trim()) {
      payload.reasoning_instruction = reasoningInstruction.trim()
    }

    setLoading(true)
    try {
      const response = await fetch('/api/generate/batch/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await response.json()
      if (data.success) {
        if (onNotification) {
          onNotification('✅ Batch generation started!', 'success')
        }
        setGenerationModalOpen(false) // Close modal on success
        loadBatchHistory() // Immediately refresh batch list so user sees new batch
      } else {
        if (onNotification) {
          onNotification(`Error: ${data.error}`, 'error')
        }
      }
    } catch (error) {
      console.error('Error starting batch:', error)
      if (onNotification) {
        onNotification(`Failed to start: ${error.message}`, 'error')
      }
    } finally {
      setLoading(false)
    }
  }

  const stopBatch = async (batchId = null) => {
    try {
      const body = batchId ? JSON.stringify({ batch_id: batchId }) : JSON.stringify({})
      await fetch('/api/generate/batch/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body
      })
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
  }

  const loadBatchQuality = async (batchId) => {
    setLoadingQuality(true)
    setBatchQuality(null)
    try {
      const response = await fetch(`/api/batch/${batchId}/quality`)
      const data = await response.json()

      if (data.success) {
        setBatchQuality(data)
        setQualityDialogOpen(true)
      } else {
        if (onNotification) {
          onNotification(`Quality data unavailable: ${data.error}`, 'warning')
        }
      }
    } catch (error) {
      console.error('Error loading batch quality:', error)
      if (onNotification) {
        onNotification('Failed to load quality metrics', 'error')
      }
    } finally {
      setLoadingQuality(false)
    }
  }

  const loadBatchSamples = async (batchId) => {
    setLoadingSamples(true)
    try {
      const response = await fetch(`/api/batch/${batchId}/samples`)
      const data = await response.json()

      if (data.success) {
        setBatchSamples(data.samples)
      } else {
        console.error('Failed to load batch samples:', data.error)
        setBatchSamples([])
        if (onNotification) {
          onNotification('No samples found for this batch', 'info')
        }
      }
    } catch (error) {
      console.error('Error loading batch samples:', error)
      setBatchSamples([])
    } finally {
      setLoadingSamples(false)
    }
  }

  const handleViewDetails = (batch) => {
    setSelectedBatch(batch)
    setDetailsOpen(true)
    setDetailsTab(0)
    setSampleSearch('')
    setBatchSamples([])
    // Load samples when opening details
    loadBatchSamples(batch.id)
  }

  const filteredSamples = batchSamples.filter(sample => {
    if (!sampleSearch) return true
    const searchLower = sampleSearch.toLowerCase()
    return (
      sample.question?.toLowerCase().includes(searchLower) ||
      sample.answer?.toLowerCase().includes(searchLower) ||
      sample.topic?.toLowerCase().includes(searchLower) ||
      sample.difficulty?.toLowerCase().includes(searchLower) ||
      sample.case_citation?.toLowerCase().includes(searchLower)
    )
  })

  const applyPreset = (preset) => {
    switch(preset) {
      case 'quick_100_basic':
        setTargetCount(currentSamples + 100)
        setSelectedDifficulty('basic')
        setSelectedTopic('all')
        break
      case 'balanced_50':
        setTargetCount(currentSamples + 50)
        setSelectedDifficulty('balanced')
        setSelectedTopic('all')
        break
      case 'expert_25':
        setTargetCount(currentSamples + 25)
        setSelectedDifficulty('expert')
        setSelectedTopic('all')
        break
    }
  }

  const getProviderIcon = (providerId) => {
    const icons = { 'groq': '⚡', 'cerebras': '🧠' }
    return icons[providerId] || '🔮'
  }

  const getProviderColor = (providerId) => {
    const colors = { 'groq': '#f55036', 'cerebras': '#7c3aed' }
    return colors[providerId] || '#2196f3'
  }

  const getStatusChip = (status) => {
    const configs = {
      running: {
        label: 'Running',
        icon: <PlayArrow sx={{ fontSize: 14 }} />,
        sx: {
          background: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
          color: 'white',
          fontWeight: 600,
          animation: 'pulse 2s ease-in-out infinite'
        }
      },
      completed: {
        label: 'Completed',
        icon: <CheckCircle sx={{ fontSize: 14 }} />,
        sx: {
          background: 'linear-gradient(135deg, #388e3c 0%, #4caf50 100%)',
          color: 'white',
          fontWeight: 600
        }
      },
      stopped: {
        label: 'Stopped',
        icon: <Cancel sx={{ fontSize: 14 }} />,
        sx: {
          background: 'linear-gradient(135deg, #d32f2f 0%, #f44336 100%)',
          color: 'white',
          fontWeight: 600
        }
      }
    }
    const config = configs[status] || configs.stopped
    return <Chip size="small" label={config.label} icon={config.icon} sx={config.sx} />
  }

  const getDuration = (batch) => {
    if (!batch.started_at) return 'N/A'
    try {
      const start = new Date(batch.started_at)
      const end = batch.completed_at ? new Date(batch.completed_at) : new Date()
      const seconds = Math.round((end - start) / 1000)
      const minutes = Math.floor(seconds / 60)
      return minutes > 0 ? `${minutes}m ${seconds % 60}s` : `${seconds}s`
    } catch (e) {
      return 'N/A'
    }
  }

  const progress = batchStatus?.total > 0 ? (batchStatus.progress / batchStatus.total) * 100 : 0
  const runningBatches = batchHistory.filter(b => b.status === 'running')

  const columns = [
    {
      field: 'status',
      headerName: 'Status',
      width: 130,
      renderCell: (params) => getStatusChip(params.value)
    },
    {
      field: 'started_at',
      headerName: 'Started',
      width: 180,
      valueFormatter: (value) => {
        if (!value) return 'N/A'
        try {
          return new Date(value).toLocaleString()
        } catch (e) {
          return 'Invalid Date'
        }
      }
    },
    { field: 'model', headerName: 'Model', width: 200 },
    {
      field: 'progress',
      headerName: 'Progress',
      width: 200,
      renderCell: (params) => {
        const generated = params.row.samples_generated || 0
        const target = params.row.target || 0
        const displayText = target > 0 ? `${generated} / ${target}` : `${generated} samples`
        const progress = target > 0 ? (generated / target) * 100 : 0

        return (
          <Box sx={{ width: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              {params.row.status === 'running' && <CircularProgress size={14} sx={{ color: '#2196f3' }} />}
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {displayText}
              </Typography>
            </Box>
            {target > 0 && (
              <LinearProgress
                variant="determinate"
                value={Math.min(100, progress)}
                sx={{
                  height: 4,
                  borderRadius: 2,
                  bgcolor: 'rgba(33, 150, 243, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 2,
                    bgcolor: params.row.status === 'running' ? '#2196f3' : '#4caf50'
                  }
                }}
              />
            )}
          </Box>
        )
      }
    },
    {
      field: 'samples_generated',
      headerName: 'Generated',
      width: 110,
      renderCell: (params) => (
        <Typography sx={{ color: 'success.main', fontWeight: 600 }}>
          {params.value}
        </Typography>
      )
    },
    {
      field: 'tokens_used',
      headerName: 'Tokens',
      width: 110,
      valueFormatter: (value) => value?.toLocaleString()
    },
    {
      field: 'duration',
      headerName: 'Duration',
      width: 100,
      renderCell: (params) => getDuration(params.row)
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 160,
      sortable: false,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {params.row.status === 'running' && (
            <IconButton
              size="small"
              color="error"
              onClick={() => stopBatch(params.row.id)}
              title="Stop this batch"
            >
              <Stop />
            </IconButton>
          )}
          <IconButton
            size="small"
            color="primary"
            onClick={() => handleViewDetails(params.row)}
            title="View Details"
          >
            <Visibility />
          </IconButton>
          {(params.row.status === 'completed' || params.row.status === 'stopped') && params.row.samples_generated > 0 && (
            <IconButton
              size="small"
              color="success"
              onClick={() => loadBatchQuality(params.row.id)}
              title="View Quality Metrics"
            >
              <QualityIcon />
            </IconButton>
          )}
        </Box>
      )
    }
  ]

  return (
    <Box>
      {/* Page Header with Add New Batch Button */}
      <Fade in={true} timeout={500}>
        <Card className="fade-in">
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <Typography variant="h5" sx={{ fontWeight: 600, mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Rocket sx={{ color: '#2196f3' }} />
                  Generation Hub
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Monitor batch generation jobs and dataset growth
                </Typography>
              </div>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                {batchStatus?.running && (
                  <Grow in={true}>
                    <Chip
                      label="Generating..."
                      color="primary"
                      className="pulse"
                      icon={<CircularProgress size={16} sx={{ color: 'white' }} />}
                    />
                  </Grow>
                )}
                <Button
                  variant="contained"
                  startIcon={<PlayArrow />}
                  onClick={() => setGenerationModalOpen(true)}
                  size="large"
                  sx={{
                    background: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)',
                    }
                  }}
                >
                  Add New Batch
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Fade>

      {/* Generation Configuration Modal */}
      <Dialog
        open={generationModalOpen}
        onClose={() => setGenerationModalOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            bgcolor: '#001219',
            border: '2px solid rgba(33, 150, 243, 0.3)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.8)'
          }
        }}
      >
        <DialogTitle sx={{ fontWeight: 600, borderBottom: '1px solid rgba(33, 150, 243, 0.2)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Rocket sx={{ color: '#2196f3' }} />
            Configure New Batch Generation
          </Box>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Box>
            <Divider sx={{ mb: 3, borderColor: 'rgba(33, 150, 243, 0.2)' }} />

            {/* Smart Mode Toggle */}
            <Box sx={{ mb: 3, p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)', borderRadius: 2, border: '1px solid rgba(33, 150, 243, 0.2)' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Bolt sx={{ color: '#4caf50', fontSize: 20 }} />
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#4caf50' }}>
                      Smart Mode
                    </Typography>
                    <Chip
                      label="Recommended"
                      size="small"
                      sx={{
                        height: 20,
                        fontSize: '0.7rem',
                        bgcolor: 'rgba(76, 175, 80, 0.2)',
                        color: '#4caf50',
                        fontWeight: 600
                      }}
                    />
                  </Box>
                  <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary', lineHeight: 1.4 }}>
                    {smartMode ? (
                      <>
                        🤖 Auto provider failover • 🎯 Balanced topics & difficulty • 🔄 Sample type rotation • ⚡ Champion models
                      </>
                    ) : (
                      'Enable for intelligent provider failover and automatic balancing'
                    )}
                  </Typography>
                </Box>
                <Switch
                  checked={smartMode}
                  onChange={(e) => setSmartMode(e.target.checked)}
                  sx={{
                    '& .MuiSwitch-switchBase.Mui-checked': {
                      color: '#4caf50',
                    },
                    '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                      backgroundColor: '#4caf50',
                    },
                  }}
                />
              </Box>
            </Box>

            {/* Quick Start Presets */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1.5, display: 'flex', alignItems: 'center', gap: 1, fontWeight: 600 }}>
                <Bolt sx={{ color: '#ff9800', fontSize: 20 }} />
                Quick Start Presets
              </Typography>
              <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => applyPreset('quick_100_basic')}
                  disabled={smartMode}
                  sx={{
                    flex: '1 1 auto',
                    minWidth: '140px',
                    borderColor: '#4caf50',
                    color: '#4caf50',
                    '&:hover': { borderColor: '#45a049', bgcolor: 'rgba(76, 175, 80, 0.08)' }
                  }}
                >
                  100 Basic
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => applyPreset('balanced_50')}
                  disabled={smartMode}
                  sx={{
                    flex: '1 1 auto',
                    minWidth: '140px',
                    borderColor: '#2196f3',
                    color: '#2196f3',
                    '&:hover': { borderColor: '#1976d2', bgcolor: 'rgba(33, 150, 243, 0.08)' }
                  }}
                >
                  50 Balanced
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => applyPreset('expert_25')}
                  disabled={smartMode}
                  sx={{
                    flex: '1 1 auto',
                    minWidth: '140px',
                    borderColor: '#f44336',
                    color: '#f44336',
                    '&:hover': { borderColor: '#d32f2f', bgcolor: 'rgba(244, 67, 54, 0.08)' }
                  }}
                >
                  25 Expert
                </Button>
              </Box>
            </Box>

            {/* Essential Configuration */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1.5, display: 'flex', alignItems: 'center', gap: 1, fontWeight: 600 }}>
                <Settings sx={{ color: '#2196f3', fontSize: 20 }} />
                Essential Settings
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Zoom in={true} timeout={300}>
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)', borderRadius: 3, border: '1px solid rgba(33, 150, 243, 0.2)' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                        <CloudIcon sx={{ color: '#2196f3', fontSize: 24 }} />
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2196f3' }}>
                          Provider
                        </Typography>
                      </Box>
                      <FormControl fullWidth variant="outlined">
                        <Select
                          value={selectedProvider}
                          onChange={(e) => setSelectedProvider(e.target.value)}
                          disabled={smartMode}
                          displayEmpty
                          sx={{
                            '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(33, 150, 243, 0.3)' },
                            '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(33, 150, 243, 0.5)' }
                          }}
                        >
                          {providers.map(provider => (
                            <MenuItem key={provider.id} value={provider.id}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <span>{getProviderIcon(provider.id)}</span>
                                <span>{provider.name}</span>
                                <Chip
                                  size="small"
                                  label={`${(provider.requests_per_minute/60).toFixed(0)} req/min`}
                                  sx={{ ml: 'auto', fontSize: '0.7rem' }}
                                />
                              </Box>
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Paper>
                  </Zoom>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Zoom in={true} timeout={400}>
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)', borderRadius: 3, border: '1px solid rgba(33, 150, 243, 0.2)' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                        <AIIcon sx={{ color: '#2196f3', fontSize: 24 }} />
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2196f3' }}>
                          Model
                        </Typography>
                        <Chip
                          label={selectedProvider}
                          size="small"
                          sx={{
                            ml: 'auto',
                            bgcolor: getProviderColor(selectedProvider),
                            color: 'white',
                            fontSize: '0.7rem',
                            fontWeight: 600
                          }}
                        />
                      </Box>
                      <FormControl fullWidth variant="outlined">
                        <Select
                          value={selectedModel}
                          onChange={(e) => setSelectedModel(e.target.value)}
                          disabled={smartMode}
                          displayEmpty
                          sx={{
                            '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(33, 150, 243, 0.3)' },
                            '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(33, 150, 243, 0.5)' }
                          }}
                        >
                          {filteredModels.map(model => (
                            <MenuItem key={model.id} value={model.id}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                                <span>{model.id}</span>
                                {model.context_window && (
                                  <Chip size="small" label={`${(model.context_window/1000).toFixed(0)}k ctx`} sx={{ ml: 1 }} />
                                )}
                              </Box>
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Paper>
                  </Zoom>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Zoom in={true} timeout={500}>
                    <Paper elevation={0} sx={{ p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)', borderRadius: 3, border: '1px solid rgba(33, 150, 243, 0.2)' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                        <CountIcon sx={{ color: '#2196f3', fontSize: 24 }} />
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2196f3' }}>
                          Target Count
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1, mb: 1.5 }}>
                        {[10, 50, 100, 500].map((amount) => (
                          <Tooltip key={amount} title={`Add ${amount} samples`} arrow>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => setTargetCount(currentSamples + amount)}
                              sx={{
                                minWidth: '60px',
                                borderColor: 'rgba(33, 150, 243, 0.5)',
                                color: '#2196f3',
                                fontSize: '0.75rem',
                                '&:hover': {
                                  borderColor: '#2196f3',
                                  bgcolor: 'rgba(33, 150, 243, 0.1)'
                                }
                              }}
                            >
                              +{amount}
                            </Button>
                          </Tooltip>
                        ))}
                      </Box>
                      <TextField
                        fullWidth
                        type="number"
                        value={targetCount}
                        onChange={(e) => setTargetCount(Number(e.target.value))}
                        size="small"
                        helperText={`Current: ${currentSamples.toLocaleString()} (+${(targetCount - currentSamples).toLocaleString()})`}
                        inputProps={{ min: currentSamples + 1 }}
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            '& fieldset': { borderColor: 'rgba(33, 150, 243, 0.3)' },
                            '&:hover fieldset': { borderColor: 'rgba(33, 150, 243, 0.5)' },
                          },
                        }}
                      />
                    </Paper>
                  </Zoom>
                </Grid>
              </Grid>
            </Box>

            {/* Filters - Collapsible */}
            <Box sx={{ mb: 3 }}>
              <Button
                variant="text"
                fullWidth
                onClick={() => setShowFilters(!showFilters)}
                disabled={smartMode}
                sx={{
                  justifyContent: 'space-between',
                  textTransform: 'none',
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: 'rgba(33, 150, 243, 0.05)',
                  border: '1px solid rgba(33, 150, 243, 0.2)',
                  mb: showFilters ? 2 : 0,
                  '&:hover': { bgcolor: 'rgba(33, 150, 243, 0.1)' }
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <FilterAlt sx={{ color: '#2196f3', fontSize: 20 }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2196f3' }}>
                    Filters (Optional)
                  </Typography>
                  <Chip label="Topic, Difficulty, Sample Type" size="small" sx={{ fontSize: '0.7rem', bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                </Box>
                {showFilters ? <ExpandLess sx={{ color: '#2196f3' }} /> : <ExpandMore sx={{ color: '#2196f3' }} />}
              </Button>

              {showFilters && (
                <Fade in={showFilters}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={4}>
                      <Paper elevation={0} sx={{ p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)', borderRadius: 3, border: '1px solid rgba(33, 150, 243, 0.2)' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                          <TopicIcon sx={{ color: '#2196f3', fontSize: 24 }} />
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2196f3' }}>
                            Topic
                          </Typography>
                        </Box>
                        <FormControl fullWidth variant="outlined">
                          <Select
                            value={selectedTopic}
                            onChange={(e) => setSelectedTopic(e.target.value)}
                            disabled={smartMode}
                            displayEmpty
                            size="small"
                            sx={{
                              '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(33, 150, 243, 0.3)' },
                              '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(33, 150, 243, 0.5)' }
                            }}
                          >
                            <MenuItem value="all">All Topics (Balanced)</MenuItem>
                            {topics.map((topicObj, idx) => {
                              const topicLabel = `${topicObj.practice_area} - ${topicObj.topic}`
                              return <MenuItem key={idx} value={topicLabel}>{topicLabel}</MenuItem>
                            })}
                          </Select>
                        </FormControl>
                      </Paper>
                    </Grid>

                    <Grid item xs={12} md={4}>
                      <Paper elevation={0} sx={{ p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)', borderRadius: 3, border: '1px solid rgba(33, 150, 243, 0.2)' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                          <DifficultyIcon sx={{ color: '#2196f3', fontSize: 24 }} />
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2196f3' }}>
                            Difficulty
                          </Typography>
                        </Box>
                        <FormControl fullWidth variant="outlined">
                          <Select
                            value={selectedDifficulty}
                            onChange={(e) => setSelectedDifficulty(e.target.value)}
                            disabled={smartMode}
                            displayEmpty
                            size="small"
                            sx={{
                              '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(33, 150, 243, 0.3)' },
                              '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(33, 150, 243, 0.5)' }
                            }}
                          >
                            <MenuItem value="balanced">⚖️ Balanced</MenuItem>
                            <MenuItem value="foundational">📚 Foundational</MenuItem>
                            <MenuItem value="basic">🟢 Basic</MenuItem>
                            <MenuItem value="intermediate">🟡 Intermediate</MenuItem>
                            <MenuItem value="advanced">🟠 Advanced</MenuItem>
                            <MenuItem value="expert">🔴 Expert</MenuItem>
                          </Select>
                        </FormControl>
                      </Paper>
                    </Grid>

                    <Grid item xs={12} md={4}>
                      <Paper elevation={0} sx={{ p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)', borderRadius: 3, border: '1px solid rgba(33, 150, 243, 0.2)' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                          <SampleTypeIcon sx={{ color: '#2196f3', fontSize: 24 }} />
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2196f3' }}>
                            Sample Type
                          </Typography>
                        </Box>
                        <FormControl fullWidth variant="outlined">
                          <Select
                            value={selectedSampleType}
                            onChange={(e) => setSelectedSampleType(e.target.value)}
                            disabled={smartMode}
                            displayEmpty
                            size="small"
                            sx={{
                              '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(33, 150, 243, 0.3)' },
                              '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(33, 150, 243, 0.5)' }
                            }}
                          >
                            {sampleTypes.map((sampleType) => (
                              <MenuItem key={sampleType.id} value={sampleType.id}>
                                {sampleType.name}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Paper>
                    </Grid>
                  </Grid>
                </Fade>
              )}
            </Box>

            {/* Advanced Settings - Collapsible */}
            <Box sx={{ mb: 3 }}>
              <Button
                variant="text"
                fullWidth
                onClick={() => setShowAdvanced(!showAdvanced)}
                sx={{
                  justifyContent: 'space-between',
                  textTransform: 'none',
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: 'rgba(33, 150, 243, 0.05)',
                  border: '1px solid rgba(33, 150, 243, 0.2)',
                  mb: showAdvanced ? 2 : 0,
                  '&:hover': { bgcolor: 'rgba(33, 150, 243, 0.1)' }
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CustomIcon sx={{ color: '#2196f3', fontSize: 20 }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2196f3' }}>
                    Advanced Settings (Optional)
                  </Typography>
                  <Chip label="Custom Reasoning Instructions" size="small" sx={{ fontSize: '0.7rem', bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                </Box>
                {showAdvanced ? <ExpandLess sx={{ color: '#2196f3' }} /> : <ExpandMore sx={{ color: '#2196f3' }} />}
              </Button>

              {showAdvanced && (
                <Fade in={showAdvanced}>
                  <Paper elevation={0} sx={{ p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)', borderRadius: 3, border: '1px solid rgba(33, 150, 243, 0.2)' }}>
                    <TextField
                      fullWidth
                      multiline
                      rows={3}
                      value={reasoningInstruction}
                      onChange={(e) => setReasoningInstruction(e.target.value)}
                      placeholder="e.g., 'Focus on complex multi-step analysis with at least 5 reasoning steps' or 'Include practical examples and counter-arguments'"
                      helperText="Provide specific instructions for how the AI should structure the reasoning section"
                      size="small"
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          '& fieldset': { borderColor: 'rgba(33, 150, 243, 0.3)' },
                          '&:hover fieldset': { borderColor: 'rgba(33, 150, 243, 0.5)' },
                        },
                      }}
                    />
                  </Paper>
                </Fade>
              )}
            </Box>

          </Box>
        </DialogContent>
        <DialogActions sx={{ borderTop: '1px solid rgba(33, 150, 243, 0.2)', p: 2 }}>
          <Button
            onClick={() => setGenerationModalOpen(false)}
            variant="outlined"
            sx={{ borderColor: 'rgba(33, 150, 243, 0.5)' }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} sx={{ color: 'white' }} /> : <PlayArrow />}
            onClick={startBatchGeneration}
            disabled={loading}
            sx={{
              minWidth: 180,
              background: loading ? undefined : 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
              '&:hover': {
                background: loading ? undefined : 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)',
              }
            }}
          >
            {loading ? 'Starting...' : 'Start Generation'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Stuck Batch Warning */}
      {stuckBatches.length > 0 && (
        <Grow in={true}>
          <Alert
            severity="warning"
            icon={<Cancel />}
            sx={{
              mt: 3,
              border: '2px solid #ffb74d',
              background: 'linear-gradient(135deg, rgba(255, 183, 77, 0.15) 0%, rgba(255, 183, 77, 0.05) 100%)'
            }}
            action={
              <Button color="inherit" size="small" onClick={() => stopBatch()}>
                Stop All Stuck Batches
              </Button>
            }
          >
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
              ⚠️ {stuckBatches.length} Stuck Batch{stuckBatches.length > 1 ? 'es' : ''} Detected
            </Typography>
            {stuckBatches.map(stuck => (
              <Typography key={stuck.batch_id} variant="body2" sx={{ mb: 0.5 }}>
                <strong>{stuck.model}</strong> • Running for {stuck.elapsed_minutes} min •
                {stuck.samples_generated} / {stuck.target} samples •
                <strong style={{ color: '#ff9800' }}> May need manual intervention</strong>
              </Typography>
            ))}
          </Alert>
        </Grow>
      )}

      {/* Live Running Batches */}
      {runningBatches.length > 0 && stuckBatches.length === 0 && (
        <Grow in={true}>
          <Alert
            severity="info"
            icon={<Timer />}
            sx={{
              mt: 3,
              border: '2px solid #2196f3',
              background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.15) 0%, rgba(33, 150, 243, 0.05) 100%)'
            }}
            action={
              runningBatches.length > 1 && (
                <Button color="inherit" size="small" onClick={() => stopBatch()}>
                  Stop All
                </Button>
              )
            }
          >
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
              🔥 {runningBatches.length} Batch{runningBatches.length > 1 ? 'es' : ''} Running Concurrently
            </Typography>
            <Stack spacing={2} sx={{ mt: 2 }}>
              {runningBatches.map((batch) => (
                <Box
                  key={batch.id}
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    border: '1px solid rgba(33, 150, 243, 0.3)',
                    background: 'rgba(33, 150, 243, 0.05)'
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: '#2196f3' }}>
                      {batch.id}
                    </Typography>
                    <IconButton size="small" color="error" onClick={() => stopBatch(batch.id)} title="Stop this batch">
                      <Stop fontSize="small" />
                    </IconButton>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap', mb: 1 }}>
                    <Typography variant="body2">
                      <strong>{batch.samples_generated}</strong> / {batch.target > 0 ? batch.target : '∞'} samples
                    </Typography>
                    <Typography variant="body2">•</Typography>
                    <Typography variant="body2">
                      Model: <strong>{batch.model}</strong>
                    </Typography>
                    <Typography variant="body2">•</Typography>
                    <Typography variant="body2">
                      Tokens: <strong>{batch.tokens_used?.toLocaleString()}</strong>
                    </Typography>
                  </Box>
                  {batch.target > 0 && (
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(100, (batch.samples_generated / batch.target) * 100)}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        bgcolor: 'rgba(33, 150, 243, 0.1)',
                        '& .MuiLinearProgress-bar': { bgcolor: '#2196f3' }
                      }}
                    />
                  )}
                </Box>
              ))}
            </Stack>
          </Alert>
        </Grow>
      )}

      {/* Batch History */}
      <Fade in={true} timeout={500}>
        <Card sx={{ mt: 3 }} className="fade-in">
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <div>
                <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
                  📜 Batch Generation History
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {batchHistory.length ? `${batchHistory.length} batch${batchHistory.length !== 1 ? 'es' : ''} tracked` : 'No batches yet'}
                </Typography>
              </div>
              {runningBatches.length > 0 && (
                <Chip
                  label={`${runningBatches.length} Active Batch${runningBatches.length > 1 ? 'es' : ''}`}
                  color="primary"
                  className="pulse"
                  sx={{ fontWeight: 600 }}
                />
              )}
            </Box>

            <Box sx={{ height: 400, width: '100%' }}>
              <DataGrid
                rows={batchHistory}
                columns={columns}
                initialState={{
                  pagination: {
                    paginationModel: { pageSize: 10, page: 0 }
                  },
                  rowSelection: []
                }}
                pageSizeOptions={[10, 25, 50]}
                disableRowSelectionOnClick
                sx={{
                  border: '1px solid rgba(33, 150, 243, 0.3)',
                  '& .MuiDataGrid-cell': { borderColor: 'rgba(33, 150, 243, 0.1)' },
                  '& .MuiDataGrid-columnHeaders': {
                    backgroundColor: 'rgba(33, 150, 243, 0.15)',
                    borderColor: 'rgba(33, 150, 243, 0.3)',
                    fontWeight: 600,
                  },
                  '& .MuiDataGrid-row:hover': { backgroundColor: 'rgba(33, 150, 243, 0.08)' },
                }}
              />
            </Box>
          </CardContent>
        </Card>
      </Fade>

      {/* Batch Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ fontWeight: 600, pb: 0 }}>
          📊 Batch Details
          {selectedBatch && (
            <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: 'text.secondary' }}>
              Batch ID: {selectedBatch.id}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          {selectedBatch && (
            <Box>
              <Tabs
                value={detailsTab}
                onChange={(e, newValue) => setDetailsTab(newValue)}
                sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}
              >
                <Tab label="Details" />
                <Tab label={`Samples (${batchSamples.length})`} />
              </Tabs>

              {/* Details Tab */}
              {detailsTab === 0 && (
                <Box>
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2, mb: 3 }}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Status</Typography>
                      <Box sx={{ mt: 0.5 }}>{getStatusChip(selectedBatch.status)}</Box>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Model</Typography>
                      <Typography variant="body1">{selectedBatch.model}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Topic Filter</Typography>
                      <Typography variant="body1">{selectedBatch.topic_filter || 'All topics'}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Difficulty Filter</Typography>
                      <Typography variant="body1">{selectedBatch.difficulty_filter || 'Balanced'}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Samples Generated</Typography>
                      <Typography variant="h6" sx={{ color: 'success.main' }}>
                        {selectedBatch.samples_generated}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Tokens Used</Typography>
                      <Typography variant="h6">{selectedBatch.tokens_used?.toLocaleString()}</Typography>
                    </Box>
                    <Box sx={{ gridColumn: '1 / -1' }}>
                      <Typography variant="caption" color="text.secondary">Duration</Typography>
                      <Typography variant="body1">{getDuration(selectedBatch)}</Typography>
                    </Box>
                  </Box>

                  {selectedBatch.errors && selectedBatch.errors.length > 0 && (
                    <Box sx={{ mt: 2, p: 2, bgcolor: 'error.dark', borderRadius: 1 }}>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        Errors ({selectedBatch.errors.length})
                      </Typography>
                      {selectedBatch.errors.map((error, idx) => (
                        <Typography key={idx} variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                          {typeof error === 'string' ? error : error.error}
                        </Typography>
                      ))}
                    </Box>
                  )}
                </Box>
              )}

              {/* Samples Tab */}
              {detailsTab === 1 && (
                <Box>
                  {loadingSamples ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
                      <CircularProgress />
                      <Typography sx={{ ml: 2 }}>Loading samples...</Typography>
                    </Box>
                  ) : batchSamples.length === 0 ? (
                    <Box sx={{ textAlign: 'center', py: 8 }}>
                      <Typography variant="h6" color="text.secondary">
                        No samples found for this batch
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        Samples may still be generating or were not saved with batch_id
                      </Typography>
                    </Box>
                  ) : (
                    <Box>
                      {/* Search Bar */}
                      <TextField
                        fullWidth
                        size="small"
                        placeholder="Search samples..."
                        value={sampleSearch}
                        onChange={(e) => setSampleSearch(e.target.value)}
                        InputProps={{
                          startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
                        }}
                        sx={{ mb: 2 }}
                      />

                      {/* Samples List */}
                      <Box sx={{ maxHeight: 500, overflowY: 'auto' }}>
                        {filteredSamples.length === 0 ? (
                          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                            No samples match your search
                          </Typography>
                        ) : (
                          filteredSamples.map((sample, idx) => (
                            <Accordion key={sample.id || idx} sx={{ mb: 1 }}>
                              <AccordionSummary expandIcon={<ExpandMore />}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                                  <Chip
                                    label={sample.difficulty || 'unknown'}
                                    size="small"
                                    color={
                                      sample.difficulty === 'expert' ? 'error' :
                                      sample.difficulty === 'advanced' ? 'warning' :
                                      sample.difficulty === 'intermediate' ? 'primary' :
                                      'default'
                                    }
                                  />
                                  <Typography variant="body2" sx={{ flexGrow: 1, fontWeight: 500 }}>
                                    {sample.topic || 'No topic'}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {sample.id}
                                  </Typography>
                                </Box>
                              </AccordionSummary>
                              <AccordionDetails>
                                <Stack spacing={2}>
                                  <Box>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
                                      Question
                                    </Typography>
                                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                                      {sample.question}
                                    </Typography>
                                  </Box>
                                  <Box>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: 'success.main' }}>
                                      Answer
                                    </Typography>
                                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                                      {sample.answer}
                                    </Typography>
                                  </Box>
                                  <Box>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: 'warning.main' }}>
                                      Reasoning
                                    </Typography>
                                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontStyle: 'italic' }}>
                                      {sample.reasoning}
                                    </Typography>
                                  </Box>
                                  <Box>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: 'info.main' }}>
                                      Case Citation
                                    </Typography>
                                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                                      {sample.case_citation}
                                    </Typography>
                                  </Box>
                                </Stack>
                              </AccordionDetails>
                            </Accordion>
                          ))
                        )}
                      </Box>
                    </Box>
                  )}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Batch Quality Metrics Dialog */}
      <Dialog
        open={qualityDialogOpen}
        onClose={() => setQualityDialogOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            bgcolor: '#001219',
            border: '2px solid rgba(76, 175, 80, 0.3)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.8)'
          }
        }}
      >
        <DialogTitle sx={{ fontWeight: 600, borderBottom: '1px solid rgba(76, 175, 80, 0.2)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <QualityIcon sx={{ color: '#4caf50' }} />
            Quality Metrics Report
          </Box>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          {loadingQuality ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
              <CircularProgress sx={{ color: '#4caf50' }} />
              <Typography sx={{ ml: 2 }}>Loading quality metrics...</Typography>
            </Box>
          ) : batchQuality ? (
            <Box>
              {/* Quality Score Banner */}
              <Alert
                severity={batchQuality.quality_score.rating === 'Good' ? 'success' : 'warning'}
                icon={batchQuality.quality_score.rating === 'Good' ? <CheckCircle /> : <Cancel />}
                sx={{ mb: 3 }}
              >
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {batchQuality.quality_score.rating === 'Good' ? '✅ High Quality Batch' : '⚠️ Review Recommended'}
                </Typography>
                {batchQuality.quality_score.issues.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    {batchQuality.quality_score.issues.map((issue, idx) => (
                      <Typography key={idx} variant="body2">
                        • {issue}
                      </Typography>
                    ))}
                  </Box>
                )}
              </Alert>

              {/* Metrics Cards */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6} md={3}>
                  <Paper sx={{ p: 2, bgcolor: 'rgba(33, 150, 243, 0.1)', border: '1px solid rgba(33, 150, 243, 0.3)' }}>
                    <Typography variant="caption" color="text.secondary">Total Samples</Typography>
                    <Typography variant="h5" sx={{ color: '#2196f3', fontWeight: 600 }}>
                      {batchQuality.metrics.total_samples}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Paper sx={{ p: 2, bgcolor: 'rgba(156, 39, 176, 0.1)', border: '1px solid rgba(156, 39, 176, 0.3)' }}>
                    <Typography variant="caption" color="text.secondary">Total Tokens</Typography>
                    <Typography variant="h5" sx={{ color: '#9c27b0', fontWeight: 600 }}>
                      {batchQuality.metrics.total_tokens.toLocaleString()}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Paper sx={{ p: 2, bgcolor: 'rgba(255, 152, 0, 0.1)', border: '1px solid rgba(255, 152, 0, 0.3)' }}>
                    <Typography variant="caption" color="text.secondary">Avg Tokens/Sample</Typography>
                    <Typography variant="h5" sx={{ color: '#ff9800', fontWeight: 600 }}>
                      {Math.round(batchQuality.metrics.avg_tokens_per_sample)}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Paper sx={{ p: 2, bgcolor: 'rgba(76, 175, 80, 0.1)', border: '1px solid rgba(76, 175, 80, 0.3)' }}>
                    <Typography variant="caption" color="text.secondary">Avg Answer Length</Typography>
                    <Typography variant="h5" sx={{ color: '#4caf50', fontWeight: 600 }}>
                      {Math.round(batchQuality.metrics.avg_answer_length)}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>

              {/* Content Quality Metrics */}
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>📝 Content Quality</Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2, mb: 3 }}>
                <Paper sx={{ p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)' }}>
                  <Typography variant="caption" color="text.secondary">Avg Reasoning</Typography>
                  <Typography variant="h6">{Math.round(batchQuality.metrics.avg_reasoning_length)} chars</Typography>
                </Paper>
                <Paper sx={{ p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)' }}>
                  <Typography variant="caption" color="text.secondary">Avg Citations</Typography>
                  <Typography variant="h6">{Math.round(batchQuality.metrics.avg_citation_length)} chars</Typography>
                </Paper>
                <Paper sx={{ p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)' }}>
                  <Typography variant="caption" color="text.secondary">Batch ID</Typography>
                  <Typography variant="caption" sx={{ fontFamily: 'monospace', display: 'block', mt: 0.5 }}>
                    {batchQuality.batch_id}
                  </Typography>
                </Paper>
              </Box>

              {/* Difficulty Distribution */}
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>📊 Difficulty Distribution</Typography>
              <Box sx={{ mb: 3 }}>
                {Object.entries(batchQuality.distributions.difficulty).map(([level, count]) => (
                  <Box key={level} sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2">{level.charAt(0).toUpperCase() + level.slice(1)}</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>{count}</Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(count / batchQuality.metrics.total_samples) * 100}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        bgcolor: 'rgba(33, 150, 243, 0.1)',
                        '& .MuiLinearProgress-bar': { bgcolor: '#2196f3', borderRadius: 4 }
                      }}
                    />
                  </Box>
                ))}
              </Box>

              {/* Topic Distribution */}
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>🎯 Topic Coverage</Typography>
              <Paper sx={{ p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)', maxHeight: 200, overflow: 'auto', mb: 3 }}>
                {Object.entries(batchQuality.distributions.topics).slice(0, 10).map(([topic, count]) => (
                  <Box key={topic} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                    <Typography variant="body2">{topic}</Typography>
                    <Chip size="small" label={count} sx={{ minWidth: 40 }} />
                  </Box>
                ))}
                {Object.keys(batchQuality.distributions.topics).length > 10 && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    + {Object.keys(batchQuality.distributions.topics).length - 10} more topics
                  </Typography>
                )}
              </Paper>

              {/* Sample Types & Jurisdictions */}
              {Object.keys(batchQuality.distributions.sample_types).length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>🔖 Sample Types</Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {Object.entries(batchQuality.distributions.sample_types).map(([type, count]) => (
                      <Chip
                        key={type}
                        label={`${type}: ${count}`}
                        sx={{ bgcolor: 'rgba(76, 175, 80, 0.2)', color: '#4caf50' }}
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {Object.keys(batchQuality.distributions.jurisdictions).length > 0 && (
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>🌍 Jurisdictions</Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {Object.entries(batchQuality.distributions.jurisdictions).map(([jurisdiction, count]) => (
                      <Chip
                        key={jurisdiction}
                        label={`${jurisdiction.toUpperCase()}: ${count}`}
                        sx={{ bgcolor: 'rgba(33, 150, 243, 0.2)', color: '#2196f3' }}
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </Box>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No quality data available
            </Typography>
          )}
        </DialogContent>
        <DialogActions sx={{ borderTop: '1px solid rgba(76, 175, 80, 0.2)', p: 2 }}>
          <Button onClick={() => setQualityDialogOpen(false)} variant="outlined" sx={{ borderColor: 'rgba(76, 175, 80, 0.5)' }}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Completion Message */}
      {batchStatus && !batchStatus.running && batchStatus.samples_generated > 0 && (
        <Alert icon={<CheckCircle />} severity="success" sx={{ mt: 3 }}>
          <Typography variant="h6">Generation Complete!</Typography>
          Successfully generated {batchStatus.samples_generated} new samples
        </Alert>
      )}
    </Box>
  )
}
