import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listAnalyses, deleteAnalysis } from '../services/api';
import './AnalysisListPage.css';

function AnalysisListPage() {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    loadAnalyses();
  }, []);

  const loadAnalyses = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await listAnalyses(0, 50);
      setAnalyses(data.results);
      setTotalCount(data.total);
    } catch (err) {
      setError('Failed to load analyses');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (analysisId, filename) => {
    if (!window.confirm(`Are you sure you want to delete analysis for "${filename}"?`)) {
      return;
    }

    try {
      await deleteAnalysis(analysisId);
      // Reload list
      loadAnalyses();
    } catch (err) {
      alert('Failed to delete analysis');
    }
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading analyses...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="analysis-list-page">
        <div className="card">
          <div className="header-section">
            <h2>Music Analyses</h2>
            <p className="count">Total: {totalCount}</p>
          </div>

          {analyses.length === 0 ? (
            <div className="empty-state">
              <p>No analyses yet. Upload your first music file to get started!</p>
              <Link to="/" className="btn">Upload Music</Link>
            </div>
          ) : (
            <div className="analyses-grid">
              {analyses.map((analysis) => (
                <div key={analysis.id} className="analysis-card">
                  <div className="analysis-header">
                    <h3>{analysis.title || analysis.filename}</h3>
                    {analysis.artist && <p className="artist">{analysis.artist}</p>}
                  </div>

                  <div className="analysis-info">
                    <div className="info-item">
                      <span className="label">Duration:</span>
                      <span className="value">{formatDuration(analysis.duration)}</span>
                    </div>
                    <div className="info-item">
                      <span className="label">Sample Rate:</span>
                      <span className="value">{analysis.sample_rate} Hz</span>
                    </div>
                    <div className="info-item">
                      <span className="label">Source:</span>
                      <span className="value">{analysis.source}</span>
                    </div>
                    <div className="info-item">
                      <span className="label">Analyzed:</span>
                      <span className="value">{formatDate(analysis.created_at)}</span>
                    </div>
                  </div>

                  <div className="analysis-actions">
                    <Link to={`/analysis/${analysis.id}`} className="btn">
                      View Details
                    </Link>
                    <button
                      onClick={() => handleDelete(analysis.id, analysis.filename)}
                      className="btn-delete"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AnalysisListPage;
