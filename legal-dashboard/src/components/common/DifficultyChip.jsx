import { Chip, useTheme } from '@mui/material'

export default function DifficultyChip({ difficulty, size = 'small' }) {
  const theme = useTheme()

  const difficultyConfig = theme.palette.difficulty[difficulty] || {
    gradient: theme.palette.gradient.info,
  }

  return (
    <Chip
      label={difficulty}
      size={size}
      sx={{
        textTransform: 'capitalize',
        background: difficultyConfig.gradient,
        color: 'white',
        fontWeight: 600,
        border: '1px solid rgba(255, 255, 255, 0.2)',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'scale(1.05)',
          boxShadow: (theme) => theme.shadows[2],
        },
      }}
    />
  )
}
