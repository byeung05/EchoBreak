(function () {
  const article = new Readability(document.cloneNode(true)).parse();

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getArticle") {
      sendResponse({
        title: article.title,
        content: article.textContent,
        byline: article.byline || "Unknown Author",
        url: window.location.href
      });
    }
  });
})();
