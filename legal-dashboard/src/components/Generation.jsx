import { useState, useEffect, useRef } from 'react'
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  LinearProgress,
  Box,
  Chip,
  Alert,
  CircularProgress,
  Fade,
  Grow,
  Tooltip,
  Divider,
  Zoom,
  InputAdornment,
  Paper,
  Grid
} from '@mui/material'
import {
  PlayArrow,
  Stop,
  CheckCircle,
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
  Bolt
} from '@mui/icons-material'

export default function Generation({ onStatsUpdate }) {
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
  const [batchStatus, setBatchStatus] = useState(null)
  const [reasoningInstruction, setReasoningInstruction] = useState('')
  const [loading, setLoading] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const eventSourceRef = useRef(null)

  useEffect(() => {
    loadProviders()
    loadModels()
    loadTopics()
    loadSampleTypes()
    loadCurrentCount()
    connectSSE()

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  // Filter models when provider changes
  useEffect(() => {
    const filtered = models.filter(m => m.provider === selectedProvider)
    setFilteredModels(filtered)

    // Set default model for selected provider if current model doesn't match
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
        // Models will be filtered by provider in useEffect
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

  const connectSSE = () => {
    const eventSource = new EventSource('http://127.0.0.1:5001/api/generate/batch/stream')

    eventSource.onmessage = (event) => {
      if (event.data && event.data !== ': heartbeat') {
        try {
          const message = JSON.parse(event.data)

          // Extract actual batch data from nested message structure
          let batchData = null
          if (message.type === 'batch_update' && message.batch) {
            // Single batch update
            batchData = message.batch
          } else if (message.type === 'all_batches' && message.batches) {
            // Multiple batches - find first running batch or use first available
            const batches = Object.values(message.batches)
            const runningBatch = batches.find(b => b.running)
            batchData = runningBatch || batches[0]
          } else if (!message.type) {
            // Fallback: assume it's already the batch data (backward compatibility)
            batchData = message
          }

          if (batchData) {
            setBatchStatus(batchData)

            if (!batchData.running && batchData.samples_generated > 0) {
              onStatsUpdate()
              loadCurrentCount()
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
      // Reconnect after 5 seconds
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
      if (!data.success) {
        alert(`Error: ${data.error}`)
      }
    } catch (error) {
      console.error('Error starting batch:', error)
      alert(`Failed to start: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const stopBatchGeneration = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/generate/batch/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      const data = await response.json()
      if (data.success) {
        onStatsUpdate()
        loadCurrentCount()
      } else {
        console.error('Failed to stop batch:', data.error)
      }
    } catch (error) {
      console.error('Error stopping batch:', error)
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
      case 'custom':
        // User will configure manually
        break
    }
  }

  const progress = batchStatus?.total > 0
    ? (batchStatus.progress / batchStatus.total) * 100
    : 0

  // Helper functions for provider display
  const getProviderIcon = (providerId) => {
    const icons = {
      'groq': '⚡',
      'cerebras': '🧠'
    }
    return icons[providerId] || '🔮'
  }

  const getProviderColor = (providerId) => {
    const colors = {
      'groq': '#f55036',
      'cerebras': '#7c3aed'
    }
    return colors[providerId] || '#2196f3'
  }

  return (
    <Box>
      <Fade in={true} timeout={500}>
        <Card className="fade-in">
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <div>
                <Typography variant="h5" sx={{ fontWeight: 600, mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Rocket sx={{ color: '#2196f3' }} />
                  LLM Sample Generation
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Generate high-quality UK legal samples using advanced AI models
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

            {/* Tier 1: Essential Configuration - Always Visible */}
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
                            '& .MuiOutlinedInput-notchedOutline': {
                              borderColor: 'rgba(33, 150, 243, 0.3)',
                            },
                            '&:hover .MuiOutlinedInput-notchedOutline': {
                              borderColor: 'rgba(33, 150, 243, 0.5)',
                            }
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
                            '& .MuiOutlinedInput-notchedOutline': {
                              borderColor: 'rgba(33, 150, 243, 0.3)',
                            },
                            '&:hover .MuiOutlinedInput-notchedOutline': {
                              borderColor: 'rgba(33, 150, 243, 0.5)',
                            }
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
                            '& fieldset': {
                              borderColor: 'rgba(33, 150, 243, 0.3)',
                            },
                            '&:hover fieldset': {
                              borderColor: 'rgba(33, 150, 243, 0.5)',
                            },
                          },
                        }}
                      />
                    </Paper>
                  </Zoom>
                </Grid>
              </Grid>
            </Box>

            {/* Tier 2: Filters - Collapsible */}
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
                  '&:hover': {
                    bgcolor: 'rgba(33, 150, 243, 0.1)',
                  }
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <FilterAlt sx={{ color: '#2196f3', fontSize: 20 }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2196f3' }}>
                    Filters (Optional)
                  </Typography>
                  <Chip
                    label="Topic, Difficulty, Sample Type"
                    size="small"
                    sx={{ fontSize: '0.7rem', bgcolor: 'rgba(33, 150, 243, 0.1)' }}
                  />
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
                              '& .MuiOutlinedInput-notchedOutline': {
                                borderColor: 'rgba(33, 150, 243, 0.3)',
                              },
                              '&:hover .MuiOutlinedInput-notchedOutline': {
                                borderColor: 'rgba(33, 150, 243, 0.5)',
                              }
                            }}
                          >
                            <MenuItem value="all">All Topics (Balanced)</MenuItem>
                            {topics.map((topicObj, idx) => {
                              const topicLabel = `${topicObj.practice_area} - ${topicObj.topic}`
                              return (
                                <MenuItem key={idx} value={topicLabel}>
                                  {topicLabel}
                                </MenuItem>
                              )
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
                              '& .MuiOutlinedInput-notchedOutline': {
                                borderColor: 'rgba(33, 150, 243, 0.3)',
                              },
                              '&:hover .MuiOutlinedInput-notchedOutline': {
                                borderColor: 'rgba(33, 150, 243, 0.5)',
                              }
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
                              '& .MuiOutlinedInput-notchedOutline': {
                                borderColor: 'rgba(33, 150, 243, 0.3)',
                              },
                              '&:hover .MuiOutlinedInput-notchedOutline': {
                                borderColor: 'rgba(33, 150, 243, 0.5)',
                              }
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

            {/* Tier 3: Advanced Settings - Collapsible */}
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
                  '&:hover': {
                    bgcolor: 'rgba(33, 150, 243, 0.1)',
                  }
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CustomIcon sx={{ color: '#2196f3', fontSize: 20 }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2196f3' }}>
                    Advanced Settings (Optional)
                  </Typography>
                  <Chip
                    label="Custom Reasoning Instructions"
                    size="small"
                    sx={{ fontSize: '0.7rem', bgcolor: 'rgba(33, 150, 243, 0.1)' }}
                  />
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
                          '& fieldset': {
                            borderColor: 'rgba(33, 150, 243, 0.3)',
                          },
                          '&:hover fieldset': {
                            borderColor: 'rgba(33, 150, 243, 0.5)',
                          },
                        },
                      }}
                    />
                  </Paper>
                </Fade>
              )}
            </Box>

            <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
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
            <Tooltip title={!batchStatus?.running ? "No active generation" : "Stop current generation"} arrow>
              <span>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<Stop />}
                  onClick={stopBatchGeneration}
                  disabled={!batchStatus?.running}
                  size="large"
                  sx={{ minWidth: 140 }}
                >
                  Stop
                </Button>
              </span>
            </Tooltip>
          </Box>
        </CardContent>
      </Card>
      </Fade>

      {/* Live Status */}
      {batchStatus && batchStatus.running && (
        <Grow in={true} timeout={600}>
          <Card sx={{
            mt: 3,
            border: '2px solid #2196f3',
            background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.15) 0%, rgba(33, 150, 243, 0.05) 100%)',
            boxShadow: '0 8px 24px rgba(33, 150, 243, 0.2)'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Speed className="pulse" sx={{ color: '#2196f3' }} />
                  Generation in Progress
                </Typography>
                <Chip
                  label={`${Math.round(progress)}%`}
                  color="primary"
                  className="pulse"
                  sx={{ fontSize: '1rem', fontWeight: 700 }}
                />
              </Box>

              <LinearProgress
                variant="determinate"
                value={progress}
                sx={{
                  height: 12,
                  borderRadius: 2,
                  mb: 3,
                  background: 'rgba(33, 150, 243, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    background: 'linear-gradient(90deg, #1976d2 0%, #2196f3 100%)',
                  }
                }}
              />

              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }}>
                    <Typography variant="caption" color="text.secondary">Provider</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600, mt: 0.5, display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <span>{getProviderIcon(batchStatus.current_provider || 'groq')}</span>
                      <span>{batchStatus.current_provider || 'groq'}</span>
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }}>
                    <Typography variant="caption" color="text.secondary">Model</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600, mt: 0.5 }}>{batchStatus.current_model}</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }}>
                    <Typography variant="caption" color="text.secondary">Progress</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600, mt: 0.5 }}>
                      {batchStatus.progress} / {batchStatus.total}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'rgba(105, 240, 174, 0.15)' }}>
                    <Typography variant="caption" color="text.secondary">Generated</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600, color: 'success.main', mt: 0.5 }}>
                      +{batchStatus.samples_generated}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }}>
                    <Typography variant="caption" color="text.secondary">Tokens Used</Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600, mt: 0.5 }}>
                      {batchStatus.total_tokens?.toLocaleString()}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              {batchStatus.current_sample && (
                <Fade in={true}>
                  <Alert icon={<TrendingUp />} severity="info" sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary">Currently Processing</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>{batchStatus.current_sample}</Typography>
                  </Alert>
                </Fade>
              )}
            </CardContent>
          </Card>
        </Grow>
      )}

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
