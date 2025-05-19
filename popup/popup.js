document.getElementById("analyzeBtn").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  chrome.tabs.sendMessage(tab.id, { action: "getArticle" }, (response) => {
    console.log("Extracted article content:", response);
    alert("Article title: " + response?.title);
  });
});
