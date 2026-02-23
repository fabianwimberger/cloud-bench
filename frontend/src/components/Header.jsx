function Header({ metadata }) {
  const generatedAt = metadata?.generated_at
    ? new Date(metadata.generated_at).toLocaleString()
    : 'Sample Data'

  return (
    <header className="header">
      <div className="header-logo">
        Cloud<span>Bench</span>
      </div>
      <div className="header-meta">
        Generated: {generatedAt} • Median of 5 runs
      </div>
    </header>
  )
}

export default Header
