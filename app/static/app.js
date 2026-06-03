'use strict';

// ---- Session (localStorage UUID, 7-day sliding window) ----
function _getSessionId() {
  const key = 'nz_building_session_id';
  let id = localStorage.getItem(key);
  if (!id) { id = crypto.randomUUID(); localStorage.setItem(key, id); }
  return id;
}

// ---- Debug mode (#debug or Ctrl+Shift+D) ----
let _debugKey = '';
let _debugMode = false;

const compareGrid = document.getElementById('compare-grid') || document.createElement('div');

function _getSelectedStrategies() {
  const boxes = document.querySelectorAll('.strategy-check:checked');
  return boxes.length ? [...boxes].map(cb => cb.value) : ['vector'];
}

function _setDebugUI(on) {
  const badge = document.getElementById('debug-badge');
  const strat = document.getElementById('debug-strategy');
  if (badge) badge.classList.toggle('hidden', !on);
  if (strat) strat.style.display = on ? 'flex' : '';
  if (!on) {
    compareGrid.style.display = '';
    compareGrid.innerHTML = '';
    askAnotherRow.classList.remove('visible');
  }
}

async function _activateDebug() {
  if (_debugMode) {
    _debugMode = false; _debugKey = '';
    _setDebugUI(false);
    history.replaceState(null, '', location.pathname);
    alert('Debug mode off.');
    return;
  }
  const key = prompt('Debug key:');
  if (!key) return;
  try {
    const r = await fetch('/debug/ping', { headers: { 'X-API-Key': _apiToken, 'X-Debug-Key': key } });
    if (r.ok) { _debugKey = key; _debugMode = true; _setDebugUI(true); }
    else alert('Invalid debug key.');
  } catch (_) { alert('Could not validate debug key.'); }
}

function _initDebugShortcut() {
  if (location.hash === '#debug') { history.replaceState(null, '', location.pathname); _activateDebug(); }
  window.addEventListener('hashchange', () => {
    if (location.hash === '#debug') { history.replaceState(null, '', location.pathname); _activateDebug(); }
  });
  document.addEventListener('keydown', e => {
    if (e.ctrlKey && e.shiftKey && e.key === 'D') { e.preventDefault(); _activateDebug(); }
  });
}

const _STRATEGY_LABELS = { vector: 'Vector', mmr: 'MMR diverse' };

function _renderDebugPanel(dbg, dbgDone) {
  const existing = document.getElementById('debug-panel');
  if (existing) existing.remove();
  const scores = dbg.scores || [];
  const bars = scores.map((s, i) => {
    const pct = Math.round(s * 100);
    const cls = s >= 0.80 ? 'high' : s >= 0.76 ? 'mid' : 'low';
    return `<div class="debug-score-row"><span class="debug-score-label">S${i+1}</span><div class="debug-score-bar-wrap"><div class="debug-score-bar ${cls}" style="width:${pct}%"></div></div><span class="debug-score-val">${s.toFixed(4)}</span></div>`;
  }).join('');
  const panel = document.createElement('div');
  panel.id = 'debug-panel';
  panel.className = 'debug-panel';
  panel.innerHTML = `<h4>Retrieval debug</h4>${bars}<div class="debug-stats">chunks <span>${dbg.chunks}</span> | retrieve <span>${dbg.retrieve_ms}ms</span>${dbgDone ? ` | generate <span>${dbgDone.generate_ms}ms</span> | total <span>${dbgDone.total_ms}ms</span>` : ''}</div>`;
  resultCard.appendChild(panel);
}

function _renderContextDebugPanel(ev, container) {
  const existing = (container || resultCard).querySelector('.context-debug-panel');
  if (existing) existing.remove();
  const panel = document.createElement('details');
  panel.className = 'context-debug-panel';
  const summary = document.createElement('summary');
  summary.className = 'context-debug-toggle';
  summary.textContent = 'Context sent to model';
  panel.appendChild(summary);
  const body = document.createElement('div');
  body.className = 'context-debug-body';

  const sr = ev.statute_routing || {};
  let qHtml = '<div class="ctx-query-block">';
  qHtml += `<div class="ctx-query-row"><span class="ctx-label">Original query</span><span class="ctx-query-text">${Astraea.escapeHtml(ev.original_query || '')}</span></div>`;
  if (ev.rewritten_query !== undefined) {
    const changed = ev.rewritten_query && ev.rewritten_query !== ev.original_query;
    qHtml += `<div class="ctx-query-row"><span class="ctx-label">Rewritten query</span><span class="ctx-query-text${changed ? ' ctx-rewrite-changed' : ''}">${Astraea.escapeHtml(ev.rewritten_query || ev.original_query || '')}</span></div>`;
    qHtml += `<div class="ctx-query-row"><span class="ctx-label">Rewrite</span><span class="ctx-meta-val">${ev.rewrite_used ? 'yes' : 'no'}</span></div>`;
  }
  if (sr.triggered) {
    const routes = (sr.matched_routes || []).join(', ');
    const injected = (sr.forced_sections || []).join(', ') || 'none';
    qHtml += `<div class="ctx-query-row"><span class="ctx-label">Statute routing</span><span class="ctx-meta-val ctx-gate-yes">routes: ${Astraea.escapeHtml(routes)} | injected: ${Astraea.escapeHtml(injected)}</span></div>`;
  }
  qHtml += '</div>';
  const qBlock = document.createElement('div');
  qBlock.innerHTML = qHtml;
  body.appendChild(qBlock.firstElementChild);

  const anchor = ev.anchor || {};
  if (anchor.sections && anchor.sections.length) {
    const lbl = document.createElement('div');
    lbl.className = 'ctx-section-label';
    lbl.textContent = `Legislation anchor - ${anchor.method || 'vector'} (not [SN] cited)`;
    body.appendChild(lbl);
    anchor.sections.forEach(s => {
      const card = document.createElement('div');
      card.className = 'ctx-card ctx-card-leg';
      card.innerHTML = `<div class="ctx-card-header">${Astraea.escapeHtml(s.document_id || s.title || '')}</div><div class="ctx-card-meta">legislation | ~${s.tokens ?? '?'} tokens</div><div class="ctx-card-preview">${Astraea.escapeHtml((s.preview || '').slice(0, 400))}</div>`;
      body.appendChild(card);
    });
  }

  const chunks = ev.chunks || [];
  if (chunks.length) {
    const lbl = document.createElement('div');
    lbl.className = 'ctx-section-label';
    lbl.textContent = `Guidance chunks (${chunks.length})`;
    body.appendChild(lbl);
    chunks.forEach(c => {
      const card = document.createElement('div');
      card.className = 'ctx-card ctx-card-case';
      card.id = `ctx-S${c.source_index}`;
      card.innerHTML = `<div class="ctx-card-header">[S${c.source_index}] ${Astraea.escapeHtml(c.document_id || '')}</div><div class="ctx-card-meta">score: ${c.score != null ? c.score.toFixed(4) : 'n/a'} | ~${c.tokens ?? '?'} tokens</div><div class="ctx-card-preview">${Astraea.escapeHtml((c.preview || '').slice(0, 300))}</div>`;
      body.appendChild(card);
    });
  }

  panel.appendChild(body);
  (container || resultCard).appendChild(panel);
}

// ---- Zone lookup ----
let _zoneAbort = null;
let _zoneTimeout = null;
let _currentZone = null;

async function lookupZone(address) {
  const zoneEl = document.getElementById('zone-result');
  if (!zoneEl) return;
  if (!address.trim()) { zoneEl.innerHTML = ''; _currentZone = null; return; }
  zoneEl.innerHTML = '<span class="zone-badge loading">Looking up zone...</span>';
  _currentZone = null;
  if (_zoneAbort) _zoneAbort.abort();
  _zoneAbort = new AbortController();
  try {
    const r = await fetch('/zone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': _apiToken },
      body: JSON.stringify({ address: address.trim() }),
      signal: _zoneAbort.signal,
    });
    const data = await r.json();
    if (data.found && data.zone) {
      _currentZone = data.zone;
      zoneEl.innerHTML = `<span class="zone-badge">${Astraea.escapeHtml(data.zone.zone_name)} (${Astraea.escapeHtml(data.zone.zone_code)}) - ${Astraea.escapeHtml(data.zone.council)}</span>`;
    } else if (data.found) {
      zoneEl.innerHTML = '<span class="zone-badge error">Address found but outside covered zones</span>';
    } else {
      zoneEl.innerHTML = '<span class="zone-badge error">Address not found - try including city name</span>';
    }
  } catch (e) {
    if (e.name !== 'AbortError') zoneEl.innerHTML = '';
  }
}

// ---- Token + DOM refs ----
let _apiToken = '';

const form = document.getElementById('ask-form');
const addressEl = document.getElementById('address');
const questionEl = document.getElementById('question');
const charCountEl = document.getElementById('char-count');
const submitBtn = document.getElementById('submit-btn');
const queueNotice = document.getElementById('queue-notice');
const loadingCard = document.getElementById('loading-card');
const loadingText = document.getElementById('loading-text');
const resultCard = document.getElementById('result-card');
const answerBody = document.getElementById('answer-body');
const sourcesSection = document.getElementById('sources-section');
const sourcesList = document.getElementById('sources-list');
const errorCard = document.getElementById('error-card');
const errorText = document.getElementById('error-text');
const askAnotherRow = document.getElementById('ask-another-row');
const thumbUp = document.getElementById('thumb-up');
const thumbDown = document.getElementById('thumb-down');
const feedbackComment = document.getElementById('feedback-comment');
const feedbackText = document.getElementById('feedback-text');
const feedbackSubmit = document.getElementById('feedback-submit');
const feedbackThanks = document.getElementById('feedback-thanks');

const LOADING_MESSAGES = [
  'Searching Building Act and district plan rules...',
  'Analysing consent requirements...',
  'Checking Schedule 1 exemptions...',
  'Preparing your answer...',
];

let loadingInterval = null;
let loadingStep = 0;
let currentQuestion = '';
let currentRating = null;
let _debugInfo = null;
let _artifact = {};

// ---- Address lookup ----
addressEl.addEventListener('input', () => {
  clearTimeout(_zoneTimeout);
  const val = addressEl.value.trim();
  if (!val) { document.getElementById('zone-result').innerHTML = ''; _currentZone = null; return; }
  _zoneTimeout = setTimeout(() => lookupZone(val), 600);
});

// ---- Char counter ----
questionEl.addEventListener('input', () => {
  const len = questionEl.value.length;
  charCountEl.textContent = len;
  charCountEl.parentElement.classList.toggle('near-limit', len > 1100);
});

// ---- Example buttons ----
document.querySelectorAll('.example-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    questionEl.value = btn.dataset.q;
    questionEl.dispatchEvent(new Event('input'));
    questionEl.focus();
  });
});

// ---- Queue polling ----
async function pollQueue() {
  await Astraea.pollQueue(queueNotice);
}

// ---- Source rendering (building-specific labels) ----
function renderSources(sources, legislation) {
  Astraea.renderSources(sources, legislation, {
    legislationGroupLabel: 'Relevant legislation',
    decisionGroupLabel: 'MBIE guidance',
    decisionLabel: 'MBIE Guidance',
  });
}

function renderConfidence(ev) {
  Astraea.renderConfidence(ev, resultCard);
}

// ---- Artifact ----
function _resetArtifact(question, strategy) {
  _artifact = {
    question, strategy,
    irac: false,
    debug_mode: _debugMode,
    ts_start: new Date().toISOString(), ts_end: null,
    user_agent: navigator.userAgent,
    answer: '', sources: [], legislation: [],
    confidence: null, debug: null, debug_timing: null, context_debug: null,
  };
}

// ---- Feedback ----
function resetFeedback() {
  currentRating = null;
  thumbUp.classList.remove('active');
  thumbDown.classList.remove('active');
  feedbackComment.style.display = 'none';
  feedbackText.value = '';
  feedbackThanks.style.display = 'none';
  document.getElementById('feedback-row').style.display = 'flex';
}

function submitFeedback(rating) {
  if (currentRating === rating) {
    currentRating = null;
    thumbUp.classList.remove('active'); thumbDown.classList.remove('active');
    feedbackComment.style.display = 'none'; return;
  }
  currentRating = rating;
  thumbUp.classList.toggle('active', rating === 1);
  thumbDown.classList.toggle('active', rating === -1);
  feedbackComment.style.display = 'block';
  if (rating === -1) Astraea.saveFullFeedback(_artifact, -1, '', false, _apiToken);
}

thumbUp.addEventListener('click', () => submitFeedback(1));
thumbDown.addEventListener('click', () => submitFeedback(-1));
document.getElementById('debug-capture').addEventListener('click', async () => {
  const btn = document.getElementById('debug-capture');
  await Astraea.saveFullFeedback(_artifact, 0, '', true, _apiToken);
  btn.classList.add('saved');
  btn.title = 'Debug context saved';
  setTimeout(() => { btn.classList.remove('saved'); btn.title = 'Save debug context for analysis'; }, 2000);
});
feedbackSubmit.addEventListener('click', async () => {
  if (currentRating === null) return;
  try {
    await fetch('/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': _apiToken },
      body: JSON.stringify({ question: currentQuestion, rating: currentRating, comment: feedbackText.value.trim() }),
    });
  } catch (_) {}
  feedbackComment.style.display = 'none';
  document.getElementById('feedback-row').style.display = 'none';
  feedbackThanks.style.display = 'block';
});

// ---- State helpers ----
function showLoading() {
  const vp = document.getElementById('verification-panel');
  if (vp) vp.remove();
  loadingCard.classList.add('visible');
  resultCard.classList.remove('visible');
  errorCard.classList.remove('visible');
  sourcesSection.classList.remove('visible');
  askAnotherRow.classList.remove('visible');
  submitBtn.disabled = true;
  loadingStep = 0;
  loadingText.textContent = LOADING_MESSAGES[0];
  loadingInterval = setInterval(() => {
    loadingStep = (loadingStep + 1) % LOADING_MESSAGES.length;
    loadingText.textContent = LOADING_MESSAGES[loadingStep];
  }, 5000);
}

function showStreamingResult() {
  clearInterval(loadingInterval);
  loadingCard.classList.remove('visible');
  errorCard.classList.remove('visible');
  resultCard.classList.add('visible');
  askAnotherRow.classList.add('visible');
  resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function finaliseResult(fullText, sources, legislation) {
  _artifact.answer = fullText;
  _artifact.ts_end = new Date().toISOString();
  answerBody.innerHTML = Astraea.renderAnswer(fullText);
  renderSources(sources, legislation);
  resetFeedback();
  submitBtn.disabled = false;
}

function showError(message) {
  clearInterval(loadingInterval);
  loadingCard.classList.remove('visible');
  resultCard.classList.remove('visible');
  sourcesSection.classList.remove('visible');
  errorText.textContent = message;
  errorCard.classList.add('visible');
  submitBtn.disabled = false;
}

function resetToForm() {
  resultCard.classList.remove('visible');
  errorCard.classList.remove('visible');
  sourcesSection.classList.remove('visible');
  askAnotherRow.classList.remove('visible');
  ['confidence-badge', 'debug-panel'].forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });
  resultCard.querySelectorAll('.context-debug-panel').forEach(p => p.remove());
  questionEl.value = '';
  charCountEl.textContent = '0';
  questionEl.focus();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ---- Form submit ----
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const question = questionEl.value.trim();
  if (!question) { questionEl.focus(); return; }
  currentQuestion = question;
  const address = addressEl.value.trim() || null;

  showLoading();
  _debugInfo = null;
  _resetArtifact(question, 'vector');

  let res;
  try {
    res = await fetch('/ask/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': _apiToken },
      body: JSON.stringify({
        question,
        address,
        session_id: _getSessionId(),
        debug_key: _debugKey,
        strategy: 'vector',
        irac: false,
        feedback_context: true,
      }),
    });
  } catch (_) {
    showError('Could not connect to the server. Please check your connection and try again.');
    return;
  }

  if (!res.ok) {
    let msg = 'An error occurred.';
    try { const d = await res.json(); msg = (d.detail && d.detail.error) || d.detail || msg; } catch (_) {}
    if (res.status === 429) showError('You already have a query in progress. Please wait for it to finish.');
    else if (res.status === 503) showError('The server is busy right now. Please try again in a moment.');
    else showError(msg);
    return;
  }

  let rawAnswer = '';
  let streamedSources = [];
  let streamedLegislation = [];
  let streamingStarted = false;

  try {
    await Astraea.streamEvents(res, event => {
      if (event.type === 'sources') {
        streamedSources = event.sources;
        streamedLegislation = event.legislation || [];
        _artifact.sources = event.sources || [];
        _artifact.legislation = event.legislation || [];
        renderSources(streamedSources, streamedLegislation);
      } else if (event.type === 'confidence') {
        _artifact.confidence = { level: event.level, message: event.message };
        renderConfidence(event);
      } else if (event.type === 'debug') {
        _artifact.debug = event;
        _debugInfo = event;
      } else if (event.type === 'debug_done') {
        _artifact.debug_timing = { generate_ms: event.generate_ms, total_ms: event.total_ms };
        if (_debugInfo) _renderDebugPanel(_debugInfo, event);
      } else if (event.type === 'queue') {
        loadingText.textContent = `Position ${event.position} in queue - ~${event.estimated_wait_s}s`;
      } else if (event.type === 'context_debug') {
        _artifact.context_debug = event;
        if (_debugMode) _renderContextDebugPanel(event, resultCard);
      } else if (event.type === 'token') {
        if (!streamingStarted) { streamingStarted = true; showStreamingResult(); answerBody.textContent = ''; }
        rawAnswer += event.text;
        _artifact.answer = rawAnswer;
        answerBody.textContent = rawAnswer;
      } else if (event.type === 'done') {
        finaliseResult(rawAnswer, streamedSources, streamedLegislation);
      } else if (event.type === 'error') {
        showError(event.message || 'An error occurred.');
      }
    });
    if (streamingStarted && rawAnswer) finaliseResult(rawAnswer, streamedSources, streamedLegislation);
  } catch (_) {
    showError('Lost connection while receiving the answer. Please try again.');
  }
});

// ---- Ask another / retry ----
document.getElementById('ask-another-btn').addEventListener('click', resetToForm);
document.getElementById('retry-btn').addEventListener('click', resetToForm);

// ---- Disclaimer ----
document.getElementById('show-terms').addEventListener('click', e => {
  e.preventDefault();
  document.getElementById('disclaimer-modal').classList.add('visible');
  document.body.classList.add('modal-open');
});

// ---- Init ----
Astraea.loadToken().then(t => { _apiToken = t; });
_initDebugShortcut();
pollQueue();
setInterval(pollQueue, 15000);
Astraea.initDisclaimer('nzbc_agreed_v1');
