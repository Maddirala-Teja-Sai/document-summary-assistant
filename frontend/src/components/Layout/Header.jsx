import { MdDescription } from 'react-icons/md'
import ThemeToggle from './ThemeToggle'

export default function Header({ isDark, toggleTheme }) {
  return (
    <header className="
      sticky top-0 z-10
      border-b border-slate-200 dark:border-slate-700
      bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm
    ">
      <div className="max-w-5xl mx-auto px-4 sm:px-8 h-16 flex items-center justify-between">

        {/* Logo + title */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500 text-white shadow-sm">
            <MdDescription className="h-6 w-6" aria-hidden="true" />
          </div>
          <span className="font-bold text-slate-800 dark:text-slate-100 text-base sm:text-lg">
            Document Summary Assistant
          </span>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          <ThemeToggle isDark={isDark} toggle={toggleTheme} />
        </div>

      </div>
    </header>
  )
}
