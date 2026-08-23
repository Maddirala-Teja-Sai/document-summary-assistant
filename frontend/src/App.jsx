import { MdAutoAwesome } from 'react-icons/md'
import ErrorBanner from './components/common/ErrorBanner'
import Loader from './components/common/Loader'
import Header from './components/Layout/Header'
import SummaryCard from './components/Summary/SummaryCard'
import LengthSelector from './components/Summary/LengthSelector'
import DropZone from './components/Upload/DropZone'
import FileList from './components/Upload/FileList'
import Button from './components/common/Button'
import { useTheme } from './hooks/useTheme'
import { useUpload } from './hooks/useUpload'

const FEATURES = [
  'PDF & Image support',
  'AI-Powered Summarization',
  'Doc-Type Detection',
  'Export to PDF / TXT',
]

export default function App() {
  const { isDark, toggle: toggleTheme } = useTheme()

  const {
    files, length, loading, results, error, copied,
    addFiles, removeFile, clearAll,
    setLength, submit,
    handleCopy, handleDownloadTxt, handleDownloadPdf,
  } = useUpload()

  const hasResults = results.length > 0

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100">

      {/* ── Header ── */}
      <Header isDark={isDark} toggleTheme={toggleTheme} />

      {/* ── Main content ── */}
      <main className="flex-1 w-full max-w-5xl mx-auto px-4 sm:px-8 xl:px-0 py-10 sm:py-16 space-y-8">

        {/* ── Hero ── */}
        {!hasResults && !loading && (
          <div className="text-center space-y-4 animate-fade-in">
            <h1 className="text-3xl sm:text-4xl xl:text-5xl font-extrabold tracking-tight text-slate-800 dark:text-white leading-tight">
              Summarise any document
              <span className="block text-brand-500 mt-1">instantly</span>
            </h1>
            <p className="text-base sm:text-lg text-slate-500 dark:text-slate-400 max-w-xl mx-auto leading-relaxed">
              Upload a PDF or scanned image to receive an intelligent, auto-tailored
              summary and automatic document classification in seconds.
            </p>
            {/* Feature badges */}
            <div className="flex flex-wrap justify-center gap-2 pt-1">
              {FEATURES.map((f) => (
                <span
                  key={f}
                  className="inline-flex items-center gap-1.5 rounded-full
                    bg-white dark:bg-slate-800
                    border border-slate-200 dark:border-slate-700
                    text-slate-600 dark:text-slate-300
                    px-3.5 py-1.5 text-xs sm:text-sm font-medium shadow-sm"
                >
                  <span className="h-2 w-2 rounded-full bg-brand-400 flex-shrink-0" />
                  {f}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ── Upload card ── */}
        <section
          className="w-full rounded-2xl border border-slate-200 dark:border-slate-700
            bg-white dark:bg-slate-800 shadow-md
            p-6 sm:p-10 space-y-6"
          aria-label="Document upload"
        >
          <DropZone onFilesAdded={addFiles} disabled={loading} />

          <FileList files={files} onRemove={removeFile} disabled={loading} />

          {error && (
            <ErrorBanner message={error} onDismiss={() => {}} />
          )}

          {/* Controls row — only shown after files are selected */}
          {files.length > 0 && (
            <div className="
              flex flex-col sm:flex-row sm:items-end justify-between gap-4
              pt-4 border-t border-slate-100 dark:border-slate-700
              animate-fade-in
            ">
              <LengthSelector value={length} onChange={setLength} disabled={loading} />

              <div className="flex gap-3 self-end sm:self-auto">
                <Button variant="secondary" size="lg" onClick={clearAll} disabled={loading}>
                  Clear all
                </Button>
                <Button
                  variant="primary"
                  size="lg"
                  onClick={submit}
                  loading={loading}
                  disabled={files.length === 0}
                >
                  <MdAutoAwesome className="h-5 w-5" aria-hidden="true" />
                  {files.length === 1 ? 'Summarise' : `Summarise ${files.length} files`}
                </Button>
              </div>
            </div>
          )}
        </section>

        {/* ── Loading ── */}
        {loading && <Loader />}

        {/* ── Results ── */}
        {hasResults && !loading && (
          <section aria-label="Summary results" className="space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-700 dark:text-slate-200">
                {results.length === 1 ? 'Summary result' : `${results.length} summary results`}
              </h2>
              <Button variant="ghost" size="sm" onClick={clearAll}>
                ← New upload
              </Button>
            </div>

            {results.map((result, i) =>
              result.error_code ? (
                <ErrorBanner
                  key={i}
                  message={`${result.filename}: ${result.detail}`}
                  onDismiss={null}
                />
              ) : (
                <SummaryCard
                  key={`${result.filename}-${i}`}
                  result={result}
                  isCopied={copied === result.filename}
                  onCopy={handleCopy}
                  onDownloadTxt={handleDownloadTxt}
                  onDownloadPdf={handleDownloadPdf}
                />
              )
            )}
          </section>
        )}

      </main>

      {/* ── Footer ── */}
      <footer className="mt-auto py-6 text-center text-sm text-slate-400 dark:text-slate-600 border-t border-slate-100 dark:border-slate-800">
        Document Summary Assistant &nbsp;·&nbsp; Intelligent Summarization &nbsp;·&nbsp; Fast &amp; Secure
      </footer>

    </div>
  )
}
