import { useMemo, useRef, useEffect, useState, useLayoutEffect } from 'react'
import * as Diff from 'diff'
import './DiffViewer.css'

interface DiffViewerProps {
  original: string
  redacted: string
  editableRedacted?: boolean
  onRedactedChange?: (value: string) => void
  highlightValue?: string | null
  onManualRedactSpan?: (selectedText: string, piiType: string) => void
}

interface DiffChange {
  value: string
  added?: boolean
  removed?: boolean
}

function countWords(text: string): number {
  return text.trim().split(/\s+/).filter(w => w.length > 0).length
}

function getTagCategoryClass(val: string): string {
  const upper = val.toUpperCase()
  if (upper.includes('NAME')) return 'tag-names'
  if (upper.includes('DATE') || upper.includes('AGE')) return 'tag-dates'
  if (upper.includes('ADDRESS') || upper.includes('LOCATION') || upper.includes('ZIP') || upper.includes('ADDR')) return 'tag-locations'
  if (upper.includes('ID') || upper.includes('SSN') || upper.includes('MRN') || upper.includes('AADHAAR') || upper.includes('PAN') || upper.includes('LICENSE') || upper.includes('VIN') || upper.includes('DEVICE')) return 'tag-ids'
  if (upper.includes('PHONE') || upper.includes('EMAIL') || upper.includes('URL') || upper.includes('IP') || upper.includes('FAX')) return 'tag-contact'
  return 'tag-other'
}

export default function DiffViewer({
  original,
  redacted,
  editableRedacted = false,
  onRedactedChange,
  highlightValue,
  onManualRedactSpan,
}: DiffViewerProps) {
  const originalRef = useRef<HTMLElement | null>(null)
  const redactedRef = useRef<HTMLElement | null>(null)
  const redactedScrollTopRef = useRef(0)
  const [syncScrollEnabled, setSyncScrollEnabled] = useState(true)
  const syncScrollEnabledRef = useRef(syncScrollEnabled)
  const lastScrollPositions = useRef({ original: 0, redacted: 0 })
  const [popover, setPopover] = useState<{ text: string; top: number; left: number } | null>(null)


  useEffect(() => {
    syncScrollEnabledRef.current = syncScrollEnabled
    if (syncScrollEnabled && originalRef.current && redactedRef.current) {
      lastScrollPositions.current = {
        original: originalRef.current.scrollTop,
        redacted: redactedRef.current.scrollTop,
      }
      redactedScrollTopRef.current = redactedRef.current.scrollTop
    }
  }, [syncScrollEnabled])

  useLayoutEffect(() => {
    const panel = redactedRef.current
    if (panel) {
      panel.scrollTop = redactedScrollTopRef.current
      lastScrollPositions.current.redacted = panel.scrollTop
    }

    return () => {
      const currentRedactedTop = redactedRef.current?.scrollTop
      if (typeof currentRedactedTop === 'number') {
        redactedScrollTopRef.current = currentRedactedTop
        lastScrollPositions.current.redacted = currentRedactedTop
      }
    }
  }, [editableRedacted])

  const changes = useMemo((): DiffChange[] => Diff.diffWords(original, redacted), [original, redacted])

  const stats = useMemo(() => {
    let removed = 0, added = 0
    for (const c of changes) {
      const wc = countWords(c.value)
      if (c.removed) removed += wc
      else if (c.added) added += wc
    }
    return { removed, added }
  }, [changes])

  useEffect(() => {
    const oPanel = originalRef.current
    const rPanel = redactedRef.current
    if (!oPanel || !rPanel) return

    let isSyncing = false

    const syncScroll = (
      source: HTMLElement,
      sourceKey: 'original' | 'redacted',
      target: HTMLElement,
      targetKey: 'original' | 'redacted',
    ) => {
      if (!syncScrollEnabledRef.current) {
        lastScrollPositions.current[sourceKey] = source.scrollTop
        if (sourceKey === 'redacted') {
          redactedScrollTopRef.current = source.scrollTop
        }
        return
      }
      if (isSyncing) return
      isSyncing = true

      const delta = source.scrollTop - lastScrollPositions.current[sourceKey]
      lastScrollPositions.current[sourceKey] = source.scrollTop
      if (sourceKey === 'redacted') {
        redactedScrollTopRef.current = source.scrollTop
      }

      const newTop = lastScrollPositions.current[targetKey] + delta
      const maxScroll = target.scrollHeight - target.clientHeight
      target.scrollTop = Math.max(0, Math.min(maxScroll, newTop))
      lastScrollPositions.current[targetKey] = target.scrollTop
      if (targetKey === 'redacted') {
        redactedScrollTopRef.current = target.scrollTop
      }

      requestAnimationFrame(() => { isSyncing = false })
    }

    const handleOriginalScroll = () => syncScroll(oPanel, 'original', rPanel, 'redacted')
    const handleRedactedScroll = () => syncScroll(rPanel, 'redacted', oPanel, 'original')

    oPanel.addEventListener('scroll', handleOriginalScroll)
    rPanel.addEventListener('scroll', handleRedactedScroll)

    return () => {
      oPanel.removeEventListener('scroll', handleOriginalScroll)
      rPanel.removeEventListener('scroll', handleRedactedScroll)
    }
  }, [editableRedacted])

  const renderOriginal = (diffs: DiffChange[]) =>
    diffs.map((change, i) => {
      if (change.added) return null
      const isFocused =
        Boolean(highlightValue) &&
        change.value.toLowerCase().includes((highlightValue || '').toLowerCase().trim())
      const baseClass = change.removed ? 'diff-removed' : ''
      const focusedClass = isFocused ? 'diff-focused-match' : ''
      const className = [baseClass, focusedClass].filter(Boolean).join(' ')

      return (
        <span key={i} className={className || undefined}>
          {change.value}
        </span>
      )
    })

  const renderRedacted = (diffs: DiffChange[]) =>
    diffs.map((change, i) => {
      if (change.removed) return null
      if (change.added) {
        const isTag = change.value.includes('[') || change.value.startsWith('**')
        const tagCategory = isTag ? getTagCategoryClass(change.value) : ''
        return (
          <span key={i} className={`diff-added ${isTag ? `phi-tag-badge ${tagCategory}` : ''}`}>
            {change.value}
          </span>
        )
      }
      return <span key={i}>{change.value}</span>
    })

  const handleOriginalMouseUp = () => {
    if (!onManualRedactSpan) return
    const selection = window.getSelection()
    if (!selection || selection.isCollapsed) {
      setPopover(null)
      return
    }
    const selectedText = selection.toString().trim()
    if (selectedText.length > 0) {
      try {
        const range = selection.getRangeAt(0)
        const rect = range.getBoundingClientRect()
        setPopover({
          text: selectedText,
          top: Math.max(10, rect.top - 46),
          left: Math.max(10, rect.left),
        })
      } catch {
        setPopover(null)
      }
    } else {
      setPopover(null)
    }
  }

  const applyQuickRedact = (piiType: string) => {
    if (popover && onManualRedactSpan) {
      onManualRedactSpan(popover.text, piiType)
      setPopover(null)
      window.getSelection()?.removeAllRanges()
    }
  }

  return (
    <div className="diff-viewer">
      <div className="diff-toolbar">
        <button
          className={`sync-scroll-btn ${syncScrollEnabled ? 'active' : ''}`}
          onClick={() => setSyncScrollEnabled(v => !v)}
        >
          {syncScrollEnabled ? 'Sync On' : 'Sync Off'}
        </button>
        <div className="diff-legend">
          <span className="legend-item">
            <span className="legend-color legend-removed"></span>
            PHI (removed)
          </span>
          <span className="legend-item">
            <span className="legend-color legend-added"></span>
            Redacted (replaced)
          </span>
        </div>
      </div>

      <div className="diff-panels">
        <div className="diff-panel">
          <div className="diff-panel-header">
            <span className="diff-panel-label">Original</span>
            <span className="diff-panel-stats">{countWords(original)} words</span>
          </div>
          <div
            className="diff-panel-content"
            ref={(element) => {
              originalRef.current = element
            }}
            onMouseUp={handleOriginalMouseUp}
          >
            <pre className="diff-text">{renderOriginal(changes)}</pre>
          </div>
        </div>

        <div className="diff-panel">
          <div className="diff-panel-header">
            <span className="diff-panel-label">Redacted</span>
            <span className="diff-panel-stats diff-stats-info">
              {stats.removed} removed &middot; {stats.added} replaced
            </span>
          </div>
          {editableRedacted ? (
            <textarea
              className="diff-text diff-text-editable"
              value={redacted}
              onChange={(event) => onRedactedChange?.(event.target.value)}
              readOnly={!onRedactedChange}
              spellCheck={false}
              ref={(element) => {
                redactedRef.current = element
              }}
            />
          ) : (
            <div
              className="diff-panel-content"
              ref={(element) => {
                redactedRef.current = element
              }}
            >
              <pre className="diff-text">{renderRedacted(changes)}</pre>
            </div>
          )}
        </div>
      </div>

      {popover && (
        <div
          className="quick-redact-popover"
          style={{ position: 'fixed', top: `${popover.top}px`, left: `${popover.left}px`, zIndex: 1000 }}
        >
          <span className="popover-title">Redact as:</span>
          <button className="popover-btn tag-names" onClick={() => applyQuickRedact('person_name')}>Name</button>
          <button className="popover-btn tag-dates" onClick={() => applyQuickRedact('date')}>Date</button>
          <button className="popover-btn tag-locations" onClick={() => applyQuickRedact('address')}>Location</button>
          <button className="popover-btn tag-ids" onClick={() => applyQuickRedact('id')}>ID</button>
          <button className="popover-btn tag-contact" onClick={() => applyQuickRedact('phone_number')}>Phone</button>
          <button className="popover-btn tag-other" onClick={() => applyQuickRedact('other')}>Other</button>
          <button className="popover-close" onClick={() => setPopover(null)}>&times;</button>
        </div>
      )}
    </div>
  )
}

