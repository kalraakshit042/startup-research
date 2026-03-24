import Section from './Section'

export default function ReportView({ query, sections, progress, slug, onReset }) {
  return (
    <div style={{ paddingTop: '48px', paddingBottom: '80px' }}>
      {/* Header */}
      <div className="report-header">
        <button className="back-button" onClick={onReset}>
          New search
        </button>

        <h2 className="report-title">{query}</h2>

        <div className="report-meta">
          {slug && <span className="badge badge-accent">Just generated</span>}
          <span style={{
            color: 'var(--text-faint)',
            fontFamily: 'var(--font-mono)',
            fontSize: '12px',
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          }}>
            {sections.length} section{sections.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Progress */}
      {progress && (
        <div className="progress-bar">
          <span className="pulse-dot" />
          {progress}
        </div>
      )}

      {/* Sections */}
      {sections.map((section) => (
        <Section
          key={section.key}
          sectionKey={section.key}
          title={section.title}
          content={section.content}
        />
      ))}

      {/* Shareable URL */}
      {slug && (
        <div style={{ textAlign: 'center', marginTop: '48px' }}>
          <div className="share-link" style={{ display: 'inline-flex' }}>
            <span>Shareable link</span>
            <a href={`/r/${slug}`}>/r/{slug}</a>
          </div>
        </div>
      )}
    </div>
  )
}
