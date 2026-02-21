import { useEffect, useRef } from 'react'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

function ComparisonCharts({ charts }) {
  const singleRef = useRef(null)
  const multiRef = useRef(null)
  const memoryRef = useRef(null)
  const diskRef = useRef(null)
  const valueRef = useRef(null)

  const chartInstances = useRef({})

  useEffect(() => {
    if (!charts) return

    Object.values(chartInstances.current).forEach(chart => chart?.destroy())

    const commonOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: '#334155' },
          ticks: { color: '#94a3b8' }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#94a3b8' }
        }
      }
    }

    const colors = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

    const createChart = (ref, data, title, max = 100) => {
      if (!ref.current || !data) return null
      
      return new Chart(ref.current, {
        type: 'bar',
        data: {
          labels: data.labels,
          datasets: [{
            data: data.values,
            backgroundColor: colors,
            borderRadius: 6
          }]
        },
        options: {
          ...commonOptions,
          scales: {
            ...commonOptions.scales,
            y: {
              ...commonOptions.scales.y,
              max: max
            }
          },
          plugins: {
            ...commonOptions.plugins,
            title: {
              display: true,
              text: title,
              color: '#f8fafc',
              font: { size: 14, weight: '600' }
            }
          }
        }
      })
    }

    chartInstances.current.single = createChart(singleRef, charts.single_core, 'Single Core Performance')
    chartInstances.current.multi = createChart(multiRef, charts.multi_core, 'Multi Core Performance')
    chartInstances.current.memory = createChart(memoryRef, charts.memory, 'Memory Throughput')
    chartInstances.current.disk = createChart(diskRef, charts.disk, 'Disk IOPS')
    
    // Value chart - dynamic max
    if (valueRef.current && charts.value) {
      const maxValue = Math.max(...charts.value.values) * 1.1
      chartInstances.current.value = createChart(valueRef, charts.value, 'Value (Perf per €)', maxValue)
    }

    return () => {
      Object.values(chartInstances.current).forEach(chart => chart?.destroy())
    }
  }, [charts])

  if (!charts) return null

  return (
    <div className="card">
      <h2 className="card-title">Performance Charts</h2>
      <div className="grid grid-3" style={{ marginTop: '1rem' }}>
        <div style={{ height: '280px' }}>
          <canvas ref={singleRef}></canvas>
        </div>
        <div style={{ height: '280px' }}>
          <canvas ref={multiRef}></canvas>
        </div>
        <div style={{ height: '280px' }}>
          <canvas ref={memoryRef}></canvas>
        </div>
        <div style={{ height: '280px' }}>
          <canvas ref={diskRef}></canvas>
        </div>
        <div style={{ height: '280px', gridColumn: 'span 2' }}>
          <canvas ref={valueRef}></canvas>
        </div>
      </div>
    </div>
  )
}

export default ComparisonCharts
