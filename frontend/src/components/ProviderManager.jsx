import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  CardActions,
  Switch,
  Button,
  TextField,
  Chip,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  LinearProgress,
  Tooltip,
  InputAdornment,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
  Speed as SpeedIcon,
  CloudQueue as CloudQueueIcon,
  Cached as CachedIcon,
  DragIndicator as DragIndicatorIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

const API_URL = 'http://127.0.0.1:5001/api';

const ProviderManager = () => {
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [editingApiKey, setEditingApiKey] = useState(null);
  const [showApiKey, setShowApiKey] = useState({});
  const [apiKeyValue, setApiKeyValue] = useState('');
  const [expandedProvider, setExpandedProvider] = useState(null);
  const [draggedModel, setDraggedModel] = useState(null);

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/providers/all`);
      const data = await response.json();
      if (data.success) {
        setProviders(data.providers);
      } else {
        setError(data.error || 'Failed to load providers');
      }
    } catch (err) {
      setError(`Failed to load providers: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const toggleProvider = async (providerId, currentStatus) => {
    try {
      const response = await fetch(`${API_URL}/providers/${providerId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await response.json();
      if (data.success) {
        setSuccess(`Provider ${currentStatus ? 'disabled' : 'enabled'} successfully`);
        loadProviders();
      } else {
        setError(data.error || 'Failed to toggle provider');
      }
    } catch (err) {
      setError(`Failed to toggle provider: ${err.message}`);
    }
  };

  const toggleModel = async (modelId, providerId, currentStatus) => {
    try {
      const response = await fetch(`${API_URL}/models/${modelId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_id: providerId })
      });
      const data = await response.json();
      if (data.success) {
        setSuccess(`Model ${currentStatus ? 'disabled' : 'enabled'} successfully`);
        loadProviders();
      } else {
        setError(data.error || 'Failed to toggle model');
      }
    } catch (err) {
      setError(`Failed to toggle model: ${err.message}`);
    }
  };

  const updateApiKey = async () => {
    if (!editingApiKey || !apiKeyValue.trim()) return;

    try {
      const response = await fetch(`${API_URL}/providers/${editingApiKey}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKeyValue })
      });
      const data = await response.json();
      if (data.success) {
        setSuccess('API key updated and encrypted successfully');
        setEditingApiKey(null);
        setApiKeyValue('');
        loadProviders();
      } else {
        setError(data.error || 'Failed to update API key');
      }
    } catch (err) {
      setError(`Failed to update API key: ${err.message}`);
    }
  };

  const updateModelPriority = async (modelId, providerId, newPriority) => {
    try {
      const response = await fetch(`${API_URL}/models/${modelId}/priority`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_id: providerId,
          priority: newPriority
        })
      });
      const data = await response.json();
      if (data.success) {
        setSuccess('Model priority updated successfully');
        loadProviders();
      } else {
        setError(data.error || 'Failed to update priority');
      }
    } catch (err) {
      setError(`Failed to update priority: ${err.message}`);
    }
  };

  const handleDragStart = (e, model) => {
    setDraggedModel(model);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = async (e, targetModel, providerId) => {
    e.preventDefault();
    if (!draggedModel || draggedModel.model_id === targetModel.model_id) return;

    // Swap priorities
    const temp = draggedModel.fallback_priority;
    await updateModelPriority(draggedModel.model_id, providerId, targetModel.fallback_priority);
    await updateModelPriority(targetModel.model_id, providerId, temp);

    setDraggedModel(null);
  };

  const getProviderIcon = (providerId) => {
    const icons = {
      groq: '⚡',
      cerebras: '🧠',
      google: '🔍',
      mistral: '🌟',
      ollama: '🦙'
    };
    return icons[providerId] || '🔮';
  };

  const getProviderColor = (providerId) => {
    const colors = {
      groq: '#f55036',
      cerebras: '#7c3aed',
      google: '#4285f4',
      mistral: '#f97316',
      ollama: '#22c55e'
    };
    return colors[providerId] || '#2196f3';
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ textAlign: 'center', mt: 2 }}>Loading providers...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Paper sx={{
        p: 4,
        mb: 4,
        background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(17, 25, 40, 0.8) 100%)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(33, 150, 243, 0.2)',
        borderRadius: 3,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)'
      }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h4" sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              mb: 1,
              fontWeight: 700,
              background: 'linear-gradient(135deg, #ffffff 0%, #2196f3 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              <Box sx={{
                p: 1.5,
                borderRadius: 2,
                background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.2) 0%, rgba(33, 150, 243, 0.1) 100%)',
                border: '1px solid rgba(33, 150, 243, 0.3)'
              }}>
                <SettingsIcon sx={{ fontSize: 32 }} />
              </Box>
              Provider & Model Manager
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.8, color: 'rgba(255,255,255,0.8)' }}>
              Configure AI providers, manage encrypted API keys, and set model fallback priorities
            </Typography>
          </Box>
          <Tooltip title="Reload all provider data from database" arrow>
            <Button
              variant="contained"
              startIcon={<CachedIcon />}
              onClick={loadProviders}
              disabled={loading}
              sx={{
                background: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
                px: 3,
                py: 1.5,
                '&:hover': {
                  background: 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 4px 12px rgba(33, 150, 243, 0.4)'
                },
                transition: 'all 0.3s ease'
              }}
            >
              Refresh
            </Button>
          </Tooltip>
        </Box>
      </Paper>

      {/* Alerts */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Summary Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(17, 25, 40, 0.8) 100%)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(33, 150, 243, 0.2)',
            borderRadius: 3,
            transition: 'all 0.3s ease',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: '0 8px 24px rgba(33, 150, 243, 0.3)',
              border: '1px solid rgba(33, 150, 243, 0.4)'
            }
          }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Box sx={{
                  p: 1.5,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.2) 0%, rgba(33, 150, 243, 0.1) 100%)',
                  border: '1px solid rgba(33, 150, 243, 0.3)'
                }}>
                  <CloudQueueIcon sx={{ fontSize: 28, color: '#2196f3' }} />
                </Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'rgba(255,255,255,0.7)' }}>
                  Total Providers
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 700, mb: 0.5 }}>{providers.length}</Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.6)' }}>
                {providers.filter(p => p.enabled).length} enabled • {providers.filter(p => !p.enabled).length} disabled
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: 'linear-gradient(135deg, rgba(156, 39, 176, 0.1) 0%, rgba(17, 25, 40, 0.8) 100%)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(156, 39, 176, 0.2)',
            borderRadius: 3,
            transition: 'all 0.3s ease',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: '0 8px 24px rgba(156, 39, 176, 0.3)',
              border: '1px solid rgba(156, 39, 176, 0.4)'
            }
          }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Box sx={{
                  p: 1.5,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, rgba(156, 39, 176, 0.2) 0%, rgba(156, 39, 176, 0.1) 100%)',
                  border: '1px solid rgba(156, 39, 176, 0.3)'
                }}>
                  <SettingsIcon sx={{ fontSize: 28, color: '#9c27b0' }} />
                </Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'rgba(255,255,255,0.7)' }}>
                  Total Models
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 700, mb: 0.5 }}>
                {providers.reduce((sum, p) => sum + (p.models?.length || 0), 0)}
              </Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.6)' }}>
                {providers.reduce((sum, p) => sum + (p.models?.filter(m => m.enabled).length || 0), 0)} enabled • {providers.reduce((sum, p) => sum + (p.models?.filter(m => !m.enabled).length || 0), 0)} disabled
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: 'linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(17, 25, 40, 0.8) 100%)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(76, 175, 80, 0.2)',
            borderRadius: 3,
            transition: 'all 0.3s ease',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: '0 8px 24px rgba(76, 175, 80, 0.3)',
              border: '1px solid rgba(76, 175, 80, 0.4)'
            }
          }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Box sx={{
                  p: 1.5,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, rgba(76, 175, 80, 0.2) 0%, rgba(76, 175, 80, 0.1) 100%)',
                  border: '1px solid rgba(76, 175, 80, 0.3)'
                }}>
                  <SpeedIcon sx={{ fontSize: 28, color: '#4caf50' }} />
                </Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'rgba(255,255,255,0.7)' }}>
                  Total Capacity
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 700, mb: 0.5 }}>
                {providers.filter(p => p.enabled).reduce((sum, p) => sum + (p.requests_per_minute || 0), 0)}
              </Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.6)' }}>
                requests per minute
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: 'linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, rgba(17, 25, 40, 0.8) 100%)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 152, 0, 0.2)',
            borderRadius: 3,
            transition: 'all 0.3s ease',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: '0 8px 24px rgba(255, 152, 0, 0.3)',
              border: '1px solid rgba(255, 152, 0, 0.4)'
            }
          }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Box sx={{
                  p: 1.5,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, rgba(255, 152, 0, 0.2) 0%, rgba(255, 152, 0, 0.1) 100%)',
                  border: '1px solid rgba(255, 152, 0, 0.3)'
                }}>
                  <LockIcon sx={{ fontSize: 28, color: '#ff9800' }} />
                </Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'rgba(255,255,255,0.7)' }}>
                  API Keys
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 700, mb: 0.5 }}>
                {providers.filter(p => p.has_api_key).length}
              </Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.6)' }}>
                encrypted & stored securely
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Provider Cards */}
      <Grid container spacing={3}>
        {providers.map((provider) => (
          <Grid item xs={12} key={provider.id}>
            <Card sx={{
              background: `linear-gradient(135deg, ${getProviderColor(provider.id)}15 0%, rgba(17, 25, 40, 0.8) 100%)`,
              backdropFilter: 'blur(20px)',
              border: `2px solid ${getProviderColor(provider.id)}40`,
              borderRadius: 3,
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: `0 12px 32px ${getProviderColor(provider.id)}40`,
                border: `2px solid ${getProviderColor(provider.id)}60`
              }
            }}>
              <CardHeader
                avatar={
                  <Box sx={{
                    fontSize: '3rem',
                    p: 2,
                    borderRadius: 3,
                    background: `linear-gradient(135deg, ${getProviderColor(provider.id)}30 0%, ${getProviderColor(provider.id)}15 100%)`,
                    border: `1px solid ${getProviderColor(provider.id)}50`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'scale(1.1) rotate(5deg)'
                    }
                  }}>
                    {getProviderIcon(provider.id)}
                  </Box>
                }
                title={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                    <Typography variant="h5" sx={{ fontWeight: 700, color: getProviderColor(provider.id) }}>
                      {provider.name}
                    </Typography>
                    <Chip
                      label={provider.enabled ? 'Active' : 'Inactive'}
                      color={provider.enabled ? 'success' : 'default'}
                      size="small"
                      icon={provider.enabled ? <CheckCircleIcon /> : <ErrorIcon />}
                      sx={{
                        fontWeight: 600,
                        animation: provider.enabled ? 'pulse 2s ease-in-out infinite' : 'none'
                      }}
                    />
                    <Chip
                      icon={<SpeedIcon />}
                      label={`${provider.requests_per_minute} RPM`}
                      size="small"
                      sx={{
                        backgroundColor: `${getProviderColor(provider.id)}30`,
                        border: `1px solid ${getProviderColor(provider.id)}60`,
                        fontWeight: 600
                      }}
                    />
                    <Chip
                      label={`${provider.tokens_per_minute.toLocaleString()} TPM`}
                      size="small"
                      variant="outlined"
                      sx={{ fontWeight: 600 }}
                    />
                    {provider.has_api_key && (
                      <Tooltip title="API Key encrypted and stored in database" arrow>
                        <Chip
                          icon={<LockIcon />}
                          label="Secured"
                          size="small"
                          sx={{
                            bgcolor: 'rgba(76, 175, 80, 0.2)',
                            border: '1px solid rgba(76, 175, 80, 0.5)',
                            color: '#4caf50',
                            fontWeight: 600
                          }}
                        />
                      </Tooltip>
                    )}
                  </Box>
                }
                action={
                  <Tooltip title={provider.enabled ? 'Disable provider' : 'Enable provider'} arrow>
                    <Box>
                      <Switch
                        checked={provider.enabled}
                        onChange={() => toggleProvider(provider.id, provider.enabled)}
                        sx={{
                          '& .MuiSwitch-switchBase.Mui-checked': {
                            color: getProviderColor(provider.id)
                          },
                          '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                            backgroundColor: getProviderColor(provider.id)
                          }
                        }}
                      />
                    </Box>
                  </Tooltip>
                }
                subheader={
                  <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                    <Chip
                      label={provider.base_url}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem' }}
                    />
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)' }}>•</Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)', fontWeight: 600 }}>
                      Champion: {provider.champion_model_id}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)' }}>•</Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                      {provider.models?.length || 0} models available
                    </Typography>
                  </Box>
                }
                sx={{ pb: 1 }}
              />
              <CardContent>
                {/* API Key Management */}
                <Accordion
                  sx={{
                    background: 'rgba(255, 255, 255, 0.03)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    borderRadius: 2,
                    mb: 2,
                    '&:before': { display: 'none' },
                    '&.Mui-expanded': {
                      background: 'rgba(255, 255, 255, 0.06)'
                    }
                  }}
                >
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    sx={{
                      '&:hover': {
                        background: 'rgba(255, 255, 255, 0.05)'
                      }
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, width: '100%' }}>
                      <Box sx={{
                        p: 1,
                        borderRadius: 1.5,
                        background: 'linear-gradient(135deg, rgba(255, 152, 0, 0.2) 0%, rgba(255, 152, 0, 0.1) 100%)',
                        border: '1px solid rgba(255, 152, 0, 0.3)'
                      }}>
                        <LockIcon fontSize="small" sx={{ color: '#ff9800' }} />
                      </Box>
                      <Typography sx={{ fontWeight: 600 }}>
                        API Key Configuration
                      </Typography>
                      {provider.has_api_key && (
                        <Chip
                          icon={<CheckCircleIcon />}
                          label="Configured"
                          size="small"
                          sx={{
                            ml: 'auto',
                            bgcolor: 'rgba(76, 175, 80, 0.2)',
                            border: '1px solid rgba(76, 175, 80, 0.5)',
                            color: '#4caf50',
                            fontWeight: 600
                          }}
                        />
                      )}
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails sx={{ p: 3 }}>
                    <Alert
                      severity="info"
                      icon={<LockIcon />}
                      sx={{
                        mb: 3,
                        background: 'rgba(33, 150, 243, 0.1)',
                        border: '1px solid rgba(33, 150, 243, 0.3)'
                      }}
                    >
                      <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                        🔐 Secure API Key Storage
                      </Typography>
                      <Typography variant="caption">
                        API keys are encrypted using Fernet (AES-128) symmetric encryption before being stored in the PostgreSQL database.
                        Your keys are never stored in plain text.
                      </Typography>
                    </Alert>
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                      <TextField
                        fullWidth
                        type={showApiKey[provider.id] ? 'text' : 'password'}
                        label="API Key"
                        placeholder={provider.has_api_key ? '••••••••••••••••' : 'Paste your API key here'}
                        value={editingApiKey === provider.id ? apiKeyValue : ''}
                        onChange={(e) => setApiKeyValue(e.target.value)}
                        onFocus={() => setEditingApiKey(provider.id)}
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <Tooltip title={showApiKey[provider.id] ? 'Hide API key' : 'Show API key'} arrow>
                                <IconButton
                                  onClick={() => setShowApiKey(prev => ({ ...prev, [provider.id]: !prev[provider.id] }))}
                                  edge="end"
                                  sx={{
                                    color: showApiKey[provider.id] ? '#2196f3' : 'rgba(255,255,255,0.5)',
                                    '&:hover': { color: '#2196f3' }
                                  }}
                                >
                                  {showApiKey[provider.id] ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                </IconButton>
                              </Tooltip>
                            </InputAdornment>
                          )
                        }}
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            '&:hover fieldset': {
                              borderColor: getProviderColor(provider.id)
                            },
                            '&.Mui-focused fieldset': {
                              borderColor: getProviderColor(provider.id)
                            }
                          }
                        }}
                      />
                      <Tooltip
                        title={
                          editingApiKey !== provider.id || !apiKeyValue.trim()
                            ? 'Enter an API key first'
                            : 'Save and encrypt API key'
                        }
                        arrow
                      >
                        <span>
                          <Button
                            variant="contained"
                            startIcon={<SaveIcon />}
                            onClick={updateApiKey}
                            disabled={editingApiKey !== provider.id || !apiKeyValue.trim()}
                            sx={{
                              minWidth: 140,
                              height: 56,
                              background: `linear-gradient(135deg, ${getProviderColor(provider.id)} 0%, ${getProviderColor(provider.id)}dd 100%)`,
                              '&:hover': {
                                background: `linear-gradient(135deg, ${getProviderColor(provider.id)}dd 0%, ${getProviderColor(provider.id)}bb 100%)`,
                                transform: 'translateY(-2px)',
                                boxShadow: `0 4px 12px ${getProviderColor(provider.id)}60`
                              },
                              transition: 'all 0.3s ease'
                            }}
                          >
                            Save Key
                          </Button>
                        </span>
                      </Tooltip>
                    </Box>
                  </AccordionDetails>
                </Accordion>

                {/* Models Table */}
                <Accordion
                  expanded={expandedProvider === provider.id}
                  onChange={() => setExpandedProvider(expandedProvider === provider.id ? null : provider.id)}
                  sx={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    '&:before': { display: 'none' }
                  }}
                >
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <SettingsIcon fontSize="small" />
                      Models ({provider.models?.length || 0})
                      <Chip
                        label={`${provider.models?.filter(m => m.enabled).length || 0} enabled`}
                        size="small"
                        color="primary"
                        sx={{ ml: 1 }}
                      />
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Alert severity="info" sx={{ mb: 2 }}>
                      <Typography variant="body2">
                        <strong>Drag and drop</strong> models to reorder fallback priority. Lower priority = tried first.
                      </Typography>
                    </Alert>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell width={40}></TableCell>
                            <TableCell>Priority</TableCell>
                            <TableCell>Model</TableCell>
                            <TableCell>Max Tokens</TableCell>
                            <TableCell>Context</TableCell>
                            <TableCell>Features</TableCell>
                            <TableCell align="right">Enabled</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {provider.models
                            ?.sort((a, b) => a.fallback_priority - b.fallback_priority)
                            .map((model) => (
                              <TableRow
                                key={model.model_id}
                                draggable
                                onDragStart={(e) => handleDragStart(e, model)}
                                onDragOver={handleDragOver}
                                onDrop={(e) => handleDrop(e, model, provider.id)}
                                sx={{
                                  cursor: 'grab',
                                  '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.05)' },
                                  opacity: model.enabled ? 1 : 0.5
                                }}
                              >
                                <TableCell>
                                  <DragIndicatorIcon fontSize="small" sx={{ opacity: 0.5 }} />
                                </TableCell>
                                <TableCell>
                                  <Chip
                                    label={model.fallback_priority}
                                    size="small"
                                    color={model.fallback_priority === 1 ? 'primary' : 'default'}
                                  />
                                </TableCell>
                                <TableCell>
                                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                    {model.display_name}
                                  </Typography>
                                  <Typography variant="caption" sx={{ opacity: 0.6 }}>
                                    {model.model_id}
                                  </Typography>
                                </TableCell>
                                <TableCell>
                                  <Chip
                                    label={model.max_tokens?.toLocaleString() || 'N/A'}
                                    size="small"
                                    variant="outlined"
                                  />
                                </TableCell>
                                <TableCell>
                                  <Chip
                                    label={model.context_window?.toLocaleString() || 'N/A'}
                                    size="small"
                                    variant="outlined"
                                  />
                                </TableCell>
                                <TableCell>
                                  {model.is_thinking_model && (
                                    <Chip label="Thinking" size="small" color="secondary" sx={{ mr: 0.5 }} />
                                  )}
                                  {model.supports_json && (
                                    <Chip label="JSON" size="small" color="info" sx={{ mr: 0.5 }} />
                                  )}
                                  {provider.champion_model_id === model.model_id && (
                                    <Chip label="Champion" size="small" color="warning" />
                                  )}
                                </TableCell>
                                <TableCell align="right">
                                  <Switch
                                    checked={model.enabled}
                                    onChange={() => toggleModel(model.model_id, provider.id, model.enabled)}
                                    size="small"
                                  />
                                </TableCell>
                              </TableRow>
                            ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </AccordionDetails>
                </Accordion>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default ProviderManager;
