import React, { useState } from 'react'
import { exportBatch, getBatchCertificate } from '../api/client'
import './ExportBatchModal.css'

export interface ExportBatchModalProps {
  isOpen: boolean
  batchId: string
  onClose: () => void
}

type ExportFormat = 'zip' | 'csv' | 'json' | 'certificate'

export default function ExportBatchModal({ isOpen, batchId, onClose }: ExportBatchModalProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('zip')
  const [isExporting, setIsExporting] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  if (!isOpen) return null

  const handleDownloadTrigger = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleExecuteExport = async () => {
    setIsExporting(true)
    setErrorMsg('')

    try {
      if (selectedFormat === 'certificate') {
        const certRes = await getBatchCertificate(batchId, 'html')
        if (certRes.html) {
          const blob = new Blob([certRes.html], { type: 'text/html;charset=utf-8' })
          handleDownloadTrigger(blob, `${batchId}_Compliance_Certificate.html`)
        } else {
          throw new Error('Certificate HTML payload was empty')
        }
      } else if (selectedFormat === 'zip') {
        const res = await exportBatch(batchId, 'zip')
        if (res.data_base64) {
          const byteChars = atob(res.data_base64)
          const byteNumbers = new Array(byteChars.length)
          for (let i = 0; i < byteChars.length; i++) {
            byteNumbers[i] = byteChars.charCodeAt(i)
          }
          const byteArray = new Uint8Array(byteNumbers)
          const blob = new Blob([byteArray], { type: 'application/zip' })
          handleDownloadTrigger(blob, res.filename || `${batchId}_redacted.zip`)
        } else {
          throw new Error('ZIP data payload was empty')
        }
      } else if (selectedFormat === 'csv') {
        const res = await exportBatch(batchId, 'csv')
        if (res.content) {
          const blob = new Blob([res.content], { type: 'text/csv;charset=utf-8' })
          handleDownloadTrigger(blob, res.filename || `${batchId}_audit.csv`)
        }
      } else {
        const res = await exportBatch(batchId, 'json')
        const jsonStr = JSON.stringify(res, null, 2)
        const blob = new Blob([jsonStr], { type: 'application/json;charset=utf-8' })
        handleDownloadTrigger(blob, `${batchId}_manifest.json`)
      }

      onClose()
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="export-modal" onClick={(e) => e.stopPropagation()}>
        <div className="export-modal-header">
          <div className="export-header-title">
            <span className="export-icon">📦</span>
            <h3>Export Batch: {batchId}</h3>
          </div>
          <button className="export-close-btn" onClick={onClose} disabled={isExporting}>
            &times;
          </button>
        </div>

        <div className="export-modal-body">
          <p className="export-instructions">
            Choose an export package format for sanitized clinical records and compliance verification:
          </p>

          <div className="export-options-grid">
            <label
              className={`export-option-card ${selectedFormat === 'zip' ? 'selected' : ''}`}
              onClick={() => setSelectedFormat('zip')}
            >
              <input
                type="radio"
                name="export-format"
                checked={selectedFormat === 'zip'}
                onChange={() => setSelectedFormat('zip')}
              />
              <div className="option-info">
                <span className="option-title">🗜️ Sanitized Notes (.zip)</span>
                <span className="option-desc">Compressed archive of all approved, de-identified clinical notes (.txt).</span>
              </div>
            </label>

            <label
              className={`export-option-card ${selectedFormat === 'certificate' ? 'selected' : ''}`}
              onClick={() => setSelectedFormat('certificate')}
            >
              <input
                type="radio"
                name="export-format"
                checked={selectedFormat === 'certificate'}
                onChange={() => setSelectedFormat('certificate')}
              />
              <div className="option-info">
                <span className="option-title">📜 Compliance Certificate (.html)</span>
                <span className="option-desc">Official verification certificate with SHA-256 hash chains for IRB audits.</span>
              </div>
            </label>

            <label
              className={`export-option-card ${selectedFormat === 'csv' ? 'selected' : ''}`}
              onClick={() => setSelectedFormat('csv')}
            >
              <input
                type="radio"
                name="export-format"
                checked={selectedFormat === 'csv'}
                onChange={() => setSelectedFormat('csv')}
              />
              <div className="option-info">
                <span className="option-title">📊 Audit Summary (.csv)</span>
                <span className="option-desc">Tabular audit manifest with approval states, entity tallies, and categories.</span>
              </div>
            </label>

            <label
              className={`export-option-card ${selectedFormat === 'json' ? 'selected' : ''}`}
              onClick={() => setSelectedFormat('json')}
            >
              <input
                type="radio"
                name="export-format"
                checked={selectedFormat === 'json'}
                onChange={() => setSelectedFormat('json')}
              />
              <div className="option-info">
                <span className="option-title">📄 Structured Manifest (.json)</span>
                <span className="option-desc">Machine-readable JSON schema with detected entity spans and note payloads.</span>
              </div>
            </label>
          </div>

          {errorMsg && <div className="export-error-banner">{errorMsg}</div>}
        </div>

        <div className="export-modal-footer">
          <button className="btn btn-secondary" onClick={onClose} disabled={isExporting}>
            Cancel
          </button>
          <button className="btn btn-primary btn-export" onClick={handleExecuteExport} disabled={isExporting}>
            {isExporting ? 'Preparing Package...' : 'Download Package'}
          </button>
        </div>
      </div>
    </div>
  )
}
