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
  Stack
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
  Timer
} from '@mui/icons-material'

export default function GenerationHub({ onStatsUpdate, onNotification }) {
  // Generation state
  const [providers, setProviders] = useState([])
  const [selectedProvider, setSelectedProvider] = useState('groq')
  const [models, setModels] = useState([])
  const [filteredModels, setFilteredModels] = useState([])
  const [topics, setTopics] = useState([])
  const [sampleTypes, setSampleTypes] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [selectedTopic, setSelectedTopic] = useState('all')
  const [selectedDifficulty, setSelectedDifficulty] = useState('balanced')
  const [selectedSampleType, setSelectedSampleType] = useState('case_analysis')
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
  const [stuckBatches, setStuckBatches] = useState([])
  const [previousStuckCount, setPreviousStuckCount] = useState(0)
  const eventSourceRef = useRef(null)

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
      const response = await fetch('http://127.0.0.1:5001/api/providers')
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
      const response = await fetch('http://127.0.0.1:5001/api/models')
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
      const response = await fetch('http://127.0.0.1:5001/api/topics')
      const data = await response.json()
      setTopics(data.topics || [])
    } catch (error) {
      console.error('Error loading topics:', error)
    }
  }

  const loadSampleTypes = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/sample-types')
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
      const response = await fetch('http://127.0.0.1:5001/api/stats')
      const data = await response.json()
      setCurrentSamples(data.total || 0)
    } catch (error) {
      console.error('Error loading stats:', error)
    }
  }

  const loadBatchHistory = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/generate/batch/history')
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
      const response = await fetch('http://127.0.0.1:5001/api/batches/stuck')
      const data = await response.json()

      if (data.success) {
        setStuckBatches(data.stuck_batches || [])
      }
    } catch (error) {
      console.error('Error checking stuck batches:', error)
    }
  }

  const connectSSE = () => {
    const eventSource = new EventSource('http://127.0.0.1:5001/api/generate/batch/stream')

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
      provider: selectedProvider,
      model: selectedModel,
      sample_type: selectedSampleType
    }

    if (selectedTopic !== 'all') {
      payload.topic = selectedTopic
    }
    if (selectedDifficulty !== 'balanced') {
      payload.difficulty = selectedDifficulty
    }
    if (reasoningInstruction.trim()) {
      payload.reasoning_instruction = reasoningInstruction.trim()
    }

    setLoading(true)
    try {
      const response = await fetch('http://127.0.0.1:5001/api/generate/batch/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await response.json()
      if (data.success) {
        if (onNotification) {
          onNotification('✅ Batch generation started!', 'success')
        }
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
      await fetch('http://127.0.0.1:5001/api/generate/batch/stop', {
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
      width: 120,
      sortable: false,
      renderCell: (params) => (
        <Box>
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
            onClick={() => {
              setSelectedBatch(params.row)
              setDetailsOpen(true)
            }}
            title="View Details"
          >
            <Visibility />
          </IconButton>
        </Box>
      )
    }
  ]

  return (
    <Box>
      {/* Generation Configuration */}
      <Fade in={true} timeout={500}>
        <Card className="fade-in">
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <div>
                <Typography variant="h5" sx={{ fontWeight: 600, mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Rocket sx={{ color: '#2196f3' }} />
                  Generation Hub
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Configure and monitor LLM sample generation
                </Typography>
              </div>
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
            </Box>

            <Divider sx={{ mb: 3, borderColor: 'rgba(33, 150, 243, 0.2)' }} />

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
                  disabled={batchStatus?.running}
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
                  disabled={batchStatus?.running}
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
                  disabled={batchStatus?.running}
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
                          disabled={batchStatus?.running}
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
                          disabled={batchStatus?.running}
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
                              disabled={batchStatus?.running}
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
                        disabled={batchStatus?.running}
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
                disabled={batchStatus?.running}
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
                            disabled={batchStatus?.running}
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
                            disabled={batchStatus?.running}
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
                            disabled={batchStatus?.running}
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
                disabled={batchStatus?.running}
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
                      disabled={batchStatus?.running}
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

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Tooltip title={batchStatus?.running ? "Generation already running" : "Start batch generation"} arrow>
                <span>
                  <Button
                    variant="contained"
                    startIcon={loading ? <CircularProgress size={20} sx={{ color: 'white' }} /> : <PlayArrow />}
                    onClick={startBatchGeneration}
                    disabled={batchStatus?.running || loading}
                    size="large"
                    sx={{
                      minWidth: 180,
                      background: (batchStatus?.running || loading) ? undefined : 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
                      '&:hover': {
                        background: (batchStatus?.running || loading) ? undefined : 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)',
                      }
                    }}
                  >
                    {loading ? 'Starting...' : 'Start Generation'}
                  </Button>
                </span>
              </Tooltip>
              <Tooltip title={!runningBatches.length ? "No active generation" : "Stop all running batches"} arrow>
                <span>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<Stop />}
                    onClick={() => stopBatch()}
                    disabled={!runningBatches.length}
                    size="large"
                    sx={{ minWidth: 140 }}
                  >
                    Stop All
                  </Button>
                </span>
              </Tooltip>
            </Box>
          </CardContent>
        </Card>
      </Fade>

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
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ fontWeight: 600 }}>📊 Batch Details</DialogTitle>
        <DialogContent>
          {selectedBatch && (
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
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
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
