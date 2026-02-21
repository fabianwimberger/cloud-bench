function ProviderBadge({ provider }) {
  // Hetzner is now the only provider
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
      background: 'rgba(213, 12, 45, 0.2)',
      color: '#fb7185'
    }}>
      🇩🇪 Hetzner
    </span>
  )
}

export default ProviderBadge
