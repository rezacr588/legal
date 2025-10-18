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
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3, background: 'rgba(17, 25, 40, 0.75)', backdropFilter: 'blur(16px)' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <SettingsIcon /> Provider & Model Manager
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.7 }}>
              Configure providers, manage API keys, and set model fallback priorities
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<CachedIcon />}
            onClick={loadProviders}
            disabled={loading}
          >
            Refresh
          </Button>
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
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'rgba(17, 25, 40, 0.75)', backdropFilter: 'blur(16px)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CloudQueueIcon color="primary" />
                Total Providers
              </Typography>
              <Typography variant="h3">{providers.length}</Typography>
              <Typography variant="caption" sx={{ opacity: 0.7 }}>
                {providers.filter(p => p.enabled).length} enabled
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'rgba(17, 25, 40, 0.75)', backdropFilter: 'blur(16px)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SettingsIcon color="secondary" />
                Total Models
              </Typography>
              <Typography variant="h3">
                {providers.reduce((sum, p) => sum + (p.models?.length || 0), 0)}
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.7 }}>
                {providers.reduce((sum, p) => sum + (p.models?.filter(m => m.enabled).length || 0), 0)} enabled
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'rgba(17, 25, 40, 0.75)', backdropFilter: 'blur(16px)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SpeedIcon color="success" />
                Total RPM
              </Typography>
              <Typography variant="h3">
                {providers.filter(p => p.enabled).reduce((sum, p) => sum + (p.requests_per_minute || 0), 0)}
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.7 }}>
                requests per minute
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'rgba(17, 25, 40, 0.75)', backdropFilter: 'blur(16px)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LockIcon color="warning" />
                API Keys
              </Typography>
              <Typography variant="h3">
                {providers.filter(p => p.has_api_key).length}
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.7 }}>
                encrypted & stored
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Provider Cards */}
      <Grid container spacing={3}>
        {providers.map((provider) => (
          <Grid item xs={12} key={provider.id}>
            <Card sx={{ background: 'rgba(17, 25, 40, 0.75)', backdropFilter: 'blur(16px)' }}>
              <CardHeader
                avatar={
                  <Box sx={{ fontSize: '2rem' }}>
                    {getProviderIcon(provider.id)}
                  </Box>
                }
                title={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="h6">{provider.name}</Typography>
                    <Chip
                      label={provider.enabled ? 'Enabled' : 'Disabled'}
                      color={provider.enabled ? 'success' : 'default'}
                      size="small"
                    />
                    <Chip
                      icon={<SpeedIcon />}
                      label={`${provider.requests_per_minute} RPM`}
                      size="small"
                      sx={{ backgroundColor: getProviderColor(provider.id) + '33' }}
                    />
                    <Chip
                      label={`${provider.tokens_per_minute.toLocaleString()} TPM`}
                      size="small"
                      variant="outlined"
                    />
                    {provider.has_api_key && (
                      <Chip
                        icon={<LockIcon />}
                        label="API Key Configured"
                        size="small"
                        color="success"
                      />
                    )}
                  </Box>
                }
                action={
                  <Switch
                    checked={provider.enabled}
                    onChange={() => toggleProvider(provider.id, provider.enabled)}
                    color="primary"
                  />
                }
                subheader={
                  <Typography variant="caption" sx={{ opacity: 0.7 }}>
                    {provider.base_url} • Champion: {provider.champion_model_id}
                  </Typography>
                }
              />
              <CardContent>
                {/* API Key Management */}
                <Accordion
                  sx={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    mb: 2,
                    '&:before': { display: 'none' }
                  }}
                >
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LockIcon fontSize="small" />
                      API Key Configuration
                      {provider.has_api_key && (
                        <CheckCircleIcon color="success" fontSize="small" sx={{ ml: 1 }} />
                      )}
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                      <TextField
                        fullWidth
                        type={showApiKey[provider.id] ? 'text' : 'password'}
                        label="API Key"
                        placeholder={provider.has_api_key ? 'API key is encrypted and stored' : 'Enter new API key'}
                        value={editingApiKey === provider.id ? apiKeyValue : ''}
                        onChange={(e) => setApiKeyValue(e.target.value)}
                        onFocus={() => setEditingApiKey(provider.id)}
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={() => setShowApiKey(prev => ({ ...prev, [provider.id]: !prev[provider.id] }))}
                                edge="end"
                              >
                                {showApiKey[provider.id] ? <VisibilityOffIcon /> : <VisibilityIcon />}
                              </IconButton>
                            </InputAdornment>
                          )
                        }}
                        helperText={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                            <InfoIcon fontSize="small" />
                            <span>Keys are encrypted using Fernet (AES-128) before storage</span>
                          </Box>
                        }
                      />
                      <Button
                        variant="contained"
                        startIcon={<SaveIcon />}
                        onClick={updateApiKey}
                        disabled={editingApiKey !== provider.id || !apiKeyValue.trim()}
                        sx={{ minWidth: 120, height: 56 }}
                      >
                        Save
                      </Button>
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
