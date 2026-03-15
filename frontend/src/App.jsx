import { useState, useEffect, useCallback, useMemo } from 'react'
import Header from './components/Header'
import StatsOverview from './components/StatsOverview'
import InstanceFilter from './components/InstanceFilter'
import InstanceComparison from './components/InstanceComparison'
import ComparisonTable from './components/ComparisonTable'
import ComparisonCharts from './components/ComparisonCharts'
import InstanceBreakdown from './components/InstanceBreakdown'
import InstanceHistory from './components/InstanceHistory'
import Footer from './components/Footer'
import './App.css'

const DataAPI = {
  async loadBenchmarkData() {
    const response = await fetch('./data/benchmark-data.json')
    if (!response.ok) throw new Error('Failed to load benchmark data')
    return await response.json()
  },

  async loadHistory() {
    const response = await fetch('./data/history.json')
    if (!response.ok) throw new Error('Failed to load history')
    return await response.json()
  }
}

function parseExprFilter(expr, value) {
  if (!expr || expr.trim() === '') return true
  const match = expr.trim().match(/^([<>]=?|=)?\s*(\d+\.?\d*)$/)
  if (!match) return true
  const op = match[1] || '='
  const threshold = parseFloat(match[2])
  if (op === '>') return value > threshold
  if (op === '>=') return value >= threshold
  if (op === '<') return value < threshold
  if (op === '<=') return value <= threshold
  if (op === '=') return value === threshold
  return true
}

function transformData(data) {
  if (!data || data.schema_version !== '2.0') {
    throw new Error('Unsupported data format')
  }

  const instances = data.summary?.instances || []

  return {
    metadata: {
      ...data.metadata,
      currency: data.metadata?.currency || 'USD',
      exchange_rates: data.metadata?.exchange_rates || null,
    },
    ranking: instances.map(inst => ({
      instance_type: inst.id,
      display_name: inst.name,
      arch: inst.specs?.arch || 'X86',
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
      provider: inst.provider || data.metadata?.provider || '',
      region: inst.region || data.metadata?.region || '',
      metrics: inst.metrics || {
        cpu_single_events: 0,
        cpu_multi_events: 0,
        memory_mib_per_sec: 0,
        disk_iops: 0,
      }
    })),
  }
}

function filterData(ranking, filters) {
  if (!ranking) return []

  return ranking.filter(inst => {
    if (filters.arch && inst.arch !== filters.arch) return false
    if (filters.provider && inst.provider !== filters.provider) return false
    if (!parseExprFilter(filters.vcpu, inst.vcpu)) return false
    if (!parseExprFilter(filters.ram, inst.ram_gb)) return false
    if (!parseExprFilter(filters.disk, inst.disk_gb)) return false
    if (inst.price_monthly > filters.max_monthly_price) return false
    if (inst.price_monthly < filters.min_monthly_price) return false
    if (filters.search && !inst.instance_type.toLowerCase().includes(filters.search.toLowerCase())) return false
    return true
  })
}

function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [displayCurrency, setDisplayCurrency] = useState('USD')

  useEffect(() => {
    const handleUnhandledRejection = (event) => {
      console.error('Unhandled promise rejection:', event.reason)
      setError(`Unexpected error: ${event.reason?.message || 'Unknown error'}`)
      event.preventDefault()
    }
    window.addEventListener('unhandledrejection', handleUnhandledRejection)
    return () => window.removeEventListener('unhandledrejection', handleUnhandledRejection)
  }, [])

  const [filters, setFilters] = useState({
    arch: '',
    provider: '',
    vcpu: '',
    ram: '',
    disk: '',
    min_monthly_price: 0,
    max_monthly_price: 100,
    search: ''
  })

  const [selectedForComparison, setSelectedForComparison] = useState([])
  const [selectedHistoryInstance, setSelectedHistoryInstance] = useState(null)
  const [historyData, setHistoryData] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)

      const summary = await DataAPI.loadBenchmarkData()
      const transformed = transformData(summary)
      setData(transformed)

      setDisplayCurrency(transformed.metadata?.currency || 'USD')

      setFilters(prev => ({
        ...prev,
        min_monthly_price: 0,
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

  const filteredRanking = useMemo(() => {
    return filterData(data?.ranking, filters)
  }, [data?.ranking, filters])

  const filteredCharts = useMemo(() => {
    if (!filteredRanking.length) return null

    const sorted = [...filteredRanking]
    const buildChart = (scoreFn) => {
      const pairs = sorted.map(r => [r.instance_type, scoreFn(r)])
      pairs.sort((a, b) => b[1] - a[1])
      return { labels: pairs.map(p => p[0]), values: pairs.map(p => p[1]) }
    }

    return {
      single_core: buildChart(r => r.single_core_score),
      multi_core: buildChart(r => r.multi_core_score),
      memory: buildChart(r => r.memory_score),
      disk: buildChart(r => r.disk_score),
      value: buildChart(r => r.cpu_value_monthly),
    }
  }, [filteredRanking])

  const toggleInstanceSelection = (instanceType) => {
    setSelectedForComparison(prev => {
      if (prev.includes(instanceType)) {
        return prev.filter(id => id !== instanceType)
      }
      if (prev.length >= 3) return prev
      return [...prev, instanceType]
    })
  }

  const handleSelectHistory = useCallback(async (instanceType) => {
    setSelectedHistoryInstance(instanceType)
    if (!historyData) {
      try {
        const data = await DataAPI.loadHistory()
        setHistoryData(data)
      } catch (err) {
        console.error('Failed to load history:', err)
        setHistoryData({ instances: {} })
      }
    }
  }, [historyData])

  const handleCloseHistory = useCallback(() => {
    setSelectedHistoryInstance(null)
  }, [])

  const nativeCurrency = data?.metadata?.currency || 'USD'
  const exchangeRates = data?.metadata?.exchange_rates

  const convertAmount = (amount) => {
    if (displayCurrency === nativeCurrency || !exchangeRates) {
      return amount
    }
    if (nativeCurrency === 'EUR' && displayCurrency === 'USD') {
      return amount * (exchangeRates.eur_to_usd || 1)
    }
    if (nativeCurrency === 'USD' && displayCurrency === 'EUR') {
      return amount * (exchangeRates.usd_to_eur || 1)
    }
    return amount
  }

  const currencyProps = {
    displayCurrency,
    nativeCurrency,
    exchangeRates,
    formatPrice: (amount) => {
      const converted = convertAmount(amount)
      const symbol = displayCurrency === 'EUR' ? '\u20AC' : '$'
      return `${symbol}${converted.toFixed(2)}`
    },
    formatPriceRaw: (amount) => convertAmount(amount),
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

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          {data?.metadata?.exchange_rates && (
            <div className="filter-group">
              <label>Currency</label>
              <div style={{ display: 'flex', borderRadius: 'var(--radius-sm)', overflow: 'hidden', border: '1px solid var(--color-border)' }}>
                {['EUR', 'USD'].map(cur => (
                  <button
                    key={cur}
                    onClick={() => setDisplayCurrency(cur)}
                    style={{
                      padding: '0.375rem 0.75rem',
                      border: 'none',
                      background: displayCurrency === cur ? 'var(--color-primary)' : 'var(--color-surface)',
                      color: displayCurrency === cur ? '#fff' : 'var(--color-text-muted)',
                      cursor: 'pointer',
                      fontSize: '0.8125rem',
                      fontWeight: displayCurrency === cur ? 600 : 400,
                    }}
                  >
                    {cur === 'EUR' ? '\u20AC EUR' : '$ USD'}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <StatsOverview data={data} currency={currencyProps} />

        <InstanceFilter
          ranking={data?.ranking}
          filters={filters}
          onFilterChange={setFilters}
          currency={currencyProps}
        />

        {selectedForComparison.length > 0 && (
          <InstanceComparison
            ranking={data?.ranking}
            metadata={data?.metadata}
            selectedInstances={selectedForComparison}
            onClear={setSelectedForComparison}
            currency={currencyProps}
          />
        )}

        <ComparisonTable
          ranking={filteredRanking}
          metadata={data?.metadata}
          selectedForComparison={selectedForComparison}
          onToggleSelection={toggleInstanceSelection}
          maxSelections={3}
          currency={currencyProps}
          onSelectHistory={handleSelectHistory}
        />

        <ComparisonCharts charts={filteredCharts} currency={currencyProps} />
        <InstanceBreakdown ranking={filteredRanking} metadata={data?.metadata} currency={currencyProps} onSelectHistory={handleSelectHistory} />
        <Footer metadata={data?.metadata} />
      </div>

      {selectedHistoryInstance && (
        <InstanceHistory
          instanceType={selectedHistoryInstance}
          historyEntry={historyData?.instances?.[selectedHistoryInstance] || null}
          onClose={handleCloseHistory}
          currency={currencyProps}
        />
      )}
    </div>
  )
}

export default App
