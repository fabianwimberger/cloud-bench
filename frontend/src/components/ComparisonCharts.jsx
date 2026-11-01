import { useEffect, useRef, useState } from 'react'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const COLORS = ['#8b5cf6', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#ec4899']

const TABS = [
  { id: 'cpu', label: 'CPU' },
  { id: 'memory', label: 'Memory' },
  { id: 'disk', label: 'Disk' },
  { id: 'value', label: 'Value' },
]

const AXIS_COLOR = '#6b6b7b'
const GRID_COLOR = '#2a2a3c'

/** Rounds a chart maximum up to a readable tick, so the last gridline is not
 * an arbitrary value like 162.7. */
function niceMax(value) {
  if (!Number.isFinite(value) || value <= 0) return undefined
  const step = value > 100 ? 20 : value > 20 ? 10 : value > 5 ? 5 : 1
  return Math.ceil(value / step) * step
}

/** Charts shown per tab; each one pulls its dataset out of a chart group. */
function tabCharts(tab, group, currencySymbol) {
  if (tab === 'cpu') {
    return [
      { key: 'single_core', title: 'Single Core Score', max: 100 },
      { key: 'multi_core', title: 'Multi Core Score', max: 100 },
    ]
  }
  if (tab === 'memory') return [{ key: 'memory', title: 'Memory Score', max: 100 }]
  if (tab === 'disk') return [{ key: 'disk', title: 'Disk Score', max: 100 }]
  return [
    {
      key: 'value',
      title: `Value (perf/${currencySymbol})`,
      max: group.value ? niceMax(Math.max(...group.value.values) * 1.05) : undefined,
    },
  ]
}

function HorizontalBarChart({ data, title, max }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    if (!canvasRef.current || !data) return undefined

    const chart = new Chart(canvasRef.current, {
      type: 'bar',
      data: {
        labels: data.labels,
        datasets: [
          {
            data: data.values,
            backgroundColor: COLORS,
            borderRadius: 4,
            borderSkipped: false,
          },
        ],
      },
      options: {
        // Horizontal bars keep instance labels level and readable once a
        // filter lets dozens of instances through.
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: {
            display: true,
            text: title,
            color: '#e8e8ef',
            font: { size: 12, weight: '600', family: 'Inter' },
            padding: { bottom: 12 },
          },
          tooltip: {
            callbacks: {
              label: (item) => String(item.parsed.x),
            },
          },
        },
        scales: {
          x: {
            beginAtZero: true,
            max,
            grid: { color: GRID_COLOR },
            ticks: { color: AXIS_COLOR, font: { size: 11, family: 'Inter' } },
          },
          y: {
            grid: { display: false },
            ticks: {
              color: AXIS_COLOR,
              font: { size: 11, family: 'Inter' },
              autoSkip: false,
            },
          },
        },
      },
    })

    return () => chart.destroy()
  }, [data, title, max])

  return <canvas ref={canvasRef}></canvas>
}

function ComparisonCharts({ charts, currency }) {
  const [activeTab, setActiveTab] = useState('cpu')
  const [scope, setScope] = useState('all')

  // Filters can remove the vCPU group a visitor is looking at; fall back to
  // the whole set instead of showing an empty view.
  const groups = charts?.byVcpu ?? []
  const activeScope =
    scope === 'all' || groups.some((g) => String(g.vcpu) === scope) ? scope : 'all'
  const group = activeScope === 'all'
    ? charts?.all
    : groups.find((g) => String(g.vcpu) === activeScope)?.charts

  if (!charts || !group) return null

  const displayCurrency = currency?.displayCurrency || 'EUR'
  const currencySymbol = displayCurrency === 'EUR' ? '\u20AC' : '$'
  const chartDefs = tabCharts(activeTab, group, currencySymbol)
  // Bars need room: one row per instance, plus axis and title space.
  const height = (labels) => Math.max(200, labels * 26 + 64)

  return (
    <div className="card" style={{ overflow: 'hidden' }}>
      <div className="chart-head">
        <h2 className="card-title" style={{ marginBottom: 0 }}>
          Performance Charts
        </h2>
        {groups.length > 1 && (
          <div className="chart-scope" role="group" aria-label="Instance group">
            <button
              type="button"
              className="chart-scope-btn"
              aria-pressed={activeScope === 'all'}
              onClick={() => setScope('all')}
            >
              All instances
            </button>
            {groups.map((g) => (
              <button
                key={g.vcpu}
                type="button"
                className="chart-scope-btn"
                aria-pressed={activeScope === String(g.vcpu)}
                onClick={() => setScope(String(g.vcpu))}
              >
                {g.vcpu} vCPU
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="chart-tabs" role="tablist" aria-label="Performance metric">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            className="chart-tab"
            aria-selected={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className={`grid ${chartDefs.length > 1 ? 'grid-2' : ''}`}>
        {chartDefs.map((def) => {
          const data = group[def.key]
          if (!data) return null
          return (
            <div key={def.key} className="chart-cell" style={{ height: `${height(data.labels.length)}px` }}>
              <HorizontalBarChart data={data} title={def.title} max={def.max} />
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ComparisonCharts
