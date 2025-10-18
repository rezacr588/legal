import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Typography,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Send as SendIcon,
  Delete as DeleteIcon,
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  Psychology as PsychologyIcon,
  Speed as SpeedIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';

const API_URL = 'http://127.0.0.1:5001/api';

const Chat = () => {
  const [providers, setProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState('cerebras');
  const [selectedModel, setSelectedModel] = useState('');
  const [availableModels, setAvailableModels] = useState([]);
  const [systemPrompts, setSystemPrompts] = useState({});
  const [selectedPrompt, setSelectedPrompt] = useState('legal_assistant');
  const [customSystemPrompt, setCustomSystemPrompt] = useState('');
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastResponse, setLastResponse] = useState(null);

  const messagesEndRef = useRef(null);

  // Load providers on mount
  useEffect(() => {
    loadProviders();
    loadSystemPrompts();
  }, []);

  // Update available models when provider changes
  useEffect(() => {
    if (providers.length > 0 && selectedProvider) {
      const provider = providers.find(p => p.id === selectedProvider);
      if (provider) {
        setAvailableModels(provider.models || []);
        setSelectedModel(provider.champion_model || '');
      }
    }
  }, [selectedProvider, providers]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadProviders = async () => {
    try {
      const response = await fetch(`${API_URL}/chat/providers`);
      const data = await response.json();
      if (data.success) {
        setProviders(data.providers);
        if (data.providers.length > 0) {
          setSelectedProvider(data.providers[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to load providers:', error);
      setError('Failed to load providers');
    }
  };

  const loadSystemPrompts = async () => {
    try {
      const response = await fetch(`${API_URL}/chat/system-prompts`);
      const data = await response.json();
      if (data.success) {
        setSystemPrompts(data.prompts);
        setCustomSystemPrompt(data.prompts.legal_assistant?.prompt || '');
      }
    } catch (error) {
      console.error('Failed to load system prompts:', error);
    }
  };

  const handlePromptChange = (promptKey) => {
    setSelectedPrompt(promptKey);
    if (systemPrompts[promptKey]) {
      setCustomSystemPrompt(systemPrompts[promptKey].prompt);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    setError(null);

    try {
      const conversationMessages = [
        { role: 'system', content: customSystemPrompt },
        ...messages.filter(m => m.role !== 'system'),
        userMessage
      ];

      const response = await fetch(`${API_URL}/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: selectedProvider,
          model: selectedModel,
          messages: conversationMessages,
          temperature: 0.7,
          max_tokens: 2000
        })
      });

      const data = await response.json();

      if (data.success) {
        const assistantMessage = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString(),
          provider: data.provider,
          model: data.model,
          tokens: data.tokens_used,
          elapsed: data.elapsed_time
        };

        setMessages(prev => [...prev, assistantMessage]);
        setLastResponse({
          tokens: data.tokens_used,
          elapsed: data.elapsed_time,
          provider: data.provider,
          model: data.model
        });
      } else {
        setError(data.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      setError('Failed to send message: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setLastResponse(null);
    setError(null);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
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

  const currentProvider = providers.find(p => p.id === selectedProvider);

  return (
    <Box sx={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column', gap: 2, p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 2, background: 'rgba(17, 25, 40, 0.75)', backdropFilter: 'blur(16px)' }}>
        <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <PsychologyIcon /> Interactive Chat Testing
        </Typography>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr 1fr' }, gap: 2 }}>
          {/* Provider Selection */}
          <FormControl fullWidth size="small">
            <InputLabel>Provider</InputLabel>
            <Select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              label="Provider"
            >
              {providers.map(provider => (
                <MenuItem key={provider.id} value={provider.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <span>{getProviderIcon(provider.id)}</span>
                    <span>{provider.name}</span>
                    <Chip
                      label={`${provider.requests_per_minute} RPM`}
                      size="small"
                      sx={{ ml: 'auto', height: 20 }}
                    />
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Model Selection */}
          <FormControl fullWidth size="small">
            <InputLabel>Model</InputLabel>
            <Select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              label="Model"
            >
              {availableModels.map(model => (
                <MenuItem key={model.id} value={model.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <span>{model.name}</span>
                    {model.is_thinking && <Chip label="Thinking" size="small" color="primary" sx={{ height: 20 }} />}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* System Prompt Selection */}
          <FormControl fullWidth size="small">
            <InputLabel>System Prompt</InputLabel>
            <Select
              value={selectedPrompt}
              onChange={(e) => handlePromptChange(e.target.value)}
              label="System Prompt"
            >
              {Object.entries(systemPrompts).map(([key, value]) => (
                <MenuItem key={key} value={key}>
                  {value.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        {/* System Instruction Editor */}
        <Accordion sx={{ mt: 2, background: 'rgba(255, 255, 255, 0.05)' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SettingsIcon fontSize="small" />
              Edit System Instruction
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <TextField
              fullWidth
              multiline
              rows={4}
              value={customSystemPrompt}
              onChange={(e) => setCustomSystemPrompt(e.target.value)}
              placeholder="Enter custom system instruction..."
              variant="outlined"
            />
          </AccordionDetails>
        </Accordion>

        {/* Current Configuration Display */}
        {currentProvider && (
          <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
            <Chip
              icon={<span>{getProviderIcon(selectedProvider)}</span>}
              label={`${currentProvider.name} / ${selectedModel}`}
              sx={{ backgroundColor: getProviderColor(selectedProvider) + '33' }}
            />
            {lastResponse && (
              <>
                <Chip
                  icon={<TimerIcon />}
                  label={`${lastResponse.elapsed}s`}
                  size="small"
                  variant="outlined"
                />
                <Chip
                  icon={<SpeedIcon />}
                  label={`${lastResponse.tokens} tokens`}
                  size="small"
                  variant="outlined"
                />
              </>
            )}
          </Box>
        )}
      </Paper>

      {/* Error Display */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Chat Messages */}
      <Paper
        sx={{
          flex: 1,
          p: 2,
          overflow: 'auto',
          background: 'rgba(17, 25, 40, 0.75)',
          backdropFilter: 'blur(16px)',
          display: 'flex',
          flexDirection: 'column',
          gap: 2
        }}
      >
        {messages.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 8, color: 'text.secondary' }}>
            <PsychologyIcon sx={{ fontSize: 64, opacity: 0.3, mb: 2 }} />
            <Typography variant="h6" sx={{ opacity: 0.5 }}>
              Start a conversation with any provider
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.3, mt: 1 }}>
              Select a provider, model, and system prompt above, then send a message
            </Typography>
          </Box>
        ) : (
          <>
            {messages.map((message, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                <Card
                  sx={{
                    maxWidth: '70%',
                    background: message.role === 'user'
                      ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                      : 'rgba(255, 255, 255, 0.05)',
                    backdropFilter: 'blur(10px)'
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                      <Typography variant="caption" sx={{ opacity: 0.7 }}>
                        {message.role === 'user' ? '👤 You' : `🤖 ${message.provider || 'Assistant'}`}
                      </Typography>
                      {message.tokens && (
                        <Chip
                          label={`${message.tokens} tokens • ${message.elapsed}s`}
                          size="small"
                          sx={{ height: 18, fontSize: '0.7rem' }}
                        />
                      )}
                    </Box>
                    <Typography
                      variant="body1"
                      sx={{
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word'
                      }}
                    >
                      {message.content}
                    </Typography>
                    <Typography variant="caption" sx={{ opacity: 0.5, display: 'block', mt: 1 }}>
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}

        {loading && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CircularProgress size={20} />
            <Typography variant="body2" sx={{ opacity: 0.7 }}>
              Generating response...
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Input Area */}
      <Paper sx={{ p: 2, background: 'rgba(17, 25, 40, 0.75)', backdropFilter: 'blur(16px)' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Shift+Enter for new line)"
            disabled={loading}
            variant="outlined"
          />
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Button
              variant="contained"
              onClick={sendMessage}
              disabled={loading || !inputMessage.trim()}
              startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
              sx={{ minWidth: 100 }}
            >
              Send
            </Button>
            <Button
              variant="outlined"
              onClick={clearChat}
              startIcon={<DeleteIcon />}
              disabled={messages.length === 0}
              sx={{ minWidth: 100 }}
            >
              Clear
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default Chat;
