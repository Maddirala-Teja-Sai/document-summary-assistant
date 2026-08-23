import { MdErrorOutline } from 'react-icons/md'

/**
 * Error banner with a dismiss button.
 *
 * @param {string}   message  - Error message to display
 * @param {Function} onDismiss - Called when user closes the banner
 */
export default function ErrorBanner({ message, onDismiss }) {
  if (!message) return null

  return (
    <div
      role="alert"
      className="
        flex items-start gap-3 rounded-xl border border-red-200 dark:border-red-800
        bg-red-50 dark:bg-red-900/20 px-4 py-3 text-sm
        animate-fade-in
      "
    >
      <MdErrorOutline
        className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500"
        aria-hidden="true"
      />
      <p className="flex-1 text-red-700 dark:text-red-300">{message}</p>
      {onDismiss && (
        <button
          onClick={onDismiss}
          aria-label="Dismiss error"
          className="
            flex-shrink-0 rounded p-0.5 text-red-400 hover:text-red-600
            dark:text-red-500 dark:hover:text-red-300 transition-colors
          "
        >
          ✕
        </button>
      )}
    </div>
  )
}
