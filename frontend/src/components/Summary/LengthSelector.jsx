/**
 * Short / Medium / Long summary length selector.
 * Rendered as a segmented control.
 *
 * @param {string}   value    - Currently selected length
 * @param {Function} onChange - Called with new length string
 * @param {boolean}  disabled
 */

const OPTIONS = [
  { value: 'short',  label: 'Short',  hint: '3 sentences' },
  { value: 'medium', label: 'Medium', hint: '7 sentences' },
  { value: 'long',   label: 'Long',   hint: '12 sentences' },
]

export default function LengthSelector({ value, onChange, disabled = false }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500 mb-2">
        Summary length
      </p>
      <div className="
        inline-flex rounded-lg border border-slate-200 dark:border-slate-700
        bg-slate-100 dark:bg-slate-800 p-0.5 gap-0.5
      ">
        {OPTIONS.map((opt) => {
          const active = value === opt.value
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => !disabled && onChange(opt.value)}
              disabled={disabled}
              aria-pressed={active}
              className={`
                px-4 py-1.5 rounded-md text-sm font-medium transition-all duration-150
                disabled:opacity-50 disabled:cursor-not-allowed
                ${active
                  ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-400 shadow-sm'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }
              `}
            >
              <span>{opt.label}</span>
              <span className="hidden sm:inline text-xs opacity-60 ml-1">({opt.hint})</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
