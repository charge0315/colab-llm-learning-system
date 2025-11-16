import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadAudioFile, analyzeFromGoogleDrive } from '../services/api';
import './UploadPage.css';

function UploadPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [googleDriveUrl, setGoogleDriveUrl] = useState('');
  const [extractLyrics, setExtractLyrics] = useState(true);
  const [uploadMethod, setUploadMethod] = useState('file'); // 'file' or 'gdrive'
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const navigate = useNavigate();

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
    setError(null);
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();

    if (!selectedFile) {
      setError('Please select a file to upload');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    setProgress(0);

    try {
      const result = await uploadAudioFile(selectedFile, extractLyrics, setProgress);

      setSuccess(`Analysis completed! Processing time: ${result.processing_time?.toFixed(2)}s`);
      setLoading(false);

      // Redirect to analysis detail page after 2 seconds
      setTimeout(() => {
        navigate(`/analysis/${result.analysis_id}`);
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
      setLoading(false);
    }
  };

  const handleGoogleDriveSubmit = async (e) => {
    e.preventDefault();

    if (!googleDriveUrl.trim()) {
      setError('Please enter a Google Drive URL');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await analyzeFromGoogleDrive(googleDriveUrl, extractLyrics);

      setSuccess(`Analysis completed! Processing time: ${result.processing_time?.toFixed(2)}s`);
      setLoading(false);

      // Redirect to analysis detail page after 2 seconds
      setTimeout(() => {
        navigate(`/analysis/${result.analysis_id}`);
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="upload-page">
        <div className="card">
          <h2>Upload Music for Analysis</h2>
          <p className="subtitle">
            Extract comprehensive audio features, metadata, lyrics, and chord progressions
          </p>

          {error && <div className="error">{error}</div>}
          {success && <div className="success">{success}</div>}

          <div className="upload-method-selector">
            <button
              className={`method-btn ${uploadMethod === 'file' ? 'active' : ''}`}
              onClick={() => setUploadMethod('file')}
            >
              Local File Upload
            </button>
            <button
              className={`method-btn ${uploadMethod === 'gdrive' ? 'active' : ''}`}
              onClick={() => setUploadMethod('gdrive')}
            >
              Google Drive
            </button>
          </div>

          {uploadMethod === 'file' ? (
            <form onSubmit={handleFileUpload} className="upload-form">
              <div className="file-input-wrapper">
                <input
                  type="file"
                  id="file-input"
                  accept="audio/*,.mp3,.wav,.flac,.m4a,.ogg,.aac,.wma"
                  onChange={handleFileChange}
                  disabled={loading}
                />
                <label htmlFor="file-input" className="file-input-label">
                  {selectedFile ? selectedFile.name : 'Choose audio file...'}
                </label>
              </div>

              <div className="checkbox-wrapper">
                <input
                  type="checkbox"
                  id="extract-lyrics"
                  checked={extractLyrics}
                  onChange={(e) => setExtractLyrics(e.target.checked)}
                  disabled={loading}
                />
                <label htmlFor="extract-lyrics">
                  Extract lyrics using Whisper AI (may take longer)
                </label>
              </div>

              {loading && (
                <div className="progress-wrapper">
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${progress}%` }}
                    ></div>
                  </div>
                  <p>Uploading: {progress}%</p>
                  {progress === 100 && <p>Analyzing... This may take a while.</p>}
                </div>
              )}

              <button type="submit" className="btn" disabled={loading || !selectedFile}>
                {loading ? 'Analyzing...' : 'Upload & Analyze'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleGoogleDriveSubmit} className="upload-form">
              <div className="input-wrapper">
                <label htmlFor="gdrive-url">Google Drive File URL or ID:</label>
                <input
                  type="text"
                  id="gdrive-url"
                  value={googleDriveUrl}
                  onChange={(e) => setGoogleDriveUrl(e.target.value)}
                  placeholder="https://drive.google.com/file/d/FILE_ID/view"
                  disabled={loading}
                />
              </div>

              <div className="checkbox-wrapper">
                <input
                  type="checkbox"
                  id="extract-lyrics-gdrive"
                  checked={extractLyrics}
                  onChange={(e) => setExtractLyrics(e.target.checked)}
                  disabled={loading}
                />
                <label htmlFor="extract-lyrics-gdrive">
                  Extract lyrics using Whisper AI (may take longer)
                </label>
              </div>

              {loading && (
                <div className="loading">
                  <div className="spinner"></div>
                  <p>Downloading and analyzing... This may take a while.</p>
                </div>
              )}

              <button type="submit" className="btn" disabled={loading || !googleDriveUrl.trim()}>
                {loading ? 'Analyzing...' : 'Analyze from Google Drive'}
              </button>
            </form>
          )}

          <div className="info-section">
            <h3>Supported Formats</h3>
            <p>MP3, WAV, FLAC, M4A, OGG, AAC, WMA</p>

            <h3>Analysis Includes</h3>
            <ul>
              <li>Spectral features (centroid, bandwidth, contrast, etc.)</li>
              <li>Rhythm features (BPM, beats, danceability)</li>
              <li>Timbral features (MFCCs, chroma)</li>
              <li>Tonal features (key, scale, tonnetz)</li>
              <li>Chord progression analysis</li>
              <li>Lyrics transcription (optional)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UploadPage;
