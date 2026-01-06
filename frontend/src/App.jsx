import { useState } from 'react'
import './index.css'
import ReactMarkdown from 'react-markdown'

function App() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('/agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      })

      if (!response.ok) {
        throw new Error('Network response was not ok')
      }

      const data = await response.json()
      
      setResult(data.response)
    } catch (err) {
      console.error(err)
      setError('Failed to fetch research results. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1 className="title">Research Agent AI</h1>

      <form onSubmit={handleSearch} className="input-group">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="What would you like to research?"
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Researching...' : 'Search'}
        </button>
      </form>

      {loading && <span className="loader"></span>}

      {error && (
        <div className="response-area" style={{ borderColor: '#ef4444' }}>
          <p style={{ color: '#ef4444' }}>{error}</p>
        </div>
      )}

      {result && (
        <div className="response-area">
          {typeof result === 'string' ? (
            <p>{result}</p>
          ) : (
            <>
              <h3>{result.topic}</h3>
              <div className="markdown-content">
                <ReactMarkdown>{result.summary}</ReactMarkdown>
              </div>

              {result.sources && result.sources.length > 0 && (
                <div className="sources">
                  <strong>Sources:</strong><br />
                  {result.sources.map((source, index) => (
                    <div key={index}>
                      {/* Identify if source is a URL or text */}
                      {source.startsWith('http') ? (
                        <a href={source} target="_blank" rel="noopener noreferrer">{source}</a>
                      ) : (
                        <span>{source}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default App
