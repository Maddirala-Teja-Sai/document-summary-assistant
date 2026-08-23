import { useState } from 'react'
import {
  MdCheck,
  MdContentCopy,
  MdDownload,
  MdExpandLess,
  MdExpandMore,
  MdLightbulbOutline,
  MdPictureAsPdf,
} from 'react-icons/md'
import Button from '../common/Button'

/** Map doc_type → badge colour */
function DocTypeBadge({ type }) {
  const colours = {
    resume:           'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    'cover letter':   'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300',
    'research paper': 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    contract:         'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
    invoice:          'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
    report:           'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300',
    letter:           'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300',
  }
  const colour = colours[type?.toLowerCase()] ?? 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-sm font-semibold capitalize ${colour}`}>
      {type}
    </span>
  )
}

/**
 * Card showing the summary result for a single document.
 */
export default function SummaryCard({
  result,
  isCopied,
  onCopy,
  onDownloadTxt,
  onDownloadPdf,
}) {
  const [keyOpen, setKeyOpen] = useState(false)
  const [suggestionsOpen, setSuggestionsOpen] = useState(true)
  const confidence = Math.round((result.document_type_confidence ?? 0) * 100)

  return (
    <article className="
      rounded-2xl border border-slate-200 dark:border-slate-700
      bg-white dark:bg-slate-800 shadow-md animate-slide-up
      overflow-hidden
    ">
      {/* ── Header ── */}
      <div className="flex flex-wrap items-start gap-3 justify-between px-6 py-5 border-b border-slate-100 dark:border-slate-700">
        <div className="min-w-0 space-y-1.5">
          <p className="text-sm text-slate-400 dark:text-slate-500 truncate">{result.filename}</p>
          <div className="flex items-center gap-2 flex-wrap">
            <DocTypeBadge type={result.document_type} />
            {confidence > 0 && (
              <span className="text-sm text-slate-400 dark:text-slate-500">
                {confidence}% confidence
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 text-sm text-slate-400 dark:text-slate-500 whitespace-nowrap">
          <span>{result.word_count} words</span>
          <span>·</span>
          <span>{result.processing_time_ms} ms</span>
        </div>
      </div>

      {/* ── Summary ── */}
      <div className="px-6 py-5">
        <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500 mb-4">
          Summary
        </h3>
        <ul className="space-y-3">
          {result.key_sentences && result.key_sentences.length > 0 ? (
            result.key_sentences.map((sentence, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className="mt-2 h-2 w-2 flex-shrink-0 rounded-full bg-brand-400" aria-hidden="true" />
                <p className="text-base leading-relaxed text-slate-700 dark:text-slate-200">
                  {sentence}
                </p>
              </li>
            ))
          ) : (
            <li className="flex items-start gap-3">
              <span className="mt-2 h-2 w-2 flex-shrink-0 rounded-full bg-brand-400" aria-hidden="true" />
              <p className="text-base leading-relaxed text-slate-700 dark:text-slate-200">
                {result.summary}
              </p>
            </li>
          )}
        </ul>
      </div>

      {/* ── Improvement Suggestions collapsible ── */}
      {result.suggestions && result.suggestions.length > 0 && (
        <div className="px-6 border-t border-slate-100 dark:border-slate-700 bg-amber-50/40 dark:bg-amber-950/10">
          <button
            onClick={() => setSuggestionsOpen(o => !o)}
            className="flex w-full items-center justify-between py-4 text-sm font-semibold uppercase tracking-widest text-amber-700 dark:text-amber-400 hover:text-amber-800 dark:hover:text-amber-300 transition-colors"
          >
            <span className="flex items-center gap-2">
              <MdLightbulbOutline className="h-4 w-4 text-amber-500" />
              Improvement Suggestions
            </span>
            {suggestionsOpen ? <MdExpandLess className="h-5 w-5" /> : <MdExpandMore className="h-5 w-5" />}
          </button>
          {suggestionsOpen && (
            <ul className="space-y-2 pb-5 animate-fade-in">
              {result.suggestions.map((suggestion, i) => (
                <li key={i} className="flex items-start gap-2.5 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                  <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-500" />
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* ── Key sentences collapsible ── */}
      {result.key_sentences && result.key_sentences.length > 0 && (
        <div className="px-6 border-t border-slate-100 dark:border-slate-700">
          <button
            onClick={() => setKeyOpen(o => !o)}
            className="flex w-full items-center justify-between py-4 text-sm font-semibold uppercase tracking-widest text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
          >
            <span>Raw key sentences</span>
            {keyOpen ? <MdExpandLess className="h-5 w-5" /> : <MdExpandMore className="h-5 w-5" />}
          </button>
          {keyOpen && (
            <ol className="space-y-2 pb-4 list-decimal list-inside animate-fade-in">
              {result.key_sentences.map((s, i) => (
                <li key={i} className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  {s}
                </li>
              ))}
            </ol>
          )}
        </div>
      )}

      {/* ── Actions ── */}
      <div className="flex flex-wrap gap-2 px-6 py-4 border-t border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
        <Button
          variant="ghost"
          size="md"
          onClick={() => onCopy(result)}
          className={isCopied ? 'text-emerald-500 dark:text-emerald-400' : ''}
        >
          {isCopied
            ? <><MdCheck className="h-4 w-4" /> Copied!</>
            : <><MdContentCopy className="h-4 w-4" /> Copy</>}
        </Button>

        <Button variant="ghost" size="md" onClick={() => onDownloadTxt(result)}>
          <MdDownload className="h-4 w-4" /> Download .txt
        </Button>

        <Button variant="ghost" size="md" onClick={() => onDownloadPdf(result)}>
          <MdPictureAsPdf className="h-4 w-4" /> Export PDF
        </Button>
      </div>
    </article>
  )
}
