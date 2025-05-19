document.getElementById("analyzeBtn").addEventListener("click", async () => {
  // 1) Find the active tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  // 2) Execute extraction code inside the page and get its return value
  const [injection] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      // Attempt to use Readability.js
      let article;
      try {
        article = new Readability(document.cloneNode(true)).parse();
      } catch (e) {
        console.error("Readability error:", e);
      }

      // Fallback #1: <p> tags
      let content = article?.textContent;
      if (!content || content.length < 100) {
        content = Array.from(document.querySelectorAll("p"))
          .map(p => p.innerText)
          .join("\n");
      }

      // Fallback #2: full body text
      if (!content || content.length < 100) {
        content = document.body.innerText;
      }

      return {
        title:  article?.title  || document.title,
        byline: article?.byline  || "Unknown Author",
        content,
        url:    location.href
      };
    },
  });

  // 3) Store the extracted data so the sidebar can read it
  const articleData = injection.result;
  await chrome.storage.local.set({ articleData });

  // 4) Inject the sidebar iframe (only once)
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      if (document.getElementById("__fakenews_sidebar")) return;
      const iframe = document.createElement("iframe");
      iframe.id  = "__fakenews_sidebar";
      iframe.src = chrome.runtime.getURL("sidebar/index.html");
      iframe.style.cssText = `
        position: fixed;
        top: 0;
        right: 0;
        width: 400px;
        height: 100%;
        border: none;
        z-index: 999999;
        box-shadow: -2px 0 8px rgba(0,0,0,0.2);
      `;
      document.body.appendChild(iframe);
    }
  });
});
