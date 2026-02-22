function Header({ metadata }) {
  const generatedAt = metadata?.generated_at
    ? new Date(metadata.generated_at).toLocaleString()
    : 'Sample Data'

  return (
    <header className="header">
      <div className="header-brand">
        <div className="header-logo">
          Cloud<span>Bench</span>
        </div>
        <nav className="header-nav">
          <a href="#" className="nav-tab active">Instances</a>
        </nav>
      </div>
      
      <div className="header-meta">
        Generated: {generatedAt} • Median of 5 runs
      </div>
    </header>
  )
}

export default Header
