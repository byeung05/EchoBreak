(async function () {
  // Check if Readability is available
  if (typeof Readability === 'undefined') {
    console.error("❌ Readability.js not loaded");
    return;
  }

  const article = new Readability(document.cloneNode(true)).parse();

  if (!article || !article.textContent) {
    console.error("❌ Failed to parse article");
    return;
  }

  // Function to show progress updates in the sidebar
  function updateProgress(message, isError = false) {
    // Try to update the sidebar if it exists
    const iframe = document.getElementById("__fakenews_sidebar");
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.postMessage({
        type: 'progress_update',
        message: message,
        isError: isError,
        timestamp: new Date().toLocaleTimeString()
      }, '*');
    }
    console.log(isError ? "❌" : "🔄", message);
  }

  async function sendToBackend(text) {
    try {
      updateProgress("Connecting to AI summarization service...");
      
      const response = await fetch("https://echobreak-701039546082.europe-west1.run.app/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        updateProgress(`Server error (${response.status}): ${errorText}`, true);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      updateProgress("Processing article with AI model...");
      const result = await response.json();
      
      if (result.progress === "error") {
        updateProgress(`Analysis failed: ${result.error}`, true);
        return `Analysis failed: ${result.error}`;
      }
      
      // Show completion message with details
      const details = result.model ? ` (${result.model}, ${result.processing_time || 'unknown time'})` : '';
      updateProgress(`✅ Summary generated successfully${details}`);
      
      return result.summary;
      
    } catch (err) {
      updateProgress(`Connection failed: ${err.message}`, true);
      console.error("❌ Summarization error:", err);
      return `Summary unavailable: ${err.message}`;
    }
  }

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getArticle") {
      console.log("📰 Processing article:", article.title);
      
      // Defer sendResponse since it's async
      (async () => {
        try {
          updateProgress(`Analyzing article: "${article.title || 'Untitled'}"`);
          updateProgress(`Article length: ${article.textContent.length.toLocaleString()} characters`);
          
          const summary = await sendToBackend(article.textContent);

          sendResponse({
            title: article.title || "Untitled Article",
            content: article.textContent,
            summary: summary,
            byline: article.byline || "Unknown Author",
            url: window.location.href,
            wordCount: article.textContent.split(' ').length,
            processed: true
          });
        } catch (error) {
          updateProgress(`Processing error: ${error.message}`, true);
          console.error("❌ Error in message handler:", error);
          sendResponse({
            title: article.title || "Untitled Article",
            content: article.textContent,
            summary: `Error: ${error.message}`,
            byline: article.byline || "Unknown Author",
            url: window.location.href,
            error: true
          });
        }
      })();

      return true; // Keeps message channel open for async response
    }
  });
})();