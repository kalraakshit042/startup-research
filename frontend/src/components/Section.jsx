import { useState } from 'react'

const SECTION_NUMBERS = {
  tldr: '00', story: '01', team: '02', product: '03',
  traction: '04', competitive: '05', culture: '06',
  social: '07', signals: '08', questions: '09', sources: '10',
}

// Group labels for editorial dividers
const SECTION_GROUPS = {
  story: 'Background',
  traction: 'Business',
  culture: 'People & Culture',
  signals: 'Signals & Analysis',
  sources: 'References',
}

export default function Section({ sectionKey, title, content }) {
  const [isOpen, setIsOpen] = useState(sectionKey !== 'sources')
  const groupLabel = SECTION_GROUPS[sectionKey]

  // TL;DR gets special treatment — it's the lede
  if (sectionKey === 'tldr') {
    return (
      <div className="section-enter section-tldr">
        <span className="tldr-label">TL;DR</span>
        <div
          className="tldr-content"
          dangerouslySetInnerHTML={{ __html: inlineFormat(content) }}
        />
      </div>
    )
  }

  const cardClass = sectionKey === 'sources'
    ? 'section-card section-sources section-enter'
    : 'section-card section-enter'

  return (
    <>
      {groupLabel && (
        <div className="section-divider">
          <span className="section-divider-label">{groupLabel}</span>
          <div className="section-divider-line" />
        </div>
      )}
      <div className={cardClass}>
        <button
          className="section-header"
          onClick={() => setIsOpen(!isOpen)}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span className="section-number">
              {SECTION_NUMBERS[sectionKey] || '??'}
            </span>
            <span className="section-title">{title}</span>
          </div>
          <span
            className="section-chevron"
            style={{ transform: isOpen ? 'rotate(0deg)' : 'rotate(-90deg)' }}
          >
            &#9660;
          </span>
        </button>

        {isOpen && (
          <div
            className="section-content"
            dangerouslySetInnerHTML={{ __html: formatContent(content, sectionKey) }}
          />
        )}
      </div>
    </>
  )
}

function formatContent(markdown, sectionKey) {
  if (!markdown) return ''
  if (sectionKey === 'sources') return formatSources(markdown)

  let html = markdown

  // Tables: pipe-delimited → HTML
  html = html.replace(
    /(?:^|\n)(\|.+\|)\n(\|[\s\-:|]+\|)\n((?:\|.+\|\n?)+)/g,
    (match, headerRow, separatorRow, bodyRows) => {
      const headers = headerRow.split('|').filter(c => c.trim()).map(c => c.trim())
      const rows = bodyRows.trim().split('\n').map(row =>
        row.split('|').filter(c => c.trim()).map(c => c.trim())
      )
      let table = '<table><thead><tr>'
      headers.forEach(h => { table += `<th>${h}</th>` })
      table += '</tr></thead><tbody>'
      rows.forEach(row => {
        table += '<tr>'
        row.forEach(cell => { table += `<td>${inlineFormat(cell)}</td>` })
        table += '</tr>'
      })
      table += '</tbody></table>'
      return '\n' + table + '\n'
    }
  )

  // Split into blocks
  const blocks = html.split(/\n{2,}/)
  return blocks.map(block => {
    block = block.trim()
    if (!block) return ''
    if (block.startsWith('<table')) return block

    // Numbered list
    if (/^\d+\.\s/.test(block)) {
      const items = block.split(/\n(?=\d+\.\s)/)
      return `<ol>${items.map(i => `<li>${inlineFormat(i.replace(/^\d+\.\s*/, ''))}</li>`).join('')}</ol>`
    }

    // Bullet list
    if (/^[\-\*\u2013]\s/.test(block)) {
      const items = block.split(/\n(?=[\-\*\u2013]\s)/)
      return `<ul>${items.map(i => `<li>${inlineFormat(i.replace(/^[\-\*\u2013]\s*/, ''))}</li>`).join('')}</ul>`
    }

    // Sub-heading
    if (/^#{3,4}\s/.test(block)) {
      return `<h4>${inlineFormat(block.replace(/^#{3,4}\s*/, ''))}</h4>`
    }

    // Horizontal rule
    if (/^---+$/.test(block)) return '<hr>'

    // Paragraph
    const lines = block.split('\n')
    return `<p>${lines.map(l => inlineFormat(l)).join('<br>')}</p>`
  }).join('')
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function inlineFormat(text) {
  // Escape HTML first to prevent XSS from LLM output
  let safe = escapeHtml(text)
  return safe
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\[(.+?)\]\((https?:\/\/[^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
}

function sanitizeUrl(url) {
  // Only allow http/https URLs — blocks javascript:, data:, etc.
  try {
    const parsed = new URL(url)
    if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
      return parsed.href
    }
  } catch {}
  return '#'
}

function formatSources(markdown) {
  const lines = markdown.split('\n').filter(l => l.trim())
  return lines.map(line => {
    const mdMatch = line.match(/\[(.+?)\]\((.+?)\)/)
    if (mdMatch) {
      const safeUrl = sanitizeUrl(mdMatch[2])
      return `<a href="${safeUrl}" target="_blank" rel="noopener" class="source-link">${escapeHtml(mdMatch[1])}</a>`
    }
    const urlMatch = line.match(/(https?:\/\/[^\s]+)/)
    if (urlMatch) {
      const safeUrl = sanitizeUrl(urlMatch[1])
      const display = safeUrl.replace(/^https?:\/\//, '').replace(/\/$/, '')
      return `<a href="${safeUrl}" target="_blank" rel="noopener" class="source-link">${escapeHtml(display)}</a>`
    }
    if (line.replace(/^[\-\*]\s*/, '').trim()) {
      return `<p>${inlineFormat(line.replace(/^[\-\*]\s*/, ''))}</p>`
    }
    return ''
  }).join('')
}
