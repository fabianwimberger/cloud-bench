import { useEffect, useRef, useMemo } from 'react'
import { Chart, registerables } from 'chart.js'
import ScoreBar from './ScoreBar'
import ProviderBadge from './ProviderBadge'

Chart.register(...registerables)

function InstanceHistory({ instanceType, historyEntry, historyError, onClose, currency }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

  // Calculate relative scores where best score for each metric across all runs = 100%
  const runsWithRelativeScores = useMemo(() => {
    if (!historyEntry?.runs?.length) return []

    const runs = [...historyEntry.runs].sort(
      (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
    )

    const maxMetrics = {
      cpu_single: Math.max(...runs.map(r => r.metrics?.cpu_single_raw || 0)),
      cpu_multi: Math.max(...runs.map(r => r.metrics?.cpu_multi_raw || 0)),
      memory: Math.max(...runs.map(r => r.metrics?.mem_throughput_raw || 0)),
      disk: Math.max(...runs.map(r => r.metrics?.disk_iops_raw || 0)),
    }

    return runs.map(run => ({
      ...run,
      relative_scores: {
        single_core: maxMetrics.cpu_single > 0
          ? ((run.metrics?.cpu_single_raw || 0) / maxMetrics.cpu_single) * 100
          : 0,
        multi_core: maxMetrics.cpu_multi > 0
          ? ((run.metrics?.cpu_multi_raw || 0) / maxMetrics.cpu_multi) * 100
          : 0,
        memory: maxMetrics.memory > 0
          ? ((run.metrics?.mem_throughput_raw || 0) / maxMetrics.memory) * 100
          : 0,
        disk: maxMetrics.disk > 0
          ? ((run.metrics?.disk_iops_raw || 0) / maxMetrics.disk) * 100
          : 0,
      }
    }))
  }, [historyEntry])

  useEffect(() => {
    if (!chartRef.current || !runsWithRelativeScores.length) return

    chartInstance.current?.destroy()

    const labels = runsWithRelativeScores.map(r =>
      new Date(r.timestamp).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: '2-digit',
      })
    )

    // Compute dynamic y-axis range based on actual data
    const allValues = runsWithRelativeScores.flatMap(r => [
      r.relative_scores?.single_core ?? 0,
      r.relative_scores?.multi_core ?? 0,
      r.relative_scores?.memory ?? 0,
      r.relative_scores?.disk ?? 0,
    ])
    const dataMin = Math.min(...allValues)
    const dataMax = Math.max(...allValues)
    const range = dataMax - dataMin
    // Add 20% padding below, round down to nearest 5, ensure min range of 10
    const paddedMin = Math.max(0, Math.floor((dataMin - Math.max(range * 0.2, 2)) / 5) * 5)
    const yMin = Math.min(paddedMin, 90) // never start above 90
    const yMax = Math.min(100, Math.ceil((dataMax + Math.max(range * 0.1, 1)) / 5) * 5)

    const datasets = [
      {
        label: 'Single Core',
        data: runsWithRelativeScores.map(r => r.relative_scores?.single_core ?? 0),
        borderColor: '#8b5cf6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Multi Core',
        data: runsWithRelativeScores.map(r => r.relative_scores?.multi_core ?? 0),
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Memory',
        data: runsWithRelativeScores.map(r => r.relative_scores?.memory ?? 0),
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Disk',
        data: runsWithRelativeScores.map(r => r.relative_scores?.disk ?? 0),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ]

    chartInstance.current = new Chart(chartRef.current, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#a0a0b0',
              font: { size: 11, family: 'Inter' },
              usePointStyle: true,
              pointStyle: 'circle',
              padding: 16,
            },
          },
          tooltip: {
            backgroundColor: '#1a1a24',
            titleColor: '#e8e8ef',
            bodyColor: '#a0a0b0',
            borderColor: '#2a2a3c',
            borderWidth: 1,
            callbacks: {
              afterBody(items) {
                const idx = items[0]?.dataIndex
                if (idx == null) return ''
                const run = runsWithRelativeScores[idx]
                const m = run.metrics || {}
                return [
                  '',
                  `CPU Single: ${Math.round(m.cpu_single_raw || 0).toLocaleString()} evt/s`,
                  `CPU Multi: ${Math.round(m.cpu_multi_raw || 0).toLocaleString()} evt/s`,
                  `Memory: ${Math.round(m.mem_throughput_raw || 0)} MiB/s`,
                  `Disk: ${Math.round(m.disk_iops_raw || 0).toLocaleString()} IOPS`,
                ]
              },
            },
          },
        },
        scales: {
          y: {
            min: yMin,
            max: yMax,
            grid: { color: '#2a2a3c' },
            ticks: { color: '#6b6b7b', font: { size: 11, family: 'Inter' } },
          },
          x: {
            grid: { display: false },
            ticks: { color: '#6b6b7b', font: { size: 11, family: 'Inter' } },
          },
        },
      },
    })

    return () => chartInstance.current?.destroy()
  }, [runsWithRelativeScores])

  if (!historyEntry) {
    return (
      <div className="history-overlay" onClick={onClose}>
        <div className="history-panel" onClick={e => e.stopPropagation()}>
          <div className="history-header">
            <div>
              <strong style={{ fontSize: '1.125rem' }}>{instanceType}</strong>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem', marginTop: '0.25rem' }}>
                {historyError
                  ? `Failed to load history: ${historyError}`
                  : 'No historical data available for this instance.'}
              </p>
            </div>
            <button className="btn btn-ghost btn-small" onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    )
  }

  const specs = historyEntry.specs || {}
  const displayRuns = [...runsWithRelativeScores].sort(
    (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
  )

  const displayCurrency = currency?.displayCurrency || 'EUR'
  const fp = currency?.formatPrice || (v => `${displayCurrency === 'EUR' ? '\u20AC' : '$'}${v.toFixed(2)}`)
  // Each history run carries its own native currency (missing on runs
  // recorded before this field existed, which were already stored as USD).
  const fpRun = (amount, runCurrency) => fp(amount, runCurrency || 'USD')

  return (
    <div className="history-overlay" onClick={onClose}>
      <div className="history-panel" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="history-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <strong style={{ fontSize: '1.125rem' }}>{instanceType}</strong>
            <ProviderBadge provider={historyEntry.provider} />
            {(specs.vcpu || specs.ram_gb || specs.disk_gb) && (
              <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                {specs.vcpu && `${specs.vcpu} vCPU`}
                {specs.ram_gb && ` \u00B7 ${specs.ram_gb} GB`}
                {specs.disk_gb && ` \u00B7 ${specs.disk_gb} GB disk`}
              </span>
            )}
          </div>
          <button className="btn btn-ghost btn-small" onClick={onClose}>Close</button>
        </div>

        {/* Chart */}
        {historyEntry.runs.length > 0 && (
          <div style={{ height: '280px', marginBottom: '1.5rem' }}>
            <canvas ref={chartRef}></canvas>
          </div>
        )}

        {/* Runs table */}
        <div className="table-container">
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Region</th>
                <th className="cell-numeric">CPU Single</th>
                <th className="cell-numeric">CPU Multi</th>
                <th className="cell-numeric">Memory</th>
                <th className="cell-numeric">Disk IOPS</th>
                <th className="cell-numeric">Monthly Price</th>
              </tr>
            </thead>
            <tbody>
              {displayRuns.map((run, i) => (
                <tr key={i}>
                  <td>
                    {new Date(run.timestamp).toLocaleDateString(undefined, {
                      year: 'numeric', month: 'short', day: 'numeric',
                    })}
                  </td>
                  <td>
                    <span className="arch-badge">{run.region || '—'}</span>
                  </td>
                  <td className="cell-numeric">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <ScoreBar value={run.relative_scores?.single_core ?? 0} />
                      <span>{Math.round(run.metrics?.cpu_single_raw || 0).toLocaleString()}</span>
                    </div>
                  </td>
                  <td className="cell-numeric">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <ScoreBar value={run.relative_scores?.multi_core ?? 0} />
                      <span>{Math.round(run.metrics?.cpu_multi_raw || 0).toLocaleString()}</span>
                    </div>
                  </td>
                  <td className="cell-numeric">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <ScoreBar value={run.relative_scores?.memory ?? 0} />
                      <span>{Math.round(run.metrics?.mem_throughput_raw || 0).toLocaleString()} <span className="metric-unit">MiB/s</span></span>
                    </div>
                  </td>
                  <td className="cell-numeric">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <ScoreBar value={run.relative_scores?.disk ?? 0} />
                      <span>{Math.round(run.metrics?.disk_iops_raw || 0).toLocaleString()}</span>
                    </div>
                  </td>
                  <td className="price-cell cell-numeric">
                    {run.pricing?.monthly != null ? fpRun(run.pricing.monthly, run.currency) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="table-note">
          Showing {displayRuns.length} historical run{displayRuns.length !== 1 ? 's' : ''} for {instanceType}.
          <br />
          Chart shows relative performance (best run = 100). Table shows raw metrics from each run.
        </p>
      </div>
    </div>
  )
}

export default InstanceHistory
