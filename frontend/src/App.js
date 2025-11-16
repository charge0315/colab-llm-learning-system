import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import UploadPage from './pages/UploadPage';
import AnalysisListPage from './pages/AnalysisListPage';
import AnalysisDetailPage from './pages/AnalysisDetailPage';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="app-header">
          <div className="container">
            <h1>🎵 Web Music Analyzer</h1>
            <nav>
              <Link to="/">Upload</Link>
              <Link to="/analyses">Analyses</Link>
            </nav>
          </div>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/analyses" element={<AnalysisListPage />} />
            <Route path="/analysis/:id" element={<AnalysisDetailPage />} />
          </Routes>
        </main>

        <footer className="app-footer">
          <p>Web Music Analyzer - Comprehensive audio analysis platform</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
