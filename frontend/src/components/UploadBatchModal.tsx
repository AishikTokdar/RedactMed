import React, { useState, useRef } from 'react'
import JSZip from 'jszip'
import {
  requestUploadUrls,
  uploadFileToPresignedUrl,
  directUploadBatchFiles,
} from '../api/client'
import './UploadBatchModal.css'

export interface UploadBatchModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (batchId: string, noteCount: number) => void
}

interface NoteFileItem {
  id: string
  filename: string
  content?: string
  file?: File | Blob
  size: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

export function generateDefaultBatchId(): string {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  const yyyy = now.getUTCFullYear()
  const mm = pad(now.getUTCMonth() + 1)
  const dd = pad(now.getUTCDate())
  const hh = pad(now.getUTCHours())
  const min = pad(now.getUTCMinutes())
  const ss = pad(now.getUTCSeconds())
  return `batch-${yyyy}${mm}${dd}-${hh}${min}${ss}`
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export default function UploadBatchModal({ isOpen, onClose, onSuccess }: UploadBatchModalProps) {
  const [batchIdInput, setBatchIdInput] = useState('')
  const [isDragOver, setIsDragOver] = useState(false)
  const [files, setFiles] = useState<NoteFileItem[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [errorMessage, setErrorMessage] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  if (!isOpen) return null

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  const processIncomingFiles = async (fileList: FileList | File[]) => {
    setErrorMessage('')
    const newItems: NoteFileItem[] = []

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i]
      if (file.name.toLowerCase().endsWith('.zip')) {
        try {
          const zip = await JSZip.loadAsync(file)
          const entries = Object.values(zip.files)
          for (const entry of entries) {
            if (!entry.dir && (entry.name.toLowerCase().endsWith('.txt') || !entry.name.includes('.'))) {
              const textContent = await entry.async('string')
              const cleanName = entry.name.replace(/\\/g, '/').split('/').pop() || 'note.txt'
              newItems.push({
                id: `${Date.now()}-${Math.random()}`,
                filename: cleanName,
                content: textContent,
                size: new Blob([textContent]).size,
                status: 'pending',
              })
            }
          }
        } catch (err) {
          setErrorMessage(`Failed to read ZIP archive ${file.name}: ${err instanceof Error ? err.message : 'Invalid zip'}`)
        }
      } else if (file.name.toLowerCase().endsWith('.txt') || file.type.startsWith('text/')) {
        const textContent = await file.text()
        newItems.push({
          id: `${Date.now()}-${Math.random()}`,
          filename: file.name,
          content: textContent,
          file: file,
          size: file.size,
          status: 'pending',
        })
      }
    }

    if (newItems.length === 0 && fileList.length > 0) {
      setErrorMessage('No valid .txt clinical notes or .zip archives found.')
      return
    }

    setFiles((prev) => [...prev, ...newItems])
  }

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await processIncomingFiles(e.dataTransfer.files)
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await processIncomingFiles(e.target.files)
    }
  }

  const handleRemoveFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }

  const handleClearAll = () => {
    setFiles([])
    setErrorMessage('')
    setUploadProgress(0)
  }

  const handleStartUpload = async () => {
    if (files.length === 0) {
      setErrorMessage('Please select or drop at least one .txt note or .zip archive.')
      return
    }

    setIsUploading(true)
    setErrorMessage('')
    setUploadProgress(0)

    const targetBatchId = batchIdInput.trim() || generateDefaultBatchId()

    try {
      // Step 1: Attempt S3 Presigned URL Upload workflow
      let useDirectFallback = false
      try {
        const reqPayload = files.map((f) => ({
          filename: f.filename,
          content_type: 'text/plain',
        }))

        const { urls, batch_id: returnedBatchId } = await requestUploadUrls(targetBatchId, reqPayload)

        let completedCount = 0
        for (let i = 0; i < files.length; i++) {
          const item = files[i]
          const presignedObj = urls.find((u) => u.filename === item.filename) || urls[i]

          if (!presignedObj || !presignedObj.upload_url) {
            throw new Error(`No upload URL for ${item.filename}`)
          }

          setFiles((prev) =>
            prev.map((f) => (f.id === item.id ? { ...f, status: 'uploading' } : f))
          )

          const blobPayload = item.file || new Blob([item.content || ''], { type: 'text/plain' })
          await uploadFileToPresignedUrl(presignedObj.upload_url, blobPayload, 'text/plain')

          completedCount++
          setUploadProgress(Math.round((completedCount / files.length) * 100))

          setFiles((prev) =>
            prev.map((f) => (f.id === item.id ? { ...f, status: 'success' } : f))
          )
        }

        onSuccess(returnedBatchId, files.length)
        onClose()
        return
      } catch (presignedErr) {
        console.warn('Presigned upload failed, falling back to direct upload handler:', presignedErr)
        useDirectFallback = true
      }

      // Step 2: Fallback direct content upload
      if (useDirectFallback) {
        const directPayload = await Promise.all(
          files.map(async (f) => ({
            filename: f.filename,
            content: f.content !== undefined ? f.content : f.file ? await f.file.text() : '',
          }))
        )

        const result = await directUploadBatchFiles(targetBatchId, directPayload)
        setUploadProgress(100)
        setFiles((prev) => prev.map((f) => ({ ...f, status: 'success' })))

        onSuccess(result.batch_id, files.length)
        onClose()
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed. Please try again.'
      setErrorMessage(msg)
      setFiles((prev) => prev.map((f) => (f.status === 'uploading' ? { ...f, status: 'error', error: msg } : f)))
    } finally {
      setIsUploading(false)
    }
  }

  const totalBytes = files.reduce((acc, f) => acc + f.size, 0)

  return (
    <div className="upload-modal-backdrop" onClick={onClose}>
      <div className="upload-modal-container" onClick={(e) => e.stopPropagation()}>
        <div className="upload-modal-header">
          <div className="upload-header-title">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <h3>Upload New Document Batch</h3>
          </div>
          <button className="upload-modal-close-btn" onClick={onClose} disabled={isUploading}>
            ✕
          </button>
        </div>

        <div className="upload-modal-body">
          <div className="upload-batch-id-group">
            <label htmlFor="batch-id-input">Custom Batch ID (Optional):</label>
            <input
              id="batch-id-input"
              type="text"
              className="batch-id-input-field"
              placeholder={`Auto-generated e.g. ${generateDefaultBatchId()}`}
              value={batchIdInput}
              onChange={(e) => setBatchIdInput(e.target.value)}
              disabled={isUploading}
            />
          </div>

          <div
            className={`upload-dropzone ${isDragOver ? 'drag-over' : ''} ${isUploading ? 'disabled' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !isUploading && fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              multiple
              accept=".txt,.zip"
              style={{ display: 'none' }}
              disabled={isUploading}
            />
            <div className="dropzone-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <path d="M12 18v-6" />
                <path d="m9 15 3-3 3 3" />
              </svg>
            </div>
            <div className="dropzone-text">
              <strong>Drag and drop clinical notes here</strong>
              <span>Supports individual <code>.txt</code> files or <code>.zip</code> archives</span>
            </div>
            <button type="button" className="btn-browse-files" disabled={isUploading}>
              Browse Files
            </button>
          </div>

          {errorMessage && <div className="upload-error-banner">{errorMessage}</div>}

          {files.length > 0 && (
            <div className="upload-files-summary">
              <div className="files-summary-header">
                <span>Selected Notes ({files.length}) • Total {formatFileSize(totalBytes)}</span>
                {!isUploading && (
                  <button type="button" className="btn-clear-all" onClick={handleClearAll}>
                    Clear All
                  </button>
                )}
              </div>

              {isUploading && (
                <div className="upload-progress-section">
                  <div className="progress-bar-track">
                    <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }} />
                  </div>
                  <span className="progress-percentage">{uploadProgress}% Uploaded</span>
                </div>
              )}

              <div className="upload-file-list">
                {files.map((file) => (
                  <div key={file.id} className="file-list-item">
                    <span className="file-item-name" title={file.filename}>
                      📄 {file.filename}
                    </span>
                    <span className="file-item-size">{formatFileSize(file.size)}</span>
                    <span className={`file-item-status status-${file.status}`}>
                      {file.status === 'pending' && 'Ready'}
                      {file.status === 'uploading' && 'Uploading...'}
                      {file.status === 'success' && '✓ Uploaded'}
                      {file.status === 'error' && '✕ Error'}
                    </span>
                    {!isUploading && (
                      <button
                        type="button"
                        className="btn-remove-file"
                        onClick={() => handleRemoveFile(file.id)}
                        title="Remove file"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="upload-modal-footer">
          <button type="button" className="btn-cancel" onClick={onClose} disabled={isUploading}>
            Cancel
          </button>
          <button
            type="button"
            className="btn-submit-upload"
            onClick={handleStartUpload}
            disabled={isUploading || files.length === 0}
          >
            {isUploading ? (
              <>
                <span className="spinner-small" /> Uploading Batch...
              </>
            ) : (
              `Create & Upload Batch (${files.length} notes)`
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
