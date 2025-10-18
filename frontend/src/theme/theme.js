import { createTheme } from '@mui/material/styles'

// Custom color palette
const palette = {
  mode: 'dark',
  primary: {
    main: '#2196f3',
    light: '#64b5f6',
    dark: '#1976d2',
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#1e88e5',
    light: '#42a5f5',
    dark: '#1565c0',
  },
  background: {
    default: '#000a12',
    paper: '#001219',
    elevated: '#001e2b',
  },
  error: {
    main: '#ff5252',
    light: '#ff6b6b',
    dark: '#d32f2f',
  },
  warning: {
    main: '#ffb74d',
    light: '#ffd54f',
    dark: '#f57c00',
  },
  success: {
    main: '#69f0ae',
    light: '#9fffe0',
    dark: '#4caf50',
  },
  info: {
    main: '#2196f3',
    light: '#64b5f6',
    dark: '#1976d2',
  },
  text: {
    primary: '#ffffff',
    secondary: '#b3e5fc',
    disabled: 'rgba(255, 255, 255, 0.38)',
  },
  divider: 'rgba(33, 150, 243, 0.2)',

  // Custom gradient colors
  gradient: {
    primary: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
    secondary: 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)',
    success: 'linear-gradient(135deg, #388e3c 0%, #4caf50 100%)',
    error: 'linear-gradient(135deg, #d32f2f 0%, #f44336 100%)',
    warning: 'linear-gradient(135deg, #f57c00 0%, #ff9800 100%)',
    info: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
  },

  // Difficulty colors
  difficulty: {
    foundational: {
      main: '#9c27b0',
      light: '#ba68c8',
      gradient: 'linear-gradient(135deg, #9c27b0 0%, #ba68c8 100%)',
    },
    basic: {
      main: '#388e3c',
      light: '#4caf50',
      gradient: 'linear-gradient(135deg, #388e3c 0%, #4caf50 100%)',
    },
    intermediate: {
      main: '#1976d2',
      light: '#2196f3',
      gradient: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
    },
    advanced: {
      main: '#f57c00',
      light: '#ff9800',
      gradient: 'linear-gradient(135deg, #f57c00 0%, #ff9800 100%)',
    },
    expert: {
      main: '#d32f2f',
      light: '#f44336',
      gradient: 'linear-gradient(135deg, #d32f2f 0%, #f44336 100%)',
    },
  },
}

// Typography configuration
const typography = {
  fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  h1: {
    fontWeight: 700,
    fontSize: '3rem',
    letterSpacing: '-0.01562em',
  },
  h2: {
    fontWeight: 700,
    fontSize: '2.5rem',
    letterSpacing: '-0.00833em',
  },
  h3: {
    fontWeight: 700,
    fontSize: '2rem',
    letterSpacing: '0em',
  },
  h4: {
    fontWeight: 700,
    fontSize: '1.75rem',
    letterSpacing: '0.00735em',
  },
  h5: {
    fontWeight: 700,
    fontSize: '1.5rem',
    letterSpacing: '0.02em',
  },
  h6: {
    fontWeight: 600,
    fontSize: '1.25rem',
    letterSpacing: '0.0075em',
  },
  subtitle1: {
    fontWeight: 600,
    fontSize: '1rem',
    letterSpacing: '0.00938em',
  },
  subtitle2: {
    fontWeight: 600,
    fontSize: '0.875rem',
    letterSpacing: '0.00714em',
  },
  body1: {
    fontWeight: 400,
    fontSize: '1rem',
    letterSpacing: '0.00938em',
    lineHeight: 1.7,
  },
  body2: {
    fontWeight: 400,
    fontSize: '0.875rem',
    letterSpacing: '0.01071em',
    lineHeight: 1.6,
  },
  button: {
    fontWeight: 600,
    fontSize: '0.875rem',
    letterSpacing: '0.02857em',
    textTransform: 'none',
  },
  caption: {
    fontWeight: 400,
    fontSize: '0.75rem',
    letterSpacing: '0.03333em',
  },
  overline: {
    fontWeight: 600,
    fontSize: '0.75rem',
    letterSpacing: '0.08333em',
    textTransform: 'uppercase',
  },
}

// Component overrides
const components = {
  MuiCssBaseline: {
    styleOverrides: {
      body: {
        scrollbarWidth: 'thin',
        scrollbarColor: '#2196f3 #001219',
        '&::-webkit-scrollbar': {
          width: '8px',
          height: '8px',
        },
        '&::-webkit-scrollbar-track': {
          background: '#001219',
        },
        '&::-webkit-scrollbar-thumb': {
          background: '#2196f3',
          borderRadius: '4px',
          '&:hover': {
            background: '#1976d2',
          },
        },
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: {
        backgroundImage: 'none',
        borderRadius: 16,
        border: '2px solid rgba(33, 150, 243, 0.4)',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
      },
      elevation1: {
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)',
      },
      elevation2: {
        boxShadow: '0 6px 16px rgba(0, 0, 0, 0.6)',
      },
      elevation3: {
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        backgroundImage: 'none',
        backgroundColor: '#001219',
        border: '2px solid rgba(33, 150, 243, 0.4)',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7)',
        borderRadius: 16,
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: '0 12px 32px rgba(33, 150, 243, 0.3)',
          borderColor: 'rgba(33, 150, 243, 0.6)',
        },
      },
    },
  },
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: 12,
        textTransform: 'none',
        fontWeight: 600,
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: '0 6px 16px rgba(0, 0, 0, 0.5)',
          transform: 'translateY(-2px)',
        },
      },
      contained: {
        background: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
        '&:hover': {
          background: 'linear-gradient(135deg, #1565c0 0%, #1976d2 100%)',
        },
      },
      outlined: {
        borderWidth: 2,
        '&:hover': {
          borderWidth: 2,
        },
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: 20,
        fontWeight: 600,
        border: '1px solid',
      },
    },
  },
  MuiTextField: {
    styleOverrides: {
      root: {
        '& .MuiOutlinedInput-root': {
          borderRadius: 12,
          transition: 'all 0.3s ease',
          '&:hover': {
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: '#2196f3',
              borderWidth: 2,
            },
          },
          '&.Mui-focused': {
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: '#2196f3',
              borderWidth: 2,
            },
          },
        },
      },
    },
  },
  MuiSelect: {
    styleOverrides: {
      root: {
        borderRadius: 12,
      },
    },
  },
  MuiDialog: {
    styleOverrides: {
      paper: {
        backgroundImage: 'none',
        borderRadius: 16,
      },
    },
  },
  MuiDrawer: {
    styleOverrides: {
      paper: {
        borderRight: '2px solid rgba(33, 150, 243, 0.3)',
        backgroundImage: 'none',
      },
    },
  },
  MuiAppBar: {
    styleOverrides: {
      root: {
        borderBottom: '2px solid rgba(33, 150, 243, 0.3)',
        boxShadow: '0 2px 12px rgba(0, 0, 0, 0.6)',
        backgroundImage: 'none',
      },
    },
  },
  MuiTooltip: {
    styleOverrides: {
      tooltip: {
        backgroundColor: '#001219',
        border: '1px solid rgba(33, 150, 243, 0.5)',
        borderRadius: 8,
        fontSize: '0.75rem',
        padding: '8px 12px',
      },
      arrow: {
        color: '#001219',
        '&::before': {
          border: '1px solid rgba(33, 150, 243, 0.5)',
        },
      },
    },
  },
  MuiLinearProgress: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        height: 8,
      },
      bar: {
        borderRadius: 8,
      },
    },
  },
}

// Spacing configuration (8px base)
const spacing = 8

// Breakpoints
const breakpoints = {
  values: {
    xs: 0,
    sm: 600,
    md: 960,
    lg: 1280,
    xl: 1920,
  },
}

// Shadows
const shadows = [
  'none',
  '0 4px 12px rgba(0, 0, 0, 0.4)',
  '0 6px 16px rgba(0, 0, 0, 0.5)',
  '0 8px 24px rgba(0, 0, 0, 0.7)',
  '0 12px 32px rgba(0, 0, 0, 0.8)',
  '0 16px 48px rgba(0, 0, 0, 0.9)',
  ...Array(19).fill('0 8px 24px rgba(0, 0, 0, 0.7)'),
]

// Create theme
const theme = createTheme({
  palette,
  typography,
  components,
  spacing,
  breakpoints,
  shadows,
})

export default theme
