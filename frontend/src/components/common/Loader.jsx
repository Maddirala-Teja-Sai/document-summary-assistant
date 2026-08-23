/**
 * Full-page loading overlay with a spinner and status message.
 */
export default function Loader({ message = 'Processing your document…' }) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-5 py-16"
      role="status"
      aria-live="polite"
    >
      {/* Spinner */}
      <div className="relative h-14 w-14">
        <div className="absolute inset-0 rounded-full border-4 border-slate-200 dark:border-slate-700" />
        <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-brand-500 animate-spin" />
      </div>

      {/* Message */}
      <div className="text-center space-y-1">
        <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
          {message}
        </p>
        <p className="text-xs text-slate-400 dark:text-slate-500">
          OCR and NER may take up to 30 seconds for large files
        </p>
      </div>
    </div>
  )
}
