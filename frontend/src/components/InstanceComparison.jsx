import { useState } from 'react'
import ScoreBar from './ScoreBar'

function formatNumber(num, decimals = 0) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(decimals) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(decimals) + 'K'
  }
  return num.toFixed(decimals)
}

function InstanceComparison({ ranking, metadata, selectedInstances, onClear }) {
  const [showSelector, setShowSelector] = useState(false)
  const currency = metadata?.currency || 'EUR'
  const currencySymbol = currency === 'EUR' ? '€' : currency

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

  const getBest = (key, isMetric = false) => {
    if (isMetric) {
      return Math.max(...selected.map(s => s.metrics?.[key] || 0))
    }
    return Math.max(...selected.map(s => s[key] || 0))
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2
    }).format(value)
  }

  return (
    <div className="card">
      <div className="section-header">
        <h2 className="section-title" style={{ margin: 0 }}>
          Side-by-Side Comparison
          <span style={{ marginLeft: '0.5rem', color: 'var(--color-text-muted)', fontWeight: 'normal' }}>
            ({selected.length}/3)
          </span>
        </h2>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {selected.length < 3 && available.length > 0 && (
            <button
              onClick={() => setShowSelector(!showSelector)}
              className="btn btn-secondary btn-small"
            >
              {showSelector ? 'Cancel' : 'Add'}
            </button>
          )}
          <button
            onClick={() => onClear([])}
            className="btn btn-ghost btn-small"
          >
            Clear
          </button>
        </div>
      </div>

      {showSelector && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'var(--color-bg)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
          <p style={{ marginBottom: '0.5rem', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
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

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: `140px repeat(${selected.length}, 1fr)`,
        gap: '1px',
        background: 'var(--color-border)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden'
      }}>
        {/* Header Row */}
        <div style={{ background: 'var(--color-surface)', padding: '0.75rem 1rem', fontWeight: 500, color: 'var(--color-text-muted)', fontSize: '0.6875rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Metric
        </div>
        {selected.map(inst => (
          <div key={inst.instance_type} style={{ background: 'var(--color-surface)', padding: '0.75rem 1rem', position: 'relative' }}>
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
                fontSize: '1rem',
                lineHeight: 1
              }}
              title="Remove"
            >
              ×
            </button>
            <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>{inst.instance_type}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{inst.arch}</div>
          </div>
        ))}

        {/* Specs Row */}
        <div style={{ background: 'var(--color-surface)', padding: '0.75rem 1rem', color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>
          Specs
        </div>
        {selected.map(inst => (
          <div key={inst.instance_type} style={{ background: 'var(--color-surface)', padding: '0.75rem 1rem', fontSize: '0.8125rem' }}>
            {inst.vcpu} vCPU<br />
            {inst.ram_gb} GB RAM<br />
            {inst.disk_gb} GB Disk
          </div>
        ))}

        {/* Price Row */}
        <div style={{ background: 'var(--color-surface)', padding: '0.75rem 1rem', color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>
          Price
        </div>
        {selected.map(inst => (
          <div key={inst.instance_type} style={{ background: 'var(--color-surface)', padding: '0.75rem 1rem', fontSize: '0.8125rem' }}>
            <div>{formatCurrency(inst.price_monthly)}/mo</div>
            <div style={{ color: 'var(--color-text-muted)' }}>
              {formatCurrency(inst.price_hourly)}/hr
            </div>
          </div>
        ))}

        {/* CPU Single Row */}
        <div style={{ background: 'var(--color-surface)', padding: '0.75rem 1rem', color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>
          CPU Single
        </div>
        {selected.map(inst => {
          const value = inst.metrics?.cpu_single_events || 0
          const best = getBest('cpu_single_events', true)
          const isBest = value === best && value > 0
          return (
            <div key={inst.instance_type} style={{ 
              background: isBest ? 'rgba(139, 92, 246, 0.15)' : 'var(--color-surface)', 
              padding: '0.75rem 1rem',
              fontFamily: 'var(--font-mono)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ScoreBar value={inst.single_core_score} />
                <span style={{ fontWeight: isBest ? 600 : 400 }}>
                  {formatNumber(value)}
                </span>
                {isBest && <span style={{ color: 'var(--color-primary-light)', fontSize: '0.75rem' }}>★</span>}
              </div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                events/sec
              </div>
            </div>
          )
        })}

        {/* CPU Multi Row */}
        <div style={{ background: 'var(--color-surface)', padding: '0.75rem 1rem', color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>
          CPU Multi
        </div>
        {selected.map(inst => {
          const value = inst.metrics?.cpu_multi_events || 0
          const best = getBest('cpu_multi_events', true)
          const isBest = value === best && value > 0
          return (
            <div key={inst.instance_type} style={{ 
              background: isBest ? 'rgba(139, 92, 246, 0.15)' : 'var(--color-surface)', 
              padding: '0.75rem 1rem',
              fontFamily: 'var(--font-mono)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ScoreBar value={inst.multi_core_score} />
                <span style={{ fontWeight: isBest ? 600 : 400 }}>
                  {formatNumber(value)}
                </span>
                {isBest && <span style={{ color: 'var(--color-primary-light)', fontSize: '0.75rem' }}>★</span>}
              </div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                events/sec
              </div>
            </div>
          )
        })}

        {/* Memory Row */}
        <div style={{ background: 'var(--color-surface)', padding: '0.75rem 1rem', color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>
          Memory
        </div>
        {selected.map(inst => {
          const value = inst.metrics?.memory_mib_per_sec || 0
          const best = getBest('memory_mib_per_sec', true)
          const isBest = value === best && value > 0
          return (
            <div key={inst.instance_type} style={{ 
              background: isBest ? 'rgba(139, 92, 246, 0.15)' : 'var(--color-surface)', 
              padding: '0.75rem 1rem',
              fontFamily: 'var(--font-mono)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ScoreBar value={inst.memory_score} />
                <span style={{ fontWeight: isBest ? 600 : 400 }}>
                  {Math.round(value)}
                </span>
                {isBest && <span style={{ color: 'var(--color-primary-light)', fontSize: '0.75rem' }}>★</span>}
              </div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                MiB/s
              </div>
            </div>
          )
        })}

        {/* Disk IOPS Row */}
        <div style={{ background: 'var(--color-surface)', padding: '0.75rem 1rem', color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>
          Disk IOPS
        </div>
        {selected.map(inst => {
          const value = inst.metrics?.disk_iops || 0
          const best = getBest('disk_iops', true)
          const isBest = value === best && value > 0
          return (
            <div key={inst.instance_type} style={{ 
              background: isBest ? 'rgba(139, 92, 246, 0.15)' : 'var(--color-surface)', 
              padding: '0.75rem 1rem',
              fontFamily: 'var(--font-mono)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ScoreBar value={inst.disk_score} />
                <span style={{ fontWeight: isBest ? 600 : 400 }}>
                  {formatNumber(value)}
                </span>
                {isBest && <span style={{ color: 'var(--color-primary-light)', fontSize: '0.75rem' }}>★</span>}
              </div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                read IOPS
              </div>
            </div>
          )
        })}

        {/* Overall Score Row */}
        <div style={{ background: 'var(--color-surface)', padding: '0.75rem 1rem', color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>
          Overall
        </div>
        {selected.map(inst => {
          const value = inst.overall_score
          const best = getBest('overall_score')
          const isBest = value === best && value > 0
          return (
            <div key={inst.instance_type} style={{ 
              background: isBest ? 'rgba(139, 92, 246, 0.15)' : 'var(--color-surface)', 
              padding: '0.75rem 1rem',
              fontFamily: 'var(--font-mono)'
            }}>
              <span style={{ fontWeight: isBest ? 600 : 400, fontSize: '1.125rem' }}>
                {value.toFixed(0)}/100
              </span>
              {isBest && <span style={{ color: 'var(--color-primary-light)', fontSize: '0.75rem', marginLeft: '0.5rem' }}>★</span>}
            </div>
          )
        })}

        {/* Value Row */}
        <div style={{ background: 'var(--color-surface)', padding: '0.75rem 1rem', color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>
          Value
        </div>
        {selected.map(inst => {
          const value = inst.cpu_value_monthly
          const best = getBest('cpu_value_monthly')
          const isBest = value === best && value > 0
          return (
            <div key={inst.instance_type} style={{ 
              background: isBest ? 'rgba(139, 92, 246, 0.15)' : 'var(--color-surface)', 
              padding: '0.75rem 1rem',
              fontFamily: 'var(--font-mono)'
            }}>
              <span style={{ fontWeight: isBest ? 600 : 400, color: 'var(--color-primary-light)' }}>
                {value.toFixed(1)}
              </span>
              <div style={{ fontSize: '0.6875rem', color: 'var(--color-text-muted)' }}>
                pts/{currencySymbol}/mo
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default InstanceComparison
