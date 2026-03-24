import { useState } from 'react'

export default function InputForm({ onSearch }) {
  const [query, setQuery] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (query.trim().length >= 2) {
      onSearch(query.trim())
    }
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      paddingTop: '20vh',
      paddingBottom: '80px',
      minHeight: '100vh',
    }}>
      <h1 className="hero-title" style={{ textAlign: 'center' }}>
        Startup <em>Research</em>
      </h1>

      <p className="hero-subtitle">
        Paste a company name, website, or LinkedIn page.
        Get a complete research brief in 90 seconds.
      </p>

      <form onSubmit={handleSubmit} style={{ width: '100%', maxWidth: '540px' }}>
        <div className="search-box">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Stripe, openai.com, or a LinkedIn URL"
            className="search-input"
            autoFocus
          />
          <button
            type="submit"
            disabled={query.trim().length < 2}
            className="search-button"
          >
            Research
          </button>
        </div>
      </form>

      <p style={{
        color: 'var(--text-faint)',
        fontSize: '12px',
        marginTop: '24px',
        fontFamily: 'var(--font-mono)',
        letterSpacing: '0.04em',
        textTransform: 'uppercase',
      }}>
        1 free search per hour
      </p>
    </div>
  )
}
