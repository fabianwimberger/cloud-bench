function InstanceBreakdown({ ranking, metadata }) {
  if (!ranking || ranking.length === 0) return null

  const byPrice = [...ranking].sort((a, b) => b.price_monthly - a.price_monthly)

  const currency = metadata?.currency || 'EUR'
  const currencySymbol = currency === 'EUR' ? '€' : currency

  return (
    <div className="card">
      <h2 className="card-title">All Instances</h2>

      <div className="grid grid-3">
        {byPrice.map((instance) => (
          <div key={instance.instance_type} className="stat-card" style={{
            textAlign: 'left',
            borderColor: 'var(--color-border)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
              <div>
                <strong style={{ fontSize: '1rem' }}>{instance.instance_type}</strong>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.125rem' }}>
                  {instance.vcpu} vCPU · {instance.ram_gb} GB · {instance.disk_gb} GB
                </div>
              </div>
              <span className="arch-badge">{instance.arch}</span>
            </div>

            <div style={{ fontSize: '0.8125rem', marginTop: '0.5rem', fontFamily: 'var(--font-mono)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ color: 'var(--color-text-muted)' }}>CPU:</span>
                <span>{Math.round(instance.metrics?.cpu_single_events || 0).toLocaleString()} evt/s</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ color: 'var(--color-text-muted)' }}>Memory:</span>
                <span>{Math.round(instance.metrics?.memory_mib_per_sec || 0)} MiB/s</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ color: 'var(--color-text-muted)' }}>Disk:</span>
                <span>{Math.round(instance.metrics?.disk_iops || 0).toLocaleString()} IOPS</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ color: 'var(--color-text-muted)' }}>Score:</span>
                <span>{instance.overall_score.toFixed(0)}/100</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '0.5rem', marginTop: '0.5rem', borderTop: '1px solid var(--color-border)' }}>
                <span style={{ color: 'var(--color-text-muted)' }}>Price:</span>
                <span>{currencySymbol}{instance.price_monthly.toFixed(2)}/mo</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default InstanceBreakdown
