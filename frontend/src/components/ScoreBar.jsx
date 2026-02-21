function ScoreBar({ value }) {
  const percentage = Math.min(Math.max(value, 0), 100)
  
  return (
    <div className="score-bar" style={{ marginBottom: '4px' }}>
      <div 
        className="score-bar-fill" 
        style={{ width: `${percentage}%` }}
      />
    </div>
  )
}

export default ScoreBar
