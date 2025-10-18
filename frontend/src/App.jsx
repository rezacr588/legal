/**
 * @fileoverview Main application component for the Legal Dashboard
 *
 * This is the root component that manages:
 * - Navigation between different sections (Overview, Generation, Batches, Dataset, Documentation)
 * - Global state for statistics and notifications
 * - Sidebar navigation with collapsible/expandable functionality
 * - Sound notifications for batch completion events
 * - Real-time monitoring of batch generation status
 * - Responsive design for mobile and desktop
 *
 * @component
 * @requires react
 * @requires @mui/material
 * @requires react-toastify
 */

import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import {
  ThemeProvider,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Badge,
  IconButton,
  Tooltip,
  Fade,
  Divider,
  Avatar,
  useMediaQuery,
  Menu,
  MenuItem,
  Chip
} from '@mui/material'
import theme from './theme/theme'
import {
  Dashboard as DashboardIcon,
  AutoAwesome as GenerateIcon,
  Storage as DatasetIcon,
  CheckCircle as SuccessIcon,
  VolumeUp,
  VolumeOff,
  MenuBook as DocumentationIcon,
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  Search as SearchIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  CloudUpload as CloudUploadIcon,
  Refresh as RefreshIcon,
  Chat as ChatIcon,
  Settings as SettingsIcon
} from '@mui/icons-material'
import { ToastContainer, toast } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'

import Overview from './components/Overview'
import GenerationHub from './components/GenerationHub'
import Dataset from './components/Dataset'
import Documentation from './components/Documentation'
import HuggingFacePush from './components/HuggingFacePush'
import Chat from './components/Chat'
import ProviderManager from './components/ProviderManager'

/** Width of the sidebar when fully expanded (in pixels) */
const DRAWER_WIDTH = 280

/** Width of the sidebar when collapsed (in pixels) */
const DRAWER_WIDTH_COLLAPSED = 70

// Removed TabPanel - now using React Router

/**
 * Main application content component
 * Must be inside BrowserRouter to use navigation hooks
 */
function AppContent() {
  const navigate = useNavigate()
  const location = useLocation()

  // ========== STATE MANAGEMENT ==========

  /** @type {[boolean, Function]} Mobile drawer open/closed state */
  const [mobileOpen, setMobileOpen] = useState(false)

  /** @type {[boolean, Function]} Desktop sidebar collapsed/expanded state */
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true)

  /** @type {[number, Function]} Count of currently running batch generation jobs */
  const [runningBatches, setRunningBatches] = useState(0)

  /** @type {[Object, Function]} Global statistics (total samples, practice areas, etc.) */
  const [stats, setStats] = useState({})

  /** @type {[Object, Function]} Legacy notification state (kept for compatibility) */
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' })

  /**
   * @type {[Object, Function]} Tracks previous status of all batches to detect state changes
   * Format: { batchId: 'running' | 'completed' | 'stopped' }
   */
  const [previousBatchStatus, setPreviousBatchStatus] = useState({})

  /** @type {[boolean, Function]} Enable/disable sound notifications (user preference) */
  const [soundEnabled, setSoundEnabled] = useState(true)

  /**
   * @type {[Array, Function]} History of all notifications with metadata
   * Format: [{ id: timestamp, message: string, severity: string, timestamp: Date }]
   */
  const [notificationHistory, setNotificationHistory] = useState([])

  /** @type {[HTMLElement|null, Function]} Anchor element for notification dropdown menu */
  const [notificationAnchorEl, setNotificationAnchorEl] = useState(null)

  /** @type {[boolean, Function]} Hugging Face push modal open/closed state */
  const [hfModalOpen, setHfModalOpen] = useState(false)

  /** @type {boolean} True if viewport is mobile/tablet (< md breakpoint) */
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

  // ========== SOUND NOTIFICATION SYSTEM ==========

  /**
   * Plays audio notification using Web Audio API with different tones for different event types
   *
   * Sound patterns:
   * - 'success': Rising triple tone (C5-E5-G5) for completed batches
   * - 'warning': Double beep for stopped batches
   * - 'error': Descending tone for failed operations
   * - 'stuck': Urgent repeating tone for stuck batches
   *
   * @param {string} type - Notification type ('success'|'warning'|'error'|'stuck')
   * @returns {void}
   */
  const playNotificationSound = (type = 'success') => {
    if (!soundEnabled) return

    try {
      // Create audio context for custom sounds
      const audioContext = new (window.AudioContext || window.webkitAudioContext)()

      const playTone = (frequency, duration, delay = 0) => {
        setTimeout(() => {
          const oscillator = audioContext.createOscillator()
          const gainNode = audioContext.createGain()

          oscillator.connect(gainNode)
          gainNode.connect(audioContext.destination)

          oscillator.frequency.value = frequency
          oscillator.type = 'sine'

          gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
          gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration)

          oscillator.start(audioContext.currentTime)
          oscillator.stop(audioContext.currentTime + duration)
        }, delay)
      }

      // Different sound patterns for different notification types
      if (type === 'success') {
        // Success: Rising triple tone (C-E-G)
        playTone(523.25, 0.15, 0)    // C5
        playTone(659.25, 0.15, 150)  // E5
        playTone(783.99, 0.3, 300)   // G5
      } else if (type === 'warning') {
        // Warning: Double beep
        playTone(659.25, 0.2, 0)
        playTone(659.25, 0.2, 250)
      } else if (type === 'error') {
        // Error: Descending tone
        playTone(659.25, 0.15, 0)
        playTone(523.25, 0.3, 150)
      } else if (type === 'stuck') {
        // Stuck batch: Repeating urgent tone
        playTone(880, 0.1, 0)
        playTone(880, 0.1, 150)
        playTone(880, 0.1, 300)
      }
    } catch (error) {
      console.error('Error playing sound:', error)
    }
  }

  // ========== LIFECYCLE HOOKS ==========

  /**
   * Initialize application on mount
   * - Load initial statistics
   * - Start batch monitoring (every 5 seconds)
   * - Start stats polling (every 10 seconds)
   * - Clean up intervals on unmount
   */
  useEffect(() => {
    loadStats()
    // Monitor batch status for completion notifications
    const batchInterval = setInterval(checkBatchStatus, 5000)
    // Poll stats every 10 seconds for real-time updates
    const statsInterval = setInterval(loadStats, 10000)
    return () => {
      clearInterval(batchInterval)
      clearInterval(statsInterval)
    }
  }, [])

  // ========== API FUNCTIONS ==========

  /**
   * Fetch latest statistics from the backend API
   * Updates global stats state with:
   * - Total sample count
   * - Practice area distribution
   * - Difficulty level distribution
   * - Provider/model statistics
   *
   * Uses cache-busting headers to ensure fresh data
   *
   * @async
   * @returns {Promise<void>}
   */
  const loadStats = async () => {
    try {
      const response = await fetch('/api/stats', {
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      })
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Error loading stats:', error)
    }
  }

  /**
   * Monitor batch generation status and detect completions
   *
   * Polls the batch history endpoint and compares current status with previous status
   * to detect state changes (running → completed/stopped). When a batch completes:
   * - Plays notification sound
   * - Shows toast notification
   * - Adds to notification history
   * - Refreshes stats
   *
   * @async
   * @returns {Promise<void>}
   */
  const checkBatchStatus = async () => {
    try {
      const response = await fetch('/api/generate/batch/history', {
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      })
      const data = await response.json()

      if (data.success && data.batches.length > 0) {
        // Check if any batch just completed
        data.batches.forEach(batch => {
          const prevStatus = previousBatchStatus[batch.id]
          if (prevStatus === 'running' && (batch.status === 'completed' || batch.status === 'stopped')) {
            // Batch just finished!
            const message = batch.status === 'completed'
              ? `Batch generation completed! Generated ${batch.samples_generated} samples using ${batch.tokens_used?.toLocaleString()} tokens.`
              : `Batch generation stopped. Generated ${batch.samples_generated} samples.`

            const severity = batch.status === 'completed' ? 'success' : 'warning'

            // Add to notification history
            addToNotificationHistory(message, severity)

            setNotification({
              open: true,
              message: message,
              severity: severity
            })

            // Play notification sound and show toast
            playNotificationSound(severity)
            toast[severity](message, {
              position: 'top-right',
              autoClose: 5000,
              hideProgressBar: false,
              closeOnClick: true,
              pauseOnHover: true,
              draggable: true,
              theme: 'dark'
            })

            // Reload stats to show updated sample count
            loadStats()
          }
        })

        // Update previous batch status
        const statusMap = {}
        data.batches.forEach(batch => {
          statusMap[batch.id] = batch.status
        })
        setPreviousBatchStatus(statusMap)
      }
    } catch (error) {
      console.error('Error checking batch status:', error)
    }
  }

  // ========== EVENT HANDLERS ==========

  /**
   * Handle navigation to a route
   * @param {string} path - Route path to navigate to
   * @returns {void}
   */
  const handleNavigation = (path) => {
    navigate(path)
    if (isMobile) {
      setMobileOpen(false) // Close mobile drawer after navigation
    }
  }

  /**
   * Close the legacy notification snackbar (kept for compatibility)
   * @returns {void}
   */
  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false })
  }

  /**
   * Add a notification to the notification history
   * Keeps only the most recent 20 notifications to prevent memory issues
   *
   * @param {string} message - Notification message to display
   * @param {string} [severity='success'] - Severity level ('success'|'warning'|'error'|'info')
   * @returns {void}
   */
  const addToNotificationHistory = (message, severity = 'success') => {
    const newNotification = {
      id: Date.now(),
      message,
      severity,
      timestamp: new Date()
    }
    setNotificationHistory(prev => [newNotification, ...prev].slice(0, 20)) // Keep last 20
  }

  /**
   * Show notification with sound and toast
   * This is the main notification function used by child components
   * Combines:
   * - Audio notification (if enabled)
   * - Toast notification (react-toastify)
   * - Notification history tracking
   *
   * @param {string} message - Notification message
   * @param {string} [severity='success'] - Severity level
   * @returns {void}
   */
  const showNotificationWithSound = (message, severity = 'success') => {
    playNotificationSound(severity)

    // Add to notification history
    addToNotificationHistory(message, severity)

    // Use toast instead of snackbar
    toast[severity](message, {
      position: 'top-right',
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      theme: 'dark'
    })
  }

  /**
   * Open notification history dropdown menu
   * @param {React.MouseEvent} event - Click event from notification bell icon
   * @returns {void}
   */
  const handleNotificationClick = (event) => {
    setNotificationAnchorEl(event.currentTarget)
  }

  /**
   * Close notification history dropdown menu
   * @returns {void}
   */
  const handleNotificationClose = () => {
    setNotificationAnchorEl(null)
  }

  /**
   * Clear all notifications from history
   * Also closes the notification menu
   * @returns {void}
   */
  const clearNotificationHistory = () => {
    setNotificationHistory([])
    handleNotificationClose()
  }

  /**
   * Toggle mobile drawer open/closed
   * @returns {void}
   */
  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  // ========== NAVIGATION CONFIGURATION ==========

  /**
   * Sidebar navigation menu items configuration
   * Each item represents a main section of the application
   *
   * @type {Array<Object>}
   * @property {string} text - Display name of the section
   * @property {JSX.Element} icon - Material-UI icon component (with optional badge)
   * @property {string} path - Route path for navigation
   */
  const menuItems = [
    { text: 'Overview', icon: <DashboardIcon />, path: '/' },
    { text: 'Generation Hub', icon: <Badge badgeContent={runningBatches} color="error"><GenerateIcon /></Badge>, path: '/generation' },
    { text: 'Chat Testing', icon: <ChatIcon />, path: '/chat' },
    { text: 'Provider Manager', icon: <SettingsIcon />, path: '/providers' },
    { text: 'Dataset', icon: <DatasetIcon />, path: '/dataset' },
    { text: 'Documentation', icon: <DocumentationIcon />, path: '/documentation' }
  ]

  // Get current page title based on route
  const getCurrentPageTitle = () => {
    const item = menuItems.find(item => item.path === location.pathname)
    return item ? item.text : 'Legal AI Training'
  }

  // ========== SIDEBAR DRAWER ==========

  /**
   * Sidebar drawer content component
   * Features:
   * - Branding header with logo and sample count
   * - Navigation menu with icons and labels
   * - Active tab highlighting with gradient
   * - Collapse/expand toggle button
   * - Responsive to collapsed state
   */
  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{
        p: sidebarCollapsed ? 1.5 : 3,
        background: 'linear-gradient(135deg, #1976d2 0%, #2196f3 50%, #42a5f5 100%)',
        backgroundSize: '200% 200%',
        animation: 'gradientShift 4s ease infinite',
        display: 'flex',
        alignItems: 'center',
        justifyContent: sidebarCollapsed ? 'center' : 'space-between',
        gap: 2,
        transition: 'all 0.3s ease',
        boxShadow: '0 4px 20px rgba(33, 150, 243, 0.4)'
      }}>
        {!sidebarCollapsed && (
          <>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{
                bgcolor: '#ffffff',
                color: '#1976d2',
                width: 48,
                height: 48,
                fontSize: '1.5rem',
                animation: 'bounce 2s ease-in-out infinite',
                cursor: 'pointer',
                '&:hover': {
                  transform: 'scale(1.1) rotate(10deg)',
                  transition: 'all 0.3s ease'
                }
              }}>
                ⚖️
              </Avatar>
              <Box>
                <Typography variant="h6" sx={{
                  fontWeight: 700,
                  color: '#ffffff',
                  fontSize: { xs: '0.95rem', sm: '1.1rem', md: '1.25rem' }
                }}>
                  Legal AI Training
                </Typography>
                <Typography variant="caption" sx={{
                  color: 'rgba(255,255,255,0.8)',
                  fontSize: { xs: '0.7rem', sm: '0.75rem' }
                }}>
                  {stats.total?.toLocaleString() || 0} Samples
                </Typography>
              </Box>
            </Box>
          </>
        )}
        {sidebarCollapsed && (
          <Avatar sx={{
            bgcolor: '#ffffff',
            color: '#1976d2',
            width: 40,
            height: 40,
            fontSize: '1.2rem',
            animation: 'bounce 2s ease-in-out infinite',
            cursor: 'pointer',
            '&:hover': {
              transform: 'scale(1.1) rotate(10deg)',
              transition: 'all 0.3s ease'
            }
          }}>
            ⚖️
          </Avatar>
        )}
      </Box>
      <Divider />
      <List sx={{ pt: 2, flexGrow: 1 }}>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path
          return (
            <ListItem key={item.text} disablePadding sx={{ px: sidebarCollapsed ? 1 : 2, mb: 1 }}>
              <Tooltip title={sidebarCollapsed ? item.text : ''} placement="right" arrow>
                <ListItemButton
                  selected={isActive}
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    borderRadius: 2,
                    transition: 'all 0.3s ease',
                    justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                    minHeight: 48,
                    '&.Mui-selected': {
                      background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.2) 0%, rgba(33, 150, 243, 0.1) 100%)',
                      borderLeft: sidebarCollapsed ? 'none' : '4px solid #2196f3',
                      '&:hover': {
                        background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.3) 0%, rgba(33, 150, 243, 0.15) 100%)'
                      }
                    },
                    '&:hover': {
                      background: 'rgba(33, 150, 243, 0.08)',
                      transform: sidebarCollapsed ? 'scale(1.05)' : 'translateX(4px)'
                    }
                  }}
                >
                  <ListItemIcon sx={{
                    color: isActive ? '#2196f3' : 'inherit',
                    minWidth: sidebarCollapsed ? 'auto' : 40,
                    justifyContent: 'center'
                  }}>
                    {item.icon}
                  </ListItemIcon>
                  {!sidebarCollapsed && (
                    <ListItemText
                      primary={item.text}
                      primaryTypographyProps={{
                        fontWeight: isActive ? 600 : 400,
                        color: isActive ? '#2196f3' : 'inherit'
                      }}
                    />
                  )}
                </ListItemButton>
              </Tooltip>
            </ListItem>
          )
        })}
      </List>
      <Divider />
      <Box sx={{ p: 1 }}>
        <Tooltip title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'} placement="right" arrow>
          <IconButton
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            sx={{
              width: '100%',
              borderRadius: 2,
              color: '#2196f3',
              '&:hover': {
                bgcolor: 'rgba(33, 150, 243, 0.1)'
              }
            }}
          >
            {sidebarCollapsed ? <ChevronRightIcon /> : <ChevronLeftIcon />}
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  )

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        {/* App Bar */}
        <AppBar
          position="fixed"
          sx={{
            width: { md: `calc(100% - ${sidebarCollapsed ? DRAWER_WIDTH_COLLAPSED : DRAWER_WIDTH}px)` },
            ml: { md: `${sidebarCollapsed ? DRAWER_WIDTH_COLLAPSED : DRAWER_WIDTH}px` },
            bgcolor: '#000a12',
            borderBottom: '3px solid transparent',
            borderImage: 'linear-gradient(90deg, #1976d2, #2196f3, #42a5f5, #2196f3, #1976d2) 1',
            backgroundImage: 'linear-gradient(#000a12, #000a12), linear-gradient(90deg, #1976d2, #2196f3, #42a5f5)',
            backgroundOrigin: 'border-box',
            backgroundClip: 'padding-box, border-box',
            boxShadow: '0 4px 20px rgba(33, 150, 243, 0.3), 0 0 40px rgba(33, 150, 243, 0.1)',
            transition: 'all 0.3s ease'
          }}
        >
          <Toolbar>
            <IconButton
              color="inherit"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2, display: { md: 'none' } }}
            >
              <MenuIcon />
            </IconButton>
            <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography
                variant="h6"
                component="div"
                sx={{
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #ffffff 0%, #2196f3 50%, #64b5f6 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  textShadow: '0 0 30px rgba(33, 150, 243, 0.5)',
                  fontSize: { xs: '1rem', sm: '1.2rem', md: '1.4rem' },
                  letterSpacing: '0.5px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: { xs: 'nowrap', sm: 'normal' }
                }}
              >
                {getCurrentPageTitle()}
              </Typography>
              {runningBatches > 0 && (
                <Chip
                  icon={<GenerateIcon sx={{ fontSize: '0.9rem' }} />}
                  label={`${runningBatches} batch${runningBatches > 1 ? 'es' : ''} running`}
                  size="small"
                  sx={{
                    bgcolor: 'rgba(33, 150, 243, 0.15)',
                    color: '#2196f3',
                    border: '1px solid rgba(33, 150, 243, 0.3)',
                    fontWeight: 600,
                    fontSize: '0.75rem',
                    animation: 'pulse 2s ease-in-out infinite',
                    '@keyframes pulse': {
                      '0%, 100%': {
                        boxShadow: '0 0 10px rgba(33, 150, 243, 0.5)'
                      },
                      '50%': {
                        boxShadow: '0 0 20px rgba(33, 150, 243, 0.8)'
                      }
                    },
                    display: { xs: 'none', sm: 'flex' }
                  }}
                />
              )}
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1, sm: 2 } }}>
              <Tooltip title="Refresh data (bypass cache)" arrow>
                <IconButton
                  onClick={() => {
                    loadStats()
                    toast.info('Refreshing data...', { autoClose: 2000, theme: 'dark' })
                  }}
                  sx={{
                    color: '#2196f3',
                    '&:hover': { bgcolor: 'rgba(33, 150, 243, 0.1)' }
                  }}
                  size="small"
                >
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Push to Hugging Face" arrow>
                <IconButton
                  onClick={() => setHfModalOpen(true)}
                  sx={{
                    color: '#ff9800',
                    '&:hover': { bgcolor: 'rgba(255, 152, 0, 0.1)' }
                  }}
                  size="small"
                >
                  <CloudUploadIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title={soundEnabled ? 'Disable sound notifications' : 'Enable sound notifications'} arrow>
                <IconButton
                  onClick={() => setSoundEnabled(!soundEnabled)}
                  sx={{
                    color: soundEnabled ? '#69f0ae' : '#666',
                    '&:hover': { bgcolor: 'rgba(105, 240, 174, 0.1)' }
                  }}
                  size="small"
                >
                  {soundEnabled ? <VolumeUp /> : <VolumeOff />}
                </IconButton>
              </Tooltip>
              <Tooltip title="View notifications" arrow>
                <IconButton
                  color="inherit"
                  size="small"
                  onClick={handleNotificationClick}
                  sx={{
                    '&:hover': { bgcolor: 'rgba(33, 150, 243, 0.1)' }
                  }}
                >
                  <Badge badgeContent={notificationHistory.length > 0 ? notificationHistory.length : null} color="error">
                    <NotificationsIcon />
                  </Badge>
                </IconButton>
              </Tooltip>
            </Box>
          </Toolbar>
        </AppBar>

        {/* Sidebar Navigation */}
        <Box
          component="nav"
          sx={{ width: { md: sidebarCollapsed ? DRAWER_WIDTH_COLLAPSED : DRAWER_WIDTH }, flexShrink: { md: 0 } }}
        >
          {/* Mobile drawer */}
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={handleDrawerToggle}
            ModalProps={{ keepMounted: true }}
            sx={{
              display: { xs: 'block', md: 'none' },
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: DRAWER_WIDTH,
                bgcolor: '#001219',
                borderRight: '2px solid rgba(33, 150, 243, 0.3)'
              }
            }}
          >
            {drawer}
          </Drawer>
          {/* Desktop drawer */}
          <Drawer
            variant="permanent"
            sx={{
              display: { xs: 'none', md: 'block' },
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: sidebarCollapsed ? DRAWER_WIDTH_COLLAPSED : DRAWER_WIDTH,
                bgcolor: '#001219',
                borderRight: '2px solid rgba(33, 150, 243, 0.3)',
                transition: 'width 0.3s ease',
                overflowX: 'hidden'
              }
            }}
            open
          >
            {drawer}
          </Drawer>
        </Box>

        {/* Main Content */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 3,
            width: { md: `calc(100% - ${sidebarCollapsed ? DRAWER_WIDTH_COLLAPSED : DRAWER_WIDTH}px)` },
            mt: { xs: 7, sm: 8 },
            transition: 'all 0.3s ease'
          }}
        >
          <Fade in={true} timeout={600}>
            <Box sx={{ py: 3 }} className="slide-in-up">
              <Routes>
                <Route path="/" element={<Overview stats={stats} onStatsUpdate={loadStats} />} />
                <Route path="/generation" element={
                  <GenerationHub
                    onStatsUpdate={loadStats}
                    onNotification={showNotificationWithSound}
                  />
                } />
                <Route path="/chat" element={<Chat />} />
                <Route path="/providers" element={<ProviderManager />} />
                <Route path="/dataset" element={
                  <Dataset
                    stats={stats}
                    onStatsUpdate={loadStats}
                    onNotification={showNotificationWithSound}
                  />
                } />
                <Route path="/documentation" element={<Documentation />} />
              </Routes>
            </Box>
          </Fade>
        </Box>
      </Box>

      {/* Toast Notifications */}
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
        style={{
          marginTop: '64px'
        }}
      />

      {/* Notification History Menu */}
      <Menu
        anchorEl={notificationAnchorEl}
        open={Boolean(notificationAnchorEl)}
        onClose={handleNotificationClose}
        PaperProps={{
          sx: {
            mt: 1.5,
            width: 420,
            maxHeight: 500,
            bgcolor: '#001219',
            border: '2px solid rgba(33, 150, 243, 0.3)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
            borderRadius: 3
          }
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ p: 2, borderBottom: '1px solid rgba(33, 150, 243, 0.2)' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#2196f3' }}>
              Notifications
            </Typography>
            {notificationHistory.length > 0 && (
              <Chip
                label="Clear All"
                size="small"
                onClick={clearNotificationHistory}
                sx={{
                  bgcolor: 'rgba(255, 82, 82, 0.1)',
                  color: '#ff5252',
                  '&:hover': {
                    bgcolor: 'rgba(255, 82, 82, 0.2)',
                  }
                }}
              />
            )}
          </Box>
        </Box>

        {notificationHistory.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <NotificationsIcon sx={{ fontSize: 48, color: 'rgba(255, 255, 255, 0.2)', mb: 2 }} />
            <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.5)' }}>
              No notifications yet
            </Typography>
          </Box>
        ) : (
          <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
            {notificationHistory.map((notif) => (
              <MenuItem
                key={notif.id}
                sx={{
                  py: 2,
                  px: 2,
                  borderBottom: '1px solid rgba(33, 150, 243, 0.1)',
                  '&:hover': {
                    bgcolor: 'rgba(33, 150, 243, 0.05)'
                  },
                  display: 'block',
                  whiteSpace: 'normal'
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      bgcolor: notif.severity === 'success' ? '#69f0ae' :
                               notif.severity === 'error' ? '#ff5252' :
                               notif.severity === 'warning' ? '#ffb74d' : '#2196f3',
                      mt: 0.5,
                      flexShrink: 0
                    }}
                  />
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography
                      variant="body2"
                      sx={{
                        color: '#ffffff',
                        mb: 0.5,
                        wordBreak: 'break-word'
                      }}
                    >
                      {notif.message}
                    </Typography>
                    <Typography
                      variant="caption"
                      sx={{
                        color: 'rgba(255, 255, 255, 0.5)',
                        display: 'block'
                      }}
                    >
                      {formatNotificationTime(notif.timestamp)}
                    </Typography>
                  </Box>
                </Box>
              </MenuItem>
            ))}
          </Box>
        )}
      </Menu>

      {/* Hugging Face Push Modal */}
      <HuggingFacePush
        open={hfModalOpen}
        onClose={() => setHfModalOpen(false)}
        stats={stats}
      />
    </ThemeProvider>
  )
}

// Helper function to format notification timestamp
function formatNotificationTime(timestamp) {
  const now = new Date()
  const notifDate = new Date(timestamp)
  const diffMs = now - notifDate
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`

  return notifDate.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * Root App component wrapped in BrowserRouter for routing
 */
function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}

export default App
