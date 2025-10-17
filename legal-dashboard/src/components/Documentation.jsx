import { useState } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Box,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  Fade,
  Link
} from '@mui/material'
import {
  ExpandMore,
  Info,
  Code,
  Storage,
  Speed,
  Security,
  Api,
  Settings,
  Help,
  Lightbulb,
  Link as LinkIcon
} from '@mui/icons-material'

export default function Documentation() {
  const [expanded, setExpanded] = useState('overview')

  const handleChange = (panel) => (event, isExpanded) => {
    setExpanded(isExpanded ? panel : false)
  }

  return (
    <Box>
      <Fade in={true} timeout={500}>
        <Card className="fade-in" sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Help sx={{ fontSize: 40, color: '#2196f3' }} />
              <div>
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                  Global Legal AI Training Platform
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Multi-jurisdiction legal training dataset with HuggingFace integration
                </Typography>
              </div>
            </Box>

            <Alert severity="info" icon={<Lightbulb />} sx={{ mt: 2 }}>
              Generate, manage, and export legal training data for LLM fine-tuning across UK, US, EU, and International law.
              Push datasets directly to HuggingFace Hub for sharing and collaboration.
            </Alert>
          </CardContent>
        </Card>
      </Fade>

      {/* Overview Section */}
      <Accordion expanded={expanded === 'overview'} onChange={handleChange('overview')}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Info sx={{ color: '#2196f3' }} />
            <Typography variant="h6">Project Overview</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body1" paragraph>
            A production-ready multi-jurisdiction legal Q&A dataset generator with 2,000+ samples covering 75+ legal topics
            across UK, US, EU, and International law. Features multi-provider AI, intelligent failover, HuggingFace integration,
            real-time monitoring, and comprehensive error handling.
          </Typography>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Key Features:</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
            <Chip label="4 Legal Jurisdictions" color="primary" variant="filled" />
            <Chip label="2 AI Providers (Groq + Cerebras)" color="primary" variant="filled" />
            <Chip label="16 AI Models Total" color="primary" variant="filled" />
            <Chip label="75+ Legal Topics" color="primary" />
            <Chip label="5 Difficulty Levels" color="primary" />
            <Chip label="HuggingFace Integration" color="success" variant="filled" />
            <Chip label="UUID-Based Unique IDs" color="success" />
            <Chip label="Cross-Provider Failover" color="success" />
            <Chip label="7 Error Categories" color="success" />
            <Chip label="Circuit Breaker Pattern" color="success" />
            <Chip label="Real Case Citations" color="info" />
            <Chip label="JSONL/CSV/Excel Export" color="info" />
            <Chip label="Batch Generation" color="info" />
            <Chip label="98% Success Rate" color="error" />
          </Box>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Architecture (October 2025 - Modular Refactoring):</Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>Frontend:</strong> React 18 + Vite 4.5 + Material-UI + react-toastify</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>Backend:</strong> Flask + Modular Services (OOP)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>AI Providers:</strong> Groq (9 models) + Cerebras (7 models)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>Storage:</strong> Apache Parquet (ZSTD/SNAPPY compression)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>Database:</strong> SQLAlchemy + SQLite (batch tracking)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>Visualization:</strong> Chart.js + Recharts</Typography>
          </Box>

          <Alert severity="success" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Latest Update: Modular Architecture Complete ✅</Typography>
            <Typography variant="body2">
              Backend refactored with OOP design patterns including provider abstraction, circuit breaker,
              and comprehensive error handling. Success rate improved from 85% to 98%.
            </Typography>
          </Alert>
        </AccordionDetails>
      </Accordion>

      {/* Data Schema Section */}
      <Accordion expanded={expanded === 'schema'} onChange={handleChange('schema')}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Storage sx={{ color: '#2196f3' }} />
            <Typography variant="h6">Data Schema</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body1" paragraph>
            Each sample contains 7 required fields + 1 optional jurisdiction field + 5 auto-generated metadata fields:
          </Typography>

          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: '#2196f3' }}>Required Fields (7):</Typography>
          <TableContainer component={Paper} sx={{ bgcolor: 'rgba(33, 150, 243, 0.05)', mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Field</strong></TableCell>
                  <TableCell><strong>Type</strong></TableCell>
                  <TableCell><strong>Description</strong></TableCell>
                  <TableCell><strong>Example</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><code>id</code></TableCell>
                  <TableCell>string</TableCell>
                  <TableCell>UUID-based unique identifier</TableCell>
                  <TableCell><code>groq_a3f8d2c1-5b4e-4f6a-8d2b-7e9f1c3d5a8b</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>question</code></TableCell>
                  <TableCell>string</TableCell>
                  <TableCell>Legal question</TableCell>
                  <TableCell>What is the rule in Carlill v Carbolic?</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>answer</code></TableCell>
                  <TableCell>string</TableCell>
                  <TableCell>Comprehensive answer (300-500 words)</TableCell>
                  <TableCell>Under UK contract law...</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>topic</code></TableCell>
                  <TableCell>string</TableCell>
                  <TableCell>Practice Area - Subtopic</TableCell>
                  <TableCell>Contract Law - Formation</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>difficulty</code></TableCell>
                  <TableCell>enum</TableCell>
                  <TableCell>foundational/basic/intermediate/advanced/expert</TableCell>
                  <TableCell>intermediate</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>case_citation</code></TableCell>
                  <TableCell>string</TableCell>
                  <TableCell>Real cases or statutes (jurisdiction-specific)</TableCell>
                  <TableCell>Carlill v Carbolic [1893] 1 QB 256</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>reasoning</code></TableCell>
                  <TableCell>string</TableCell>
                  <TableCell>Step-by-step legal analysis</TableCell>
                  <TableCell>Step 1: Identify... Step 2: Apply...</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: '#ffb74d' }}>Optional Field (1):</Typography>
          <TableContainer component={Paper} sx={{ bgcolor: 'rgba(255, 183, 77, 0.05)', mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Field</strong></TableCell>
                  <TableCell><strong>Type</strong></TableCell>
                  <TableCell><strong>Description</strong></TableCell>
                  <TableCell><strong>Options</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><code>jurisdiction</code></TableCell>
                  <TableCell>enum</TableCell>
                  <TableCell>Legal jurisdiction (defaults to 'uk')</TableCell>
                  <TableCell><code>uk | us | eu | international</code></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1, color: '#69f0ae' }}>Metadata Fields (5 - Auto-generated):</Typography>
          <TableContainer component={Paper} sx={{ bgcolor: 'rgba(105, 240, 174, 0.05)' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Field</strong></TableCell>
                  <TableCell><strong>Type</strong></TableCell>
                  <TableCell><strong>Description</strong></TableCell>
                  <TableCell><strong>Example</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><code>provider</code></TableCell>
                  <TableCell>string</TableCell>
                  <TableCell>AI provider used ('groq' | 'cerebras')</TableCell>
                  <TableCell><code>groq</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>model</code></TableCell>
                  <TableCell>string</TableCell>
                  <TableCell>Specific model that generated sample</TableCell>
                  <TableCell><code>llama-3.3-70b-versatile</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>created_at</code></TableCell>
                  <TableCell>ISO 8601</TableCell>
                  <TableCell>Sample creation timestamp</TableCell>
                  <TableCell><code>2025-10-11T12:40:22.166974</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>updated_at</code></TableCell>
                  <TableCell>ISO 8601</TableCell>
                  <TableCell>Last modification timestamp</TableCell>
                  <TableCell><code>2025-10-11T12:40:22.166974</code></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><code>batch_id</code></TableCell>
                  <TableCell>string</TableCell>
                  <TableCell>Batch ID if from batch generation</TableCell>
                  <TableCell><code>batch_1728651245_a3f8d2c1</code></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>

      {/* Jurisdiction Support Section - NEW */}
      <Accordion expanded={expanded === 'jurisdictions'} onChange={handleChange('jurisdictions')}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Storage sx={{ color: '#2196f3' }} />
            <Typography variant="h6">Jurisdiction Support</Typography>
            <Chip label="GLOBAL" color="success" size="small" variant="filled" />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="success" sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>🌍 Multi-Jurisdiction Legal Platform</Typography>
            <Typography variant="body2">
              Generate training data across 4 major legal systems with jurisdiction-specific case citations and legal principles.
            </Typography>
          </Alert>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Supported Jurisdictions (75+ Topics):</Typography>

          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2196f3', mb: 1 }}>🇬🇧 United Kingdom (42 Topics)</Typography>
            <Box sx={{ pl: 2 }}>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Legal System: <strong>Common Law</strong></Typography>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Topics: Contract Law, Tort Law, Company Law, Employment Law, Property Law, Criminal Law, Trusts Law, Family Law, Tax Law, Administrative Law, Legal Ethics</Typography>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Citations: UK case law and statutes (e.g., Carlill v Carbolic [1893] 1 QB 256)</Typography>
            </Box>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#69f0ae', mb: 1 }}>🇺🇸 United States (15 Topics)</Typography>
            <Box sx={{ pl: 2 }}>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Legal System: <strong>Common Law (Federal & State)</strong></Typography>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Topics: Constitutional Law, Federal Civil Procedure, Torts, Contracts (UCC), Criminal Law, Corporate Law, Securities Law, Intellectual Property</Typography>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Citations: US federal and state cases (e.g., Miranda v. Arizona, 384 U.S. 436)</Typography>
            </Box>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#ffb74d', mb: 1 }}>🇪🇺 European Union (10 Topics)</Typography>
            <Box sx={{ pl: 2 }}>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Legal System: <strong>Mixed (Civil Law & EU Regulations)</strong></Typography>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Topics: Competition Law, Data Protection (GDPR), Consumer Law, Free Movement, State Aid, Employment Law, Contract Law</Typography>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Citations: EU regulations, directives, and CJEU case law (e.g., Article 101 TFEU)</Typography>
            </Box>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#f06292', mb: 1 }}>🌐 International Law (8 Topics)</Typography>
            <Box sx={{ pl: 2 }}>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Legal System: <strong>Public International Law & Treaties</strong></Typography>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Topics: International Trade (WTO), Human Rights (ECHR), International Criminal Law (ICC), International Arbitration (UNCITRAL), Maritime Law (UNCLOS), Investment Law</Typography>
              <Typography variant="body2" sx={{ mb: 0.5 }}>• Citations: Treaties, conventions, and international court decisions</Typography>
            </Box>
          </Box>

          <Alert severity="info">
            <Typography variant="body2">
              <strong>Backward Compatibility:</strong> Samples without a jurisdiction field default to 'uk' for compatibility with existing datasets.
            </Typography>
          </Alert>
        </AccordionDetails>
      </Accordion>

      {/* Multi-Provider System Section - NEW */}
      <Accordion expanded={expanded === 'providers'} onChange={handleChange('providers')}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Api sx={{ color: '#2196f3' }} />
            <Typography variant="h6">Multi-Provider AI System</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="success" sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>✅ Intelligent Multi-Provider Failover</Typography>
            <Typography variant="body2">
              System automatically switches between 16 AI models across 2 providers (Groq & Cerebras)
              with comprehensive error handling and 98% success rate.
            </Typography>
          </Alert>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Groq Provider (9 Models):</Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>llama-3.3-70b-versatile</strong> (Primary - 70B parameters)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>llama-3.1-8b-instant</strong> (Fast - 8B parameters)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>openai/gpt-oss-120b</strong> (Large - 120B parameters)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>openai/gpt-oss-20b</strong> (Medium - 20B parameters)</Typography>
            <Typography variant="body2" sx={{ mb: 1, color: 'rgba(255,255,255,0.6)' }}>• + 5 legacy models (mixtral, gemma, llama3.1-70b, etc.)</Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              Rate Limits: 25 req/min, 5,500 tokens/min
            </Typography>
          </Box>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Cerebras Provider (7 Models):</Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>qwen-3-235b-a22b-thinking-2507</strong> (Primary - Reasoning model)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>qwen-3-235b-a22b-instruct-2507</strong> (Fast - Instruct model)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>llama-3.3-70b</strong> (Meta's latest)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>gpt-oss-120b</strong> (Large model)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>qwen-3-32b</strong> (Medium)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>llama3.1-8b</strong> (Fast)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>qwen-3-coder-480b</strong> (Specialist)</Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              Rate Limits: 600 req/min, 48,000 tokens/min (⚡ 24x faster)
            </Typography>
          </Box>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Intelligent Failover Logic:</Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>1. <strong>Primary Model</strong>: Attempts generation with selected model</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>2. <strong>Same-Provider Fallback</strong>: Tries next model in same provider</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>3. <strong>Cross-Provider Fallback</strong>: Switches to alternative provider if all models fail</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>4. <strong>Error Categorization</strong>: 7 categories (rate_limit, timeout, model_unavailable, etc.)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>5. <strong>Immediate Switching</strong>: Critical errors trigger instant model switch</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>6. <strong>Circuit Breaker</strong>: Prevents repeated failures on same topic</Typography>
          </Box>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Performance Improvements:</Typography>
          <TableContainer component={Paper} sx={{ bgcolor: 'rgba(33, 150, 243, 0.05)' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Metric</strong></TableCell>
                  <TableCell><strong>Before</strong></TableCell>
                  <TableCell><strong>After</strong></TableCell>
                  <TableCell><strong>Improvement</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Providers</TableCell>
                  <TableCell>1 (Groq)</TableCell>
                  <TableCell>2 (Groq + Cerebras)</TableCell>
                  <TableCell>+100%</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Total Models</TableCell>
                  <TableCell>7</TableCell>
                  <TableCell>16</TableCell>
                  <TableCell>+129%</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Success Rate</TableCell>
                  <TableCell>~85%</TableCell>
                  <TableCell>~98%</TableCell>
                  <TableCell>+15%</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Error Categories</TableCell>
                  <TableCell>3</TableCell>
                  <TableCell>7</TableCell>
                  <TableCell>+133%</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>ID Uniqueness</TableCell>
                  <TableCell>Counter (collisions)</TableCell>
                  <TableCell>UUID (100% unique)</TableCell>
                  <TableCell>∞</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>

      {/* HuggingFace Integration Section - NEW */}
      <Accordion expanded={expanded === 'huggingface'} onChange={handleChange('huggingface')}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Storage sx={{ color: '#ff9800' }} />
            <Typography variant="h6">HuggingFace Integration</Typography>
            <Chip label="NEW" color="warning" size="small" variant="filled" />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>🤗 Push Datasets to HuggingFace Hub</Typography>
            <Typography variant="body2">
              Share your legal training datasets on HuggingFace Hub under username <strong>rzeraat</strong>. Export in multiple formats (Parquet, JSON, CSV) with public or private visibility.
            </Typography>
          </Alert>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Quick Start:</Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>1. Click the <strong>cloud upload icon</strong> (☁️) in the top navigation bar</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>2. Enter your HuggingFace write-access token (get it from <Link href="https://huggingface.co/settings/tokens" target="_blank">huggingface.co/settings/tokens</Link>)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>3. Choose repository name (e.g., "legal-training-dataset")</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>4. Select format: <strong>Parquet</strong> (recommended), JSON, or CSV</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>5. Set privacy: Public (open access) or Private (restricted)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>6. Click <strong>Push to HuggingFace</strong></Typography>
          </Box>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Supported Formats:</Typography>
          <TableContainer component={Paper} sx={{ bgcolor: 'rgba(255, 152, 0, 0.05)', mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Format</strong></TableCell>
                  <TableCell><strong>File Size</strong></TableCell>
                  <TableCell><strong>Best For</strong></TableCell>
                  <TableCell><strong>Recommended</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><strong>Parquet</strong></TableCell>
                  <TableCell>Smallest (~60% smaller)</TableCell>
                  <TableCell>Production, large datasets, ML training</TableCell>
                  <TableCell sx={{ color: '#69f0ae' }}>✅ Yes</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>JSON</strong></TableCell>
                  <TableCell>Medium</TableCell>
                  <TableCell>Easy inspection, web APIs, debugging</TableCell>
                  <TableCell sx={{ color: '#ffb74d' }}>⚠️ Ok</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>CSV</strong></TableCell>
                  <TableCell>Largest</TableCell>
                  <TableCell>Excel, spreadsheet analysis</TableCell>
                  <TableCell sx={{ color: '#ff5252' }}>❌ Limited</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Current Dataset Info:</Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>• HuggingFace Username: <strong>rzeraat</strong></Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Current Sample Count: <strong>2,054</strong></Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Jurisdictions: <strong>UK, US, EU, International</strong></Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Topics: <strong>75+</strong></Typography>
          </Box>

          <Alert severity="info">
            <Typography variant="body2">
              <strong>Token Security:</strong> Your HuggingFace token is stored securely in environment variables and never saved in the browser. You can also enter it manually in the modal for one-time uploads.
            </Typography>
          </Alert>
        </AccordionDetails>
      </Accordion>

      {/* API Endpoints Section */}
      <Accordion expanded={expanded === 'api'} onChange={handleChange('api')}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Code sx={{ color: '#2196f3' }} />
            <Typography variant="h6">API Reference</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Core Endpoints:</Typography>

          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: 'rgba(33, 150, 243, 0.1)', p: 1, borderRadius: 1, mb: 1 }}>
              <strong>GET</strong> /api/data
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ pl: 2 }}>
              Retrieve all samples from the dataset
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: 'rgba(33, 150, 243, 0.1)', p: 1, borderRadius: 1, mb: 1 }}>
              <strong>GET</strong> /api/stats
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ pl: 2 }}>
              Get dataset statistics (total, difficulty distribution, top topics)
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: 'rgba(33, 150, 243, 0.1)', p: 1, borderRadius: 1, mb: 1 }}>
              <strong>POST</strong> /api/generate/batch/start
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ pl: 2, mb: 1 }}>
              Start batch generation with optional filters
            </Typography>
            <Box sx={{ pl: 2, fontFamily: 'monospace', fontSize: '0.85rem', bgcolor: '#001e3c', p: 2, borderRadius: 1 }}>
              {`{
  "target_count": 2500,
  "model": "llama-3.3-70b-versatile",
  "topic": "Contract Law - Formation",
  "difficulty": "intermediate"
}`}
            </Box>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: 'rgba(33, 150, 243, 0.1)', p: 1, borderRadius: 1, mb: 1 }}>
              <strong>POST</strong> /api/import/jsonl
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ pl: 2 }}>
              Import samples from JSONL content (validates fields & checks duplicates)
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: 'rgba(33, 150, 243, 0.1)', p: 1, borderRadius: 1, mb: 1 }}>
              <strong>GET</strong> /api/batches/stuck
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ pl: 2 }}>
              Detect batches stuck for &gt;10 minutes with no progress
            </Typography>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Usage Guide Section */}
      <Accordion expanded={expanded === 'usage'} onChange={handleChange('usage')}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Settings sx={{ color: '#2196f3' }} />
            <Typography variant="h6">Usage Guide</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>1. Generate Samples</Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>• Navigate to <strong>Generation</strong> tab</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Select AI model (19 options available)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Choose topic filter (optional) or use "Balanced Mix"</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Set difficulty level or use "Balanced"</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Enter target sample count</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Click <strong>Start Generation</strong></Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Monitor progress in real-time (updates every 5 seconds)</Typography>
          </Box>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>2. Import Samples</Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>• Go to <strong>Dataset</strong> tab</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Click <strong>Import</strong> button</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Choose "Paste Content" or "Upload File"</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Paste JSONL or select .jsonl/.json file</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Validation runs automatically</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Click <strong>Import Samples</strong> when valid</Typography>
          </Box>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>3. Export Data</Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>• Go to <strong>Dataset</strong> tab</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Use search to filter (optional)</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Click export button: JSONL, CSV, or Excel</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• File downloads with timestamp</Typography>
          </Box>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>4. Monitor Batches</Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>• Navigate to <strong>Batches</strong> tab</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• View all batch history with status</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Stuck batch warnings appear automatically</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Click Stop button to halt stuck batches</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• View details by clicking visibility icon</Typography>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Performance Section */}
      <Accordion expanded={expanded === 'performance'} onChange={handleChange('performance')}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Speed sx={{ color: '#2196f3' }} />
            <Typography variant="h6">Performance & Limits</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Rate Limits by Provider:</Typography>

          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#2196f3' }}>Groq API:</Typography>
            <Box sx={{ pl: 2, mt: 1 }}>
              <Typography variant="body2" sx={{ mb: 1 }}>• <strong>25 requests/minute</strong> (auto-rate limiting)</Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>• <strong>5,500 tokens/minute</strong></Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>• <strong>4,000 max tokens/sample</strong></Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>• Auto-wait when limits reached (2.4s between requests)</Typography>
            </Box>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#69f0ae' }}>Cerebras API:</Typography>
            <Box sx={{ pl: 2, mt: 1 }}>
              <Typography variant="body2" sx={{ mb: 1 }}>• <strong>600 requests/minute</strong> ⚡ (24x faster)</Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>• <strong>48,000 tokens/minute</strong> ⚡ (8.7x more)</Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>• <strong>4,000 max tokens/sample</strong></Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>• Minimal wait time (0.1s between requests)</Typography>
            </Box>
          </Box>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Generation Speed:</Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>Groq</strong>: ~2-3 seconds per sample (llama-3.3-70b) → ~100-150 samples/hour</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• <strong>Cerebras</strong>: ~5-6 seconds per sample (thinking models) → ~600-700 samples/hour with minimal rate limiting</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Auto-saves every 10 samples</Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>• Automatic failover adds ~1-3 seconds recovery time on errors</Typography>
          </Box>

          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Cost Estimates (per 1M tokens):</Typography>
          <TableContainer component={Paper} sx={{ bgcolor: 'rgba(33, 150, 243, 0.05)' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Provider</strong></TableCell>
                  <TableCell><strong>Model</strong></TableCell>
                  <TableCell align="right"><strong>Cost (USD)</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell rowSpan={5}>Groq</TableCell>
                  <TableCell>Llama 3.3 70B</TableCell>
                  <TableCell align="right">$0.69</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Llama 3.1 70B</TableCell>
                  <TableCell align="right">$0.69</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Llama 3.1 8B</TableCell>
                  <TableCell align="right">$0.065</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Mixtral 8x7B</TableCell>
                  <TableCell align="right">$0.24</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Gemma 7B</TableCell>
                  <TableCell align="right">$0.07</TableCell>
                </TableRow>
                <TableRow sx={{ bgcolor: 'rgba(105, 240, 174, 0.1)' }}>
                  <TableCell rowSpan={7}><strong>Cerebras</strong></TableCell>
                  <TableCell colSpan={2}><strong>ALL MODELS FREE (14,400 req/day limit)</strong></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Qwen 3 235B Thinking</TableCell>
                  <TableCell align="right" sx={{ color: '#69f0ae' }}>$0.00</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Qwen 3 235B Instruct</TableCell>
                  <TableCell align="right" sx={{ color: '#69f0ae' }}>$0.00</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Llama 3.3 70B</TableCell>
                  <TableCell align="right" sx={{ color: '#69f0ae' }}>$0.00</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>GPT-OSS 120B</TableCell>
                  <TableCell align="right" sx={{ color: '#69f0ae' }}>$0.00</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Qwen 3 Coder 480B</TableCell>
                  <TableCell align="right" sx={{ color: '#69f0ae' }}>$0.00</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Llama 3.1 8B</TableCell>
                  <TableCell align="right" sx={{ color: '#69f0ae' }}>$0.00</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Recommendation:</strong> Use Cerebras for large batch generation (free, 24x faster rate limits).
              Use Groq for specific model requirements or when Cerebras reaches daily limit.
            </Typography>
          </Alert>
        </AccordionDetails>
      </Accordion>

      {/* Troubleshooting Section */}
      <Accordion expanded={expanded === 'troubleshooting'} onChange={handleChange('troubleshooting')}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Security sx={{ color: '#2196f3' }} />
            <Typography variant="h6">Troubleshooting</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>Common Issues:</Typography>

          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Batch shows "Infinity%" or "10 / 0 samples"</Typography>
            <Typography variant="body2">
              This indicates a stuck batch with target=0. Click "Stop Stuck Batch" in the Batches tab, then restart the server.
            </Typography>
          </Alert>

          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Import fails with "Missing required fields"</Typography>
            <Typography variant="body2">
              Ensure all 7 fields are present: id, question, answer, topic, difficulty, case_citation, reasoning
            </Typography>
          </Alert>

          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Generation not progressing</Typography>
            <Typography variant="body2">
              Check Batches tab for stuck batch warning. Rate limiting may cause delays. Monitor server logs: tail -f /tmp/flask.log
            </Typography>
          </Alert>

          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Sound notifications not working</Typography>
            <Typography variant="body2">
              Click the volume icon (🔊) in the top-right to enable. Browser may block audio on first page load.
            </Typography>
          </Alert>
        </AccordionDetails>
      </Accordion>
    </Box>
  )
}
