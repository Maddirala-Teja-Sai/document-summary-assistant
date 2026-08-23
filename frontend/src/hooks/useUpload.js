import { useCallback, useState } from 'react'
import { exportPdf, uploadBatch, uploadDocument } from '../services/api'
import { copyToClipboard, downloadAsPdf, downloadAsText, formatSummaryAsText } from '../utils/download'

const MAX_FILES = 5
const ALLOWED_TYPES = new Set([
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/tiff',
  'image/bmp',
])
const MAX_SIZE_BYTES = 10 * 1024 * 1024 // 10 MB

/**
 * Custom hook that owns the entire upload → summarise flow.
 *
 * @returns {object} State and action handlers for the upload UI
 */
export function useUpload() {
  const [files, setFiles]       = useState([])   // File[]
  const [length, setLength]     = useState('medium')
  const [loading, setLoading]   = useState(false)
  const [results, setResults]   = useState([])   // SummaryResponse[]
  const [error, setError]       = useState(null) // string | null
  const [copied, setCopied]     = useState(null) // filename of copied result

  // -------------------------------------------------------------------------
  // File selection / validation
  // -------------------------------------------------------------------------

  const addFiles = useCallback((incoming) => {
    setError(null)

    const validated = []
    for (const file of incoming) {
      if (!ALLOWED_TYPES.has(file.type)) {
        setError(`"${file.name}" is not a supported file type. Upload PDF, PNG, JPEG, TIFF, or BMP.`)
        return
      }
      if (file.size > MAX_SIZE_BYTES) {
        setError(`"${file.name}" exceeds the 10 MB file size limit.`)
        return
      }
      validated.push(file)
    }

    setFiles((prev) => {
      const combined = [...prev, ...validated]
      if (combined.length > MAX_FILES) {
        setError(`You can upload a maximum of ${MAX_FILES} files at once.`)
        return prev
      }
      return combined
    })
  }, [])

  const removeFile = useCallback((index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
    setError(null)
  }, [])

  const clearAll = useCallback(() => {
    setFiles([])
    setResults([])
    setError(null)
  }, [])

  // -------------------------------------------------------------------------
  // Submit
  // -------------------------------------------------------------------------

  const submit = useCallback(async () => {
    if (files.length === 0) return

    setLoading(true)
    setError(null)
    setResults([])

    try {
      if (files.length === 1) {
        const result = await uploadDocument(files[0], length)
        setResults([result])
      } else {
        const batch = await uploadBatch(files, length)
        setResults(batch.results)
      }
    } catch (err) {
      const message =
        err?.response?.data?.detail ??
        err?.message ??
        'An unexpected error occurred. Is the backend running?'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [files, length])

  // -------------------------------------------------------------------------
  // Per-result actions
  // -------------------------------------------------------------------------

  const handleCopy = useCallback(async (result) => {
    await copyToClipboard(formatSummaryAsText(result))
    setCopied(result.filename)
    setTimeout(() => setCopied(null), 2500)
  }, [])

  const handleDownloadTxt = useCallback((result) => {
    downloadAsText(formatSummaryAsText(result), result.filename)
  }, [])

  const handleDownloadPdf = useCallback(async (result) => {
    try {
      const blob = await exportPdf(result)
      downloadAsPdf(blob, result.filename)
    } catch {
      setError('PDF export failed. Please try again.')
    }
  }, [])

  return {
    // state
    files,
    length,
    loading,
    results,
    error,
    copied,
    // actions
    addFiles,
    removeFile,
    clearAll,
    setLength,
    submit,
    handleCopy,
    handleDownloadTxt,
    handleDownloadPdf,
  }
}
