function StatsOverview({ data, currency }) {
  const ranking = data?.ranking || []
  const metadata = data?.metadata || {}

  if (ranking.length === 0) return null

  const bestValue = [...ranking].sort((a, b) => b.cpu_value_monthly - a.cpu_value_monthly)[0]
  const bestPerformance = ranking.reduce((best, current) =>
    current.overall_score > best.overall_score ? current : best
  )
  const cheapest = ranking.reduce((cheap, current) =>
    current.price_monthly < cheap.price_monthly ? current : cheap
  )
  const fastestCpu = ranking.reduce((fastest, current) =>
    (current.metrics?.cpu_single_events || 0) > (fastest.metrics?.cpu_single_events || 0) ? current : fastest
  )

  const displayCurrency = currency?.displayCurrency || metadata.currency || 'EUR'
  const currencySymbol = displayCurrency === 'EUR' ? '\u20AC' : '$'
  const fp = currency?.formatPrice || ((v) => `${currencySymbol}${v.toFixed(2)}`)

  const stats = [
    {
      label: 'Best Value',
      value: bestValue.instance_type,
      subtext: `${bestValue.cpu_value_monthly.toFixed(1)} pts/${currencySymbol}`
    },
    {
      label: 'Top Performance',
      value: bestPerformance.instance_type,
      subtext: `${bestPerformance.overall_score.toFixed(0)}/100 overall`
    },
    {
      label: 'Fastest CPU',
      value: fastestCpu.instance_type,
      subtext: `${Math.round(fastestCpu.metrics?.cpu_single_events || 0).toLocaleString()} events/sec`
    },
    {
      label: 'Cheapest',
      value: fp(cheapest.price_monthly),
      subtext: `${cheapest.instance_type} / month`
    },
    {
      label: 'Instances',
      value: ranking.length,
      subtext: 'Tested configurations'
    },
    {
      label: 'Providers',
      value: [...new Set(ranking.map(r => r.provider))].filter(Boolean).map(p => p.length <= 3 ? p.toUpperCase() : p.charAt(0).toUpperCase() + p.slice(1)).join(', ') || 'Unknown',
      subtext: [...new Set(ranking.map(r => r.region))].filter(Boolean).join(', ')
    },
  ]

  return (
    <div className="grid grid-3" style={{ marginBottom: '1rem' }}>
      {stats.map((stat, index) => (
        <div key={index} className="stat-card">
          <div className="value">{stat.value}</div>
          <div className="label">{stat.label}</div>
          {stat.subtext && (
            <div className="subtext">{stat.subtext}</div>
          )}
        </div>
      ))}
    </div>
  )
}

export default StatsOverview
