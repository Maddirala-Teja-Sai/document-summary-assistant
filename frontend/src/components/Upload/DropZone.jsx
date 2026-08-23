import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { MdCloudUpload } from 'react-icons/md'

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'image/png':       ['.png'],
  'image/jpeg':      ['.jpg', '.jpeg'],
  'image/tiff':      ['.tiff', '.tif'],
  'image/bmp':       ['.bmp'],
}

/**
 * Drag-and-drop file upload zone.
 *
 * @param {Function} onFilesAdded - Called with File[] when files are dropped/picked
 * @param {boolean}  disabled     - Disable when a request is in flight
 */
export default function DropZone({ onFilesAdded, disabled = false }) {
  const onDrop = useCallback(
    (accepted) => {
      if (accepted.length > 0) onFilesAdded(accepted)
    },
    [onFilesAdded],
  )

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 5,
    disabled,
    multiple: true,
  })

  const borderColour = isDragReject
    ? 'border-red-400 dark:border-red-500 bg-red-50 dark:bg-red-900/10'
    : isDragActive
    ? 'border-brand-400 dark:border-brand-400 bg-brand-50 dark:bg-brand-900/10'
    : 'border-slate-300 dark:border-slate-600 hover:border-brand-400 dark:hover:border-brand-400'

  return (
    <div
      {...getRootProps()}
      className={`
        relative flex flex-col items-center justify-center gap-3
        rounded-xl border-2 border-dashed p-10 text-center
        transition-all duration-200 cursor-pointer
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${borderColour}
      `}
    >
      <input {...getInputProps()} />

      {/* Icon */}
      <div className={`
        flex h-14 w-14 items-center justify-center rounded-full
        transition-colors duration-200
        ${isDragActive
          ? 'bg-brand-100 dark:bg-brand-900/30'
          : 'bg-slate-100 dark:bg-slate-700'}
      `}>
        <MdCloudUpload className={`
          h-7 w-7 transition-colors duration-200
          ${isDragActive ? 'text-brand-500' : 'text-slate-400 dark:text-slate-500'}
        `} aria-hidden="true" />
      </div>

      {/* Text */}
      {isDragReject ? (
        <p className="text-sm font-medium text-red-500">
          Unsupported file type — drop PDF, PNG, JPEG, TIFF, or BMP
        </p>
      ) : isDragActive ? (
        <p className="text-sm font-semibold text-brand-600 dark:text-brand-400">
          Release to add files
        </p>
      ) : (
        <>
          <div>
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              Drag &amp; drop files here
            </p>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
              or <span className="text-brand-500 underline underline-offset-2">click to browse</span>
            </p>
          </div>
          <p className="text-xs text-slate-400 dark:text-slate-500">
            PDF · PNG · JPEG · TIFF · BMP &nbsp;·&nbsp; Max 10 MB per file &nbsp;·&nbsp; Up to 5 files
          </p>
        </>
      )}
    </div>
  )
}
