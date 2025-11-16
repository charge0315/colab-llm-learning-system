import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Upload audio file for analysis
export const uploadAudioFile = async (file, extractLyrics = true, onProgress = null) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('extract_lyrics', extractLyrics);

  const config = {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  };

  if (onProgress) {
    config.onUploadProgress = (progressEvent) => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      onProgress(percentCompleted);
    };
  }

  const response = await api.post('/api/analysis/upload', formData, config);
  return response.data;
};

// Analyze audio from Google Drive
export const analyzeFromGoogleDrive = async (fileUrl, extractLyrics = true) => {
  const formData = new FormData();
  formData.append('file_url', fileUrl);
  formData.append('extract_lyrics', extractLyrics);

  const response = await api.post('/api/analysis/google-drive', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Get analysis results
export const getAnalysisResults = async (analysisId) => {
  const response = await api.get(`/api/analysis/results/${analysisId}`);
  return response.data;
};

// List all analyses
export const listAnalyses = async (skip = 0, limit = 20, sortBy = 'created_at') => {
  const response = await api.get('/api/analysis/list', {
    params: { skip, limit, sort_by: sortBy },
  });
  return response.data;
};

// Delete analysis
export const deleteAnalysis = async (analysisId) => {
  const response = await api.delete(`/api/analysis/delete/${analysisId}`);
  return response.data;
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
