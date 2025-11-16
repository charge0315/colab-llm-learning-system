# 🎵 Web Music Analyzer

A comprehensive web application for analyzing music files with advanced audio feature extraction, lyrics transcription, and chord progression analysis.

## Features

### 🎼 Audio Analysis
- **Librosa Features**: Comprehensive spectral, rhythm, timbral, and tonal features
  - Spectral features (centroid, bandwidth, rolloff, contrast, flatness)
  - Rhythm features (tempo, beat tracking)
  - Timbral features (MFCCs, chroma features)
  - Tonal features (tonnetz)
  - Zero-crossing rate, RMS energy
  - Onset detection

- **Essentia Features**: Professional-grade audio descriptors
  - Low-level descriptors (loudness, dynamic complexity)
  - Rhythm descriptors (BPM, danceability, beats)
  - Tonal descriptors (key detection, tuning frequency)
  - Spectral descriptors (complexity, energy, HFC)
  - Timbre descriptors (dissonance, spectral centroid/entropy)

### 🎸 Chord Progression Analysis
- High-accuracy chord detection using **madmom**
- Chord sequence extraction with timestamps
- Key and mode estimation
- Chord transition analysis

### 🎤 Lyrics Transcription
- Powered by **OpenAI Whisper-Large** API
- Multi-language support with automatic language detection
- Time-aligned lyrics segments
- High-accuracy transcription

### 📁 File Input Options
- **Local Upload**: Upload audio files directly from your computer
- **Google Drive**: Analyze files directly from Google Drive (with proper credentials)

### 💾 Data Storage
- All analysis results stored in **MongoDB**
- Easy retrieval and management of past analyses
- Comprehensive metadata preservation

## Supported Audio Formats

MP3, WAV, FLAC, M4A, OGG, AAC, WMA

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for Python
- **Librosa**: Audio analysis library
- **Essentia**: Advanced audio analysis framework
- **madmom**: Music information retrieval library for chord detection
- **OpenAI Whisper API**: Lyrics transcription
- **MongoDB**: NoSQL database with Beanie ODM
- **Motor**: Async MongoDB driver

### Frontend
- **React 18**: Modern UI framework
- **React Router**: Client-side routing
- **Axios**: HTTP client
- **Recharts**: Data visualization (optional)

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **MongoDB 7.0**: Database

## Installation & Setup

### Prerequisites
- Docker and Docker Compose
- OpenAI API key (for Whisper transcription)
- (Optional) Google Cloud credentials for Google Drive access

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/charge0315/web-music-analyzer.git
   cd web-music-analyzer
   ```

2. **Configure environment variables**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Start all services**
   ```bash
   cd ..
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup (Development)

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start MongoDB (if not using Docker)
# mongod --dbpath /path/to/data

# Run the server
uvicorn app.main:app --reload
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# MongoDB
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DATABASE=music_analyzer

# OpenAI API (required for lyrics)
OPENAI_API_KEY=your_openai_api_key_here

# Google Drive API (optional)
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json

# File Upload
MAX_UPLOAD_SIZE=104857600  # 100MB
UPLOAD_DIR=/tmp/music_uploads

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### Google Drive Setup (Optional)

1. Create a Google Cloud project
2. Enable Google Drive API
3. Create a service account
4. Download credentials JSON
5. Set `GOOGLE_CREDENTIALS_PATH` in `.env`

## API Endpoints

### Analysis Endpoints

- `POST /api/analysis/upload` - Upload and analyze audio file
- `POST /api/analysis/google-drive` - Analyze from Google Drive
- `GET /api/analysis/results/{id}` - Get analysis results
- `GET /api/analysis/list` - List all analyses
- `DELETE /api/analysis/delete/{id}` - Delete analysis

### Health Endpoints

- `GET /health` - Health check
- `GET /health/ready` - Readiness check

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

## Usage

### 1. Upload Audio File

Navigate to the home page and:
1. Select "Local File Upload" or "Google Drive"
2. Choose your audio file or enter Google Drive URL
3. Optionally enable/disable lyrics extraction
4. Click "Upload & Analyze"

### 2. View Analysis Results

After analysis completes:
- View comprehensive metadata and file information
- Explore detected chord progressions
- Read transcribed lyrics
- Examine detailed audio features

### 3. Manage Analyses

- Browse all past analyses
- Filter and sort results
- Delete unwanted analyses

## Project Structure

```
web-music-analyzer/
├── backend/
│   ├── app/
│   │   ├── models/          # MongoDB models
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic
│   │   │   ├── audio_analyzer.py
│   │   │   ├── librosa_features.py
│   │   │   ├── essentia_features.py
│   │   │   ├── chord_analyzer.py
│   │   │   ├── whisper_transcription.py
│   │   │   └── google_drive.py
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database setup
│   │   └── main.py          # FastAPI app
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── services/        # API client
│   │   ├── components/      # React components
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Performance Considerations

- **Processing Time**: Analysis typically takes 30-120 seconds per song depending on:
  - File duration
  - Whether lyrics extraction is enabled
  - Server resources

- **File Size Limit**: Default 100MB (configurable via `MAX_UPLOAD_SIZE`)

- **Concurrent Requests**: FastAPI handles async requests efficiently

## Troubleshooting

### MongoDB Connection Issues
- Ensure MongoDB is running
- Check `MONGODB_URL` in `.env`
- Verify network connectivity in Docker

### Whisper API Errors
- Verify OpenAI API key is valid
- Check API usage limits
- Ensure audio file is compatible

### Google Drive Access Issues
- Verify service account credentials
- Check file sharing permissions
- Ensure Drive API is enabled

## Development

### Running Tests
```bash
cd backend
pytest
```

### Code Style
```bash
# Backend
black app/
flake8 app/

# Frontend
npm run lint
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Credits

- **Librosa**: Brian McFee et al.
- **Essentia**: Music Technology Group, Universitat Pompeu Fabra
- **madmom**: Sebastian Böck et al.
- **OpenAI Whisper**: OpenAI

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review API documentation at `/docs`

---

Built with ❤️ for music analysis
