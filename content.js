(async function () {
  const article = new Readability(document.cloneNode(true)).parse();

  async function sendToBackend(text) {
    try {
      const response = await fetch("https://echobreak-701039546082.europe-west1.run.app", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) throw new Error("Failed to get summary");
      const result = await response.json();
      return result.summary;
    } catch (err) {
      console.error("❌ Summarization error:", err);
      return null;
    }
  }

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getArticle") {
      // Defer sendResponse since it's async
      (async () => {
        const summary = await sendToBackend(article.textContent);

        sendResponse({
          title: article.title,
          content: article.textContent,
          summary,
          byline: article.byline || "Unknown Author",
          url: window.location.href
        });
      })();

      return true; // Keeps message channel open for async response
    }
  });
})();
