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

  async function sendToBackend(text) {
    try {
      console.log("📤 Sending to backend...", text.length, "characters");
      
      const response = await fetch("https://echobreak-701039546082.europe-west1.run.app/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      });

      console.log("📥 Response status:", response.status);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      const result = await response.json();
      console.log("✅ Summary received:", result.summary?.length, "characters");
      return result.summary;
      
    } catch (err) {
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
          const summary = await sendToBackend(article.textContent);

          sendResponse({
            title: article.title || "Untitled Article",
            content: article.textContent,
            summary: summary,
            byline: article.byline || "Unknown Author",
            url: window.location.href
          });
        } catch (error) {
          console.error("❌ Error in message handler:", error);
          sendResponse({
            title: article.title || "Untitled Article",
            content: article.textContent,
            summary: `Error: ${error.message}`,
            byline: article.byline || "Unknown Author",
            url: window.location.href
          });
        }
      })();

      return true; // Keeps message channel open for async response
    }
  });
})();