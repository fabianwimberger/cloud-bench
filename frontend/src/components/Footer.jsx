function Footer({ metadata }) {
  const provider = metadata?.provider || 'cloud'
  const providerLower = provider.toLowerCase()

  // Provider URLs mapping - extend this when adding new providers
  const providerUrls = {
    hetzner: 'https://www.hetzner.com/cloud',
    aws: 'https://aws.amazon.com/ec2/',
    gcp: 'https://cloud.google.com/compute',
    azure: 'https://azure.microsoft.com/en-us/products/virtual-machines',
  }

  const providerUrl = providerUrls[providerLower]
  const providerDisplay = provider.charAt(0).toUpperCase() + provider.slice(1)

  return (
    <footer className="footer">
      <p>
        Benchmarking {providerDisplay} instances
      </p>
      <p style={{ marginTop: '0.5rem' }}>
        <a href="https://github.com/fabianwimberger/cloud-bench" target="_blank" rel="noopener noreferrer">
          View on GitHub
        </a>
        {providerUrl && (
          <>
            {' • '}
            <a href={providerUrl} target="_blank" rel="noopener noreferrer">
              {providerDisplay}
            </a>
          </>
        )}
      </p>
    </footer>
  )
}

export default Footer
