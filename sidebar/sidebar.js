// Load analysis data from chrome.storage
window.onload = async () => {
  const { articleData } = await chrome.storage.local.get("articleData");

  if (articleData) {
    document.getElementById("title").innerText = articleData.title;
    document.getElementById("byline").innerText = articleData.byline;
    document.getElementById("url").innerText = articleData.url;
    
    // Show word count if available
    if (articleData.wordCount) {
      document.getElementById("stats").innerText = `📊 ${articleData.wordCount.toLocaleString()} words`;
    }
    
    // Display summary or error
    if (articleData.error) {
      document.getElementById("summary").innerHTML = `<div class="error">❌ ${articleData.summary}</div>`;
    } else {
      document.getElementById("summary").innerText = articleData.summary;
    }

    // Show content preview
    if (articleData.content) {
      document.getElementById("content").innerText = articleData.content.substring(0, 1000) + '...';
    }
  }
};

// Listen for progress updates from content script
window.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'progress_update') {
    const progressDiv = document.getElementById("progress");
    const message = event.data.message;
    const timestamp = event.data.timestamp;
    const isError = event.data.isError;
    
    // Create progress entry
    const progressEntry = document.createElement('div');
    progressEntry.className = isError ? 'progress-error' : 'progress-item';
    progressEntry.innerHTML = `
      <span class="progress-time">${timestamp}</span>
      <span class="progress-message">${message}</span>
    `;
    
    // Add to progress log
    progressDiv.appendChild(progressEntry);
    progressDiv.scrollTop = progressDiv.scrollHeight;
    
    // Update main summary area if it's still loading
    const summaryDiv = document.getElementById("summary");
    if (summaryDiv.innerText === "Loading summary...") {
      summaryDiv.innerHTML = `<div class="loading">${message}</div>`;
    }
  }
});