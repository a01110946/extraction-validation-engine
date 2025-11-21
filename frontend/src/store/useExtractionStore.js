// File: frontend/src/store/useExtractionStore.js
/**
 * Zustand store for extraction workflow state management.
 */

import { create } from 'zustand';

export const useExtractionStore = create((set) => ({
  // State
  uploadedImage: null,
  extractionData: null,
  geometry: null,
  corrections: [],
  loading: false,
  error: null,
  step: 'upload', // 'upload' | 'extracting' | 'validating' | 'editing' | 'complete'

  // Actions
  setUploadedImage: (image) => set({ uploadedImage: image, step: 'extracting' }),

  setExtractionData: (data, corrections = []) =>
    set({
      extractionData: data,
      corrections,
      step: 'validating',
      loading: false,
    }),

  setGeometry: (geometry) =>
    set({
      geometry,
      step: 'editing',
      loading: false,
    }),

  setLoading: (loading) => set({ loading }),

  setError: (error) =>
    set({
      error,
      loading: false,
    }),

  updateExtractionField: (path, value) =>
    set((state) => {
      const newData = { ...state.extractionData };
      const keys = path.split('.');
      let current = newData;

      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }

      current[keys[keys.length - 1]] = value;

      return { extractionData: newData };
    }),

  markAsValidated: () =>
    set((state) => ({
      extractionData: {
        ...state.extractionData,
        validated: true,
      },
      step: 'complete',
    })),

  reset: () =>
    set({
      uploadedImage: null,
      extractionData: null,
      geometry: null,
      corrections: [],
      loading: false,
      error: null,
      step: 'upload',
    }),
}));
