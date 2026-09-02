import { useState, useCallback } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const FORMATS = [
  { key: 'instagram_reels', label: 'Instagram Reels', detail: '15-60s · 9:16' },
  { key: 'tiktok', label: 'TikTok', detail: '15-60s · 9:16' },
  { key: 'ooh_digital', label: 'OOH Digital', detail: '10-15s loop · 16:9' },
  { key: 'radio_spot', label: 'Radio Spot', detail: '20-30s · Audio' },
  { key: 'podcast_preroll', label: 'Podcast Pre-roll', detail: '15-30s · Audio' },
  { key: 'web_interactive', label: 'Web Interactive', detail: 'Responsive' },
  { key: 'print_press', label: 'Print Press', detail: 'Full page' },
  { key: 'newsletter', label: 'Newsletter', detail: '600px · Email' },
  { key: 'activation_retail', label: 'Activation Retail', detail: 'Physical' },
  { key: 'linkedin_b2b', label: 'LinkedIn B2B', detail: '1:1 or 4:5' },
]

const PIPELINE_STEPS = [
  { key: 'analyze', label: 'Analyse de la campagne' },
  { key: 'plan', label: 'Planification des remixes' },
  { key: 'write', label: 'Génération créative' },
  { key: 'check', label: 'Contrôle qualité' },
]

const SAMPLE_BRIEF = `Client : Intermarché
Campagne : "L'Amour L'Amour" (2017)

Insight consommateur : Les gens associent la grande distribution au prix et aux promos, jamais à l'émotion. Pourtant, la cuisine est un acte d'amour — on cuisine pour ceux qu'on aime.

Concept créatif : Un court-métrage de 3 minutes raconte l'histoire d'un père séparé qui apprend à cuisiner pour reconquérir le cœur de sa fille adolescente. Le supermarché Intermarché est le décor discret de sa transformation.

Exécutions existantes : Film TV 3min, cut 60s et 30s, affichage print, activation en magasin.

Ton : Cinématographique, émouvant, authentique. Réalisation signée par un réalisateur de cinéma. Pas de voix off, pas de pack shot agressif. La marque est présente mais jamais intrusive.

Signature : "Intermarché — Producteur de beau et de bon depuis 1969"`

export default function App() {
  // --- State ---
  const [step, setStep] = useState('input') // input | formats | loading | results
  const [brief, setBrief] = useState('')
  const [selectedFormats, setSelectedFormats] = useState([])
  const [audience, setAudience] = useState('')
  const [market, setMarket] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [results, setResults] = useState([])
  const [loadingStep, setLoadingStep] = useState('')
  const [completedSteps, setCompletedSteps] = useState([])
  const [error, setError] = useState('')

  // --- Format selection ---
  const toggleFormat = (key) => {
    setSelectedFormats(prev =>
      prev.includes(key)
        ? prev.filter(k => k !== key)
        : prev.length < 5
          ? [...prev, key]
          : prev
    )
  }

  // --- API calls ---
  const runAnalysis = useCallback(async () => {
    setError('')
    setStep('loading')
    setLoadingStep('analyze')
    setCompletedSteps([])

    try {
      const res = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaign_brief: brief }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Erreur lors de l\'analyse')
      }

      const data = await res.json()
      setAnalysis(data.analysis)
      setCompletedSteps(['analyze'])
      setStep('formats')
    } catch (err) {
      setError(err.message)
      setStep('input')
    }
  }, [brief])

  const runRemix = useCallback(async () => {
    setError('')
    setStep('loading')
    setCompletedSteps(['analyze', 'plan'])
    setLoadingStep('write')

    try {
      const res = await fetch(`${API_URL}/remix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_brief: brief,
          formats: selectedFormats,
          target_audience: audience || null,
          target_market: market || null,
        }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Erreur lors de la génération')
      }

      setCompletedSteps(prev => [...prev, 'write'])
      setLoadingStep('check')

      const data = await res.json()
      setAnalysis(data.analysis)
      setResults(data.results)
      setCompletedSteps(['analyze', 'plan', 'write', 'check'])
      setStep('results')
    } catch (err) {
      setError(err.message)
      setStep('formats')
    }
  }, [brief, selectedFormats, audience, market])

  // --- Export Markdown ---
  const exportMarkdown = useCallback(() => {
    if (!analysis || !results.length) return

    let md = `# Remix — ${analysis.brand}\n\n`
    md += `> ${analysis.creative_concept}\n\n`
    md += `**Insight:** ${analysis.consumer_insight}\n\n`
    md += `**Ton:** ${analysis.tone_of_voice}\n\n`
    md += `---\n\n`

    results.forEach((r, i) => {
      const { remix, quality } = r
      md += `## ${i + 1}. ${remix.format_label}\n\n`
      md += `**Specs:** ${remix.format_specs}\n\n`
      md += `### Concept adapté\n${remix.adapted_concept}\n\n`
      md += `### Headline\n> ${remix.headline}\n\n`
      md += `### Description narrative\n${remix.narrative_description}\n\n`
      md += `### Notes de production\n${remix.production_notes}\n\n`
      md += `### Tone check\n${remix.tone_check}\n\n`
      md += `**Score qualité:** ${quality.score}/10\n\n`
      if (quality.strengths.length) {
        md += `**Points forts:** ${quality.strengths.join(', ')}\n\n`
      }
      if (quality.issues.length) {
        md += `**Points d'attention:** ${quality.issues.join(', ')}\n\n`
      }
      md += `---\n\n`
    })

    const blob = new Blob([md], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `remix-${analysis.brand.toLowerCase().replace(/\s+/g, '-')}.md`
    a.click()
    URL.revokeObjectURL(url)
  }, [analysis, results])

  // --- Reset ---
  const reset = () => {
    setStep('input')
    setBrief('')
    setSelectedFormats([])
    setAudience('')
    setMarket('')
    setAnalysis(null)
    setResults([])
    setLoadingStep('')
    setCompletedSteps([])
    setError('')
  }

  // --- Step indicators ---
  const stepIndex = { input: 0, formats: 1, loading: 2, results: 3 }
  const currentIdx = stepIndex[step] ?? 0

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>Remix</h1>
        <p className="tagline">Feed it a campaign. Get it everywhere.</p>
      </header>

      {/* Step dots */}
      <div className="steps">
        {[0, 1, 2, 3].map(i => (
          <div
            key={i}
            className={`step-dot ${i === currentIdx ? 'active' : ''} ${i < currentIdx ? 'done' : ''}`}
          />
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="card" style={{ borderColor: 'var(--accent)', marginBottom: 24 }}>
          <p style={{ color: 'var(--accent)' }}>{error}</p>
        </div>
      )}

      {/* Step 1: Input */}
      {step === 'input' && (
        <div className="card">
          <h2>01 — Brief de campagne</h2>
          <textarea
            className="brief-textarea"
            placeholder="Décrivez la campagne : client, insight, concept créatif, exécutions existantes, ton..."
            value={brief}
            onChange={e => setBrief(e.target.value)}
          />
          <div className="btn-row">
            <button
              className="btn btn-primary"
              disabled={brief.trim().length < 50}
              onClick={runAnalysis}
            >
              Analyser la campagne
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => setBrief(SAMPLE_BRIEF)}
            >
              Essayer un exemple
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Analysis + Format selection */}
      {step === 'formats' && analysis && (
        <>
          <div className="card" style={{ marginBottom: 24 }}>
            <h2>Analyse créative</h2>
            <div className="analysis-grid">
              <div className="analysis-item">
                <div className="label">Marque & Catégorie</div>
                <div className="value">{analysis.brand} — {analysis.category}</div>
              </div>
              <div className="analysis-item">
                <div className="label">Insight consommateur</div>
                <div className="value">{analysis.consumer_insight}</div>
              </div>
              <div className="analysis-item">
                <div className="label">Concept créatif</div>
                <div className="value">{analysis.creative_concept}</div>
              </div>
              <div className="analysis-item">
                <div className="label">Territoire d'expression</div>
                <div className="value">{analysis.tone_of_voice}</div>
              </div>
              {analysis.signature && (
                <div className="analysis-item">
                  <div className="label">Signature</div>
                  <div className="value">{analysis.signature}</div>
                </div>
              )}
            </div>
            <div className="btn-row">
              <button className="btn btn-secondary" onClick={() => setStep('input')}>
                Corriger l'analyse
              </button>
            </div>
          </div>

          <div className="card">
            <h2>02 — Choisir les formats ({selectedFormats.length}/5)</h2>
            <div className="formats-grid">
              {FORMATS.map(f => (
                <div
                  key={f.key}
                  className={`format-chip ${selectedFormats.includes(f.key) ? 'selected' : ''}`}
                  onClick={() => toggleFormat(f.key)}
                >
                  <span className="chip-label">{f.label}</span>
                  <span className="chip-detail">{f.detail}</span>
                </div>
              ))}
            </div>

            <h2 style={{ marginTop: 32 }}>Options (facultatif)</h2>
            <div className="optional-fields">
              <div className="field-group">
                <label>Audience cible</label>
                <input
                  className="field-input"
                  placeholder="Ex: Gen Z, B2B, seniors..."
                  value={audience}
                  onChange={e => setAudience(e.target.value)}
                />
              </div>
              <div className="field-group">
                <label>Marché cible</label>
                <input
                  className="field-input"
                  placeholder="Ex: US, UK, DACH..."
                  value={market}
                  onChange={e => setMarket(e.target.value)}
                />
              </div>
            </div>

            <div className="btn-row">
              <button
                className="btn btn-primary"
                disabled={selectedFormats.length === 0}
                onClick={runRemix}
              >
                Générer {selectedFormats.length} déclinaison{selectedFormats.length > 1 ? 's' : ''}
              </button>
              <button className="btn btn-secondary" onClick={() => setStep('input')}>
                Retour
              </button>
            </div>
          </div>
        </>
      )}

      {/* Loading */}
      {step === 'loading' && (
        <div className="card">
          <div className="loading-container">
            <div className="spinner" />
            <div className="loading-steps-list">
              {PIPELINE_STEPS.map(s => (
                <div
                  key={s.key}
                  className={`loading-step-item ${
                    loadingStep === s.key ? 'active' : ''
                  } ${completedSteps.includes(s.key) ? 'done' : ''}`}
                >
                  <span>{completedSteps.includes(s.key) ? '✓' : loadingStep === s.key ? '⟳' : '○'}</span>
                  <span>{s.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {step === 'results' && results.length > 0 && (
        <>
          <div className="export-bar">
            <h2 style={{ fontFamily: 'var(--mono)', fontSize: 14, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, color: 'var(--text-muted)' }}>
              {results.length} déclinaison{results.length > 1 ? 's' : ''} générée{results.length > 1 ? 's' : ''}
            </h2>
            <div style={{ display: 'flex', gap: 12 }}>
              <button className="btn btn-secondary" onClick={exportMarkdown}>
                Exporter .md
              </button>
              <button className="btn btn-secondary" onClick={reset}>
                Nouveau remix
              </button>
            </div>
          </div>

          <div className="results-list">
            {results.map((r, i) => (
              <div className="remix-card" key={i}>
                <div className="remix-header">
                  <h3>{r.remix.format_label}</h3>
                  <span className={`score-badge ${r.quality.score >= 7 ? 'score-high' : 'score-mid'}`}>
                    {r.quality.score}/10
                  </span>
                </div>
                <div className="remix-body">
                  <div className="remix-specs">
                    {r.remix.format_specs}
                  </div>

                  <div className="remix-section">
                    <div className="section-label">Headline</div>
                    <div className="headline-value">{r.remix.headline}</div>
                  </div>

                  <div className="remix-section">
                    <div className="section-label">Concept adapté</div>
                    <div className="section-value">{r.remix.adapted_concept}</div>
                  </div>

                  <div className="remix-section">
                    <div className="section-label">Description narrative</div>
                    <div className="section-value">{r.remix.narrative_description}</div>
                  </div>

                  <div className="remix-section">
                    <div className="section-label">Notes de production</div>
                    <div className="section-value">{r.remix.production_notes}</div>
                  </div>

                  <div className="remix-section">
                    <div className="section-label">Tone check</div>
                    <div className="section-value">{r.remix.tone_check}</div>
                  </div>

                  {(r.quality.strengths.length > 0 || r.quality.issues.length > 0) && (
                    <div className="quality-notes">
                      {r.quality.strengths.length > 0 && (
                        <>
                          <div className="qn-label">Points forts</div>
                          <div className="qn-items">{r.quality.strengths.join(' · ')}</div>
                        </>
                      )}
                      {r.quality.issues.length > 0 && (
                        <>
                          <div className="qn-label" style={{ color: 'var(--warning)', marginTop: 8 }}>Points d'attention</div>
                          <div className="qn-items">{r.quality.issues.join(' · ')}</div>
                        </>
                      )}
                      {r.quality.suggestion && (
                        <>
                          <div className="qn-label" style={{ color: 'var(--text-secondary)', marginTop: 8 }}>Suggestion</div>
                          <div className="qn-items">{r.quality.suggestion}</div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
