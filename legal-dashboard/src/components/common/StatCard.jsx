import { Card, CardContent, Typography, Box, Zoom } from '@mui/material'

export default function StatCard({ title, value, icon: Icon, gradient, delay = 0 }) {
  return (
    <Zoom in={true} timeout={500 + delay}>
      <Card
        sx={{
          background: gradient,
          border: '2px solid',
          borderColor: 'rgba(255, 255, 255, 0.2)',
          position: 'relative',
          overflow: 'hidden',
          transition: 'all 0.3s ease',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: '-100%',
            width: '100%',
            height: '100%',
            background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
            transition: 'left 0.6s',
          },
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: (theme) => theme.shadows[4],
            borderColor: 'rgba(255, 255, 255, 0.4)',
            '&::before': {
              left: '100%',
            },
          },
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Box>
              <Typography
                variant="body2"
                sx={{
                  color: 'rgba(255, 255, 255, 0.9)',
                  fontWeight: 600,
                  mb: 1,
                  textTransform: 'uppercase',
                  letterSpacing: 1,
                }}
              >
                {title}
              </Typography>
              <Typography
                variant="h3"
                sx={{
                  color: '#ffffff',
                  fontWeight: 700,
                  textShadow: '0 2px 4px rgba(0,0,0,0.3)',
                }}
              >
                {value}
              </Typography>
            </Box>
            {Icon && (
              <Icon
                sx={{
                  fontSize: 48,
                  color: 'rgba(255, 255, 255, 0.3)',
                  transition: 'all 0.3s ease',
                }}
              />
            )}
          </Box>
        </CardContent>
      </Card>
    </Zoom>
  )
}
