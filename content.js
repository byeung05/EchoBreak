(async function () {
  // Check if Readability is available
  if (typeof Readability === 'undefined') {
    console.error("❌ Readability.js not loaded");
    return;
  }

  let article;
  try {
    // Clone the document to avoid altering the live page, which Readability might do.
    const documentClone = document.cloneNode(true);
    article = new Readability(documentClone).parse();
  } catch (e) {
    console.error("❌ Error during Readability instantiation or parsing:", e);
    // If Readability itself throws an error, article will be undefined.
    // Don't proceed if article isn't valid.
  }

  // If Readability failed to parse or found no content, log and exit.
  if (!article || !article.textContent || article.textContent.trim() === "") {
    console.error("❌ Failed to parse article or article content is empty.");
     //This content script won't be able to provide an article.
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
      }, '*'); // Consider using a specific origin if possible for security, e.g., chrome.runtime.getURL('')
    }
    // Also log to the content script's console for debugging
    console.log(isError ? "❌ [Progress Error]" : "🔄 [Progress]", message);
  }

  async function sendToBackend(text) {
    if (!text || text.trim() === "") {
      updateProgress("Article text is empty, cannot summarize.", true);
      return "Summary unavailable: Article text is empty.";
    }

    try {
      updateProgress("Connecting to AI summarization service...");
      
      const response = await fetch("https://echobreak-701039546082.europe-west1.run.app/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }), // Ensure 'text' matches what your backend expects
      });

      if (!response.ok) {
        const errorText = await response.text();
        updateProgress(`Server error (${response.status}): ${errorText}`, true);
        // It's good practice to throw an error here so the calling function knows it failed
        throw new Error(`HTTP error ${response.status}: ${errorText}`);
      }
      
      updateProgress("Processing article with AI model...");
      const result = await response.json();
      
      // Check if the backend itself reported an error in the process
      if (result.progress === "error" || result.error) {
        const errorMessage = result.error || "Unknown analysis error from backend.";
        updateProgress(`Analysis failed: ${errorMessage}`, true);
        return `Summary unavailable: ${errorMessage}`;
      }
      
      // Show completion message with details if available
      const details = result.model ? ` (Model: ${result.model}, Time: ${result.processing_time || 'N/A'})` : '';
      updateProgress(`✅ Summary generated successfully${details}`);
      
      return result.summary || "Summary not found in backend response.";
      
    } catch (err) {
      // This catches network errors or errors thrown from the !response.ok block
      updateProgress(`Connection or processing failed: ${err.message}`, true);
      console.error("❌ Summarization error details:", err);
      return `Summary unavailable: ${err.message}`;
    }
  }

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getArticle") {
      // Ensure article was successfully parsed earlier
      if (!article || !article.textContent || article.textContent.trim() === "") {
        console.error("❌ Cannot process 'getArticle': Article content was not properly parsed or is empty.");
        sendResponse({
          title: "Error",
          content: "",
          summary: "Failed to extract readable content from this page.",
          byline: "N/A",
          url: window.location.href,
          error: true,
          processed: false
        });
        return false; // No async work, so return false or nothing.
      }

      console.log("📰 Processing article request for:", article.title || "Untitled Article");
      
      // Defer sendResponse since sendToBackend is async
      (async () => {
        try {
          updateProgress(`Analyzing article: "${article.title || 'Untitled'}"`);
          updateProgress(`Article length: ${article.textContent.length.toLocaleString()} characters`);
          
          const summary = await sendToBackend(article.textContent);

          sendResponse({
            title: article.title || "Untitled Article",
            content: article.textContent, // The full extracted content
            summary: summary,             // The summary from the backend
            byline: article.byline || "Unknown Author",
            url: window.location.href,
            wordCount: article.textContent.split(/\s+/).filter(Boolean).length, // More robust word count
            error: summary.startsWith("Summary unavailable:"), // Check if summary indicates an error
            processed: true
          });
        } catch (error) {
          // This catch is for unexpected errors within this async IIFE itself,
          // though sendToBackend should handle its own errors and return error strings.
          const errorMessage = `Critical error during article processing: ${error.message}`;
          updateProgress(errorMessage, true);
          console.error("❌ Error in 'getArticle' message handler:", error);
          sendResponse({
            title: article.title || "Untitled Article",
            content: article.textContent, // Still send content if available
            summary: errorMessage,
            byline: article.byline || "Unknown Author",
            url: window.location.href,
            error: true,
            processed: false // Indicate processing was not fully successful
          });
        }
      })();

      return true; // Crucial: Keeps the message channel open for the async sendResponse
    }
    // Handle other actions if any
    // return false; // if not handling this message type or not using async sendResponse
  });

  console.log("[EchoBreak] Content script loaded and ready.");
})();
