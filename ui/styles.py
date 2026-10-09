CSS_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Manrope:wght@400;500;600;700;800&display=swap');
@import url('https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.css');

/* ═══════════════════════════════════════════════════
   DESIGN TOKENS  (from the reference landing HTML)
═══════════════════════════════════════════════════ */
:root {
  --vellum-parchment:   #E8E0D2;
  --vellum-ivory:       #F5F1E8;
  --vellum-page:        #F9F6EF;
  --vellum-ink:         #24231F;
  --vellum-ink-soft:    rgba(36,35,31,0.92);
  --vellum-muted:       rgba(36,35,31,0.70);
  --vellum-faint:       rgba(36,35,31,0.48);
  --vellum-border:      rgba(36,35,31,0.20);
  --vellum-border-soft: rgba(36,35,31,0.12);
  --vellum-sage:        #7D8A72;
  --vellum-terra:       #B97862;
  --vellum-dusk:        #C8A39B;
  --vellum-shadow:      rgba(36,35,31,0.18);

  --spring-micro: cubic-bezier(0.22, 0.7, 0.25, 1);
  --dur-micro:    260ms;
  --dur-soft:     620ms;
}

/* ═══════════════════════════════════════════════════
   GLOBAL PAPER BACKGROUND
═══════════════════════════════════════════════════ */
html, body, [data-testid="stAppViewContainer"] {
  font-family: 'Manrope', 'Helvetica Neue', sans-serif !important;
  color: var(--vellum-ink) !important;
  background:
    radial-gradient(120% 90% at 16% 6%, rgba(248,244,236,.85), rgba(248,244,236,0) 55%),
    radial-gradient(110% 85% at 88% 104%, rgba(36,35,31,.07), rgba(36,35,31,0) 60%),
    var(--vellum-parchment) !important;
  -webkit-font-smoothing: antialiased;
}
::selection { background: rgba(183,120,98,0.28); }

/* Morning-light drift */
[data-testid="stAppViewContainer"]::before {
  content: "";
  position: fixed; inset: -12%; pointer-events: none; z-index: 0;
  background: radial-gradient(46% 38% at 30% 24%, rgba(252,249,242,.5), rgba(252,249,242,0) 70%);
  animation: vellum-morning 34s ease-in-out infinite alternate;
}
@keyframes vellum-morning {
  from { transform: translate(-2.2%,-1.4%); }
  to   { transform: translate(2.8%,2%) scale(1.05); }
}

/* Grain */
[data-testid="stAppViewContainer"]::after {
  content: "";
  position: fixed; inset: 0; pointer-events: none; z-index: 60;
  opacity: 0.05; mix-blend-mode: multiply;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='260' height='260'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter><rect width='260' height='260' filter='url(%23n)'/></svg>");
  background-size: 260px 260px;
}

/* Serif editorial body */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
.source-snippet {
  font-family: 'Cormorant Garamond', 'KaTeX_Main', Georgia, serif !important;
  font-size: 16px !important;
  line-height: 1.78 !important;
  color: var(--vellum-ink-soft) !important;
  font-weight: 500 !important;
}

/* ═══════════════════════════════════════════════════
   HIDE STREAMLIT CHROME  (workspace only)
═══════════════════════════════════════════════════ */
[data-testid="stSidebar"]                    { display: none !important; }
[data-testid="stToolbar"]                    { display: none !important; }
[data-testid="stStatusWidget"]               { display: none !important; }
[data-testid="stDecoration"]                 { display: none !important; }
header[data-testid="stHeader"]               { display: none !important; }
.block-container {
  padding-top: 1rem !important;
  padding-bottom: 1rem !important;
  max-width: 1440px !important;
}

/* Workspace entrance */
@keyframes vellum-settle {
  from { opacity: 0; transform: translateY(18px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ═══════════════════════════════════════════════════
   WORKSPACE TITLEPLATE
═══════════════════════════════════════════════════ */
.desk-header {
  background: var(--vellum-ivory);
  border: 1px solid var(--vellum-border);
  box-shadow: 0 24px 48px -32px var(--vellum-shadow);
  padding: 26px 34px 24px;
  margin-bottom: 26px;
  position: relative;
  animation: vellum-settle 0.9s var(--spring-micro) 0.05s backwards;
}
.desk-header::after {
  content: "";
  position: absolute; top: -1px; right: 34px;
  width: 5px; height: 34px;
  background: var(--vellum-terra);
  clip-path: polygon(0 0, 100% 0, 100% 100%, 50% calc(100% - 7px), 0 100%);
}
.desk-title-row {
  display: flex; justify-content: space-between; align-items: baseline;
  border-bottom: 1px solid var(--vellum-border);
  padding-bottom: 14px; margin-bottom: 14px; gap: 20px;
}
.desk-brand {
  font-family: 'Cormorant Garamond', Georgia, serif !important;
  font-weight: 600 !important;
  font-size: clamp(38px, 4.6vw, 58px) !important;
  line-height: 0.95 !important;
  color: var(--vellum-ink) !important;
  letter-spacing: 0.02em !important;
  text-transform: none !important;
  font-variant: normal !important;
  white-space: nowrap;
}
.desk-brand em {
  font-family: 'Cormorant Garamond', Georgia, serif !important;
  font-style: italic !important; font-weight: 500 !important;
  font-size: 0.42em !important; letter-spacing: 0.04em !important;
  color: rgba(36,35,31,0.88) !important; margin-left: 14px;
}
.desk-folio {
  font-family: 'Manrope', sans-serif;
  font-size: 11px; letter-spacing: 0.07em;
  color: var(--vellum-muted); text-align: right; line-height: 1.6; white-space: nowrap;
}
.desk-folio strong { display: block; color: var(--vellum-ink); font-weight: 700; font-size: 11.5px; }
.desk-intro {
  font-family: 'Cormorant Garamond', Georgia, serif !important;
  font-size: 16px !important; line-height: 1.72 !important;
  color: var(--vellum-ink-soft) !important; font-weight: 500 !important; margin: 0 !important;
}

/* Section headings — columns */
[data-testid="stMarkdownContainer"] h3 {
  font-family: 'Cormorant Garamond', Georgia, serif !important;
  font-weight: 600 !important; font-size: 27px !important;
  color: var(--vellum-ink) !important; letter-spacing: 0.01em !important; margin-bottom: 2px !important;
}
/* Center the Discussion heading in the chat column */
[data-testid="column"]:nth-child(2) [data-testid="stMarkdownContainer"] h3 {
  text-align: center !important;
}
[data-testid="stMarkdownContainer"] h4 {
  font-family: 'Manrope', sans-serif !important;
  font-weight: 800 !important; font-size: 11.5px !important;
  text-transform: uppercase !important; letter-spacing: 0.1em !important;
  color: var(--vellum-muted) !important;
}

/* ═══════════════════════════════════════════════════
   DOCUMENT LIBRARY
═══════════════════════════════════════════════════ */
.doc-row {
  background: var(--vellum-page);
  border: 1px solid var(--vellum-border-soft); border-radius: 0;
  padding: 14px 16px; margin-bottom: 10px;
  box-shadow: 0 10px 22px -18px var(--vellum-shadow);
  transition: transform var(--dur-micro) var(--spring-micro), box-shadow var(--dur-micro) ease;
  animation: leaf-in 0.55s var(--spring-micro) backwards;
}
.doc-row:hover { transform: translateY(-2px); box-shadow: 0 18px 30px -20px var(--vellum-shadow); }
@keyframes leaf-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.doc-title {
  font-family: 'Cormorant Garamond', Georgia, serif !important;
  font-size: 17px !important; font-weight: 600 !important; color: var(--vellum-ink) !important;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.doc-meta {
  font-family: 'Manrope', sans-serif; font-size: 10.5px; color: var(--vellum-muted);
  margin-top: 5px; text-transform: uppercase; letter-spacing: 0.07em; font-weight: 600;
}

.status-indicator { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 6px; }
.status-ready    { background-color: var(--vellum-sage); }
.status-indexing { background-color: var(--vellum-terra); animation: pulse-dot 1.3s infinite ease-in-out; }
@keyframes pulse-dot {
  0%,100% { opacity: .45; transform: scale(.9); }
  50%      { opacity: 1;   transform: scale(1.15); }
}
.doc-progress { height: 2px; background: rgba(36,35,31,.08); margin-top: 10px; overflow: hidden; }
.doc-progress span { display: block; height: 100%; background: var(--vellum-sage); transition: width 0.45s var(--spring-micro); }
.scanned-pill {
  font-family: 'Manrope', sans-serif; font-size: 10px; color: #9a4b34;
  background: rgba(183,120,98,.12); border: 1px solid rgba(183,120,98,.4);
  padding: 3px 8px; margin-top: 6px; font-weight: 600; letter-spacing: 0.02em;
}

/* ═══════════════════════════════════════════════════
   EVIDENCE
═══════════════════════════════════════════════════ */
.source-card {
  background: var(--vellum-ivory);
  border: 1px solid var(--vellum-border-soft); border-left: 2px solid var(--vellum-sage);
  padding: 16px 18px; margin-bottom: 14px;
  box-shadow: 0 14px 26px -22px var(--vellum-shadow);
  transition: transform var(--dur-micro) var(--spring-micro), box-shadow var(--dur-micro) ease;
  animation: leaf-in 0.5s var(--spring-micro) backwards;
}
.source-card:hover { transform: translateY(-2px); box-shadow: 0 22px 34px -22px var(--vellum-shadow); }
.source-card-active { border-left: 2px solid var(--vellum-terra); background: #FBF7EE; }
.source-header {
  display: flex; justify-content: space-between; align-items: baseline;
  gap: 10px; margin-bottom: 10px;
  border-bottom: 1px solid var(--vellum-border-soft); padding-bottom: 7px;
}
.source-doc-ref {
  font-family: 'Manrope', sans-serif; font-size: 11px; font-weight: 800;
  text-transform: uppercase; letter-spacing: 0.08em; color: var(--vellum-ink);
}
.source-sim-score {
  font-family: 'Manrope', sans-serif; font-size: 9.5px;
  color: var(--vellum-ivory); background: var(--vellum-sage);
  padding: 2px 8px; font-weight: 700; letter-spacing: 0.06em; white-space: nowrap;
}
.source-snippet { font-size: 15px !important; color: var(--vellum-ink-soft) !important; font-weight: 500 !important; }
.source-highlight { background: rgba(183,120,98,.22); color: var(--vellum-ink); padding: 1px 4px; font-weight: 700; }
.inline-evidence-label {
  font-family: 'Manrope', sans-serif; font-size: 10.5px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.1em; color: var(--vellum-muted); margin: 4px 0 10px;
}

.citation-chip {
  display: inline-flex; align-items: center;
  font-family: 'Manrope', sans-serif; font-size: 10px;
  color: var(--vellum-ivory); background: var(--vellum-ink);
  border-radius: 1px; padding: 1px 6px; margin: 0 3px;
  cursor: pointer; vertical-align: middle; text-decoration: none;
  font-weight: 700; transition: all var(--dur-micro) ease;
}
.citation-chip:hover { background: var(--vellum-terra); transform: translateY(-1px); }

.process-status {
  font-family: 'Manrope', sans-serif; font-size: 11px; font-weight: 700;
  letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--vellum-muted); display: flex; align-items: center; gap: 10px;
}
.process-bar {
  width: 26px; height: 2px; background: var(--vellum-terra); display: inline-block;
  animation: process-sweep 1.1s ease-in-out infinite alternate;
}
@keyframes process-sweep { from { transform: scaleX(.35); } to { transform: scaleX(1); } }
.rewritten-notice {
  font-family: 'Manrope', sans-serif; font-size: 11px; font-weight: 600;
  color: var(--vellum-muted); border-left: 2px solid var(--vellum-border);
  padding-left: 10px; margin-bottom: 6px;
}

/* ═══════════════════════════════════════════════════
   EMPTY STATE
═══════════════════════════════════════════════════ */
.empty-state {
  text-align: center; padding: 64px 36px;
  background: var(--vellum-ivory); border: 1px solid var(--vellum-border);
  margin: 24px auto; max-width: 560px;
  box-shadow: 0 30px 54px -40px var(--vellum-shadow);
  animation: vellum-settle 0.8s var(--spring-micro) 0.15s backwards;
}
.empty-state-eyebrow {
  font-family: 'Manrope', sans-serif; font-size: 9.5px; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--vellum-faint); margin-bottom: 14px; font-weight: 700;
}
.empty-state-title {
  font-family: 'Cormorant Garamond', Georgia, serif;
  font-size: 28px; font-weight: 600; color: var(--vellum-ink); margin-bottom: 10px;
}
.empty-state-subtitle {
  font-family: 'Cormorant Garamond', Georgia, serif;
  font-style: italic; font-size: 17px; color: var(--vellum-muted); line-height: 1.6;
}
.empty-state-cta {
  margin-top: 26px; font-family: 'Manrope', sans-serif;
  font-size: 10.5px; font-weight: 800; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--vellum-terra);
  border-top: 1px solid var(--vellum-border-soft); padding-top: 16px;
}

/* ═══════════════════════════════════════════════════
   UPLOADER
═══════════════════════════════════════════════════ */
[data-testid="stFileUploader"] section {
  border: 1px dashed var(--vellum-border) !important;
  background: var(--vellum-ivory) !important; border-radius: 0 !important;
  box-shadow: none !important; transition: all var(--dur-micro) var(--spring-micro) !important;
}
[data-testid="stFileUploader"] section:hover {
  transform: translateY(-2px) !important;
  border-color: var(--vellum-sage) !important;
  box-shadow: 0 16px 26px -20px var(--vellum-shadow) !important;
}
[data-testid="stFileUploader"] button {
  font-family: 'Manrope', sans-serif !important; text-transform: uppercase !important;
  letter-spacing: 0.06em !important; font-size: 11px !important; font-weight: 700 !important;
}

/* ═══════════════════════════════════════════════════
   CHAT
═══════════════════════════════════════════════════ */
[data-testid="stChatMessage"] {
  background: var(--vellum-page) !important;
  border: 1px solid var(--vellum-border-soft) !important;
  box-shadow: 0 12px 24px -20px var(--vellum-shadow) !important;
  border-radius: 0 !important; margin-bottom: 16px !important;
  animation: leaf-in 0.5s var(--spring-micro) backwards;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li { font-size: 16px !important; font-weight: 500 !important; }

/* ── Chat input: blends into the parchment, sits flush at the bottom ── */
/* The stBottom container itself */
.stBottom, [data-testid="stBottom"] {
  background: var(--vellum-parchment) !important;
  border-top: 1px solid var(--vellum-border) !important;
  padding: 10px 24px 14px !important;
  margin: 0 !important;
}
/* Remove any internal gaps inside stBottomBlockContainer */
[data-testid="stBottomBlockContainer"] {
  padding: 0 !important;
  margin: 0 !important;
  max-width: 1440px !important;
  margin-left: auto !important;
  margin-right: auto !important;
}
/* The textarea itself */
[data-testid="stChatInput"] textarea {
  border: 1px solid var(--vellum-border) !important;
  background: var(--vellum-ivory) !important;
  color: var(--vellum-ink) !important;
  font-family: 'Cormorant Garamond', Georgia, serif !important;
  font-size: 16.5px !important;
  font-weight: 500 !important;
  border-radius: 0 !important;
  padding-left: 16px !important;
  transition: border-color var(--dur-micro) ease, box-shadow var(--dur-micro) ease !important;
}
[data-testid="stChatInput"] textarea:focus {
  outline: none !important;
  border-color: var(--vellum-sage) !important;
  box-shadow: 0 14px 26px -22px var(--vellum-shadow) !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--vellum-muted) !important; }
[data-testid="stChatInput"] button { border-radius: 0 !important; }

/* ═══════════════════════════════════════════════════
   BUTTONS & CONTROLS
═══════════════════════════════════════════════════ */
.stButton > button {
  background-color: transparent !important; color: var(--vellum-ink) !important;
  border: 1px solid var(--vellum-border) !important; border-radius: 0 !important;
  font-family: 'Manrope', sans-serif !important; font-size: 10.5px !important;
  font-weight: 800 !important; text-transform: uppercase !important;
  letter-spacing: 0.08em !important; box-shadow: none !important;
  transition: all var(--dur-micro) var(--spring-micro) !important;
}
.stButton > button:hover {
  border-color: var(--vellum-sage) !important; color: var(--vellum-ink) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 10px 18px -14px var(--vellum-shadow) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

div[data-testid="stRadio"] > div {
  background: transparent !important; padding: 0 !important;
  border: none !important; box-shadow: none !important; gap: 10px !important;
}
div[data-testid="stRadio"] label {
  background: transparent; border: 1px solid var(--vellum-border-soft);
  padding: 4px 12px; font-family: 'Manrope', sans-serif;
  font-size: 10.5px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.07em; color: var(--vellum-ink); cursor: pointer;
  transition: all var(--dur-micro) ease;
}
div[data-testid="stRadio"] label:hover { border-color: var(--vellum-sage); }

[data-testid="stExpander"] {
  border: 1px solid var(--vellum-border-soft) !important;
  background: var(--vellum-page) !important;
  border-radius: 10px !important;
  overflow: hidden !important;
}
[data-testid="stExpander"] summary {
  font-family: 'Cormorant Garamond', Georgia, serif !important;
  font-size: 15.5px !important; font-weight: 600 !important;
  border-radius: 10px !important;
}
[data-testid="stExpander"] p { font-size: 14.5px !important; }
[data-testid="stExpander"] svg { color: var(--vellum-faint) !important; }

/* ═══════════════════════════════════════════════════
   RESPONSIVE
═══════════════════════════════════════════════════ */
@media (max-width: 1024px) {
  .desk-title-row { flex-direction: column; gap: 6px; }
  .desk-folio { text-align: left; }
}
@media (max-width: 640px) {
  .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
  .desk-header { padding: 20px 22px 18px; }
  .source-header { flex-direction: column; gap: 4px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
"""
