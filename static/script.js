/**
 * script.js
 * Handles frontend interactivity for the Digital Library:
 * - Modal open/close
 * - Dark mode toggle
 * - Toast notifications
 * - Fetching book recommendations with caching & refresh
 */

// -----------------------------------------------------------------------------
// Modal Handling
// -----------------------------------------------------------------------------

/**
 * Open a modal by ID.
 * @param {string} id - The modal's element ID.
 */
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.style.display = "block";
  }
}

/**
 * Close a modal by ID.
 * @param {string} id - The modal's element ID.
 */
function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.style.display = "none";
  }
}

/**
 * Close any open modal if user clicks outside modal content.
 */
window.onclick = function (event) {
  if (event.target.classList.contains("modal")) {
    event.target.style.display = "none";
  }
};

// -----------------------------------------------------------------------------
// Dark Mode Toggle
// -----------------------------------------------------------------------------

const themeToggle = document.getElementById("themeToggle");

// Load saved theme preference
if (themeToggle) {
  const prefersDark = localStorage.getItem("theme") === "dark";
  if (prefersDark) {
    document.body.classList.add("dark-mode");
    themeToggle.checked = true;
  }

  // Toggle listener
  themeToggle.addEventListener("change", function () {
    if (this.checked) {
      document.body.classList.add("dark-mode");
      localStorage.setItem("theme", "dark");
    } else {
      document.body.classList.remove("dark-mode");
      localStorage.setItem("theme", "light");
    }
  });
}

// -----------------------------------------------------------------------------
// Toast Notifications
// -----------------------------------------------------------------------------

/**
 * Show a temporary toast message.
 * @param {string} msg - Message to display.
 * @param {number} duration - Duration in ms (default: 3000).
 */
function showToast(msg, duration = 3000) {
  const toast = document.getElementById("toast");
  if (!toast) return;

  toast.textContent = msg;
  toast.className = "show";

  setTimeout(() => {
    toast.className = toast.className.replace("show", "");
  }, duration);
}

// -----------------------------------------------------------------------------
// Recommendations (AI + Open Library + Fallback)
// With caching + request lock + refresh button
// -----------------------------------------------------------------------------

let isFetchingRecommendation = false;
let cachedRecommendation = null;

const recommendOpen = document.getElementById("recommendOpen");

if (recommendOpen) {
  recommendOpen.addEventListener("click", async () => {
    // Prevent multiple requests at once
    if (isFetchingRecommendation) {
      showToast("⏳ Please wait, loading recommendation...");
      return;
    }

    // Use cached result if available
    if (cachedRecommendation) {
      displayRecommendation(cachedRecommendation);
      return;
    }

    try {
      isFetchingRecommendation = true;
      showToast("✨ Fetching recommendation...");

      const response = await fetch("/recommend");
      const data = await response.json();

      // Cache result for reuse
      cachedRecommendation = data;
      displayRecommendation(data);
    } catch (err) {
      console.error("Recommendation fetch failed:", err);
      showToast("❌ Could not fetch recommendation");
    } finally {
      isFetchingRecommendation = false;
    }
  });
}

/**
 * Render recommendation into modal and attach refresh button.
 * @param {Object} data - Recommendation data from backend.
 */
function displayRecommendation(data) {
  const resultDiv = document.getElementById("recommendResult");
  if (resultDiv) {
    resultDiv.innerHTML = `
      <div class="recommend-card">
        <img src="${data.cover_url}" alt="Cover of ${data.title}">
        <h3>${data.title}</h3>
        <p><strong>Author:</strong> ${data.author}</p>
        <p><em>${data.reason || ""}</em></p>
        <button class="btn primary" id="refreshRecommendation">🔄 New Suggestion</button>
      </div>
    `;
  }

  // Open modal
  openModal("recommendModal");

  // Attach refresh button
  const refreshBtn = document.getElementById("refreshRecommendation");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", async () => {
      cachedRecommendation = null; // clear cache
      closeModal("recommendModal");
      recommendOpen.click(); // trigger fresh fetch
    });
  }
}
