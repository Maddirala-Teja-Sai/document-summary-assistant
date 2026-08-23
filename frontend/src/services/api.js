/**
 * API service layer.
 *
 * In development, Vite proxies /api requests to http://localhost:8000
 * (configured in vite.config.js), so no base URL is needed.
 *
 * In production (Vercel → Render), set the VITE_API_URL env var to
 * your Render backend URL, e.g. https://doc-summary-api.onrender.com
 */

import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000, // 2 min — OCR on large images can be slow
})

/**
 * Upload a single document and return its summary.
 *
 * @param {File}   file    - The file to upload
 * @param {string} length  - 'short' | 'medium' | 'long'
 * @returns {Promise<object>} SummaryResponse
 */
export async function uploadDocument(file, length = 'medium') {
  const form = new FormData()
  form.append('file', file)
  form.append('length', length)

  const { data } = await client.post('/api/summarize', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

/**
 * Upload multiple documents and return an array of summaries.
 *
 * @param {File[]} files   - Array of files (max 5)
 * @param {string} length  - 'short' | 'medium' | 'long'
 * @returns {Promise<object>} BatchResponse
 */
export async function uploadBatch(files, length = 'medium') {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  form.append('length', length)

  const { data } = await client.post('/api/batch-summarize', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

/**
 * Request a PDF export of a summary result.
 *
 * @param {object} summaryData - SummaryResponse object
 * @returns {Promise<Blob>} PDF blob
 */
export async function exportPdf(summaryData) {
  const payload = {
    filename:       summaryData.filename,
    document_type:  summaryData.document_type,
    summary:        summaryData.summary,
    key_sentences:  summaryData.key_sentences,
    entities:       summaryData.entities,
  }

  const { data } = await client.post('/api/export-pdf', payload, {
    responseType: 'blob',
    headers: { 'Content-Type': 'application/json' },
  })
  return data
}
