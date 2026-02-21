function Header({ metadata }) {
  const generatedAt = metadata?.generated_at
    ? new Date(metadata.generated_at).toLocaleString()
    : 'Sample Data'

  const provider = metadata?.provider || 'Cloud'
  const providerDisplay = provider.charAt(0).toUpperCase() + provider.slice(1)

  return (
    <header className="header">
      <h1>Cloud-Bench</h1>
      <p>{providerDisplay} Performance & Value Comparison</p>
      <div className="meta">
        <span>Generated: {generatedAt}</span>
        {metadata?.total_instances && (
          <span> • {metadata.total_instances} instances</span>
        )}
        <span> • Median of 5 runs</span>
      </div>
    </header>
  )
}

export default Header
