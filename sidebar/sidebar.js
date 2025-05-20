// Load analysis data from chrome.storage
window.onload = async () => {
    const { articleData } = await chrome.storage.local.get("articleData");
  
    document.getElementById("title").innerText   = articleData.title;
    document.getElementById("byline").innerText  = articleData.byline;
    document.getElementById("url").innerText     = articleData.url;
    document.getElementById("summary").innerText = articleData.summary;
  };