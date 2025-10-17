import { useState, useEffect } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  TextField,
  Chip,
  ButtonGroup,
  Fade,
  Grow,
  InputAdornment,
  Tooltip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Divider,
  Tab,
  Tabs
} from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'
import { Download, FileDownload, TableChart, Search, FilterList, Upload, Add, Code, CheckCircle, Edit, Save, Cancel, Delete, GetApp, CloudUpload } from '@mui/icons-material'
import DifficultyChip from './common/DifficultyChip'

export default function Dataset({ stats, onStatsUpdate, onNotification }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filteredData, setFilteredData] = useState([])
  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [importContent, setImportContent] = useState('')
  const [importTab, setImportTab] = useState(0) // 0 = paste, 1 = file upload
  const [importLoading, setImportLoading] = useState(false)
  const [importResult, setImportResult] = useState(null)
  const [selectedSample, setSelectedSample] = useState(null)
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editedSample, setEditedSample] = useState(null)
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [operationLoading, setOperationLoading] = useState(false)
  const [selectedRows, setSelectedRows] = useState([])

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (searchTerm) {
      const filtered = data.filter(row =>
        Object.values(row).some(val =>
          String(val).toLowerCase().includes(searchTerm.toLowerCase())
        )
      )
      setFilteredData(filtered)
    } else {
      setFilteredData(data)
    }
  }, [searchTerm, data])

  const loadData = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/data')
      const rows = await response.json()
      // Add numeric IDs for DataGrid
      const rowsWithIds = rows.map((row, idx) => ({ ...row, numericId: idx + 1 }))
      setData(rowsWithIds)
      setFilteredData(rowsWithIds)
      setLoading(false)
    } catch (error) {
      console.error('Error loading data:', error)
      setLoading(false)
    }
  }


  const exportToJsonl = () => {
    const dataToExport = searchTerm ? filteredData : data
    const jsonlContent = dataToExport.map(row => {
      const { numericId, ...cleanRow } = row
      return JSON.stringify(cleanRow)
    }).join('\n')

    const blob = new Blob([jsonlContent], { type: 'application/jsonl' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `uk_legal_dataset_${new Date().toISOString().split('T')[0]}.jsonl`
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportToCsv = () => {
    const dataToExport = searchTerm ? filteredData : data
    const headers = ['id', 'question', 'answer', 'topic', 'difficulty', 'case_citation', 'reasoning']

    const escapeCsv = (val) => {
      if (val === null || val === undefined) return ''
      const str = String(val)
      if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`
      }
      return str
    }

    const csvRows = [
      headers.join(','),
      ...dataToExport.map(row => headers.map(h => escapeCsv(row[h])).join(','))
    ]
    const csvContent = csvRows.join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `uk_legal_dataset_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportToExcel = () => {
    const dataToExport = searchTerm ? filteredData : data
    const headers = ['ID', 'Question', 'Answer', 'Topic', 'Difficulty', 'Case Citation', 'Reasoning']
    const htmlContent = `
      <html xmlns:x="urn:schemas-microsoft-com:office:excel">
      <head><meta charset="UTF-8"></head>
      <body>
        <table border="1">
          <thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead>
          <tbody>
            ${dataToExport.map(row => `
              <tr>
                <td>${row.id || ''}</td>
                <td>${row.question || ''}</td>
                <td>${row.answer || ''}</td>
                <td>${row.topic || ''}</td>
                <td>${row.difficulty || ''}</td>
                <td>${row.case_citation || ''}</td>
                <td>${row.reasoning || ''}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </body>
      </html>
    `

    const blob = new Blob([htmlContent], { type: 'application/vnd.ms-excel' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `uk_legal_dataset_${new Date().toISOString().split('T')[0]}.xls`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImport = async () => {
    setImportLoading(true)
    setImportResult(null)

    try {
      const response = await fetch('http://127.0.0.1:5001/api/import/jsonl', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: importContent })
      })

      const result = await response.json()

      if (result.success) {
        setImportResult({
          success: true,
          message: result.message,
          total: result.total_samples
        })

        // Play success sound and show notification
        if (onNotification) {
          onNotification(result.message, 'success')
        }

        // Reload data
        loadData()
        if (onStatsUpdate) onStatsUpdate()

        // Clear import content after 2 seconds
        setTimeout(() => {
          setImportContent('')
          setImportDialogOpen(false)
          setImportResult(null)
        }, 2000)
      } else {
        setImportResult({
          success: false,
          message: result.error
        })

        // Play error sound
        if (onNotification) {
          onNotification(result.error, 'error')
        }
      }
    } catch (error) {
      const errorMsg = `Import failed: ${error.message}`
      setImportResult({
        success: false,
        message: errorMsg
      })

      // Play error sound
      if (onNotification) {
        onNotification(errorMsg, 'error')
      }
    } finally {
      setImportLoading(false)
    }
  }

  const handleFileUpload = (event) => {
    const file = event.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        setImportContent(e.target.result)
      }
      reader.readAsText(file)
    }
  }

  const handleRowClick = (params) => {
    setSelectedSample(params.row)
    setEditedSample({ ...params.row })
    setDetailModalOpen(true)
    setIsEditing(false)
  }

  const handleCloseDetailModal = () => {
    setDetailModalOpen(false)
    setIsEditing(false)
    setTimeout(() => {
      setSelectedSample(null)
      setEditedSample(null)
    }, 300) // Clear after animation
  }

  const handleEditClick = () => {
    setIsEditing(true)
  }

  const handleCancelEdit = () => {
    setEditedSample({ ...selectedSample })
    setIsEditing(false)
  }

  const handleFieldChange = (field, value) => {
    setEditedSample(prev => ({ ...prev, [field]: value }))
  }

  const handleSaveEdit = async () => {
    setOperationLoading(true)
    try {
      const response = await fetch(`http://127.0.0.1:5001/api/sample/${selectedSample.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: editedSample.id,
          question: editedSample.question,
          answer: editedSample.answer,
          topic: editedSample.topic,
          difficulty: editedSample.difficulty,
          case_citation: editedSample.case_citation,
          reasoning: editedSample.reasoning
        })
      })

      const result = await response.json()

      if (result.success) {
        if (onNotification) {
          onNotification(result.message, 'success')
        }

        // Reload data and stats
        await loadData()
        if (onStatsUpdate) onStatsUpdate()

        // Update the selected sample with new data
        setSelectedSample(editedSample)
        setIsEditing(false)
      } else {
        if (onNotification) {
          onNotification(result.error, 'error')
        }
      }
    } catch (error) {
      if (onNotification) {
        onNotification(`Update failed: ${error.message}`, 'error')
      }
    } finally {
      setOperationLoading(false)
    }
  }

  const handleDeleteClick = () => {
    setDeleteConfirmOpen(true)
  }

  const handleDeleteConfirm = async () => {
    setOperationLoading(true)
    try {
      const response = await fetch(`http://127.0.0.1:5001/api/sample/${selectedSample.id}`, {
        method: 'DELETE'
      })

      const result = await response.json()

      if (result.success) {
        if (onNotification) {
          onNotification(result.message, 'success')
        }

        // Reload data and stats
        await loadData()
        if (onStatsUpdate) onStatsUpdate()

        // Close modals
        setDeleteConfirmOpen(false)
        setDetailModalOpen(false)
        setTimeout(() => {
          setSelectedSample(null)
          setEditedSample(null)
        }, 300)
      } else {
        if (onNotification) {
          onNotification(result.error, 'error')
        }
      }
    } catch (error) {
      if (onNotification) {
        onNotification(`Delete failed: ${error.message}`, 'error')
      }
    } finally {
      setOperationLoading(false)
    }
  }

  const handleDownloadSample = () => {
    if (!selectedSample) return
    window.open(`http://127.0.0.1:5001/api/sample/${selectedSample.id}/download`, '_blank')
  }

  const handleDownloadSelected = async () => {
    if (selectedRows.length === 0) return

    try {
      // Get the actual IDs from the selected rows
      const sampleIds = selectedRows.map(numericId => {
        const sample = filteredData.find(row => row.numericId === numericId)
        return sample?.id
      }).filter(id => id)

      const response = await fetch('http://127.0.0.1:5001/api/samples/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sample_ids: sampleIds })
      })

      if (response.ok) {
        // Get the filename from the Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition')
        const filenameMatch = contentDisposition && contentDisposition.match(/filename="(.+)"/)
        const filename = filenameMatch ? filenameMatch[1] : 'samples.jsonl'

        // Download the file
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        a.click()
        URL.revokeObjectURL(url)

        if (onNotification) {
          onNotification(`Downloaded ${selectedRows.length} samples as JSONL`, 'success')
        }
      } else {
        const error = await response.json()
        if (onNotification) {
          onNotification(error.error || 'Download failed', 'error')
        }
      }
    } catch (error) {
      if (onNotification) {
        onNotification(`Download failed: ${error.message}`, 'error')
      }
    }
  }

  const getImportPreview = () => {
    if (!importContent.trim()) return null

    try {
      const lines = importContent.trim().split('\n').filter(l => l.trim())
      const sampleCount = lines.length

      // Try to parse first line to validate
      const firstSample = JSON.parse(lines[0])
      const hasAllFields = ['id', 'question', 'answer', 'topic', 'difficulty', 'case_citation', 'reasoning']
        .every(field => field in firstSample)

      return {
        valid: hasAllFields,
        count: sampleCount,
        missingFields: hasAllFields ? [] : ['id', 'question', 'answer', 'topic', 'difficulty', 'case_citation', 'reasoning']
          .filter(field => !(field in firstSample))
      }
    } catch (error) {
      return {
        valid: false,
        error: 'Invalid JSON format'
      }
    }
  }

  const preview = getImportPreview()

  const columns = [
    { field: 'id', headerName: 'ID', width: 180 },
    { field: 'question', headerName: 'Question', width: 300, flex: 1 },
    { field: 'answer', headerName: 'Answer', width: 300, flex: 1 },
    { field: 'topic', headerName: 'Topic', width: 200 },
    {
      field: 'difficulty',
      headerName: 'Difficulty',
      width: 130,
      renderCell: (params) => <DifficultyChip difficulty={params.value} />
    },
    { field: 'case_citation', headerName: 'Citation', width: 250 },
    { field: 'reasoning', headerName: 'Reasoning', width: 300, flex: 1 },
    {
      field: 'sample_type',
      headerName: 'Sample Type',
      width: 160,
      renderCell: (params) => params.value ? (
        <Chip
          label={params.value.replace('_', ' ')}
          size="small"
          sx={{
            bgcolor: params.value === 'case_analysis' ? 'rgba(33, 150, 243, 0.15)' :
                     params.value === 'educational' ? 'rgba(76, 175, 80, 0.15)' :
                     params.value === 'client_interaction' ? 'rgba(255, 152, 0, 0.15)' :
                     'rgba(156, 39, 176, 0.15)',
            color: params.value === 'case_analysis' ? '#2196f3' :
                   params.value === 'educational' ? '#4caf50' :
                   params.value === 'client_interaction' ? '#ff9800' :
                   '#9c27b0',
            fontWeight: 600,
            textTransform: 'capitalize'
          }}
        />
      ) : null
    },
    {
      field: 'provider',
      headerName: 'Provider',
      width: 110,
      renderCell: (params) => params.value ? (
        <Chip
          label={params.value}
          size="small"
          sx={{
            bgcolor: params.value === 'groq' ? 'rgba(245, 80, 54, 0.15)' :
                     params.value === 'cerebras' ? 'rgba(124, 58, 237, 0.15)' :
                     'rgba(33, 150, 243, 0.15)',
            color: params.value === 'groq' ? '#f55036' :
                   params.value === 'cerebras' ? '#7c3aed' :
                   '#2196f3',
            fontWeight: 600
          }}
        />
      ) : null
    },
    {
      field: 'model',
      headerName: 'Model',
      width: 200,
      renderCell: (params) => params.value ? (
        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
          {params.value}
        </Typography>
      ) : null
    },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 180,
      valueFormatter: (value) => {
        if (!value) return ''
        try {
          return new Date(value).toLocaleString()
        } catch (e) {
          return ''
        }
      }
    },
    {
      field: 'batch_id',
      headerName: 'Batch ID',
      width: 200,
      renderCell: (params) => params.value ? (
        <Tooltip title={params.value} arrow>
          <Typography variant="body2" sx={{
            fontFamily: 'monospace',
            fontSize: '0.75rem',
            color: 'text.secondary',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
          }}>
            {params.value.split('_').slice(-1)[0]}
          </Typography>
        </Tooltip>
      ) : null
    }
  ]

  return (
    <Box>
      <Fade in={true} timeout={500}>
        <Card className="fade-in">
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
              <div>
                <Typography variant="h5" sx={{ fontWeight: 600, mb: 0.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TableChart sx={{ color: '#2196f3' }} />
                  Dataset Explorer
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Browse, search, import, and export your training data
                </Typography>
              </div>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Tooltip title="Import samples from JSONL or JSON" arrow>
                  <Button
                    variant="contained"
                    startIcon={<Upload />}
                    onClick={() => setImportDialogOpen(true)}
                    sx={{
                      background: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)',
                      }
                    }}
                  >
                    Import
                  </Button>
                </Tooltip>
                <Tooltip title="View dataset on HuggingFace Hub" arrow>
                  <Button
                    variant="contained"
                    startIcon={<CloudUpload />}
                    onClick={() => window.open('https://huggingface.co/datasets/rezazerait/uk-legal-training-data', '_blank')}
                    sx={{
                      background: 'linear-gradient(135deg, #ff9800 0%, #ff6f00 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #f57c00 0%, #e65100 100%)',
                        transform: 'translateY(-2px)',
                        boxShadow: '0 6px 20px rgba(255, 152, 0, 0.4)'
                      },
                      fontWeight: 600,
                      boxShadow: '0 4px 12px rgba(255, 152, 0, 0.3)'
                    }}
                  >
                    🤗 HuggingFace
                  </Button>
                </Tooltip>
                <Tooltip title="Export dataset in various formats" arrow>
                  <ButtonGroup variant="outlined" size="small">
                    <Tooltip title="Export as JSONL format" arrow>
                      <Button startIcon={<FileDownload />} onClick={exportToJsonl}>
                        JSONL
                      </Button>
                    </Tooltip>
                    <Tooltip title="Export as CSV format" arrow>
                      <Button startIcon={<TableChart />} onClick={exportToCsv}>
                        CSV
                      </Button>
                    </Tooltip>
                    <Tooltip title="Export as Excel format" arrow>
                      <Button startIcon={<Download />} onClick={exportToExcel}>
                        Excel
                      </Button>
                    </Tooltip>
                  </ButtonGroup>
                </Tooltip>
              </Box>
            </Box>

            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                placeholder="Search across all fields (ID, question, answer, topic, difficulty, citation, reasoning)..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                size="medium"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search sx={{ color: '#2196f3' }} />
                    </InputAdornment>
                  ),
                  endAdornment: searchTerm && (
                    <InputAdornment position="end">
                      <Chip
                        label={`${filteredData.length} results`}
                        size="small"
                        color="primary"
                        icon={<FilterList />}
                      />
                    </InputAdornment>
                  )
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    '&:hover fieldset': {
                      borderColor: '#2196f3',
                    },
                  }
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                <strong>{filteredData.length.toLocaleString()}</strong> / <strong>{data.length.toLocaleString()}</strong> samples
                {searchTerm && (
                  <>
                    <span>•</span>
                    <Chip
                      label={`Export will include ${filteredData.length} filtered samples`}
                      size="small"
                      variant="outlined"
                      color="info"
                    />
                  </>
                )}
              </Typography>
            </Box>

            <Box sx={{ height: 600, width: '100%' }}>
              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                  <CircularProgress />
                </Box>
              ) : (
                <Fade in={!loading} timeout={600}>
                  <div style={{ height: '100%', width: '100%' }}>
                    <DataGrid
                      rows={filteredData}
                      columns={columns}
                      getRowId={(row) => row.numericId}
                      loading={loading}
                      initialState={{
                        pagination: {
                          paginationModel: { pageSize: 25, page: 0 }
                        }
                      }}
                      pageSizeOptions={[10, 25, 50, 100]}
                      onRowClick={handleRowClick}
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
                          cursor: 'pointer',
                        },
                      }}
                    />
                  </div>
                </Fade>
              )}
            </Box>
          </CardContent>
        </Card>
      </Fade>

      {/* Sample Detail Modal */}
      <Dialog
        open={detailModalOpen}
        onClose={handleCloseDetailModal}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            background: 'linear-gradient(135deg, #001219 0%, #000a12 100%)',
            border: '2px solid rgba(33, 150, 243, 0.3)',
          }
        }}
      >
        {selectedSample && (
          <>
            <DialogTitle sx={{
              pb: 1,
              borderBottom: '1px solid rgba(33, 150, 243, 0.2)',
              background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.15) 0%, rgba(33, 150, 243, 0.05) 100%)'
            }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 2 }}>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5, color: '#2196f3' }}>
                    Sample Details
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                    ID: {selectedSample.id}
                  </Typography>
                </Box>
                <DifficultyChip difficulty={selectedSample.difficulty} />
              </Box>
            </DialogTitle>
            <DialogContent sx={{ pt: 3 }}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* ID (always read-only) */}
                <Box>
                  <Typography variant="caption" sx={{ color: '#2196f3', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                    ID
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 0.5, fontWeight: 500, color: 'rgba(255, 255, 255, 0.6)' }}>
                    {selectedSample.id}
                  </Typography>
                </Box>

                <Divider sx={{ borderColor: 'rgba(33, 150, 243, 0.2)' }} />

                {/* Topic */}
                <Box>
                  <Typography variant="caption" sx={{ color: '#2196f3', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Topic
                  </Typography>
                  {isEditing ? (
                    <TextField
                      fullWidth
                      value={editedSample.topic}
                      onChange={(e) => handleFieldChange('topic', e.target.value)}
                      sx={{ mt: 1 }}
                      size="small"
                    />
                  ) : (
                    <Typography variant="body1" sx={{ mt: 0.5, fontWeight: 500 }}>
                      {selectedSample.topic}
                    </Typography>
                  )}
                </Box>

                {/* Difficulty */}
                <Box>
                  <Typography variant="caption" sx={{ color: '#2196f3', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Difficulty
                  </Typography>
                  {isEditing ? (
                    <TextField
                      fullWidth
                      select
                      value={editedSample.difficulty}
                      onChange={(e) => handleFieldChange('difficulty', e.target.value)}
                      sx={{ mt: 1 }}
                      size="small"
                      SelectProps={{ native: true }}
                    >
                      <option value="foundational">Foundational</option>
                      <option value="basic">Basic</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                      <option value="expert">Expert</option>
                    </TextField>
                  ) : (
                    <Box sx={{ mt: 1 }}>
                      <DifficultyChip difficulty={selectedSample.difficulty} />
                    </Box>
                  )}
                </Box>

                <Divider sx={{ borderColor: 'rgba(33, 150, 243, 0.2)' }} />

                {/* Question */}
                <Box>
                  <Typography variant="caption" sx={{ color: '#2196f3', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Question
                  </Typography>
                  {isEditing ? (
                    <TextField
                      fullWidth
                      multiline
                      rows={4}
                      value={editedSample.question}
                      onChange={(e) => handleFieldChange('question', e.target.value)}
                      sx={{ mt: 1 }}
                    />
                  ) : (
                    <Card sx={{
                      mt: 1,
                      p: 2,
                      background: 'rgba(33, 150, 243, 0.05)',
                      border: '1px solid rgba(33, 150, 243, 0.2)',
                      borderLeft: '4px solid #2196f3'
                    }}>
                      <Typography variant="body1" sx={{ lineHeight: 1.7 }}>
                        {selectedSample.question}
                      </Typography>
                    </Card>
                  )}
                </Box>

                {/* Answer */}
                <Box>
                  <Typography variant="caption" sx={{ color: '#69f0ae', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Answer
                  </Typography>
                  {isEditing ? (
                    <TextField
                      fullWidth
                      multiline
                      rows={8}
                      value={editedSample.answer}
                      onChange={(e) => handleFieldChange('answer', e.target.value)}
                      sx={{ mt: 1 }}
                    />
                  ) : (
                    <Card sx={{
                      mt: 1,
                      p: 2,
                      background: 'rgba(105, 240, 174, 0.05)',
                      border: '1px solid rgba(105, 240, 174, 0.2)',
                      borderLeft: '4px solid #69f0ae'
                    }}>
                      <Typography variant="body1" sx={{ lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                        {selectedSample.answer}
                      </Typography>
                    </Card>
                  )}
                </Box>

                {/* Reasoning */}
                <Box>
                  <Typography variant="caption" sx={{ color: '#ffb74d', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Legal Reasoning
                  </Typography>
                  {isEditing ? (
                    <TextField
                      fullWidth
                      multiline
                      rows={6}
                      value={editedSample.reasoning}
                      onChange={(e) => handleFieldChange('reasoning', e.target.value)}
                      sx={{ mt: 1 }}
                    />
                  ) : (
                    <Card sx={{
                      mt: 1,
                      p: 2,
                      background: 'rgba(255, 183, 77, 0.05)',
                      border: '1px solid rgba(255, 183, 77, 0.2)',
                      borderLeft: '4px solid #ffb74d'
                    }}>
                      <Typography variant="body1" sx={{ lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                        {selectedSample.reasoning}
                      </Typography>
                    </Card>
                  )}
                </Box>

                {/* Case Citation */}
                <Box>
                  <Typography variant="caption" sx={{ color: '#ba68c8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Case Citation
                  </Typography>
                  {isEditing ? (
                    <TextField
                      fullWidth
                      multiline
                      rows={2}
                      value={editedSample.case_citation}
                      onChange={(e) => handleFieldChange('case_citation', e.target.value)}
                      sx={{ mt: 1 }}
                    />
                  ) : (
                    <Card sx={{
                      mt: 1,
                      p: 2,
                      background: 'rgba(186, 104, 200, 0.05)',
                      border: '1px solid rgba(186, 104, 200, 0.2)',
                      borderLeft: '4px solid #ba68c8'
                    }}>
                      <Typography variant="body1" sx={{ lineHeight: 1.7, fontStyle: 'italic' }}>
                        {selectedSample.case_citation}
                      </Typography>
                    </Card>
                  )}
                </Box>
              </Box>
            </DialogContent>
            <DialogActions sx={{
              p: 2,
              borderTop: '1px solid rgba(33, 150, 243, 0.2)',
              background: 'rgba(33, 150, 243, 0.05)',
              display: 'flex',
              justifyContent: 'space-between'
            }}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {!isEditing && (
                  <>
                    <Button
                      onClick={handleDeleteClick}
                      variant="outlined"
                      color="error"
                      startIcon={<Delete />}
                      disabled={operationLoading}
                    >
                      Delete
                    </Button>
                    <Button
                      onClick={handleDownloadSample}
                      variant="outlined"
                      startIcon={<GetApp />}
                      sx={{
                        borderColor: '#4caf50',
                        color: '#4caf50',
                        '&:hover': {
                          borderColor: '#388e3c',
                          background: 'rgba(76, 175, 80, 0.08)',
                        }
                      }}
                    >
                      Download JSON
                    </Button>
                  </>
                )}
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {isEditing ? (
                  <>
                    <Button
                      onClick={handleCancelEdit}
                      variant="outlined"
                      startIcon={<Cancel />}
                      disabled={operationLoading}
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleSaveEdit}
                      variant="contained"
                      startIcon={operationLoading ? <CircularProgress size={20} /> : <Save />}
                      disabled={operationLoading}
                      sx={{
                        background: 'linear-gradient(135deg, #388e3c 0%, #4caf50 100%)',
                        '&:hover': {
                          background: 'linear-gradient(135deg, #2e7d32 0%, #388e3c 100%)',
                        }
                      }}
                    >
                      {operationLoading ? 'Saving...' : 'Save'}
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      onClick={handleCloseDetailModal}
                      variant="outlined"
                    >
                      Close
                    </Button>
                    <Button
                      onClick={handleEditClick}
                      variant="contained"
                      startIcon={<Edit />}
                      sx={{
                        background: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
                        '&:hover': {
                          background: 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)',
                        }
                      }}
                    >
                      Edit
                    </Button>
                  </>
                )}
              </Box>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            background: 'linear-gradient(135deg, #1a0000 0%, #0a0000 100%)',
            border: '2px solid rgba(244, 67, 54, 0.3)',
          }
        }}
      >
        <DialogTitle sx={{
          borderBottom: '1px solid rgba(244, 67, 54, 0.2)',
          background: 'rgba(244, 67, 54, 0.1)'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Delete sx={{ color: '#f44336' }} />
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#f44336' }}>
              Confirm Delete
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This action cannot be undone!
          </Alert>
          <Typography variant="body1" sx={{ mb: 2 }}>
            Are you sure you want to delete this sample?
          </Typography>
          {selectedSample && (
            <Box sx={{
              p: 2,
              background: 'rgba(244, 67, 54, 0.05)',
              border: '1px solid rgba(244, 67, 54, 0.2)',
              borderRadius: 1
            }}>
              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)', display: 'block', mb: 0.5 }}>
                ID
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                {selectedSample.id}
              </Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)', display: 'block', mb: 0.5 }}>
                Question
              </Typography>
              <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                {selectedSample.question.substring(0, 100)}...
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2, borderTop: '1px solid rgba(244, 67, 54, 0.2)' }}>
          <Button
            onClick={() => setDeleteConfirmOpen(false)}
            variant="outlined"
            disabled={operationLoading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            startIcon={operationLoading ? <CircularProgress size={20} /> : <Delete />}
            disabled={operationLoading}
            sx={{
              background: 'linear-gradient(135deg, #c62828 0%, #f44336 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #b71c1c 0%, #c62828 100%)',
              }
            }}
          >
            {operationLoading ? 'Deleting...' : 'Delete Sample'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Import Dialog */}
      <Dialog open={importDialogOpen} onClose={() => setImportDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
          <Upload sx={{ color: '#2196f3' }} />
          Import Samples
        </DialogTitle>
        <DialogContent>
          <Tabs value={importTab} onChange={(e, v) => setImportTab(v)} sx={{ mb: 2 }}>
            <Tab label="Paste Content" icon={<Code />} iconPosition="start" />
            <Tab label="Upload File" icon={<FileDownload />} iconPosition="start" />
          </Tabs>

          <Divider sx={{ mb: 2 }} />

          {importTab === 0 ? (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Paste JSONL (one JSON object per line) or JSON array of samples:
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={12}
                value={importContent}
                onChange={(e) => setImportContent(e.target.value)}
                placeholder={`{"id":"sample_001","question":"What is...","answer":"...","topic":"Contract Law","difficulty":"basic","case_citation":"...","reasoning":"Step 1:..."}\n{"id":"sample_002","question":"...","answer":"...","topic":"Tort Law","difficulty":"intermediate","case_citation":"...","reasoning":"Step 1:..."}`}
                sx={{
                  fontFamily: 'monospace',
                  '& .MuiInputBase-input': {
                    fontFamily: 'monospace',
                    fontSize: '0.85rem'
                  }
                }}
              />
            </>
          ) : (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Upload a .jsonl or .json file containing samples:
              </Typography>
              <Button
                variant="outlined"
                component="label"
                fullWidth
                startIcon={<Upload />}
                sx={{ mb: 2, py: 2 }}
              >
                Choose File
                <input
                  type="file"
                  hidden
                  accept=".jsonl,.json"
                  onChange={handleFileUpload}
                />
              </Button>
              {importContent && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  File loaded! {importContent.split('\n').length} lines detected
                </Alert>
              )}
            </>
          )}

          {/* Preview */}
          {preview && (
            <Fade in={true}>
              <Box sx={{ mt: 2 }}>
                {preview.valid ? (
                  <Alert severity="success" icon={<CheckCircle />}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      ✅ Valid Format • {preview.count} sample{preview.count !== 1 ? 's' : ''} ready to import
                    </Typography>
                    <Typography variant="caption">
                      All required fields detected: id, question, answer, topic, difficulty, case_citation, reasoning
                    </Typography>
                  </Alert>
                ) : (
                  <Alert severity="error">
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      ❌ Invalid Format
                    </Typography>
                    <Typography variant="caption">
                      {preview.error || `Missing required fields: ${preview.missingFields?.join(', ')}`}
                    </Typography>
                  </Alert>
                )}
              </Box>
            </Fade>
          )}

          {/* Import Result */}
          {importResult && (
            <Fade in={true}>
              <Alert severity={importResult.success ? 'success' : 'error'} sx={{ mt: 2 }}>
                {importResult.message}
                {importResult.total && (
                  <Typography variant="caption" sx={{ display: 'block', mt: 1 }}>
                    Total samples in dataset: {importResult.total}
                  </Typography>
                )}
              </Alert>
            </Fade>
          )}

          <Box sx={{ mt: 3, p: 2, bgcolor: 'rgba(33, 150, 243, 0.05)', borderRadius: 1 }}>
            <Typography variant="caption" sx={{ fontWeight: 600, display: 'block', mb: 1 }}>
              💡 Required Fields:
            </Typography>
            <Typography variant="caption" component="div" color="text.secondary">
              • <strong>id</strong>: Unique identifier<br />
              • <strong>question</strong>: Legal question<br />
              • <strong>answer</strong>: Comprehensive answer<br />
              • <strong>topic</strong>: Practice area and topic<br />
              • <strong>difficulty</strong>: foundational, basic, intermediate, advanced, or expert<br />
              • <strong>case_citation</strong>: Real UK cases or statutes<br />
              • <strong>reasoning</strong>: Step-by-step legal reasoning
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleImport}
            disabled={!preview?.valid || importLoading}
            startIcon={importLoading ? <CircularProgress size={20} /> : <Add />}
            sx={{
              background: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)',
              }
            }}
          >
            {importLoading ? 'Importing...' : 'Import Samples'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
