import { useState, useEffect, useCallback, useMemo } from 'react'
import Header from './components/Header'
import StatsOverview from './components/StatsOverview'
import InstanceFilter from './components/InstanceFilter'
import InstanceComparison from './components/InstanceComparison'
import ComparisonTable from './components/ComparisonTable'
import ComparisonCharts from './components/ComparisonCharts'
import InstanceBreakdown from './components/InstanceBreakdown'
import Footer from './components/Footer'
import './App.css'

const DataAPI = {
  async loadManifest() {
    const response = await fetch('./data/manifest.json')
    if (!response.ok) throw new Error('Failed to load manifest')
    return await response.json()
  },

  async loadSummary(filename = 'benchmark-data.json') {
    const response = await fetch(`./data/${filename}`)
    if (!response.ok) throw new Error(`Failed to load ${filename}`)
    return await response.json()
  },

  async loadDetail(filename) {
    const response = await fetch(`./data/${filename}`)
    if (!response.ok) throw new Error(`Failed to load ${filename}`)
    return await response.json()
  }
}

function transformData(data) {
  if (!data || data.schema_version !== '2.0') {
    throw new Error('Unsupported data format')
  }

  const instances = data.summary?.instances || []
  const labels = data.summary?.labels || []
  const charts = data.summary?.charts || {}

  return {
    metadata: {
      ...data.metadata,
      currency: data.metadata?.currency || 'EUR',
    },
    ranking: instances.map(inst => ({
      instance_type: inst.id,
      display_name: inst.name,
      arch: inst.specs?.arch || 'Unknown',
      vcpu: inst.specs?.vcpu || 0,
      ram_gb: inst.specs?.ram_gb || 0,
      disk_gb: inst.specs?.disk_gb || 0,
      price_hourly: inst.pricing?.hourly || 0,
      price_monthly: inst.pricing?.monthly || 0,
      single_core_score: inst.scores?.single_core || 0,
      multi_core_score: inst.scores?.multi_core || 0,
      memory_score: inst.scores?.memory || 0,
      disk_score: inst.scores?.disk || 0,
      overall_score: inst.scores?.overall || 0,
      cpu_value_monthly: inst.value || 0,
      // Include raw metrics
      metrics: inst.metrics || {
        cpu_single_events: 0,
        cpu_multi_events: 0,
        memory_mib_per_sec: 0,
        disk_iops: 0,
      }
    })),
    charts: {
      single_core: { labels, values: charts.single_core || [] },
      multi_core: { labels, values: charts.multi_core || [] },
      memory: { labels, values: charts.memory || [] },
      disk: { labels, values: charts.disk || [] },
      value: { labels, values: charts.value || [] },
    }
  }
}

function filterData(ranking, filters) {
  if (!ranking) return []
  
  return ranking.filter(inst => {
    if (filters.arch && inst.arch !== filters.arch) return false
    if (filters.min_vcpu && inst.vcpu < parseInt(filters.min_vcpu)) return false
    if (filters.min_ram && inst.ram_gb < parseInt(filters.min_ram)) return false
    if (inst.price_monthly > filters.max_monthly_price) return false
    if (filters.search && !inst.instance_type.toLowerCase().includes(filters.search.toLowerCase())) return false
    return true
  })
}

function App() {
  const [data, setData] = useState(null)
  const [manifest, setManifest] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Global error handler for uncaught promise rejections
  useEffect(() => {
    const handleUnhandledRejection = (event) => {
      console.error('Unhandled promise rejection:', event.reason)
      setError(`Unexpected error: ${event.reason?.message || 'Unknown error'}`)
      event.preventDefault()
    }
    window.addEventListener('unhandledrejection', handleUnhandledRejection)
    return () => window.removeEventListener('unhandledrejection', handleUnhandledRejection)
  }, [])
  
  const [selectedRunId, setSelectedRunId] = useState('latest')
  
  const [filters, setFilters] = useState({
    arch: '',
    min_vcpu: '',
    min_ram: '',
    max_monthly_price: 100,
    search: ''
  })
  
  const [selectedForComparison, setSelectedForComparison] = useState([])

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    try {
      setLoading(true)
      
      const manifestData = await DataAPI.loadManifest()
      setManifest(manifestData)
      
      const latest = manifestData.runs?.[0]
      if (!latest) throw new Error('No runs found in manifest')
      
      const summary = await DataAPI.loadSummary(latest.files?.summary)
      const transformed = transformData(summary)
      setData(transformed)
      
      setFilters(prev => ({
        ...prev,
        max_monthly_price: Math.ceil(Math.max(...transformed.ranking.map(r => r.price_monthly)) * 1.2)
      }))
      
      setError(null)
    } catch (err) {
      console.error('Failed to fetch benchmark data:', err)
      setError(err.message)
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  const loadHistoricalRun = useCallback(async (runId) => {
    if (!manifest || runId === 'latest') {
      await loadInitialData()
      return
    }

    try {
      setLoading(true)
      const run = manifest.runs.find(r => r.id === runId)
      if (!run) throw new Error('Run not found')

      const summary = await DataAPI.loadSummary(run.files?.summary)
      const transformed = transformData(summary)
      setData(transformed)
      setSelectedForComparison([])
      setError(null)
    } catch (err) {
      console.error('Failed to load historical data:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [manifest])

  const handleRunChange = (runId) => {
    setSelectedRunId(runId)
    if (runId === 'latest') {
      loadInitialData()
    } else {
      loadHistoricalRun(runId)
    }
  }

  const filteredRanking = useMemo(() => {
    return filterData(data?.ranking, filters)
  }, [data?.ranking, filters])

  const filteredCharts = useMemo(() => {
    if (!data?.charts || !filteredRanking.length) return null
    
    const filteredTypes = new Set(filteredRanking.map(r => r.instance_type))
    const filteredIndices = data.ranking
      .map((r, i) => filteredTypes.has(r.instance_type) ? i : -1)
      .filter(i => i !== -1)
    
    return {
      single_core: {
        labels: filteredIndices.map(i => data.charts.single_core.labels[i]),
        values: filteredIndices.map(i => data.charts.single_core.values[i])
      },
      multi_core: {
        labels: filteredIndices.map(i => data.charts.multi_core.labels[i]),
        values: filteredIndices.map(i => data.charts.multi_core.values[i])
      },
      memory: {
        labels: filteredIndices.map(i => data.charts.memory.labels[i]),
        values: filteredIndices.map(i => data.charts.memory.values[i])
      },
      disk: {
        labels: filteredIndices.map(i => data.charts.disk.labels[i]),
        values: filteredIndices.map(i => data.charts.disk.values[i])
      },
      value: {
        labels: filteredIndices.map(i => data.charts.value.labels[i]),
        values: filteredIndices.map(i => data.charts.value.values[i])
      }
    }
  }, [data?.charts, data?.ranking, filteredRanking])

  const toggleInstanceSelection = (instanceType) => {
    setSelectedForComparison(prev => {
      if (prev.includes(instanceType)) {
        return prev.filter(id => id !== instanceType)
      }
      if (prev.length >= 3) return prev
      return [...prev, instanceType]
    })
  }

  if (loading && !data) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div className="app">
      <Header metadata={data?.metadata} />
      
      <div className="container">
        {error && (
          <div className="card" style={{ marginBottom: '1rem', borderColor: 'var(--color-warning)', backgroundColor: 'rgba(245, 158, 11, 0.1)' }}>
            <p style={{ margin: 0, color: 'var(--color-warning)' }}>
              Error loading data: {error}
            </p>
          </div>
        )}

        {manifest && manifest.runs && manifest.runs.length > 1 && (
          <div className="run-selector">
            <div className="filter-group">
              <label>Run</label>
              <select
                className="filter-select"
                value={selectedRunId}
                onChange={(e) => handleRunChange(e.target.value)}
                style={{ minWidth: '280px' }}
              >
                <option value="latest">Latest ({manifest.runs[0]?.region?.toUpperCase()})</option>
                {manifest.runs.map((run) => (
                  <option key={run.id} value={run.id}>
                    {new Date(run.timestamp).toLocaleString()} ({run.provider?.toUpperCase()} / {run.region?.toUpperCase()})
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              {manifest.runs.length} historical run{manifest.runs.length !== 1 ? 's' : ''}
              {loading && <span style={{ marginLeft: '10px' }}>Loading...</span>}
            </div>
          </div>
        )}

        <StatsOverview data={data} />
        
        <InstanceFilter 
          ranking={data?.ranking} 
          filters={filters} 
          onFilterChange={setFilters} 
        />

        {selectedForComparison.length > 0 && (
          <InstanceComparison
            ranking={data?.ranking}
            metadata={data?.metadata}
            selectedInstances={selectedForComparison}
            onClear={setSelectedForComparison}
          />
        )}

        <ComparisonTable 
          ranking={filteredRanking} 
          metadata={data?.metadata}
          selectedForComparison={selectedForComparison}
          onToggleSelection={toggleInstanceSelection}
          maxSelections={3}
        />
        
        <ComparisonCharts charts={filteredCharts} />
        <InstanceBreakdown ranking={filteredRanking} metadata={data?.metadata} />
        <Footer metadata={data?.metadata} />
      </div>
    </div>
  )
}

export default App
