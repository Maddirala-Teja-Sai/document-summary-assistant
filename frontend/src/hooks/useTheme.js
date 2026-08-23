import { useEffect, useState } from 'react'

const STORAGE_KEY = 'dsa-theme'

/**
 * Custom hook for dark/light mode.
 *
 * - Reads initial preference from localStorage, then OS preference.
 * - Persists the user's choice to localStorage.
 * - Applies/removes the 'dark' class on <html> to activate Tailwind dark mode.
 *
 * @returns {{ isDark: boolean, toggle: () => void }}
 */
export function useTheme() {
  const [isDark, setIsDark] = useState(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored !== null) return stored === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    const root = document.documentElement
    if (isDark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    localStorage.setItem(STORAGE_KEY, isDark ? 'dark' : 'light')
  }, [isDark])

  const toggle = () => setIsDark((prev) => !prev)

  return { isDark, toggle }
}
