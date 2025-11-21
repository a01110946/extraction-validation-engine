// File: frontend/src/services/api.js
/**
 * API client for backend communication.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Extract column data from an uploaded image.
 * @param {File} file - Image file
 * @param {boolean} autoValidate - Auto-apply ACI validation
 * @returns {Promise<Object>} Extraction result
 */
export const extractFromImage = async (file, autoValidate = true) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post(
    `/api/v1/extract?auto_validate=${autoValidate}`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
};

/**
 * Validate extraction data with ACI 318 rules.
 * @param {Object} extractionData - Extraction data to validate
 * @param {string} exposure - Exposure condition
 * @returns {Promise<Object>} Validated data with corrections
 */
export const validateExtraction = async (extractionData, exposure = 'interior_beams_columns') => {
  const response = await api.post('/api/v1/validate', extractionData, {
    params: { exposure },
  });

  return response.data;
};

/**
 * Generate 3D geometry from extraction data.
 * @param {Object} extractionData - Validated extraction data
 * @param {number} columnHeight - Column height in mm
 * @returns {Promise<Object>} 3D geometry data
 */
export const generateGeometry = async (extractionData, columnHeight = 3000) => {
  const response = await api.post('/api/v1/geometry', extractionData, {
    params: { column_height_mm: columnHeight },
  });

  return response.data;
};

/**
 * Save extraction to database.
 * @param {Object} extractionData - Complete extraction data
 * @param {boolean} validated - Human validation status
 * @param {string} validationNotes - Optional notes
 * @returns {Promise<Object>} Save result with ID
 */
export const saveExtraction = async (extractionData, validated = false, validationNotes = null) => {
  const response = await api.post('/api/v1/extractions', extractionData, {
    params: { validated, validation_notes: validationNotes },
  });

  return response.data;
};

/**
 * List saved extractions.
 * @param {number} skip - Pagination skip
 * @param {number} limit - Results limit
 * @param {boolean} validatedOnly - Only validated extractions
 * @returns {Promise<Object>} List of extractions
 */
export const listExtractions = async (skip = 0, limit = 20, validatedOnly = false) => {
  const response = await api.get('/api/v1/extractions', {
    params: { skip, limit, validated_only: validatedOnly },
  });

  return response.data;
};

/**
 * Get a single extraction by ID.
 * @param {string} extractionId - Extraction ID
 * @returns {Promise<Object>} Extraction data
 */
export const getExtraction = async (extractionId) => {
  const response = await api.get(`/api/v1/extractions/${extractionId}`);
  return response.data;
};

/**
 * Update an existing extraction.
 * @param {string} extractionId - Extraction ID
 * @param {Object} extractionData - Updated data
 * @param {boolean} validated - Validation status
 * @param {string} validationNotes - Notes
 * @returns {Promise<Object>} Update result
 */
export const updateExtraction = async (
  extractionId,
  extractionData,
  validated = null,
  validationNotes = null
) => {
  const response = await api.put(`/api/v1/extractions/${extractionId}`, extractionData, {
    params: { validated, validation_notes: validationNotes },
  });

  return response.data;
};

export default api;
