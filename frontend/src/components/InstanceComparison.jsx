import { useState } from 'react'
import ScoreBar from './ScoreBar'

function getScoreColor(score) {
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#f59e0b'
  return '#ef4444'
}

function InstanceComparison({ ranking, metadata, selectedInstances, onClear }) {
  const [showSelector, setShowSelector] = useState(false)
  const currency = metadata?.currency || 'EUR'

  const selected = ranking?.filter(r => selectedInstances.includes(r.instance_type)) || []
  const available = ranking?.filter(r => !selectedInstances.includes(r.instance_type)) || []

  const handleAdd = (instanceType) => {
    if (selectedInstances.length < 3) {
      onClear([...selectedInstances, instanceType])
    }
    setShowSelector(false)
  }

  const handleRemove = (instanceType) => {
    onClear(selectedInstances.filter(id => id !== instanceType))
  }

  if (selected.length === 0) return null

  const metrics = [
    { key: 'single_core_score', label: 'Single Core' },
    { key: 'multi_core_score', label: 'Multi Core' },
    { key: 'memory_score', label: 'Memory' },
    { key: 'disk_score', label: 'Disk IOPS' },
    { key: 'overall_score', label: 'Overall' },
    { key: 'cpu_value_monthly', label: `Value (${currency})` },
  ]

  const getBest = (key) => {
    return Math.max(...selected.map(s => s[key] || 0))
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 className="card-title" style={{ margin: 0 }}>
          Instance Comparison
          <span style={{ marginLeft: '0.5rem', fontSize: '0.875rem', color: 'var(--color-text-muted)', fontWeight: 'normal' }}>
            ({selected.length}/3)
          </span>
        </h2>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {selected.length < 3 && available.length > 0 && (
            <button
              onClick={() => setShowSelector(!showSelector)}
              className="btn btn-secondary"
            >
              {showSelector ? 'Cancel' : 'Add Instance'}
            </button>
          )}
          <button
            onClick={() => onClear([])}
            className="btn btn-ghost"
          >
            Clear All
          </button>
        </div>
      </div>

      {showSelector && (
        <div style={{ marginBottom: '1rem', padding: '1rem', background: 'var(--color-bg)', borderRadius: 'var(--radius-sm)' }}>
          <p style={{ marginBottom: '0.5rem', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
            Select an instance to compare:
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {available.map(inst => (
              <button
                key={inst.instance_type}
                onClick={() => handleAdd(inst.instance_type)}
                className="btn btn-small btn-secondary"
              >
                {inst.instance_type}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="comparison-grid" style={{ 
        display: 'grid', 
        gridTemplateColumns: `repeat(${selected.length + 1}, 1fr)`,
        gap: '1px',
        background: 'var(--color-surface-light)',
        borderRadius: 'var(--radius-sm)',
        overflow: 'hidden'
      }}>
        <div style={{ background: 'var(--color-surface)', padding: '1rem', fontWeight: '600' }}>
          Metric
        </div>
        {selected.map(inst => (
          <div key={inst.instance_type} style={{ background: 'var(--color-surface)', padding: '1rem', position: 'relative' }}>
            <button
              onClick={() => handleRemove(inst.instance_type)}
              style={{
                position: 'absolute',
                top: '0.5rem',
                right: '0.5rem',
                background: 'none',
                border: 'none',
                color: 'var(--color-text-muted)',
                cursor: 'pointer',
                fontSize: '1.25rem',
                lineHeight: 1
              }}
              title="Remove"
            >
              ×
            </button>
            <div style={{ fontWeight: '600', fontSize: '1.1rem' }}>{inst.instance_type}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{inst.arch}</div>
          </div>
        ))}

        <div style={{ background: 'var(--color-surface)', padding: '1rem' }}>
          <span style={{ color: 'var(--color-text-muted)' }}>Specs</span>
        </div>
        {selected.map(inst => (
          <div key={inst.instance_type} style={{ background: 'var(--color-surface)', padding: '1rem' }}>
            {inst.vcpu} vCPU<br />
            {inst.ram_gb} GB RAM<br />
            {inst.disk_gb} GB Disk
          </div>
        ))}

        <div style={{ background: 'var(--color-surface)', padding: '1rem' }}>
          <span style={{ color: 'var(--color-text-muted)' }}>Price</span>
        </div>
        {selected.map(inst => (
          <div key={inst.instance_type} style={{ background: 'var(--color-surface)', padding: '1rem' }}>
            <div>€{inst.price_monthly.toFixed(2)}/mo</div>
            <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
              €{inst.price_hourly.toFixed(4)}/hr
            </div>
          </div>
        ))}

        {metrics.map(metric => {
          const best = getBest(metric.key)
          return (
            <>
              <div key={metric.key} style={{ background: 'var(--color-surface)', padding: '1rem' }}>
                <span style={{ color: 'var(--color-text-muted)' }}>{metric.label}</span>
              </div>
              {selected.map(inst => {
                const value = inst[metric.key] || 0
                const isBest = value === best && value > 0
                return (
                  <div 
                    key={inst.instance_type} 
                    style={{ 
                      background: isBest ? 'rgba(34, 197, 94, 0.1)' : 'var(--color-surface)', 
                      padding: '1rem'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {metric.key.includes('score') && <ScoreBar value={value} />}
                      <span style={{ 
                        fontWeight: isBest ? '700' : '400',
                        color: metric.key === 'overall_score' ? getScoreColor(value) : 'inherit'
                      }}>
                        {value.toFixed(metric.key === 'cpu_value_monthly' ? 1 : 0)}
                      </span>
                      {isBest && <span style={{ color: '#22c55e', fontSize: '0.75rem' }}>★</span>}
                    </div>
                  </div>
                )
              })}
            </>
          )
        })}
      </div>
    </div>
  )
}

export default InstanceComparison
