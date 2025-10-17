# UK Legal Dataset Dashboard

A comprehensive React dashboard for managing and generating UK legal training datasets with AI-powered sample generation.

## Features

### Dashboard Overview
- Real-time statistics with auto-refresh (10-second intervals)
- Visual analytics with interactive charts (Recharts)
- Practice area and difficulty distribution
- Token usage statistics and cost estimation
- Material UI glassmorphism design

### Sample Management (CRUD Operations)
- **Create**: Generate samples using Groq AI models
- **Read**: Browse all samples with full-text search
- **Update**: Click on any sample to view details and edit inline
- **Delete**: Remove samples with confirmation dialog
- View detailed sample information in modal dialogs
- Color-coded fields (question, answer, reasoning, citation)

### AI-Powered Generation
- 19 Groq AI models available (default: llama-3.3-70b-versatile)
- Automatic model fallback on rate limits or failures
- Batch generation with real-time progress tracking
- Server-Sent Events (SSE) for live updates
- Model switching with detailed history tracking
- Custom reasoning instructions support

### Data Import/Export
- Import samples from JSONL files
- Export to JSONL, CSV, and Excel formats
- Duplicate detection and validation
- Batch history tracking in SQLite database

### Real-Time Features
- Dashboard stats auto-refresh every 10 seconds
- Batch generation progress with pulsing indicator
- Notification system with sound effects
- Notification history with timestamps
- Toast notifications for all operations

## Tech Stack

- **Frontend**: React 18 + Vite 4.5.0
- **UI Framework**: Material UI v5 with custom theme
- **Charts**: Recharts for data visualization
- **Backend**: Flask + Flask-CORS
- **Database**: SQLite (batch history) + Apache Parquet (dataset)
- **Data Processing**: Polars (high-performance DataFrames)
- **AI**: Groq API with multi-model support
- **Notifications**: React Toastify with custom sounds

## Installation

```bash
# Install dependencies
npm install

# Install Python dependencies
pip3 install flask flask-cors flask-sqlalchemy polars groq tiktoken

# Start the backend (from legal-dashboard directory)
python3 api_server.py

# Start the frontend (in another terminal)
npm run dev
```

## Usage

### Starting the Application

```bash
# Backend (runs on port 5001)
python3 api_server.py

# Frontend (runs on port 5173)
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173) in your browser.

### Viewing and Editing Samples

1. Navigate to the **Dataset** tab
2. Click on any row to view sample details
3. Click **Edit** to modify the sample
4. Edit any field (ID is read-only)
5. Click **Save** to update or **Cancel** to discard changes
6. Click **Delete** to remove the sample (with confirmation)

### Generating New Samples

1. Navigate to the **Generation** tab
2. Select a model (default: llama-3.3-70b-versatile)
3. Optionally filter by topic or difficulty
4. Set target sample count
5. Click **Start Generation**
6. Monitor progress in the sidebar or generation tab
7. Generation auto-saves every 10 samples

### Importing Samples

1. Navigate to the **Dataset** tab
2. Click **Import** button
3. Paste JSONL content or upload a file
4. System validates all required fields
5. Duplicate IDs are automatically detected
6. Click **Import Samples** to add to dataset

### Exporting Data

1. Navigate to the **Dataset** tab
2. Use the export buttons to download:
   - **JSONL**: For AI training and backups
   - **CSV**: For spreadsheet analysis
   - **Excel**: For business reports
3. Exported data includes current filters (if searching)

## API Endpoints

### Dataset Operations
- `GET /api/data` - Get all samples
- `GET /api/stats` - Get dataset statistics
- `GET /api/stats/detailed` - Comprehensive statistics
- `GET /api/stats/tokens` - Token usage and costs
- `GET /api/search?q=query` - Full-text search
- `GET /api/samples/random?count=5` - Get random samples

### CRUD Operations
- `POST /api/add` - Add new sample
- `PUT /api/sample/<id>` - Update existing sample
- `DELETE /api/sample/<id>` - Delete sample
- `POST /api/import/jsonl` - Import multiple samples

### Generation
- `POST /api/generate` - Generate single sample
- `POST /api/generate/batch/start` - Start batch generation
- `POST /api/generate/batch/stop` - Stop batch generation
- `GET /api/generate/batch/status` - Get current status
- `GET /api/generate/batch/history` - Get all batch history
- `GET /api/generate/batch/stream` - SSE stream for real-time updates

### Configuration
- `GET /api/models` - List available AI models
- `GET /api/topics` - List generation topics
- `GET /api/health` - Health check

## Sample Data Format

Each sample requires 7 fields:

```json
{
  "id": "contract_law_formation_001",
  "question": "What are the essential elements of a valid contract under UK law?",
  "answer": "Under UK law, a valid contract requires...",
  "topic": "Contract Law - Formation",
  "difficulty": "intermediate",
  "case_citation": "Carlill v Carbolic Smoke Ball [1893] 1 QB 256",
  "reasoning": "Step 1: Identify offer and acceptance. Step 2: Verify consideration..."
}
```

### Difficulty Levels
- `foundational` - Basic legal concepts
- `basic` - Fundamental principles
- `intermediate` - Standard legal analysis
- `advanced` - Complex legal scenarios
- `expert` - Specialized legal expertise

## Material UI Theme

The app uses a custom dark theme with:
- **Primary**: Blue gradient (#1976d2 → #2196f3)
- **Success**: Green gradient (#388e3c → #4caf50)
- **Warning**: Orange gradient (#f57c00 → #ff9800)
- **Error**: Red gradient (#d32f2f → #f44336)
- **Background**: Deep dark blue (#000a12)
- **Glassmorphism**: Frosted glass effects with backdrop blur

### Reusable Components
- `StatCard` - Statistics display with animations
- `SectionHeader` - Consistent section headers with gradient text
- `DifficultyChip` - Color-coded difficulty badges

## Real-Time Updates

The dashboard automatically refreshes data every 10 seconds:
- Total sample count
- Practice area distribution
- Difficulty breakdown
- Recent batch generation status

This ensures you always see the latest data without manual refresh.

## Model Fallback System

The system includes intelligent model fallback:
1. **Rate Limit Detection**: Auto-switches to next model on quota errors
2. **Model Unavailability**: Tries alternative models if one is deprecated
3. **Consecutive Failures**: Switches after 5 consecutive failures
4. **Maximum Switches**: Stops after 5 model switches per batch
5. **Fallback Order**: llama-3.3-70b → llama-3.1-70b → llama-3.1-8b → mixtral-8x7b → more

All model switches are logged with timestamps and reasons.

## Batch Generation Features

- Background processing with threading
- Auto-save every 10 samples
- Real-time progress tracking
- Rate limiting (25 req/min, 5500 tokens/min)
- Persistent batch history in SQLite
- Server-Sent Events for live updates
- Error tracking and retry logic
- Stuck batch detection

## Development

### Project Structure
```
legal-dashboard/
├── src/
│   ├── components/
│   │   ├── Overview.jsx          # Dashboard overview
│   │   ├── Generation.jsx        # AI generation interface
│   │   ├── Batches.jsx          # Batch history
│   │   ├── Dataset.jsx          # Sample browser with CRUD
│   │   ├── Documentation.jsx    # Help documentation
│   │   └── common/              # Reusable components
│   │       ├── StatCard.jsx
│   │       ├── SectionHeader.jsx
│   │       └── DifficultyChip.jsx
│   ├── theme/
│   │   └── theme.js             # Material UI theme
│   ├── App.jsx                  # Main app component
│   └── main.jsx                 # Entry point
├── api_server.py                # Flask backend
├── train.parquet                # Dataset (SNAPPY compression)
├── batches.db                   # Batch history database
└── package.json
```

### Key Technologies
- **Vite**: Fast build tool with HMR
- **React Hooks**: useState, useEffect for state management
- **Material UI**: Component library with theming
- **Polars**: High-performance DataFrame operations
- **Flask-CORS**: Cross-origin resource sharing
- **SQLAlchemy**: ORM for batch persistence

## Troubleshooting

### Port Conflicts
```bash
# Kill processes on ports
lsof -ti:5001 | xargs kill -9  # Flask
lsof -ti:5173 | xargs kill -9  # Vite
```

### Backend Not Responding
```bash
# Restart Flask server
cd legal-dashboard
python3 api_server.py
```

### Dataset Not Loading
- Ensure `train.parquet` exists in `legal-dashboard/` directory
- Check file permissions
- Verify Polars is installed: `pip3 install polars`

### Real-Time Updates Not Working
- Check browser console for errors
- Verify Flask backend is running
- Check CORS is enabled in `api_server.py`

## Future Enhancements

- [ ] Advanced filtering (multiple topics, date ranges)
- [ ] Sample quality scoring
- [ ] Automated testing for generated samples
- [ ] Export to additional formats (PDF, Word)
- [ ] User authentication and permissions
- [ ] Cloud deployment (AWS/GCP/Azure)
- [ ] Collaborative editing
- [ ] Version control for samples

## License

MIT License - feel free to use this dashboard for your legal AI training projects!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions, please open an issue on the GitHub repository.
