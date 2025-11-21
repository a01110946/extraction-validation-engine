// File: frontend/src/components/EditForm.jsx
/**
 * Edit form for modifying extracted data and saving to database.
 */

import React, { useState } from 'react';
import { useExtractionStore } from '../store/useExtractionStore';
import { generateGeometry, saveExtraction } from '../services/api';
import './EditForm.css';

export default function EditForm() {
  const {
    extractionData,
    corrections,
    updateExtractionField,
    setGeometry,
    setLoading,
    markAsValidated,
  } = useExtractionStore();

  const [saveStatus, setSaveStatus] = useState(null);
  const [validationNotes, setValidationNotes] = useState('');

  if (!extractionData) {
    return null;
  }

  const handleFieldChange = async (path, value) => {
    updateExtractionField(path, value);

    // Re-generate geometry after field update
    try {
      setLoading(true);
      const result = await generateGeometry(extractionData);
      if (result.success) {
        setGeometry(result.geometry);
      }
    } catch (error) {
      console.error('Failed to regenerate geometry:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      const result = await saveExtraction(
        extractionData,
        true,
        validationNotes || null
      );

      if (result.success) {
        setSaveStatus('Saved successfully!');
        markAsValidated();
        setTimeout(() => setSaveStatus(null), 3000);
      }
    } catch (error) {
      console.error('Save failed:', error);
      setSaveStatus('Save failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const { element_identification, geometry, concrete_specifications, longitudinal_reinforcement } = extractionData;
  const longBar = longitudinal_reinforcement[0] || {};

  return (
    <div className="edit-form">
      <div className="form-header">
        <h2>
          {element_identification.element_id} - {element_identification.type_of_element}
        </h2>
        {element_identification.level_reference && (
          <p className="form-subtitle">{element_identification.level_reference}</p>
        )}
      </div>

      {/* ACI Corrections */}
      {corrections && corrections.length > 0 && (
        <div className="corrections-panel">
          <h3>ACI 318 Auto-Corrections Applied:</h3>
          <ul>
            {corrections.map((correction, idx) => (
              <li key={idx}>{correction}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Geometry Section */}
      <div className="form-section">
        <h3>Geometry</h3>
        <div className="form-row">
          <label>
            Width (mm):
            <input
              type="number"
              value={geometry.width_mm || ''}
              onChange={(e) =>
                handleFieldChange('geometry.width_mm', parseFloat(e.target.value))
              }
            />
          </label>
          <label>
            Depth (mm):
            <input
              type="number"
              value={geometry.depth_mm || ''}
              onChange={(e) =>
                handleFieldChange('geometry.depth_mm', parseFloat(e.target.value))
              }
            />
          </label>
        </div>
      </div>

      {/* Concrete Specs */}
      <div className="form-section">
        <h3>Concrete Specifications</h3>
        <div className="form-row">
          <label>
            Strength:
            <input
              type="text"
              value={concrete_specifications?.concrete_strength || ''}
              onChange={(e) =>
                handleFieldChange(
                  'concrete_specifications.concrete_strength',
                  e.target.value
                )
              }
            />
          </label>
          <label>
            Cover (mm):
            <input
              type="number"
              value={concrete_specifications?.clear_cover_mm || ''}
              onChange={(e) =>
                handleFieldChange(
                  'concrete_specifications.clear_cover_mm',
                  parseFloat(e.target.value)
                )
              }
            />
          </label>
        </div>
      </div>

      {/* Longitudinal Reinforcement */}
      <div className="form-section">
        <h3>Longitudinal Reinforcement</h3>
        <div className="form-row">
          <label>
            Bar Count:
            <input
              type="number"
              value={longBar.bar_count || ''}
              onChange={(e) =>
                handleFieldChange(
                  'longitudinal_reinforcement.0.bar_count',
                  parseInt(e.target.value)
                )
              }
            />
          </label>
          <label>
            Diameter (mm):
            <input
              type="number"
              step="0.1"
              value={longBar.bar_diameter_mm || ''}
              onChange={(e) =>
                handleFieldChange(
                  'longitudinal_reinforcement.0.bar_diameter_mm',
                  parseFloat(e.target.value)
                )
              }
            />
          </label>
        </div>
        <div className="form-row">
          <label>
            X Columns:
            <input
              type="number"
              value={longBar.bar_x_columns || ''}
              onChange={(e) =>
                handleFieldChange(
                  'longitudinal_reinforcement.0.bar_x_columns',
                  parseInt(e.target.value)
                )
              }
            />
          </label>
          <label>
            Y Matrix (comma-separated):
            <input
              type="text"
              value={longBar.bar_y_matrix?.join(',') || ''}
              onChange={(e) =>
                handleFieldChange(
                  'longitudinal_reinforcement.0.bar_y_matrix',
                  e.target.value.split(',').map((v) => parseInt(v.trim()))
                )
              }
            />
          </label>
        </div>
      </div>

      {/* Validation Notes */}
      <div className="form-section">
        <h3>Validation Notes</h3>
        <textarea
          placeholder="Add any notes about this validation..."
          value={validationNotes}
          onChange={(e) => setValidationNotes(e.target.value)}
          rows={3}
        />
      </div>

      {/* Save Button */}
      <div className="form-actions">
        <button className="btn-primary" onClick={handleSave}>
          Save & Validate
        </button>
        {saveStatus && <span className="save-status">{saveStatus}</span>}
      </div>
    </div>
  );
}
