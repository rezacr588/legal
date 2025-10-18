import { useState, useEffect } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stack,
  CircularProgress,
  Fade,
  Grow,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
  TextField,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'
import { Visibility, Stop, CheckCircle, Cancel, PlayArrow, Schedule, Timer, ExpandMore, Search } from '@mui/icons-material'

export default function Batches({ onRunningCountChange, onNotification }) {
  const [batchHistory, setBatchHistory] = useState([])
  const [selectedBatch, setSelectedBatch] = useState(null)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [stuckBatches, setStuckBatches] = useState([])
  const [previousStuckCount, setPreviousStuckCount] = useState(0)
  const [batchSamples, setBatchSamples] = useState([])
  const [loadingSamples, setLoadingSamples] = useState(false)
  const [detailsTab, setDetailsTab] = useState(0)
  const [sampleSearch, setSampleSearch] = useState('')

  useEffect(() => {
    // Load initial history from database
    loadBatchHistory()
    checkStuckBatches()

    // Poll for updates every 5 seconds
    const interval = setInterval(() => {
      loadBatchHistory()
      checkStuckBatches()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const runningCount = batchHistory.filter(b => b.status === 'running').length
    onRunningCountChange(runningCount)
  }, [batchHistory, onRunningCountChange])

  const loadBatchHistory = async () => {
    try {
      const response = await fetch('/api/generate/batch/history')
      const data = await response.json()

      if (data.success) {
        // Convert API format to component format
        const batches = data.batches.map(batch => ({
          id: batch.id,
          started_at: batch.started_at,
          completed_at: batch.completed_at,
          model: batch.model || 'Unknown',
          topic_filter: batch.topic_filter,
          difficulty_filter: batch.difficulty_filter,
          reasoning_instruction: batch.reasoning_instruction,
          target: batch.target || 0,
          progress: batch.samples_generated || 0, // Show actual samples generated
          total: batch.target || 0,
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
        const stuck = data.stuck_batches || []
        setStuckBatches(stuck)

        // Notify if new stuck batches detected
        if (stuck.length > previousStuckCount && stuck.length > 0 && onNotification) {
          const newStuckCount = stuck.length - previousStuckCount
          onNotification(
            `⚠️ ${newStuckCount} stuck batch${newStuckCount > 1 ? 'es' : ''} detected! Running longer than expected with no progress.`,
            'warning'
          )
        }

        setPreviousStuckCount(stuck.length)
      }
    } catch (error) {
      console.error('Error checking stuck batches:', error)
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

  const getStatusChip = (status) => {
    const configs = {
      running: {
        label: 'Running',
        color: 'primary',
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
        color: 'success',
        icon: <CheckCircle sx={{ fontSize: 14 }} />,
        sx: {
          background: 'linear-gradient(135deg, #388e3c 0%, #4caf50 100%)',
          color: 'white',
          fontWeight: 600
        }
      },
      stopped: {
        label: 'Stopped',
        color: 'error',
        icon: <Cancel sx={{ fontSize: 14 }} />,
        sx: {
          background: 'linear-gradient(135deg, #d32f2f 0%, #f44336 100%)',
          color: 'white',
          fontWeight: 600
        }
      }
    }
    const config = configs[status] || configs.stopped
    return (
      <Chip
        size="small"
        label={config.label}
        icon={config.icon}
        sx={config.sx}
      />
    )
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
    {
      field: 'model',
      headerName: 'Model',
      width: 200,
    },
    {
      field: 'progress',
      headerName: 'Progress',
      width: 200,
      renderCell: (params) => {
        const generated = params.row.samples_generated || 0
        const target = params.row.total || 0
        const displayText = target > 0
          ? `${generated} / ${target}`
          : `${generated} samples`
        const progress = target > 0 ? (generated / target) * 100 : 0

        return (
          <Box sx={{ width: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              {params.row.status === 'running' && (
                <CircularProgress size={14} sx={{ color: '#2196f3' }} />
              )}
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
            onClick={() => handleViewDetails(params.row)}
            title="View Details"
          >
            <Visibility />
          </IconButton>
        </Box>
      )
    }
  ]

  const runningBatches = batchHistory.filter(b => b.status === 'running')
  const hasHistory = batchHistory.length > 0

  return (
    <Box>
      {/* Stuck Batch Warning */}
      {stuckBatches.length > 0 && (
        <Grow in={true}>
          <Alert
            severity="warning"
            icon={<Cancel />}
            sx={{
              mb: 2,
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
            <Typography variant="caption" sx={{ display: 'block', mt: 1, color: 'rgba(255, 183, 77, 0.9)' }}>
              Batches running longer than expected with no progress. Click "Stop" or check server logs.
            </Typography>
          </Alert>
        </Grow>
      )}

      {/* Active Batches Alert */}
      {runningBatches.length > 0 && stuckBatches.length === 0 && (
        <Stack spacing={2} sx={{ mb: 3 }}>
          <Grow in={true}>
            <Alert
              severity="info"
              icon={<Timer />}
              sx={{
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
                        <strong>{batch.samples_generated}</strong> / {batch.total > 0 ? batch.total : '∞'} samples
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
                    {batch.total > 0 && (
                      <LinearProgress
                        variant="determinate"
                        value={Math.min(100, (batch.samples_generated / batch.total) * 100)}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          bgcolor: 'rgba(33, 150, 243, 0.1)',
                          '& .MuiLinearProgress-bar': {
                            bgcolor: '#2196f3'
                          }
                        }}
                      />
                    )}
                  </Box>
                ))}
              </Stack>
            </Alert>
          </Grow>
        </Stack>
      )}

      <Fade in={true} timeout={500}>
        <Card className="fade-in">
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <div>
                <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
                  📜 Batch Generation History
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {hasHistory ? `${batchHistory.length} batch${batchHistory.length !== 1 ? 'es' : ''} tracked` : 'No batches yet'}
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

            <Box sx={{ height: 600, width: '100%' }}>
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
                  '& .MuiDataGrid-cell': {
                    borderColor: 'rgba(33, 150, 243, 0.1)',
                  },
                  '& .MuiDataGrid-columnHeaders': {
                    backgroundColor: 'rgba(33, 150, 243, 0.15)',
                    borderColor: 'rgba(33, 150, 243, 0.3)',
                    fontWeight: 600,
                  },
                  '& .MuiDataGrid-row:hover': {
                    backgroundColor: 'rgba(33, 150, 243, 0.08)',
                  },
                }}
              />
            </Box>
          </CardContent>
        </Card>
      </Fade>

      {/* Details Dialog */}
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
    </Box>
  )
}
