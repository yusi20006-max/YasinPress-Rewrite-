const FEED_URL = "../data/pwa/feed.json";
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

function render(feed) {
  const items = Array.isArray(feed.items) ? feed.items : [];
  stateElement.textContent = items.length
    ? `${items.length} خبر`
    : "خبری برای نمایش وجود ندارد.";
  feedElement.innerHTML = items.map((item) => `
    <article class="card">
      <div class="meta">${escapeHtml(item.tags?.[0] || "خبر")}</div>
      <h2><a href="${escapeHtml(item.url || "#")}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title || "بدون عنوان")}</a></h2>
      <p>${escapeHtml(item.content_text || "")}</p>
      <time datetime="${escapeHtml(item.date_published || "")}">${new Date(item.date_published).toLocaleString("fa-IR")}</time>
    </article>`).join("");
}

async function loadFeed() {
  stateElement.textContent = "در حال دریافت اخبار…";
  try {
    const response = await fetch(`${FEED_URL}?t=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    render(await response.json());
  } catch (error) {
    stateElement.textContent = "دریافت فید ناموفق بود. بعداً دوباره تلاش کنید.";
    console.error("YasinPress PWA feed error", error);
  }
}

document.querySelector("#refresh").addEventListener("click", loadFeed);
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(console.error);
loadFeed();
