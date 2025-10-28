import React, { useState } from 'react'

// Types aligned with backend pydantic models
type FactorName = 'current_experience' | 'previous_experience' | 'title' | 'school' | 'location'

type ParsedResume = {
  full_name?: string | null
  current_company?: string | null
  previous_companies: string[]
  title?: string | null
  school?: string | null
  city?: string | null
}

type FactorPlan = {
  exact_1_0: string[]
  neighbors_0_75: string[]
  neighbors_0_5: string[]
  neighbors_0_25: string[]
}

type SimilarityPlan = {
  factors: Record<string, FactorPlan> // keys are FactorName, but keep flexible for runtime
}

type UploadResponse = {
  query_plan: SimilarityPlan
  parsed: ParsedResume
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
      const apiBase = import.meta.env.VITE_API_BASE ?? 'http://localhost:8080'
      const res = await fetch(`${apiBase.replace(/\/$/, '')}/api/upload`, { method: 'POST', body: form })
      setStatus('planning')
      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || 'Request failed')
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
      <h1>RecruitU Similarity Finder</h1>
      <p>Upload a resume (PDF) to parse, plan, search and score.</p>

      <form onSubmit={handleSubmit} style={{ marginTop: 16, marginBottom: 24 }}>
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <button type="submit" disabled={!file || status === 'uploading' || status === 'parsing' || status === 'planning' || status === 'searching' || status === 'scoring'} style={{ marginLeft: 8 }}>
          Start
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
          <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, background: '#fff', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>Full name</div>
                <div style={{ fontWeight: 600 }}>{data.parsed.full_name ?? '—'}</div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>Title</div>
                <div style={{ fontWeight: 600 }}>{data.parsed.title ?? '—'}</div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>Current company</div>
                <div style={{ fontWeight: 600 }}>{data.parsed.current_company ?? '—'}</div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>School</div>
                <div style={{ fontWeight: 600 }}>{data.parsed.school ?? '—'}</div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>City</div>
                <div style={{ fontWeight: 600 }}>{data.parsed.city ?? '—'}</div>
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <div style={{ fontSize: 12, color: '#6b7280' }}>Previous companies</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 4 }}>
                  {(data.parsed.previous_companies || []).length > 0 ? (
                    data.parsed.previous_companies.map((c, idx) => (
                      <span key={idx} style={{ display: 'inline-block', padding: '4px 8px', background: '#f3f4f6', borderRadius: 999, fontSize: 12 }}>
                        {c}
                      </span>
                    ))
                  ) : (
                    <span>—</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          <h2 style={{ marginTop: 20 }}>Similarity Plan</h2>
          <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, background: '#fff', boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
            {(['current_experience','title','school','location'] as FactorName[]).map((factor) => {
              const label: Record<FactorName, string> = {
                current_experience: 'Company',
                previous_experience: 'Previous Experience',
                title: 'Title',
                school: 'School',
                location: 'Location',
              }
              const plan: FactorPlan | undefined = data.query_plan.factors[factor]
              if (!plan) return null
              const tiers: Array<{ key: keyof FactorPlan; title: string; color: string }> = [
                { key: 'exact_1_0', title: 'Exact (1.0)', color: '#dbeafe' },
                { key: 'neighbors_0_75', title: 'Neighbors (0.75)', color: '#e0f2fe' },
                { key: 'neighbors_0_5', title: 'Neighbors (0.5)', color: '#ecfeff' },
                { key: 'neighbors_0_25', title: 'Neighbors (0.25)', color: '#f1f5f9' },
              ]
              return (
                <div key={factor} style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 700, marginBottom: 8 }}>{label[factor]}</div>
                  {tiers.map((t) => (
                    <div key={t.key} style={{ marginBottom: 8 }}>
                      <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>{t.title}</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                        {(plan[t.key] as string[]).length > 0 ? (
                          (plan[t.key] as string[]).map((v, idx) => (
                            <span key={idx} style={{ display: 'inline-block', padding: '4px 8px', background: t.color, border: '1px solid #e5e7eb', borderRadius: 999, fontSize: 12 }}>
                              {v}
                            </span>
                          ))
                        ) : (
                          <span style={{ color: '#6b7280' }}>—</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )
            })}
          </div>

          <h2 style={{ marginTop: 20 }}>Top Results</h2>
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


