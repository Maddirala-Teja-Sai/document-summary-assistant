import { MdDarkMode, MdLightMode } from 'react-icons/md'

/**
 * Dark / light mode toggle button.
 *
 * @param {boolean}  isDark - Current theme state
 * @param {Function} toggle - Callback to flip the theme
 */
export default function ThemeToggle({ isDark, toggle }) {
  return (
    <button
      onClick={toggle}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="
        p-2 rounded-lg text-slate-500 dark:text-slate-400
        hover:bg-slate-100 dark:hover:bg-slate-700
        hover:text-slate-700 dark:hover:text-slate-200
        transition-colors
      "
    >
      {isDark
        ? <MdLightMode className="h-5 w-5" aria-hidden="true" />
        : <MdDarkMode  className="h-5 w-5" aria-hidden="true" />
      }
    </button>
  )
}
