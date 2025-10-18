/**
 * @fileoverview Color constants for charts, themes, and UI elements
 */

export const CHART_COLORS = {
  primary: '#2196f3',
  primaryDark: '#1976d2',
  primaryLight: '#64b5f6',
  secondary: '#1e88e5',
  success: '#4caf50',
  warning: '#ff9800',
  error: '#f44336',
  info: '#2196f3',
} as const

export const CHART_PALETTE: readonly string[] = [
  '#2196f3', // Blue
  '#1e88e5', // Dark Blue
  '#1976d2', // Darker Blue
  '#1565c0', // Navy Blue
  '#0d47a1', // Deep Blue
  '#64b5f6', // Light Blue
] as const

export const DIFFICULTY_COLORS = {
  foundational: '#4caf50',   // Green
  basic: '#8bc34a',          // Light Green
  intermediate: '#ff9800',   // Orange
  advanced: '#ff5722',       // Deep Orange
  expert: '#f44336',         // Red
} as const

export const PROVIDER_COLORS = {
  groq: '#f55036',
  cerebras: '#7c3aed',
  ollama: '#2196f3',
} as const

export const SAMPLE_TYPE_COLORS = {
  case_analysis: '#2196f3',         // Blue
  educational: '#4caf50',           // Green
  client_interaction: '#ff9800',   // Orange
  statutory_interpretation: '#9c27b0', // Purple
} as const

export const GRADIENT_COLORS = {
  primary: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
  success: 'linear-gradient(135deg, #388e3c 0%, #4caf50 100%)',
  warning: 'linear-gradient(135deg, #f57c00 0%, #ff9800 100%)',
  error: 'linear-gradient(135deg, #c62828 0%, #f44336 100%)',
  info: 'linear-gradient(135deg, #1565c0 0%, #1e88e5 100%)',
} as const

export default {
  CHART_COLORS,
  CHART_PALETTE,
  DIFFICULTY_COLORS,
  PROVIDER_COLORS,
  SAMPLE_TYPE_COLORS,
  GRADIENT_COLORS,
}
