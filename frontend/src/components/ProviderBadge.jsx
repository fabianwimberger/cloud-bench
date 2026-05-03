const providerStyles = {
  hetzner: {
    background: 'rgba(213, 12, 45, 0.2)',
    color: '#fb7185',
    label: 'Hetzner',
    fullName: 'Hetzner Cloud',
  },
  aws: {
    background: 'rgba(255, 153, 0, 0.2)',
    color: '#f59e0b',
    label: 'AWS',
    fullName: 'AWS EC2',
  },
  ovhcloud: {
    background: 'rgba(0, 0, 155, 0.2)',
    color: '#6366f1',
    label: 'OVH',
    fullName: 'OVHcloud',
  },
  oci: {
    background: 'rgba(147, 51, 234, 0.2)',
    color: '#c084fc',
    label: 'OCI',
    fullName: 'Oracle Cloud (OCI)',
  },
  gcp: {
    background: 'rgba(66, 133, 244, 0.2)',
    color: '#93c5fd',
    label: 'GCP',
    fullName: 'Google Cloud Platform',
  },
  azure: {
    background: 'rgba(0, 120, 212, 0.2)',
    color: '#60a5fa',
    label: 'Azure',
    fullName: 'Microsoft Azure',
  },
}

const fallbackStyle = {
  background: 'rgba(148, 163, 184, 0.2)',
  color: '#94a3b8',
}

function ProviderBadge({ provider }) {
  const known = providerStyles[provider]
  const style = known || {
    ...fallbackStyle,
    label: provider || 'Unknown',
    fullName: provider || 'Unknown provider',
  }

  return (
    <span
      title={style.fullName}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '0.25rem 0.75rem',
        borderRadius: '9999px',
        fontSize: '0.75rem',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        background: style.background,
        color: style.color,
        cursor: 'help'
      }}
    >
      {style.label}
    </span>
  )
}

export default ProviderBadge
