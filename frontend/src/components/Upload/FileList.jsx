import { MdClose, MdImage, MdPictureAsPdf } from 'react-icons/md'

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function FileIcon({ type }) {
  if (type === 'application/pdf') {
    return <MdPictureAsPdf className="h-5 w-5 text-red-400" aria-hidden="true" />
  }
  return <MdImage className="h-5 w-5 text-blue-400" aria-hidden="true" />
}

/**
 * List of selected files with individual remove buttons.
 *
 * @param {File[]}   files      - Currently selected files
 * @param {Function} onRemove   - Called with index to remove
 * @param {boolean}  disabled   - Disable remove buttons during upload
 */
export default function FileList({ files, onRemove, disabled = false }) {
  if (files.length === 0) return null

  return (
    <ul className="space-y-2" aria-label="Selected files">
      {files.map((file, i) => (
        <li
          key={`${file.name}-${i}`}
          className="
            flex items-center gap-3 rounded-lg border border-slate-200
            dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2
          "
        >
          <FileIcon type={file.type} />

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-700 dark:text-slate-200">
              {file.name}
            </p>
            <p className="text-xs text-slate-400 dark:text-slate-500">
              {formatBytes(file.size)}
            </p>
          </div>

          <button
            onClick={() => onRemove(i)}
            disabled={disabled}
            aria-label={`Remove ${file.name}`}
            className="
              flex-shrink-0 rounded p-1 text-slate-400 hover:text-red-500
              dark:text-slate-500 dark:hover:text-red-400
              transition-colors disabled:opacity-40
            "
          >
            <MdClose className="h-4 w-4" aria-hidden="true" />
          </button>
        </li>
      ))}
    </ul>
  )
}
