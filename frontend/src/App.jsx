// File: frontend/src/App.jsx
/**
 * Main application component.
 * Orchestrates the extraction, validation, and editing workflow.
 */

import React from 'react';
import { useExtractionStore } from './store/useExtractionStore';
import ImageUpload from './components/ImageUpload';
import Viewer3D from './components/Viewer3D';
import EditForm from './components/EditForm';
import './App.css';

function App() {
  const { step, extractionData, reset } = useExtractionStore();

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <h1>Extraction Validation Engine</h1>
        <p className="app-subtitle">AI-Powered Reinforced Concrete Validation</p>
        {extractionData && (
          <button className="btn-reset" onClick={reset}>
            New Extraction
          </button>
        )}
      </header>

      {/* Main Content */}
      <main className="app-main">
        {step === 'upload' ? (
          <ImageUpload />
        ) : (
          <div className="workspace">
            {/* Left Panel: 3D Viewer */}
            <div className="workspace-viewer">
              <Viewer3D />
            </div>

            {/* Right Panel: Edit Form */}
            <div className="workspace-sidebar">
              <EditForm />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>
          Powered by Gemini 3.0 Pro | ACI 318-19 | NumPy + geomdl | Three.js
        </p>
      </footer>
    </div>
  );
}

export default App;
