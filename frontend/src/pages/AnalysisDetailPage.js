import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getAnalysisResults } from '../services/api';
import './AnalysisDetailPage.css';

function AnalysisDetailPage() {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadAnalysis();
  }, [id]);

  const loadAnalysis = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getAnalysisResults(id);
      setAnalysis(data);
    } catch (err) {
      setError('Failed to load analysis details');
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const renderOverview = () => (
    <div className="overview-section">
      <div className="info-grid">
        <div className="info-card">
          <h4>File Information</h4>
          <div className="info-rows">
            <div className="info-row">
              <span>Filename:</span>
              <span>{analysis.filename}</span>
            </div>
            <div className="info-row">
              <span>Duration:</span>
              <span>{formatDuration(analysis.duration)}</span>
            </div>
            <div className="info-row">
              <span>Sample Rate:</span>
              <span>{analysis.sample_rate} Hz</span>
            </div>
            <div className="info-row">
              <span>File Size:</span>
              <span>{(analysis.file_size / 1024 / 1024).toFixed(2)} MB</span>
            </div>
            <div className="info-row">
              <span>Source:</span>
              <span>{analysis.source}</span>
            </div>
          </div>
        </div>

        {(analysis.title || analysis.artist || analysis.album) && (
          <div className="info-card">
            <h4>Metadata</h4>
            <div className="info-rows">
              {analysis.title && (
                <div className="info-row">
                  <span>Title:</span>
                  <span>{analysis.title}</span>
                </div>
              )}
              {analysis.artist && (
                <div className="info-row">
                  <span>Artist:</span>
                  <span>{analysis.artist}</span>
                </div>
              )}
              {analysis.album && (
                <div className="info-row">
                  <span>Album:</span>
                  <span>{analysis.album}</span>
                </div>
              )}
              {analysis.genre && (
                <div className="info-row">
                  <span>Genre:</span>
                  <span>{analysis.genre}</span>
                </div>
              )}
              {analysis.year && (
                <div className="info-row">
                  <span>Year:</span>
                  <span>{analysis.year}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {analysis.features?.essentia && (
          <div className="info-card">
            <h4>Musical Characteristics</h4>
            <div className="info-rows">
              {analysis.features.essentia.bpm && (
                <div className="info-row">
                  <span>BPM:</span>
                  <span>{analysis.features.essentia.bpm.toFixed(1)}</span>
                </div>
              )}
              {analysis.features.essentia.key_key && (
                <div className="info-row">
                  <span>Key:</span>
                  <span>{analysis.features.essentia.key_key} {analysis.features.essentia.key_scale}</span>
                </div>
              )}
              {analysis.features.essentia.danceability && (
                <div className="info-row">
                  <span>Danceability:</span>
                  <span>{(analysis.features.essentia.danceability * 100).toFixed(1)}%</span>
                </div>
              )}
              {analysis.features.essentia.loudness && (
                <div className="info-row">
                  <span>Loudness:</span>
                  <span>{analysis.features.essentia.loudness.toFixed(2)}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderChordProgression = () => {
    const chords = analysis.features?.chord_progression;
    if (!chords || !chords.chords || chords.chords.length === 0) {
      return <p>No chord progression data available.</p>;
    }

    return (
      <div className="chords-section">
        <div className="info-card">
          <h4>Chord Analysis</h4>
          <div className="info-rows">
            {chords.key && (
              <div className="info-row">
                <span>Estimated Key:</span>
                <span>{chords.key} {chords.mode}</span>
              </div>
            )}
            <div className="info-row">
              <span>Unique Chords:</span>
              <span>{chords.unique_chords?.length || 0}</span>
            </div>
            <div className="info-row">
              <span>Most Common:</span>
              <span>{chords.most_common_chord || 'N/A'}</span>
            </div>
            <div className="info-row">
              <span>Analyzer:</span>
              <span>{chords.analyzer_used}</span>
            </div>
          </div>
        </div>

        <div className="chord-sequence">
          <h4>Chord Sequence</h4>
          <div className="chord-list">
            {chords.chords.slice(0, 50).map((chord, idx) => (
              <div key={idx} className="chord-item">
                <span className="chord-time">{chord.time?.toFixed(2)}s</span>
                <span className="chord-name">{chord.chord}</span>
              </div>
            ))}
            {chords.chords.length > 50 && (
              <p className="more-info">... and {chords.chords.length - 50} more</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderLyrics = () => {
    const lyrics = analysis.features?.lyrics;
    if (!lyrics || !lyrics.text) {
      return <p>No lyrics data available. Lyrics extraction may have been disabled or failed.</p>;
    }

    return (
      <div className="lyrics-section">
        <div className="info-card">
          <h4>Transcription Info</h4>
          <div className="info-rows">
            {lyrics.language && (
              <div className="info-row">
                <span>Language:</span>
                <span>{lyrics.language}</span>
              </div>
            )}
            <div className="info-row">
              <span>Model:</span>
              <span>{lyrics.model_used}</span>
            </div>
            {lyrics.processing_time && (
              <div className="info-row">
                <span>Processing Time:</span>
                <span>{lyrics.processing_time.toFixed(2)}s</span>
              </div>
            )}
          </div>
        </div>

        <div className="lyrics-text">
          <h4>Lyrics</h4>
          <pre>{lyrics.text}</pre>
        </div>

        {lyrics.segments && lyrics.segments.length > 0 && (
          <div className="lyrics-segments">
            <h4>Time-aligned Segments</h4>
            <div className="segments-list">
              {lyrics.segments.slice(0, 20).map((segment, idx) => (
                <div key={idx} className="segment-item">
                  <span className="segment-time">
                    {segment.start?.toFixed(2)}s - {segment.end?.toFixed(2)}s
                  </span>
                  <span className="segment-text">{segment.text}</span>
                </div>
              ))}
              {lyrics.segments.length > 20 && (
                <p className="more-info">... and {lyrics.segments.length - 20} more segments</p>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderFeatures = () => {
    const librosa = analysis.features?.librosa;
    const essentia = analysis.features?.essentia;

    return (
      <div className="features-section">
        {librosa && (
          <div className="info-card">
            <h4>Librosa Features</h4>
            <div className="info-rows">
              {librosa.tempo && (
                <div className="info-row">
                  <span>Tempo:</span>
                  <span>{librosa.tempo.toFixed(2)} BPM</span>
                </div>
              )}
              {librosa.beat_times && (
                <div className="info-row">
                  <span>Beats Detected:</span>
                  <span>{librosa.beat_times.length}</span>
                </div>
              )}
              {librosa.spectral_centroid && (
                <div className="info-row">
                  <span>Avg Spectral Centroid:</span>
                  <span>{(librosa.spectral_centroid.reduce((a, b) => a + b, 0) / librosa.spectral_centroid.length).toFixed(2)} Hz</span>
                </div>
              )}
              {librosa.mfcc && (
                <div className="info-row">
                  <span>MFCCs:</span>
                  <span>{librosa.mfcc.length} coefficients</span>
                </div>
              )}
            </div>
          </div>
        )}

        {essentia && (
          <div className="info-card">
            <h4>Essentia Features</h4>
            <div className="info-rows">
              {essentia.bpm && (
                <div className="info-row">
                  <span>BPM:</span>
                  <span>{essentia.bpm.toFixed(2)}</span>
                </div>
              )}
              {essentia.key_key && (
                <div className="info-row">
                  <span>Key:</span>
                  <span>{essentia.key_key} {essentia.key_scale} (strength: {essentia.key_strength?.toFixed(2)})</span>
                </div>
              )}
              {essentia.danceability !== undefined && (
                <div className="info-row">
                  <span>Danceability:</span>
                  <span>{(essentia.danceability * 100).toFixed(1)}%</span>
                </div>
              )}
              {essentia.loudness !== undefined && (
                <div className="info-row">
                  <span>Loudness:</span>
                  <span>{essentia.loudness.toFixed(2)}</span>
                </div>
              )}
              {essentia.dissonance !== undefined && (
                <div className="info-row">
                  <span>Dissonance:</span>
                  <span>{essentia.dissonance.toFixed(4)}</span>
                </div>
              )}
              {essentia.spectral_complexity !== undefined && (
                <div className="info-row">
                  <span>Spectral Complexity:</span>
                  <span>{essentia.spectral_complexity.toFixed(4)}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading analysis...</p>
        </div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="container">
        <div className="error">{error || 'Analysis not found'}</div>
        <Link to="/analyses" className="btn">Back to List</Link>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="analysis-detail-page">
        <div className="page-header">
          <div>
            <h2>{analysis.title || analysis.filename}</h2>
            {analysis.artist && <p className="artist">{analysis.artist}</p>}
          </div>
          <Link to="/analyses" className="btn">Back to List</Link>
        </div>

        <div className="tabs">
          <button
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab ${activeTab === 'chords' ? 'active' : ''}`}
            onClick={() => setActiveTab('chords')}
          >
            Chord Progression
          </button>
          <button
            className={`tab ${activeTab === 'lyrics' ? 'active' : ''}`}
            onClick={() => setActiveTab('lyrics')}
          >
            Lyrics
          </button>
          <button
            className={`tab ${activeTab === 'features' ? 'active' : ''}`}
            onClick={() => setActiveTab('features')}
          >
            Features
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'chords' && renderChordProgression()}
          {activeTab === 'lyrics' && renderLyrics()}
          {activeTab === 'features' && renderFeatures()}
        </div>
      </div>
    </div>
  );
}

export default AnalysisDetailPage;
