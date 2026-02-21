function StatsOverview({ data }) {
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

  const provider = metadata.provider || 'Cloud'
  const providerDisplay = provider.charAt(0).toUpperCase() + provider.slice(1)
  const currency = metadata.currency || 'EUR'
  const currencySymbol = currency === 'EUR' ? 'EUR' : currency

  const stats = [
    {
      label: 'Best Value',
      value: bestValue.instance_type,
      subtext: `${bestValue.cpu_value_monthly.toFixed(1)} pts/${currencySymbol}`
    },
    {
      label: 'Top Performance',
      value: bestPerformance.instance_type,
      subtext: `${bestPerformance.overall_score.toFixed(0)}/100`
    },
    {
      label: 'Cheapest',
      value: `${currencySymbol}${cheapest.price_monthly}`,
      subtext: cheapest.instance_type
    },
    {
      label: 'Instances Tested',
      value: ranking.length,
      subtext: providerDisplay
    },
  ]

  return (
    <div className="grid grid-4">
      {stats.map((stat, index) => (
        <div key={index} className="stat-card">
          <div className="value">{stat.value}</div>
          <div className="label">{stat.label}</div>
          {stat.subtext && (
            <small style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>
              {stat.subtext}
            </small>
          )}
        </div>
      ))}
    </div>
  )
}

export default StatsOverview
