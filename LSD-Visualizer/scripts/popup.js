document.getElementById('apply').addEventListener('click', () => {
    const raw = document.getElementById('lines').value;

    try {
        const lines = JSON.parse(raw);

        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, { type: 'HIGHLIGHT', lines: lines });
        });
    } catch (e) {
        alert('Invalid JSON');
    }
});