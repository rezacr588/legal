import { useState, useEffect } from 'react'
import { Card, CardContent, Typography, Box, Skeleton, Fade, Grow, Zoom, Divider, Tabs, Tab, Grid } from '@mui/material'
import {
  Description as DocumentIcon,
  Category as CategoryIcon,
  TrendingUp as TrendingIcon,
  Article as ArticleIcon,
  Token as TokenIcon,
  Speed as SpeedIcon,
  School as SchoolIcon,
  Assessment as AssessmentIcon,
  Dashboard as DashboardIcon,
  ShowChart as ShowChartIcon,
  VerifiedUser as VerifiedUserIcon,
  MonetizationOn as MonetizationOnIcon
} from '@mui/icons-material'
import { Pie, Bar, Line, Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

// Register Chart.js components
ChartJS.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const COLORS = ['#2196f3', '#1e88e5', '#1976d2', '#1565c0', '#0d47a1', '#64b5f6']

// TabPanel component for content organization
function TabPanel({ children, value, index }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

export default function Overview({ stats }) {
  const [detailedStats, setDetailedStats] = useState(null)
  const [tokenStats, setTokenStats] = useState(null)
  const [activeTab, setActiveTab] = useState(0)

  useEffect(() => {
    loadDetailedStats()
    loadTokenStats()
  }, [])

  const loadDetailedStats = async () => {
    try {
      const response = await fetch('/api/stats/detailed', {
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      })
      const data = await response.json()
      if (data.success) {
        setDetailedStats(data.stats)
      }
    } catch (error) {
      console.error('Error loading detailed stats:', error)
    }
  }

  const loadTokenStats = async () => {
    try {
      const response = await fetch('/api/stats/tokens', {
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      })
      const data = await response.json()
      if (data.success) {
        setTokenStats(data.stats)
      }
    } catch (error) {
      console.error('Error loading token stats:', error)
    }
  }

  // Prepare difficulty chart data
  const difficultyData = {
    labels: stats.difficulty_distribution?.map(d => d.difficulty.charAt(0).toUpperCase() + d.difficulty.slice(1)) || [],
    datasets: [{
      data: stats.difficulty_distribution?.map(d => d.len || d.count) || [],
      backgroundColor: COLORS,
      borderColor: COLORS.map(color => color + '88'),
      borderWidth: 2,
    }]
  }

  // Prepare topics chart data
  const topicsData = {
    labels: stats.top_topics?.map(t => t.topic.length > 30 ? t.topic.substring(0, 30) + '...' : t.topic) || [],
    datasets: [{
      label: 'Samples',
      data: stats.top_topics?.map(t => t.len || t.count) || [],
      backgroundColor: '#2196f3',
      borderColor: '#64b5f6',
      borderWidth: 2,
      borderRadius: 8,
    }]
  }

  // Practice areas chart (from detailed stats)
  const practiceAreasData = {
    labels: detailedStats?.practice_areas?.slice(0, 10).map(p => p.practice_area) || [],
    datasets: [{
      label: 'Samples',
      data: detailedStats?.practice_areas?.slice(0, 10).map(p => p.len || p.count) || [],
      backgroundColor: '#1e88e5',
      borderColor: '#64b5f6',
      borderWidth: 2,
      borderRadius: 8,
    }]
  }

  // Average content lengths chart
  const avgLengthsData = {
    labels: ['Question', 'Answer', 'Reasoning', 'Citation'],
    datasets: [{
      label: 'Average Characters',
      data: [
        Math.round(detailedStats?.avg_lengths?.question || 0),
        Math.round(detailedStats?.avg_lengths?.answer || 0),
        Math.round(detailedStats?.avg_lengths?.reasoning || 0),
        Math.round(detailedStats?.avg_lengths?.case_citation || 0)
      ],
      backgroundColor: ['#0d47a1', '#1565c0', '#1976d2', '#1e88e5'],
      borderColor: '#64b5f6',
      borderWidth: 2,
      borderRadius: 8,
    }]
  }

  // Answer length by difficulty
  const answerLengthByDifficulty = {
    labels: detailedStats?.difficulty_breakdown?.map(d => d.difficulty.charAt(0).toUpperCase() + d.difficulty.slice(1)) || [],
    datasets: [{
      label: 'Avg Answer Length (chars)',
      data: detailedStats?.difficulty_breakdown?.map(d => Math.round(d.avg_answer_length)) || [],
      backgroundColor: '#2196f3',
      borderColor: '#64b5f6',
      borderWidth: 2,
      borderRadius: 8,
    }]
  }

  // Token statistics chart data
  const tokensByFieldData = tokenStats ? {
    labels: Object.keys(tokenStats.tokens_by_field).map(field => field.charAt(0).toUpperCase() + field.slice(1)),
    datasets: [{
      data: Object.values(tokenStats.tokens_by_field).map(f => f.total),
      backgroundColor: COLORS,
      borderColor: COLORS.map(color => color + '88'),
      borderWidth: 2,
    }]
  } : null

  const tokensByDifficultyData = tokenStats ? {
    labels: Object.keys(tokenStats.tokens_by_difficulty).map(d => d.charAt(0).toUpperCase() + d.slice(1)),
    datasets: [{
      label: 'Avg Tokens per Sample',
      data: Object.values(tokenStats.tokens_by_difficulty).map(d => Math.round(d.avg_tokens)),
      backgroundColor: '#2196f3',
      borderColor: '#64b5f6',
      borderWidth: 2,
      borderRadius: 8,
    }]
  } : null

  const tokensByPracticeAreaData = tokenStats ? {
    labels: tokenStats.tokens_by_practice_area?.slice(0, 8).map(p => p.practice_area) || [],
    datasets: [{
      label: 'Total Tokens',
      data: tokenStats.tokens_by_practice_area?.slice(0, 8).map(p => p.total_tokens) || [],
      backgroundColor: '#1e88e5',
      borderColor: '#64b5f6',
      borderWidth: 2,
      borderRadius: 8,
    }]
  } : null

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 1500,
      easing: 'easeInOutQuart',
    },
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#ffffff',
          padding: 15,
          font: { size: 12, family: 'Inter, sans-serif' },
          usePointStyle: true,
          pointStyle: 'circle',
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 18, 25, 0.98)',
        titleColor: '#ffffff',
        bodyColor: '#b3e5fc',
        borderColor: '#2196f3',
        borderWidth: 2,
        padding: 15,
        displayColors: true,
        titleFont: { size: 14, weight: 'bold' },
        bodyFont: { size: 13 },
        cornerRadius: 8,
      }
    }
  }

  const barChartOptions = {
    ...chartOptions,
    scales: {
      x: {
        ticks: { color: '#b3e5fc', font: { size: 10, family: 'Inter, sans-serif' } },
        grid: { color: 'rgba(33, 150, 243, 0.1)' }
      },
      y: {
        ticks: { color: '#b3e5fc', font: { family: 'Inter, sans-serif' } },
        grid: { color: 'rgba(33, 150, 243, 0.1)' }
      }
    }
  }

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue)
  }

  return (
    <Box sx={{ px: { xs: 0, sm: 1, md: 2 } }}>
      {/* Header Section */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, color: '#2196f3' }}>
          📊 Dataset Overview
        </Typography>
        <Typography variant="body1" sx={{ color: '#b3e5fc', mb: 2 }}>
          Comprehensive statistics and visualizations of your UK legal training dataset
        </Typography>
      </Box>

      {/* Tabs Navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'rgba(33, 150, 243, 0.3)', mb: 2 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{
            '& .MuiTab-root': {
              color: '#b3e5fc',
              fontWeight: 600,
              fontSize: { xs: '0.85rem', sm: '0.95rem' },
              minHeight: { xs: 56, sm: 64 },
              '&.Mui-selected': {
                color: '#2196f3',
              },
            },
            '& .MuiTabs-indicator': {
              backgroundColor: '#2196f3',
              height: 3,
            },
          }}
        >
          <Tab icon={<DashboardIcon />} label="Overview" iconPosition="start" />
          <Tab icon={<ShowChartIcon />} label="Trends" iconPosition="start" />
          <Tab icon={<VerifiedUserIcon />} label="Quality" iconPosition="start" />
          <Tab icon={<MonetizationOnIcon />} label="Tokens" iconPosition="start" />
        </Tabs>
      </Box>

      {/* Tab 0: Overview Tab */}
      <TabPanel value={activeTab} index={0}>
        {/* Stats Cards */}
        <Grid container spacing={{ xs: 2, sm: 2.5, md: 3 }} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Zoom in={true} timeout={300}>
            <Card
              className="fade-in"
              sx={{
                background: 'linear-gradient(135deg, #1976d2 0%, #2196f3 100%)',
                border: '2px solid rgba(100, 181, 246, 0.3)',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
                  transform: 'translateX(-100%)',
                  transition: 'transform 0.6s',
                },
                '&:hover::before': {
                  transform: 'translateX(100%)',
                }
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                    Total Samples
                  </Typography>
                  <DocumentIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.3)' }} />
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 700, color: 'white', mb: 0.5 }}>
                  {stats.total?.toLocaleString() || 0}
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                  Comprehensive UK legal dataset
                </Typography>
              </CardContent>
            </Card>
          </Zoom>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Zoom in={true} timeout={400}>
            <Card
              className="fade-in"
              sx={{
                background: 'linear-gradient(135deg, #1565c0 0%, #1e88e5 100%)',
                border: '2px solid rgba(100, 181, 246, 0.3)',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
                  transform: 'translateX(-100%)',
                  transition: 'transform 0.6s',
                },
                '&:hover::before': {
                  transform: 'translateX(100%)',
                }
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                    Practice Areas
                  </Typography>
                  <CategoryIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.3)' }} />
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 700, color: 'white', mb: 0.5 }}>
                  {detailedStats?.unique_practice_areas || stats.top_topics?.length || 0}
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                  Diverse legal topics covered
                </Typography>
              </CardContent>
            </Card>
          </Zoom>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Zoom in={true} timeout={500}>
            <Card
              className="fade-in"
              sx={{
                background: 'linear-gradient(135deg, #0d47a1 0%, #1976d2 100%)',
                border: '2px solid rgba(100, 181, 246, 0.3)',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
                  transform: 'translateX(-100%)',
                  transition: 'transform 0.6s',
                },
                '&:hover::before': {
                  transform: 'translateX(100%)',
                }
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                    Difficulty Levels
                  </Typography>
                  <TrendingIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.3)' }} />
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 700, color: 'white', mb: 0.5 }}>
                  {stats.difficulty_distribution?.length || 0}
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                  From foundational to expert
                </Typography>
              </CardContent>
            </Card>
          </Zoom>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Zoom in={true} timeout={600}>
            <Card
              className="fade-in"
              sx={{
                background: 'linear-gradient(135deg, #1e88e5 0%, #64b5f6 100%)',
                border: '2px solid rgba(100, 181, 246, 0.3)',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
                  transform: 'translateX(-100%)',
                  transition: 'transform 0.6s',
                },
                '&:hover::before': {
                  transform: 'translateX(100%)',
                }
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                    Avg Answer Length
                  </Typography>
                  <ArticleIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.3)' }} />
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 700, color: 'white', mb: 0.5 }}>
                  {Math.round(detailedStats?.avg_lengths?.answer || 0)}
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                  Characters per answer
                </Typography>
              </CardContent>
            </Card>
          </Zoom>
        </Grid>

        {/* Additional Real-time Stats Row */}
        <Grid item xs={12} sm={6} md={3}>
          <Zoom in={true} timeout={700}>
            <Card
              className="fade-in"
              sx={{
                background: 'linear-gradient(135deg, #388e3c 0%, #4caf50 100%)',
                border: '2px solid rgba(76, 175, 80, 0.3)',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
                  transform: 'translateX(-100%)',
                  transition: 'transform 0.6s',
                },
                '&:hover::before': {
                  transform: 'translateX(100%)',
                }
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                    Total Tokens
                  </Typography>
                  <TokenIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.3)' }} />
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 700, color: 'white', mb: 0.5 }}>
                  {tokenStats ? (tokenStats.total_tokens / 1000000).toFixed(1) + 'M' : '...'}
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                  Total token count across dataset
                </Typography>
              </CardContent>
            </Card>
          </Zoom>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Zoom in={true} timeout={800}>
            <Card
              className="fade-in"
              sx={{
                background: 'linear-gradient(135deg, #f57c00 0%, #ff9800 100%)',
                border: '2px solid rgba(255, 152, 0, 0.3)',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
                  transform: 'translateX(-100%)',
                  transition: 'transform 0.6s',
                },
                '&:hover::before': {
                  transform: 'translateX(100%)',
                }
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                    Avg Tokens/Sample
                  </Typography>
                  <SpeedIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.3)' }} />
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 700, color: 'white', mb: 0.5 }}>
                  {tokenStats ? Math.round(tokenStats.avg_tokens_per_sample).toLocaleString() : '...'}
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                  Average tokens per sample
                </Typography>
              </CardContent>
            </Card>
          </Zoom>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Zoom in={true} timeout={900}>
            <Card
              className="fade-in"
              sx={{
                background: 'linear-gradient(135deg, #7b1fa2 0%, #9c27b0 100%)',
                border: '2px solid rgba(156, 39, 176, 0.3)',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
                  transform: 'translateX(-100%)',
                  transition: 'transform 0.6s',
                },
                '&:hover::before': {
                  transform: 'translateX(100%)',
                }
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                    Unique Topics
                  </Typography>
                  <SchoolIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.3)' }} />
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 700, color: 'white', mb: 0.5 }}>
                  {detailedStats?.unique_topics || '...'}
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                  Distinct legal topics
                </Typography>
              </CardContent>
            </Card>
          </Zoom>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Zoom in={true} timeout={1000}>
            <Card
              className="fade-in"
              sx={{
                background: 'linear-gradient(135deg, #d32f2f 0%, #f44336 100%)',
                border: '2px solid rgba(244, 67, 54, 0.3)',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
                  transform: 'translateX(-100%)',
                  transition: 'transform 0.6s',
                },
                '&:hover::before': {
                  transform: 'translateX(100%)',
                }
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                    Quality Score
                  </Typography>
                  <AssessmentIcon sx={{ fontSize: 40, color: 'rgba(255,255,255,0.3)' }} />
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 700, color: 'white', mb: 0.5 }}>
                  {detailedStats ? Math.round((detailedStats.avg_lengths?.answer / 500) * 100) + '%' : '...'}
                </Typography>
                <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                  Based on answer completeness
                </Typography>
              </CardContent>
            </Card>
          </Zoom>
        </Grid>
      </Grid>

        {/* Section Divider */}
        <Box sx={{ mb: 4, mt: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 1, color: '#2196f3' }}>
            📈 Distribution Analysis
          </Typography>
          <Divider sx={{ borderColor: 'rgba(33, 150, 243, 0.2)' }} />
        </Box>

        {/* Charts - Distribution */}
        <Grid container spacing={{ xs: 2, sm: 2.5, md: 3 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Difficulty Distribution
                </Typography>
                <Box sx={{ height: 350 }}>
                  <Pie data={difficultyData} options={chartOptions} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Top 10 Topics
                </Typography>
                <Box sx={{ height: 350 }}>
                  <Bar data={topicsData} options={barChartOptions} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Tab 1: Trends Tab */}
      <TabPanel value={activeTab} index={1}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 1, color: '#2196f3' }}>
            📉 Trend Analysis
          </Typography>
          <Divider sx={{ borderColor: 'rgba(33, 150, 243, 0.2)' }} />
        </Box>

        {/* Charts - Trend Analysis */}
        <Grid container spacing={{ xs: 2, sm: 2.5, md: 3 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Topic Coverage Distribution
                </Typography>
                <Box sx={{ height: 350 }}>
                  <Doughnut
                    data={{
                      labels: stats.top_topics?.slice(0, 5).map(t => t.topic.substring(0, 20) + '...') || [],
                      datasets: [{
                        data: stats.top_topics?.slice(0, 5).map(t => t.len || t.count) || [],
                        backgroundColor: COLORS.slice(0, 5),
                        borderColor: COLORS.slice(0, 5).map(c => c + '88'),
                        borderWidth: 3,
                        hoverOffset: 15
                      }]
                    }}
                    options={{
                      ...chartOptions,
                      cutout: '65%',
                      plugins: {
                        ...chartOptions.plugins,
                        legend: {
                          position: 'right',
                          labels: {
                            color: '#ffffff',
                            padding: 12,
                            font: { size: 11, family: 'Inter, sans-serif' },
                            usePointStyle: true,
                            pointStyle: 'circle',
                          }
                        }
                      }
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Difficulty Level Comparison
                </Typography>
                <Box sx={{ height: 350 }}>
                  <Line
                    data={{
                      labels: stats.difficulty_distribution?.map(d => d.difficulty.charAt(0).toUpperCase() + d.difficulty.slice(1)) || [],
                      datasets: [{
                        label: 'Sample Count',
                        data: stats.difficulty_distribution?.map(d => d.len || d.count) || [],
                        borderColor: '#2196f3',
                        backgroundColor: 'rgba(33, 150, 243, 0.2)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        pointBackgroundColor: '#2196f3',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2
                      }]
                    }}
                    options={{
                      ...barChartOptions,
                      plugins: {
                        ...barChartOptions.plugins,
                        legend: {
                          display: false
                        }
                      }
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Tab 2: Quality Tab */}
      <TabPanel value={activeTab} index={2}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 1, color: '#2196f3' }}>
            🔍 Content Quality Insights
          </Typography>
          <Divider sx={{ borderColor: 'rgba(33, 150, 243, 0.2)' }} />
        </Box>

        {/* Charts - Quality Insights Row 1 */}
        <Grid container spacing={{ xs: 2, sm: 2.5, md: 3 }} sx={{ mb: 4 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Top 10 Practice Areas
                </Typography>
                <Box sx={{ height: 350 }}>
                  {detailedStats ? (
                    <Fade in={true} timeout={600}>
                      <div style={{ height: '100%' }}>
                        <Bar data={practiceAreasData} options={barChartOptions} />
                      </div>
                    </Fade>
                  ) : (
                    <Box sx={{ p: 2 }}>
                      <Skeleton variant="rectangular" height={40} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      <Skeleton variant="rectangular" height={60} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      <Skeleton variant="rectangular" height={80} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      <Skeleton variant="rectangular" height={50} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      <Skeleton variant="rectangular" height={70} sx={{ bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Average Content Lengths
                </Typography>
                <Box sx={{ height: 350 }}>
                  {detailedStats ? (
                    <Fade in={true} timeout={700}>
                      <div style={{ height: '100%' }}>
                        <Bar data={avgLengthsData} options={barChartOptions} />
                      </div>
                    </Fade>
                  ) : (
                    <Box sx={{ p: 2 }}>
                      <Skeleton variant="rectangular" height={80} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      <Skeleton variant="rectangular" height={100} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      <Skeleton variant="rectangular" height={60} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      <Skeleton variant="rectangular" height={40} sx={{ bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Charts - Quality Insights Row 2 */}
        <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                Answer Length by Difficulty
              </Typography>
              <Box sx={{ height: 350 }}>
                {detailedStats ? (
                  <Fade in={true} timeout={800}>
                    <div style={{ height: '100%' }}>
                      <Bar data={answerLengthByDifficulty} options={barChartOptions} />
                    </div>
                  </Fade>
                ) : (
                  <Box sx={{ p: 2 }}>
                    <Skeleton variant="rectangular" height={70} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                    <Skeleton variant="rectangular" height={90} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                    <Skeleton variant="rectangular" height={50} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                    <Skeleton variant="rectangular" height={60} sx={{ bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

          <Grid item xs={12} md={6}>
            <Card sx={{ border: '1px solid rgba(33, 150, 243, 0.3)' }}>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Dataset Insights
                </Typography>
                <Box sx={{ pl: 2 }}>
                  <Typography variant="body1" sx={{ mb: 2, color: '#b3e5fc' }}>
                    <strong>Unique Topics:</strong> {detailedStats?.unique_topics || 'Loading...'}
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 2, color: '#b3e5fc' }}>
                    <strong>Avg Question Length:</strong> {Math.round(detailedStats?.avg_lengths?.question || 0)} chars
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 2, color: '#b3e5fc' }}>
                    <strong>Avg Reasoning Length:</strong> {Math.round(detailedStats?.avg_lengths?.reasoning || 0)} chars
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 2, color: '#b3e5fc' }}>
                    <strong>Avg Citation Length:</strong> {Math.round(detailedStats?.avg_lengths?.case_citation || 0)} chars
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 2, color: '#b3e5fc' }}>
                    <strong>File Size:</strong> {Math.round(stats.file_size_kb || 0)} KB
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Tab 3: Tokens Tab */}
      <TabPanel value={activeTab} index={3}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 1, color: '#2196f3' }}>
            🪙 Token Statistics & Cost Analysis
          </Typography>
          <Divider sx={{ borderColor: 'rgba(33, 150, 243, 0.2)' }} />
        </Box>

        {/* Token Charts - Row 1 */}
        <Grid container spacing={{ xs: 2, sm: 2.5, md: 3 }} sx={{ mb: 4 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Token Distribution by Field
                </Typography>
                <Box sx={{ height: 350 }}>
                  {tokenStats && tokensByFieldData ? (
                    <Fade in={true} timeout={900}>
                      <div style={{ height: '100%' }}>
                        <Pie data={tokensByFieldData} options={chartOptions} />
                      </div>
                    </Fade>
                  ) : (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                      <Box sx={{ width: 200, height: 200 }}>
                        <Skeleton variant="circular" width={200} height={200} sx={{ bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      </Box>
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Avg Tokens by Difficulty
                </Typography>
                <Box sx={{ height: 350 }}>
                  {tokenStats && tokensByDifficultyData ? (
                    <Fade in={true} timeout={1000}>
                      <div style={{ height: '100%' }}>
                        <Bar data={tokensByDifficultyData} options={barChartOptions} />
                      </div>
                    </Fade>
                  ) : (
                    <Box sx={{ p: 2 }}>
                      <Skeleton variant="rectangular" height={50} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      <Skeleton variant="rectangular" height={80} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      <Skeleton variant="rectangular" height={100} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      <Skeleton variant="rectangular" height={60} sx={{ bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Token Charts - Row 2 */}
        <Grid container spacing={{ xs: 2, sm: 2.5, md: 3 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
                  Tokens by Practice Area (Top 8)
                </Typography>
                <Box sx={{ height: 350 }}>
                  {tokenStats && tokensByPracticeAreaData ? (
                    <Fade in={true} timeout={1100}>
                      <div style={{ height: '100%' }}>
                        <Bar data={tokensByPracticeAreaData} options={barChartOptions} />
                      </div>
                    </Fade>
                  ) : (
                    <Box sx={{ p: 2 }}>
                      <Skeleton variant="rectangular" height={90} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      <Skeleton variant="rectangular" height={70} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      <Skeleton variant="rectangular" height={60} sx={{ mb: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                      <Skeleton variant="rectangular" height={50} sx={{ bgcolor: 'rgba(33, 150, 243, 0.1)' }} />
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

        </Grid>
      </TabPanel>
    </Box>
  )
}
