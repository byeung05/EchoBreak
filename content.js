chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getArticle") {
      const title = document.title;
      const content = document.body.innerText.slice(0, 500); // sample preview
      sendResponse({ title, content });
    }
  });
  