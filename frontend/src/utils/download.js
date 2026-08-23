/**
 * Download and clipboard utilities.
 */

/**
 * Copy text to the clipboard.
 * Falls back to a textarea-select-execCommand approach for older browsers.
 *
 * @param {string} text
 * @returns {Promise<void>}
 */
export async function copyToClipboard(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
  } else {
    const el = document.createElement('textarea')
    el.value = text
    el.style.position = 'fixed'
    el.style.opacity = '0'
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
  }
}

/**
 * Download a string as a .txt file.
 *
 * @param {string} text     - Content of the file
 * @param {string} filename - Desired filename (without extension)
 */
export function downloadAsText(text, filename) {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  _triggerDownload(blob, `${stripExtension(filename)}_summary.txt`)
}

/**
 * Download a Blob as a PDF file.
 *
 * @param {Blob}   blob     - PDF blob from the export-pdf endpoint
 * @param {string} filename - Original document filename
 */
export function downloadAsPdf(blob, filename) {
  _triggerDownload(blob, `${stripExtension(filename)}_summary.pdf`)
}

/**
 * Build a plain-text representation of a SummaryResponse for .txt export.
 *
 * @param {object} result - SummaryResponse
 * @returns {string}
 */
export function formatSummaryAsText(result) {
  const sentences = result.key_sentences && result.key_sentences.length > 0
    ? result.key_sentences.map((s) => `• ${s}`)
    : [result.summary]

  const lines = [
    `Document Summary Assistant`,
    `${'='.repeat(40)}`,
    `File:            ${result.filename}`,
    `Document type:   ${result.document_type}`,
    `Word count:      ${result.word_count}`,
    `Processing time: ${result.processing_time_ms} ms`,
    ``,
    `SUMMARY`,
    `${'-'.repeat(40)}`,
    ...sentences,
  ]

  if (result.suggestions && result.suggestions.length > 0) {
    lines.push(
      ``,
      `IMPROVEMENT SUGGESTIONS`,
      `${'-'.repeat(40)}`,
      ...result.suggestions.map((s) => `• ${s}`)
    )
  }

  return lines.join('\n')
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function _triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function stripExtension(filename = 'document') {
  return filename.replace(/\.[^/.]+$/, '')
}
