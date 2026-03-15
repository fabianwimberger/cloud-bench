import { useEffect, useRef } from 'react'
import { Chart, registerables } from 'chart.js'
import ScoreBar from './ScoreBar'
import ProviderBadge from './ProviderBadge'

Chart.register(...registerables)

function InstanceHistory({ instanceType, historyEntry, onClose, currency }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

  useEffect(() => {
    if (!chartRef.current || !historyEntry?.runs?.length) return

    chartInstance.current?.destroy()

    const runs = [...historyEntry.runs].sort(
      (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
    )

    const labels = runs.map(r =>
      new Date(r.timestamp).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: '2-digit',
      })
    )

    const datasets = [
      {
        label: 'Single Core',
        data: runs.map(r => r.scores?.single_core ?? 0),
        borderColor: '#8b5cf6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Multi Core',
        data: runs.map(r => r.scores?.multi_core ?? 0),
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Memory',
        data: runs.map(r => r.scores?.memory ?? 0),
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Disk',
        data: runs.map(r => r.scores?.disk ?? 0),
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
                const run = runs[idx]
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
            beginAtZero: true,
            max: 100,
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
  }, [historyEntry])

  if (!historyEntry) {
    return (
      <div className="history-overlay" onClick={onClose}>
        <div className="history-panel" onClick={e => e.stopPropagation()}>
          <div className="history-header">
            <div>
              <strong style={{ fontSize: '1.125rem' }}>{instanceType}</strong>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem', marginTop: '0.25rem' }}>
                No historical data available for this instance.
              </p>
            </div>
            <button className="btn btn-ghost btn-small" onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    )
  }

  const specs = historyEntry.specs || {}
  const runs = [...historyEntry.runs].sort(
    (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
  )

  const displayCurrency = currency?.displayCurrency || 'EUR'
  const fp = currency?.formatPrice || (v => `${displayCurrency === 'EUR' ? '\u20AC' : '$'}${v.toFixed(2)}`)

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
                <th className="cell-numeric">Single Core</th>
                <th className="cell-numeric">Multi Core</th>
                <th className="cell-numeric">Memory</th>
                <th className="cell-numeric">Disk</th>
                <th className="cell-numeric">Overall</th>
                <th className="cell-numeric">Monthly Price</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run, i) => (
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
                      <ScoreBar value={run.scores?.single_core ?? 0} />
                      <span>{(run.scores?.single_core ?? 0).toFixed(0)}</span>
                    </div>
                  </td>
                  <td className="cell-numeric">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <ScoreBar value={run.scores?.multi_core ?? 0} />
                      <span>{(run.scores?.multi_core ?? 0).toFixed(0)}</span>
                    </div>
                  </td>
                  <td className="cell-numeric">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <ScoreBar value={run.scores?.memory ?? 0} />
                      <span>{(run.scores?.memory ?? 0).toFixed(0)}</span>
                    </div>
                  </td>
                  <td className="cell-numeric">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <ScoreBar value={run.scores?.disk ?? 0} />
                      <span>{(run.scores?.disk ?? 0).toFixed(0)}</span>
                    </div>
                  </td>
                  <td className="cell-numeric" style={{ color: 'var(--color-primary-light)', fontWeight: 500 }}>
                    {(run.scores?.overall ?? 0).toFixed(0)}
                  </td>
                  <td className="price-cell cell-numeric">
                    {run.pricing?.monthly != null ? fp(run.pricing.monthly) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="table-note">
          Showing {runs.length} historical run{runs.length !== 1 ? 's' : ''} for {instanceType}.
        </p>
      </div>
    </div>
  )
}

export default InstanceHistory
