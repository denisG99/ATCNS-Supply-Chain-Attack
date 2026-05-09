const CODE_SELECTOR = '#root > div > pre > div > code';
const HIGHLIGHT_BG = 'rgba(255, 220, 0, 0.18)';
const HIGHLIGHT_BORDER = '3px solid #ffdc00';

let lastCommitHash = '';
let lastSignature = '';
let pendingTargets = null; // lines to highlight, kept across scroll events

// ── Detect the real line height from the first normal row ──────────────────
function detectLineHeight(children) {
  for (const el of children) {
    const h = parseInt(el.style.height);
    if (!isNaN(h) && h > 0 && h <= 40) return h; // sane single-line range
  }
  return 20; // safe fallback
}

// ── Find ALL spacers (GitHub can have more than one) ───────────────────────
function getSpacers(children, lineHeight) {
  // A spacer is any child whose height is a multiple of lineHeight AND > lineHeight
  return children
    .map((el, index) => {
      const h = parseInt(el.style.height);
      if (isNaN(h) || h <= lineHeight) return null;
      const lines = Math.round(h / lineHeight);
      return { index, lines };
    })
    .filter(Boolean);
}

// ── Map every DOM child index → absolute line number ──────────────────────
function buildLineMap(children, lineHeight) {
  const spacers = getSpacers(children, lineHeight);
  const map = new Map(); // domIndex → absoluteLineNumber
  let absoluteLine = 1;

  for (let i = 0; i < children.length; i++) {
    const spacer = spacers.find(s => s.index === i);
    if (spacer) {
      // advance the counter by however many lines the spacer represents
      absoluteLine += spacer.lines;
    } else {
      const h = parseInt(children[i].style.height);
      if (!isNaN(h) && Math.abs(h - lineHeight) <= 2) {
        // real code line (allow ±2 px tolerance)
        map.set(i, absoluteLine);
        absoluteLine++;
      }
    }
  }
  return map;
}

// ── Highlight helpers ──────────────────────────────────────────────────────
function clearHighlights() {
  document.querySelectorAll('[data-gh]').forEach(el => {
    el.style.background = '';
    el.style.borderLeft = '';
    el.style.paddingLeft = '';
    delete el.dataset.gh;
  });
}

function applyHighlight(el) {
  el.style.background = HIGHLIGHT_BG;
  el.style.borderLeft = HIGHLIGHT_BORDER;
  el.style.paddingLeft = '4px';
  el.dataset.gh = '1';
}

// ── Core render pass ───────────────────────────────────────────────────────
function renderHighlights(targetSet) {
  const code = document.querySelector(CODE_SELECTOR);
  if (!code || !targetSet?.size) return;

  const children = [...code.children];
  const lineHeight = detectLineHeight(children);
  const lineMap = buildLineMap(children, lineHeight);

  // Clear only rows currently in DOM (avoids flicker on partial re-renders)
  clearHighlights();

  lineMap.forEach((absoluteLine, domIndex) => {
    if (targetSet.has(absoluteLine)) {
      applyHighlight(children[domIndex]);
    }
  });
}

// ── Commit hash ────────────────────────────────────────────────────────────
function getCommitHash() {
  const link = document.querySelector('a[href*="/commit/"]');
  if (!link) return null;
  const match = link.href.match(/\/commit\/([a-f0-9]+)/);
  return match?.[1] || null;
}

// ── Signature: detect DOM changes worth re-processing ─────────────────────
function computeSignature(code) {
  const children = [...code.children];
  const lineHeight = detectLineHeight(children);
  const spacers = getSpacers(children, lineHeight);
  // Include total children count so additions/removals are caught
  return `${children.length}:${spacers.map(s => `${s.index}-${s.lines}`).join(',')}`;
}

// ── Main refresh (called by interval + scroll) ─────────────────────────────
function refresh() {
  const code = document.querySelector(CODE_SELECTOR);
  if (!code) return;

  const commitHash = getCommitHash();
  if (!commitHash) return;

  if (commitHash !== lastCommitHash) {
    lastCommitHash = commitHash;
    lastSignature = '';
    pendingTargets = null;
  }

  // If we already know the target lines, just re-render (handles scroll)
  if (pendingTargets) {
    renderHighlights(pendingTargets);
    return;
  }

  const signature = computeSignature(code);
  if (signature === lastSignature) return;
  lastSignature = signature;

  chrome.storage.local.get(['highlightedLines'], (result) => {
    if (!result.highlightedLines) return;
    let data;
    try { data = JSON.parse(result.highlightedLines); } catch { return; }
    const targets = data?.[commitHash];
    if (!targets?.length) return;

    pendingTargets = new Set(targets);
    renderHighlights(pendingTargets);
  });
}

// ── Wiring ─────────────────────────────────────────────────────────────────
setInterval(refresh, 150);

// Re-apply on scroll so newly rendered virtual rows get highlighted
document.addEventListener('scroll', () => {
  if (pendingTargets) renderHighlights(pendingTargets);
}, true); // capture phase catches the inner scrollable container

window.addEventListener('popstate', () => {
  lastSignature = '';
  lastCommitHash = '';
  pendingTargets = null;
  clearHighlights();
});

window.addEventListener('load', refresh);

document.addEventListener('keydown', (event) => {
  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
    pendingTargets = null;
    clearHighlights();
  }
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'HIGHLIGHT') {
    chrome.storage.local.set({ highlightedLines: JSON.stringify(msg.lines) });
    lastSignature = '';
    pendingTargets = null;
    setTimeout(refresh, 150);
  }
});