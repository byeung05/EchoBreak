document.getElementById("analyzeBtn").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  chrome.tabs.sendMessage(tab.id, { action: "getArticle" }, async (response) => {
    if (!response || !response.content) {
      console.error("❌ Failed to get article from content.js");
      return;
    }

    // Store extracted + summarized article
    await chrome.storage.local.set({ articleData: response });

    // Inject sidebar iframe
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        if (document.getElementById("__fakenews_sidebar")) return;

        const iframe = document.createElement("iframe");
        iframe.id = "__fakenews_sidebar";
        iframe.src = chrome.runtime.getURL("sidebar/index.html");
        iframe.style = `
          position: fixed;
          top: 0;
          right: 0;
          width: 400px;
          height: 100%;
          border: none;
          z-index: 999999;
        `;
        document.body.appendChild(iframe);
      }
    });
  });
});
