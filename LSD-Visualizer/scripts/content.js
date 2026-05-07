/*
TODO:
- fixare observer su file grossi: scendendo sulla pagina evidenzia linea agiuntive
*/
function getVisibleLines() {
  return [...document.querySelectorAll('#root > div > pre > div > code > div')].filter(div => {
    // Must have actual height (not 0px spacers or hidden transition divs)
    const h = div.style.height;
    if (h === '0px' || h === '') return false;
    // Must contain a span (actual code), not just a <br>
    return div.querySelector('span') !== null || div.innerHTML.includes('<br>');
  });
}


function highlightLines(lineNumbers) {
  // The code lines are divs inside the <code> element
  var lineDivs = getVisibleLines();
  //var lineDivs = document.querySelectorAll('#root > div > pre > div > code > div');

  lineNumbers.forEach(n => {
    // Lines are 1-indexed for the user
    var div = lineDivs[n - 1];
    if (div) {
      div.style.background = 'rgba(255, 220, 0, 0.25)';
      div.style.borderLeft = '3px solid #ffdc00';
      div.style.paddingLeft = '4px';
      div.classList.add('gh-highlight');
    }
  });
}

function clearHighlights() {
  document.querySelectorAll('.gh-highlight').forEach(el => {
    el.style.background = '';
    el.style.borderLeft = '';
    el.style.paddingLeft = '';
    
    el.classList.remove('gh-highlight');
  });
}

function getCommitHash() {
  var link = document.querySelector('a[href*="/commit/"]');
  var hash = link.href.split('/commit/')[1];

  return hash;
}

//-----------------------------------------------------------------------------

const observer = new MutationObserver(() => {
  chrome.storage.local.get(["highlightedLines"], (result) => {
    var commitHash = getCommitHash();
    var lines = JSON.parse(result.highlightedLines);

    highlightLines(lines[commitHash]);
  });
});

// clear highlights when the user navigates to a different file or changes the code view
document.addEventListener("keydown", (event) => {
  if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
    clearHighlights();
  }
});

observer.observe(document.body, { childList: true, subtree: true });


// Listen for messages from the popup
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'HIGHLIGHT') {
    chrome.storage.local.set({highlightedLines: JSON.stringify(msg.lines)}); // memorize the highlighted lines so that they can be re-applied when the code view changes

    var commitHash = getCommitHash();

    highlightLines(msg.lines[commitHash]);
  }
});