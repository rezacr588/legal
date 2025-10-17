import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Alert,
  LinearProgress,
  Chip,
  Link,
  InputAdornment,
  IconButton,
  Tooltip
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  Visibility,
  VisibilityOff,
  Info as InfoIcon
} from '@mui/icons-material'

/**
 * HuggingFacePush Modal Component
 *
 * Allows users to push the legal training dataset to Hugging Face Hub
 * Supports configuration of:
 * - HF API Token
 * - Repository name
 * - Dataset format (parquet, json, csv)
 * - Privacy settings (public/private)
 */
function HuggingFacePush({ open, onClose, stats }) {
  const [token, setToken] = useState('')
  const [showToken, setShowToken] = useState(false)
  const [repoName, setRepoName] = useState('legal-training-dataset')
  const [format, setFormat] = useState('parquet')
  const [isPrivate, setIsPrivate] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handlePush = async () => {
    setError('')
    setSuccess(false)
    setUploading(true)
    setProgress(0)

    try {
      // Validate inputs
      if (!repoName.trim()) {
        throw new Error('Repository name is required')
      }

      // Start upload - only send token if provided
      const payload = {
        repo_name: repoName,
        format,
        private: isPrivate
      }

      // Only include token if user provided one (otherwise backend uses environment token)
      if (token.trim()) {
        payload.token = token
      }

      const response = await fetch('http://127.0.0.1:5001/api/huggingface/push', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      // Simulate progress (real implementation would use streaming or polling)
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 500)

      const data = await response.json()
      clearInterval(progressInterval)
      setProgress(100)

      if (!response.ok) {
        throw new Error(data.error || 'Failed to push to Hugging Face')
      }

      setSuccess(true)
      setTimeout(() => {
        onClose()
        resetForm()
      }, 3000)
    } catch (err) {
      setError(err.message)
      setProgress(0)
    } finally {
      setUploading(false)
    }
  }

  const resetForm = () => {
    setToken('')
    setRepoName('legal-training-dataset')
    setFormat('parquet')
    setIsPrivate(false)
    setProgress(0)
    setError('')
    setSuccess(false)
  }

  const handleClose = () => {
    if (!uploading) {
      resetForm()
      onClose()
    }
  }

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          bgcolor: '#001219',
          border: '2px solid rgba(33, 150, 243, 0.3)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.8)',
          borderRadius: 3
        }
      }}
    >
      <DialogTitle sx={{
        background: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
        color: '#ffffff',
        fontWeight: 700,
        fontSize: { xs: '1.25rem', sm: '1.5rem' },
        display: 'flex',
        alignItems: 'center',
        gap: 2
      }}>
        <UploadIcon />
        Push to Hugging Face
      </DialogTitle>

      <DialogContent sx={{ mt: 3 }}>
        {/* Info Box */}
        <Alert
          severity="success"
          icon={<InfoIcon />}
          sx={{
            mb: 3,
            bgcolor: 'rgba(76, 175, 80, 0.1)',
            border: '1px solid rgba(76, 175, 80, 0.3)',
            '& .MuiAlert-message': {
              fontSize: { xs: '0.8rem', sm: '0.875rem' }
            }
          }}
        >
          Your HuggingFace token is already stored in the environment. You can push directly without entering it again,
          or optionally provide a different token below.
        </Alert>

        {/* Dataset Stats */}
        <Box sx={{
          display: 'flex',
          gap: 2,
          mb: 3,
          flexWrap: 'wrap'
        }}>
          <Chip
            label={`${stats?.total?.toLocaleString() || 0} Samples`}
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`${stats?.total_topics || 0} Topics`}
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`${stats?.total_difficulties || 0} Difficulty Levels`}
            color="primary"
            variant="outlined"
          />
        </Box>

        {/* API Token */}
        <TextField
          fullWidth
          label="Hugging Face API Token (Optional)"
          type={showToken ? 'text' : 'password'}
          value={token}
          onChange={(e) => setToken(e.target.value)}
          disabled={uploading}
          margin="normal"
          placeholder="Leave empty to use stored token"
          helperText="Token from environment will be used if not provided"
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => setShowToken(!showToken)}
                  edge="end"
                  size="small"
                >
                  {showToken ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            )
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              '& fieldset': {
                borderColor: 'rgba(33, 150, 243, 0.3)'
              }
            }
          }}
        />

        {/* Repository Name */}
        <TextField
          fullWidth
          label="Repository Name"
          value={repoName}
          onChange={(e) => setRepoName(e.target.value)}
          disabled={uploading}
          required
          margin="normal"
          placeholder="my-legal-dataset"
          helperText="Will be created under your Hugging Face username"
          sx={{
            '& .MuiOutlinedInput-root': {
              '& fieldset': {
                borderColor: 'rgba(33, 150, 243, 0.3)'
              }
            }
          }}
        />

        <Box sx={{ display: 'flex', gap: 2, mt: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
          {/* Format Selection */}
          <FormControl fullWidth disabled={uploading}>
            <InputLabel>Dataset Format</InputLabel>
            <Select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              label="Dataset Format"
              sx={{
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(33, 150, 243, 0.3)'
                }
              }}
            >
              <MenuItem value="parquet">Parquet (Recommended)</MenuItem>
              <MenuItem value="json">JSON</MenuItem>
              <MenuItem value="csv">CSV</MenuItem>
            </Select>
          </FormControl>

          {/* Privacy Selection */}
          <FormControl fullWidth disabled={uploading}>
            <InputLabel>Privacy</InputLabel>
            <Select
              value={isPrivate}
              onChange={(e) => setIsPrivate(e.target.value)}
              label="Privacy"
              sx={{
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(33, 150, 243, 0.3)'
                }
              }}
            >
              <MenuItem value={false}>Public</MenuItem>
              <MenuItem value={true}>Private</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* Upload Progress */}
        {uploading && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="body2" sx={{ mb: 1, color: '#64b5f6' }}>
              Uploading to Hugging Face... {progress}%
            </Typography>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{
                height: 8,
                borderRadius: 4,
                bgcolor: 'rgba(33, 150, 243, 0.1)',
                '& .MuiLinearProgress-bar': {
                  bgcolor: '#2196f3'
                }
              }}
            />
          </Box>
        )}

        {/* Error Message */}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {/* Success Message */}
        {success && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Successfully pushed dataset to Hugging Face! 🎉
          </Alert>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 3, pt: 0 }}>
        <Button
          onClick={handleClose}
          disabled={uploading}
          sx={{
            color: '#666',
            '&:hover': {
              bgcolor: 'rgba(255, 255, 255, 0.05)'
            }
          }}
        >
          Cancel
        </Button>
        <Button
          onClick={handlePush}
          disabled={uploading || !repoName.trim()}
          variant="contained"
          startIcon={<UploadIcon />}
          sx={{
            background: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)'
            },
            '&:disabled': {
              background: 'rgba(33, 150, 243, 0.2)',
              color: 'rgba(255, 255, 255, 0.3)'
            }
          }}
        >
          {uploading ? 'Uploading...' : 'Push to Hugging Face'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default HuggingFacePush
