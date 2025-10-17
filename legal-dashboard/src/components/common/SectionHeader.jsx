import { Typography, Box, Divider } from '@mui/material'

export default function SectionHeader({ title, subtitle, icon: Icon, action }) {
  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          {Icon && <Icon sx={{ fontSize: 32, color: 'primary.main' }} />}
          <Box>
            <Typography
              variant="h5"
              sx={{
                fontWeight: 700,
                background: (theme) => theme.palette.gradient.primary,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {subtitle}
              </Typography>
            )}
          </Box>
        </Box>
        {action}
      </Box>
      <Divider sx={{ borderColor: 'divider' }} />
    </Box>
  )
}
