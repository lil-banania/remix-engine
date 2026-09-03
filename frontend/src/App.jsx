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

const VISUAL_FORMATS = [
  { key: 'tiktok', label: 'TikTok / Reels', detail: '9:16 · Vertical' },
  { key: 'story', label: 'Instagram Story', detail: '9:16 · Vertical' },
  { key: 'print', label: 'Affiche / Print', detail: '3:4 · Poster' },
  { key: 'storyboard', label: 'Storyboard', detail: '16:9 · 4 frames' },
]

const PIPELINE_STEPS = [
  { key: 'analyze', label: 'Analyse de la campagne' },
  { key: 'plan', label: 'Planification des remixes' },
  { key: 'write', label: 'Génération créative' },
  { key: 'check', label: 'Contrôle qualité' },
  { key: 'visual_direct', label: 'Direction visuelle' },
]

const SAMPLE_BRIEF = `Client : Intermarché
Campagne : "L'Amour L'Amour" (2017)

Insight consommateur : Les gens associent la grande distribution au prix et aux promos, jamais à l'émotion. Pourtant, la cuisine est un acte d'amour — on cuisine pour ceux qu'on aime.

Concept créatif : Un court-métrage de 3 minutes raconte l'histoire d'un père séparé qui apprend à cuisiner pour reconquérir le cœur de sa fille adolescente. Le supermarché Intermarché est le décor discret de sa transformation.

Exécutions existantes : Film TV 3min, cut 60s et 30s, affichage print, activation en magasin.

Ton : Cinématographique, émouvant, authentique. Réalisation signée par un réalisateur de cinéma. Pas de voix off, pas de pack shot agressif. La marque est présente mais jamais intrusive.

Signature : "Intermarché — Producteur de beau et de bon depuis 1969"`


// ─── Visual mockup components ───

function TikTokMockup({ visual }) {
  const imgSrc = visual.image_b64
    ? `data:image/png;base64,${visual.image_b64}`
    : null

  return (
    <div className="vm-phone">
      <div className="vm-notch" />
      <div className="vm-screen">
        {imgSrc && <img className="vm-bg" src={imgSrc} alt="" />}
        {!imgSrc && <div className="vm-placeholder">Image non générée</div>}

        {/* TikTok top tabs */}
        <div className="tt-top">
          <span>Following</span>
          <span>Friends</span>
          <span className="active">For You</span>
        </div>

        {/* Right actions */}
        <div className="tt-actions">
          <div className="tt-avatar">
            {(visual.format_label || 'T')[0]}
            <div className="tt-avatar-plus">+</div>
          </div>
          <div className="tt-action">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="white"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
            <span>24.3K</span>
          </div>
          <div className="tt-action">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="white"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            <span>1,847</span>
          </div>
          <div className="tt-action">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="white"><path d="M4 12l1.41 1.41L11 7.83V20h2V7.83l5.58 5.59L20 12l-8-8-8 8z" transform="rotate(-30 12 12)"/></svg>
            <span>Share</span>
          </div>
          <div className="tt-action">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="white"><path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/></svg>
            <span>Save</span>
          </div>
          <div className="tt-disc" />
        </div>

        {/* Bottom info */}
        <div className="tt-bottom">
          <div className="tt-username">@brand_officiel</div>
          <div className="tt-desc">{visual.headline} {visual.subline}</div>
          <div className="tt-sound">
            <span className="tt-sound-icon">♫</span>
            <div className="tt-marquee">
              <span>Son original — Brand&nbsp;&nbsp;&nbsp;&nbsp;Son original — Brand</span>
            </div>
          </div>
        </div>

        {/* Progress */}
        <div className="tt-progress"><div className="tt-progress-fill" /></div>

        {/* Nav */}
        <div className="tt-nav">
          <div className="tt-nav-item active">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
          </div>
          <div className="tt-nav-item">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
          </div>
          <div className="tt-nav-item">
            <div className="tt-create-btn"><div className="tt-create-inner">+</div></div>
          </div>
          <div className="tt-nav-item">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
          </div>
          <div className="tt-nav-item">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
          </div>
        </div>
      </div>
    </div>
  )
}

function StoryMockup({ visual }) {
  const imgSrc = visual.image_b64
    ? `data:image/png;base64,${visual.image_b64}`
    : null

  return (
    <div className="vm-phone">
      <div className="vm-notch" />
      <div className="vm-screen">
        {imgSrc && <img className="vm-bg" src={imgSrc} alt="" />}
        {!imgSrc && <div className="vm-placeholder">Image non générée</div>}

        {/* Progress bars */}
        <div className="ig-progress">
          <div className="ig-seg done" />
          <div className="ig-seg current"><div className="ig-seg-fill" /></div>
          <div className="ig-seg" />
        </div>

        {/* Header */}
        <div className="ig-header">
          <div className="ig-avatar"><div className="ig-avatar-inner">T</div></div>
          <div>
            <div className="ig-name">brand_officiel</div>
            <div className="ig-time">Il y a 2h</div>
          </div>
          <div className="ig-more">···</div>
        </div>

        {/* Bottom */}
        <div className="ig-bottom">
          <div className="ig-headline">{visual.headline}</div>
          <div className="ig-cta">
            <span>↑</span> {visual.subline}
          </div>
          <div className="ig-reply-bar">
            <div className="ig-reply-input">Envoyer un message...</div>
            <div className="ig-reply-icons">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="white"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="white"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function PrintMockup({ visual }) {
  const imgSrc = visual.image_b64
    ? `data:image/png;base64,${visual.image_b64}`
    : null

  return (
    <div className="print-poster">
      {imgSrc && <img src={imgSrc} alt="" />}
      {!imgSrc && <div className="vm-placeholder" style={{ aspectRatio: '3/4' }}>Image non générée</div>}
      <div className="print-logo">BRAND</div>
      <div className="print-overlay">
        <div className="print-headline">{visual.headline}</div>
        <div className="print-sub">{visual.subline}</div>
      </div>
    </div>
  )
}

function StoryboardMockup({ visual }) {
  const frames = visual.storyboard_frames || []

  return (
    <div className="sb-grid">
      {frames.map((frame, i) => {
        const imgSrc = frame.image_b64
          ? `data:image/png;base64,${frame.image_b64}`
          : null
        return (
          <div className="sb-frame" key={i}>
            <div className="sb-img-wrap">
              <div className="sb-num">{i + 1}</div>
              {imgSrc && <img src={imgSrc} alt={`Frame ${i + 1}`} />}
              {!imgSrc && <div className="vm-placeholder-sm">—</div>}
            </div>
            <div className="sb-caption">{frame.caption}</div>
          </div>
        )
      })}
    </div>
  )
}

function VisualCard({ visual }) {
  const MockupComponent = {
    tiktok: TikTokMockup,
    story: StoryMockup,
    print: PrintMockup,
    storyboard: StoryboardMockup,
  }[visual.format] || null

  return (
    <div className="visual-card">
      <div className="visual-card-top">
        <span className="visual-format-tag">{visual.format_label}</span>
        {visual.has_image && <span className="visual-badge">Image IA</span>}
      </div>
      <div className="visual-card-mockup">
        {MockupComponent && <MockupComponent visual={visual} />}
      </div>
      <div className="visual-card-caption">
        <div className="vi-headline">{visual.headline}</div>
        {visual.subline && <div className="vi-subline">{visual.subline}</div>}
        <div className="vi-art-direction">{visual.art_direction}</div>
        {visual.image_prompt && (
          <details className="visual-prompt-details">
            <summary>Voir le prompt</summary>
            <p>{visual.image_prompt}</p>
          </details>
        )}
      </div>
    </div>
  )
}


export default function App() {
  // --- State ---
  const [step, setStep] = useState('input') // input | formats | loading | results
  const [brief, setBrief] = useState('')
  const [selectedFormats, setSelectedFormats] = useState([])
  const [selectedVisualFormats, setSelectedVisualFormats] = useState([])
  const [audience, setAudience] = useState('')
  const [market, setMarket] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [results, setResults] = useState([])
  const [visuals, setVisuals] = useState([])
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

  const toggleVisualFormat = (key) => {
    setSelectedVisualFormats(prev =>
      prev.includes(key)
        ? prev.filter(k => k !== key)
        : [...prev, key]
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
    setCompletedSteps([])
    setLoadingStep('analyze')
    setVisuals([])

    // Filter pipeline steps based on whether visuals are requested
    const activeSteps = selectedVisualFormats.length > 0
      ? PIPELINE_STEPS
      : PIPELINE_STEPS.filter(s => s.key !== 'visual_direct')

    try {
      const res = await fetch(`${API_URL}/remix/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_brief: brief,
          formats: selectedFormats,
          target_audience: audience || null,
          target_market: market || null,
          visual_formats: selectedVisualFormats,
        }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Erreur lors de la génération')
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let finalAnalysis = null
      let finalResults = []
      let finalVisuals = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event: done')) {
            const allKeys = activeSteps.map(s => s.key)
            setCompletedSteps(allKeys)
            continue
          }
          if (!line.startsWith('data: ')) continue

          try {
            const payload = JSON.parse(line.slice(6))
            const node = payload.node || payload.step

            if (node === 'analyze') {
              setLoadingStep('analyze')
              if (payload.analysis) {
                finalAnalysis = payload.analysis
                setCompletedSteps(prev => [...new Set([...prev, 'analyze'])])
                setLoadingStep('plan')
              }
            } else if (node === 'plan') {
              setCompletedSteps(prev => [...new Set([...prev, 'plan'])])
              setLoadingStep('write')
            } else if (node === 'write') {
              setCompletedSteps(prev => [...new Set([...prev, 'write'])])
              setLoadingStep('check')
            } else if (node === 'check') {
              if (payload.results) finalResults = payload.results
              setCompletedSteps(prev => [...new Set([...prev, 'check'])])
              if (selectedVisualFormats.length > 0) {
                setLoadingStep('visual_direct')
              }
            } else if (node === 'visual_direct') {
              if (payload.visuals) finalVisuals = payload.visuals
              setCompletedSteps(prev => [...new Set([...prev, 'visual_direct'])])
            }
          } catch (e) {
            // ignore malformed SSE lines
          }
        }
      }

      if (finalAnalysis) setAnalysis(finalAnalysis)
      if (finalResults.length) setResults(finalResults)
      if (finalVisuals.length) setVisuals(finalVisuals)
      setStep('results')
    } catch (err) {
      setError(err.message)
      setStep('formats')
    }
  }, [brief, selectedFormats, selectedVisualFormats, audience, market])

  // --- Regenerate visuals only ---
  const regenerateVisuals = useCallback(async () => {
    if (!brief || selectedVisualFormats.length === 0) return

    setError('')
    setVisuals([])

    try {
      const res = await fetch(`${API_URL}/visuals/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_brief: brief,
          visual_formats: selectedVisualFormats,
        }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Erreur lors de la génération visuelle')
      }

      const data = await res.json()
      if (data.visuals) setVisuals(data.visuals)
    } catch (err) {
      setError(err.message)
    }
  }, [brief, selectedVisualFormats])

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
    setSelectedVisualFormats([])
    setAudience('')
    setMarket('')
    setAnalysis(null)
    setResults([])
    setVisuals([])
    setLoadingStep('')
    setCompletedSteps([])
    setError('')
  }

  // --- Active pipeline steps (filter out visual_direct if not selected) ---
  const activeSteps = selectedVisualFormats.length > 0
    ? PIPELINE_STEPS
    : PIPELINE_STEPS.filter(s => s.key !== 'visual_direct')

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

          <div className="card" style={{ marginBottom: 24 }}>
            <h2>02 — Choisir les formats texte ({selectedFormats.length}/5)</h2>
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
          </div>

          {/* Visual format selector */}
          <div className="card" style={{ marginBottom: 24 }}>
            <h2>03 — Visuels IA (optionnel)</h2>
            <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 16 }}>
              Génère des mockups visuels avec Nano Banana pour chaque format sélectionné.
            </p>
            <div className="formats-grid">
              {VISUAL_FORMATS.map(f => (
                <div
                  key={f.key}
                  className={`format-chip visual-chip ${selectedVisualFormats.includes(f.key) ? 'selected' : ''}`}
                  onClick={() => toggleVisualFormat(f.key)}
                >
                  <span className="chip-label">{f.label}</span>
                  <span className="chip-detail">{f.detail}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="btn-row">
              <button
                className="btn btn-primary"
                disabled={selectedFormats.length === 0}
                onClick={runRemix}
              >
                Générer {selectedFormats.length} déclinaison{selectedFormats.length > 1 ? 's' : ''}
                {selectedVisualFormats.length > 0 && ` + ${selectedVisualFormats.length} visuel${selectedVisualFormats.length > 1 ? 's' : ''}`}
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
              {activeSteps.map(s => (
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

          {/* Visual Director Results — shown first */}
          {visuals.length > 0 && (
            <div className="visuals-section">
              <div className="export-bar visuals-bar">
                <h2 style={{ fontFamily: 'var(--mono)', fontSize: 14, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, color: 'var(--accent)' }}>
                  Visual Director — {visuals.length} format{visuals.length > 1 ? 's' : ''}
                </h2>
                <button className="btn btn-secondary" onClick={regenerateVisuals}>
                  Re-générer
                </button>
              </div>
              <div className="visuals-grid">
                {visuals.map((v, i) => (
                  <VisualCard key={i} visual={v} />
                ))}
              </div>
            </div>
          )}

          {/* Standalone visual generation button when no visuals were requested */}
          {visuals.length === 0 && selectedVisualFormats.length === 0 && (
            <div className="card" style={{ marginTop: 0, marginBottom: 32, textAlign: 'center' }}>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 16 }}>
                Ajouter des visuels IA à ce remix ?
              </p>
              <div className="formats-grid" style={{ marginBottom: 16 }}>
                {VISUAL_FORMATS.map(f => (
                  <div
                    key={f.key}
                    className={`format-chip visual-chip ${selectedVisualFormats.includes(f.key) ? 'selected' : ''}`}
                    onClick={() => toggleVisualFormat(f.key)}
                  >
                    <span className="chip-label">{f.label}</span>
                    <span className="chip-detail">{f.detail}</span>
                  </div>
                ))}
              </div>
              {selectedVisualFormats.length > 0 && (
                <button className="btn btn-primary" onClick={regenerateVisuals}>
                  Générer {selectedVisualFormats.length} visuel{selectedVisualFormats.length > 1 ? 's' : ''}
                </button>
              )}
            </div>
          )}

          {/* Text remix results */}
          <div className="export-bar" style={{ marginTop: visuals.length > 0 ? 40 : 0 }}>
            <h2 style={{ fontFamily: 'var(--mono)', fontSize: 14, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, color: 'var(--text-muted)' }}>
              Déclinaisons texte
            </h2>
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

                  <details className="remix-details-section">
                    <summary className="section-label">Narration détaillée</summary>
                    <div className="section-value">{r.remix.narrative_description}</div>
                  </details>

                  <details className="remix-details-section">
                    <summary className="section-label">Notes de production</summary>
                    <div className="section-value">{r.remix.production_notes}</div>
                  </details>

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
