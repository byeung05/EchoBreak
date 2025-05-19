// Load analysis data from chrome.storage
chrome.storage.local.get("articleData", (res) => {
    const data = res.articleData || {};
    document.getElementById("title").textContent = data.title || "No title";
    document.getElementById("byline").textContent = data.byline || "Unknown Author";
    document.getElementById("content").textContent = data.content || "No content available.";
  });
  