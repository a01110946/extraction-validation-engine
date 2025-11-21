// File: frontend/src/components/ImageUpload.jsx
/**
 * Image upload component with drag-and-drop support.
 */

import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { extractFromImage, generateGeometry } from '../services/api';
import { useExtractionStore } from '../store/useExtractionStore';
import './ImageUpload.css';

export default function ImageUpload() {
  const {
    setUploadedImage,
    setExtractionData,
    setGeometry,
    setLoading,
    setError,
  } = useExtractionStore();

  const onDrop = useCallback(
    async (acceptedFiles) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      setUploadedImage(URL.createObjectURL(file));
      setLoading(true);

      try {
        // Step 1: Extract from image
        const extractionResult = await extractFromImage(file, true);

        if (!extractionResult.success) {
          throw new Error('Extraction failed');
        }

        setExtractionData(
          extractionResult.data,
          extractionResult.corrections_applied || []
        );

        // Step 2: Generate geometry
        const geometryResult = await generateGeometry(extractionResult.data);

        if (!geometryResult.success) {
          throw new Error('Geometry generation failed');
        }

        setGeometry(geometryResult.geometry);
      } catch (error) {
        console.error('Upload error:', error);
        setError(error.message || 'An error occurred during extraction');
      }
    },
    [setUploadedImage, setExtractionData, setGeometry, setLoading, setError]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg'],
    },
    multiple: false,
  });

  return (
    <div className="upload-container">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'dropzone-active' : ''}`}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <p>Drop the image here...</p>
        ) : (
          <div className="dropzone-content">
            <div className="upload-icon">📄</div>
            <h2>Upload Column Drawing</h2>
            <p>Drag and drop an image here, or click to select</p>
            <p className="upload-hint">Supports PNG, JPG, JPEG</p>
          </div>
        )}
      </div>
    </div>
  );
}
