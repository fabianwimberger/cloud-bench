const providerStyles = {
  hetzner: {
    background: 'rgba(213, 12, 45, 0.2)',
    color: '#fb7185',
    label: 'Hetzner',
  },
  aws: {
    background: 'rgba(255, 153, 0, 0.2)',
    color: '#f59e0b',
    label: 'AWS',
  },
}

function ProviderBadge({ provider }) {
  const style = providerStyles[provider] || providerStyles.hetzner

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      padding: '0.25rem 0.75rem',
      borderRadius: '9999px',
      fontSize: '0.75rem',
      fontWeight: 600,
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      background: style.background,
      color: style.color
    }}>
      {style.label}
    </span>
  )
}

export default ProviderBadge
