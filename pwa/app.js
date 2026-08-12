const FEED_URL = "../data/pwa/feed.json";
const LOCAL_FEED_KEY = "yasinpress:last-feed";
const feedElement = document.querySelector("#feed");
const stateElement = document.querySelector("#state");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function safeArticleUrl(value) {
  try {
    const url = new URL(String(value || ""), window.location.href);
    return ["http:", "https:"].includes(url.protocol) ? url.href : "#";
  } catch {
    return "#";
  }
}

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleString("fa-IR");
}

function render(feed, offline = false) {
  const items = Array.isArray(feed.items) ? feed.items : [];
  stateElement.textContent = items.length
    ? `${items.length} خبر${offline ? " — حالت آفلاین" : ""}`
    : "خبری برای نمایش وجود ندارد.";
  feedElement.innerHTML = items.map((item) => {
    const url = safeArticleUrl(item.url);
    const published = String(item.date_published || "");
    return `
    <article class="card">
      <div class="meta">${escapeHtml(item.tags?.[0] || "خبر")}</div>
      <h2><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title || "بدون عنوان")}</a></h2>
      <p>${escapeHtml(item.content_text || "")}</p>
      <time datetime="${escapeHtml(published)}">${escapeHtml(formatDate(published))}</time>
    </article>`;
  }).join("");
}

function loadCachedFeed() {
  try {
    const cached = localStorage.getItem(LOCAL_FEED_KEY);
    if (!cached) return false;
    render(JSON.parse(cached), true);
    return true;
  } catch (error) {
    console.error("YasinPress cached feed error", error);
    return false;
  }
}

async function loadFeed() {
  stateElement.textContent = "در حال دریافت اخبار…";
  try {
    const response = await fetch(`${FEED_URL}?t=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const feed = await response.json();
    localStorage.setItem(LOCAL_FEED_KEY, JSON.stringify(feed));
    render(feed);
  } catch (error) {
    if (!loadCachedFeed()) stateElement.textContent = "دریافت فید ناموفق بود. بعداً دوباره تلاش کنید.";
    console.error("YasinPress PWA feed error", error);
  }
}

document.querySelector("#refresh").addEventListener("click", loadFeed);
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(console.error);
loadFeed();
