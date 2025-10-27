import React, { useState } from 'react'

type UploadResponse = {
  query_plan: any
  parsed: any
  results: Array<{
    candidate_id: string
    total_score: number
    factors: Record<string, number>
    document: {
      id: string
      full_name?: string | null
      title?: string | null
      school?: string | null
      city?: string | null
      current_company?: { company?: string | null; title?: string | null } | null
    }
  }>
}

const App: React.FC = () => {
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<'idle' | 'uploading' | 'parsing' | 'planning' | 'searching' | 'scoring' | 'done' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<UploadResponse | null>(null)
  const [visibleCount, setVisibleCount] = useState<number>(20)

  const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024 // 5MB

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null
    setError(null)
    if (!f) {
      setFile(null)
      return
    }
    const isPdf = f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf')
    if (!isPdf) {
      setFile(null)
      setError('Please upload a PDF file (.pdf).')
      return
    }
    if (f.size > MAX_FILE_SIZE_BYTES) {
      setFile(null)
      setError('File is too large. Max size is 5MB.')
      return
    }
    setFile(f)
  }

  function handleReset() {
    setFile(null)
    setError(null)
    setData(null)
    setStatus('idle')
    setVisibleCount(20)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return
    setError(null)
    setData(null)
    setStatus('uploading')
    try {
      const form = new FormData()
      form.append('file', file)
      // Client-side progress UX mirrors backend phases (approximate)
      setStatus('parsing')
      const res = await fetch('/api/upload', { method: 'POST', body: form })
      setStatus('planning')
      if (!res.ok) {
        let detail = 'Request failed'
        try {
          const text = await res.text()
          if (text) {
            try {
              const parsed = JSON.parse(text)
              detail = parsed?.detail || text
            } catch {
              detail = text
            }
          }
        } catch {}
        throw new Error(detail)
      }
      setStatus('searching')
      const json = (await res.json()) as UploadResponse
      setStatus('scoring')
      setVisibleCount(20)
      setData(json)
      setStatus('done')
    } catch (err: any) {
      setStatus('error')
      setError(err?.message ?? String(err))
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: '40px auto', fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, sans-serif' }}>
      <h1>RecruitU MVP</h1>
      <p>Upload a resume (PDF) to parse, plan, search and score.</p>

      <form onSubmit={handleSubmit} style={{ marginTop: 16, marginBottom: 24 }}>
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          disabled={status !== 'idle' && status !== 'error' && status !== 'done'}
        />
        <button type="submit" disabled={!file || status === 'uploading' || status === 'parsing' || status === 'planning' || status === 'searching' || status === 'scoring'} style={{ marginLeft: 8 }}>
          Start
        </button>
        <button type="button" onClick={handleReset} disabled={status === 'uploading' || status === 'parsing' || status === 'planning' || status === 'searching' || status === 'scoring'} style={{ marginLeft: 8 }}>
          Reset
        </button>
      </form>

      <div style={{ marginBottom: 16 }}>
        <strong>Status:</strong> {status}
        {error && (
          <div style={{ color: 'crimson', marginTop: 8 }}>{error}</div>
        )}
      </div>

      {data && (
        <div>
          <h2>Parsed</h2>
          <pre style={{ background: '#f6f8fa', padding: 12, overflow: 'auto' }}>{JSON.stringify(data.parsed, null, 2)}</pre>

          <h2>Similarity Plan</h2>
          <pre style={{ background: '#f6f8fa', padding: 12, overflow: 'auto' }}>{JSON.stringify(data.query_plan, null, 2)}</pre>

          <h2>Top Results</h2>
          {data.results.slice(0, visibleCount).map((r) => (
            <div key={r.candidate_id} style={{ border: '1px solid #ddd', borderRadius: 6, padding: 12, marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontWeight: 600 }}>{r.document.full_name ?? 'Unknown'}</div>
                  <div style={{ color: '#555' }}>{r.document.current_company?.company ?? '—'} · {r.document.title ?? r.document.current_company?.title ?? '—'}</div>
                  <div style={{ color: '#555' }}>{r.document.school ?? '—'} · {r.document.city ?? '—'}</div>
                </div>
                <div style={{ fontWeight: 700 }}>{r.total_score.toFixed(2)}</div>
              </div>
              <details style={{ marginTop: 8 }}>
                <summary>Factors</summary>
                <pre style={{ background: '#f6f8fa', padding: 8, overflow: 'auto' }}>{JSON.stringify(r.factors, null, 2)}</pre>
              </details>
            </div>
          ))}
          <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ color: '#555' }}>
              Showing {Math.min(visibleCount, data.results.length)} of {data.results.length}
            </span>
            {visibleCount < data.results.length && (
              <button
                onClick={() => setVisibleCount((c) => Math.min(c + 20, data.results.length))}
                disabled={visibleCount >= data.results.length}
              >
                Load more matches
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default App


