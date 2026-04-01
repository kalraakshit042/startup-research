import { useState, useRef } from 'react'
import { Analytics } from '@vercel/analytics/react'
import InputForm from './components/InputForm'
import ReportView from './components/ReportView'

export default function App() {
  const [state, setState] = useState('HOME') // HOME | LOADING | REPORT | ERROR
  const [query, setQuery] = useState('')
  const [sections, setSections] = useState([])
  const [progress, setProgress] = useState('')
  const [slug, setSlug] = useState(null)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  async function handleSearch(searchQuery) {
    // Abort any in-flight request
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setQuery(searchQuery)
    setSections([])
    setProgress('Starting research...')
    setError(null)
    setSlug(null)
    setState('LOADING')

    try {
      const apiUrl = import.meta.env.VITE_API_URL || ''
      const response = await fetch(`${apiUrl}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery }),
        signal: controller.signal,
      })

      if (response.status === 429) {
        const data = await response.json()
        setError({ type: 'rate_limited', message: data.message, retryAfter: data.retry_after })
        setState('ERROR')
        return
      }

      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      // Parse SSE stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let currentEvent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (currentEvent === 'progress') {
                setProgress(data.message)
              } else if (currentEvent === 'section') {
                setSections(prev => [...prev, data])
                setState('REPORT')
              } else if (currentEvent === 'complete') {
                setSlug(data.slug)
                setProgress('')
                if (data.save_error) {
                  console.warn('Report was not saved to database')
                }
              } else if (currentEvent === 'cached') {
                setSlug(data.slug)
              } else if (currentEvent === 'error') {
                setError({ type: 'generation', message: data.message })
                setState('ERROR')
              }
            } catch { /* skip malformed */ }
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') return // User navigated away
      setError({ type: 'network', message: err.message })
      setState('ERROR')
    }
  }

  function handleReset() {
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = null
    setState('HOME')
    setQuery('')
    setSections([])
    setProgress('')
    setSlug(null)
    setError(null)
  }

  return (
    <div className="min-h-screen">
      <Analytics />
      {state === 'HOME' && <InputForm onSearch={handleSearch} />}

      {(state === 'LOADING' || state === 'REPORT') && (
        <ReportView
          query={query}
          sections={sections}
          progress={progress}
          slug={slug}
          onReset={handleReset}
        />
      )}

      {state === 'ERROR' && (
        <div className="py-32 text-center">
          {error?.type === 'rate_limited' ? (
            <>
              <p style={{ color: 'var(--text-muted)' }}>{error.message}</p>
              <p className="my-4 text-2xl" style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>
                {Math.floor(error.retryAfter / 60)}:{String(error.retryAfter % 60).padStart(2, '0')}
              </p>
            </>
          ) : (
            <p style={{ color: 'var(--error)' }}>Something went wrong: {error?.message}</p>
          )}
          <button onClick={handleReset} className="mt-6 cursor-pointer px-5 py-2.5"
            style={{ background: 'var(--surface)', color: 'var(--text-primary)', borderRadius: 'var(--radius-md)', fontFamily: 'var(--font-body)', border: '1px solid var(--border)' }}>
            Try again
          </button>
        </div>
      )}
    </div>
  )
}
