import React, { useState, useMemo } from 'react'
import './EntityInspector.css'

export interface PIIEntityItem {
  type: string
  value: string
  confidence?: number
}

interface EntityInspectorProps {
  entities: PIIEntityItem[]
  selectedEntityValue?: string | null
  onSelectEntity?: (entity: PIIEntityItem) => void
  isOpen?: boolean
  onToggleOpen?: () => void
}

type CategoryKey = 'all' | 'names' | 'dates' | 'locations' | 'ids' | 'contact' | 'other'

const CATEGORY_MAP: Record<string, CategoryKey> = {
  person_name: 'names',
  nam: 'names',
  date: 'dates',
  dat: 'dates',
  address: 'locations',
  adr: 'locations',
  ssn: 'ids',
  medical_record_number: 'ids',
  mrn: 'ids',
  aadhaar_number: 'ids',
  adh: 'ids',
  pan_number: 'ids',
  pan: 'ids',
  abha_id: 'ids',
  abh: 'ids',
  national_id: 'ids',
  nid: 'ids',
  certificate_or_license_number: 'ids',
  lic: 'ids',
  account_number: 'ids',
  acc: 'ids',
  vehicle_identifier: 'ids',
  vin: 'ids',
  device_identifier: 'ids',
  dev: 'ids',
  health_plan_beneficiary_number: 'ids',
  hpb: 'ids',
  phone_number: 'contact',
  phn: 'contact',
  fax_number: 'contact',
  fax: 'contact',
  email: 'contact',
  eml: 'contact',
  url: 'contact',
  ip_address: 'contact',
  ip: 'contact',
  other: 'other',
  oth: 'other',
  biometric_identifier: 'other',
  photographic_image: 'other',
}

const CATEGORY_LABELS: Record<CategoryKey, string> = {
  all: 'All Entities',
  names: 'Names',
  dates: 'Dates',
  locations: 'Locations',
  ids: 'IDs & Numbers',
  contact: 'Contact Info',
  other: 'Other PHI',
}

export default function EntityInspector({
  entities,
  selectedEntityValue,
  onSelectEntity,
  isOpen = true,
  onToggleOpen,
}: EntityInspectorProps) {
  const [activeTab, setActiveTab] = useState<CategoryKey>('all')
  const [searchQuery, setSearchQuery] = useState('')

  const groupedCounts = useMemo(() => {
    const counts: Record<CategoryKey, number> = {
      all: entities.length,
      names: 0,
      dates: 0,
      locations: 0,
      ids: 0,
      contact: 0,
      other: 0,
    }
    for (const ent of entities) {
      const cat = CATEGORY_MAP[ent.type.toLowerCase()] || 'other'
      counts[cat] = (counts[cat] || 0) + 1
    }
    return counts
  }, [entities])

  const filteredEntities = useMemo(() => {
    return entities.filter((ent) => {
      const cat = CATEGORY_MAP[ent.type.toLowerCase()] || 'other'
      const matchesTab = activeTab === 'all' || cat === activeTab
      const matchesSearch =
        searchQuery === '' ||
        ent.value.toLowerCase().includes(searchQuery.toLowerCase()) ||
        ent.type.toLowerCase().includes(searchQuery.toLowerCase())
      return matchesTab && matchesSearch
    })
  }, [entities, activeTab, searchQuery])

  if (!isOpen) {
    return (
      <button
        className="entity-inspector-collapsed-btn"
        onClick={onToggleOpen}
        title="Open PHI Entity Inspector"
        aria-label="Open PHI Entity Inspector"
      >
        <span className="collapsed-icon">🏷️</span>
        <span className="collapsed-badge">{entities.length}</span>
      </button>
    )
  }

  return (
    <aside className="entity-inspector-panel">
      <div className="inspector-header">
        <div className="inspector-title-row">
          <div className="inspector-title">
            <span className="inspector-icon">🔍</span>
            <h4>Detected PHI Entities</h4>
            <span className="total-badge">{entities.length}</span>
          </div>
          {onToggleOpen && (
            <button
              className="inspector-close-btn"
              onClick={onToggleOpen}
              title="Collapse Inspector"
              aria-label="Collapse Inspector"
            >
              &times;
            </button>
          )}
        </div>

        <div className="inspector-search-box">
          <input
            type="text"
            className="inspector-search-input"
            placeholder="Filter entities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button className="search-clear-btn" onClick={() => setSearchQuery('')}>
              &times;
            </button>
          )}
        </div>

        <div className="category-pills-bar">
          {(['all', 'names', 'dates', 'locations', 'ids', 'contact', 'other'] as CategoryKey[]).map((cat) => {
            const count = groupedCounts[cat]
            if (count === 0 && cat !== 'all') return null
            return (
              <button
                key={cat}
                className={`category-pill ${activeTab === cat ? 'active' : ''}`}
                onClick={() => setActiveTab(cat)}
              >
                {CATEGORY_LABELS[cat]} <span className="pill-count">{count}</span>
              </button>
            )
          })}
        </div>
      </div>

      <div className="inspector-list">
        {filteredEntities.length === 0 ? (
          <div className="inspector-empty">No matching PHI entities found.</div>
        ) : (
          filteredEntities.map((ent, idx) => {
            const isSelected = selectedEntityValue === ent.value
            const cat = CATEGORY_MAP[ent.type.toLowerCase()] || 'other'
            return (
              <div
                key={`${ent.type}-${ent.value}-${idx}`}
                className={`inspector-item cat-${cat} ${isSelected ? 'selected' : ''}`}
                onClick={() => onSelectEntity?.(ent)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') onSelectEntity?.(ent)
                }}
              >
                <div className="item-header">
                  <span className={`entity-type-badge cat-${cat}`}>
                    {ent.type.toUpperCase().replace(/_/g, ' ')}
                  </span>
                  {ent.confidence && (
                    <span className="confidence-tag">{Math.round(ent.confidence * 100)}%</span>
                  )}
                </div>
                <div className="item-value">{ent.value}</div>
              </div>
            )
          })
        )}
      </div>
    </aside>
  )
}
