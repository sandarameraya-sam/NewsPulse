// The address of YOUR Flask backend
const API_URL = "http://127.0.0.1:5000/api/news";

// Elements from index.html
const newsContainer = document.getElementById("news-container");
const statusMessage = document.getElementById("status-message");
const categoryButtons = document.querySelectorAll(".category-btn");
const refreshBtn = document.getElementById("refresh-btn");
const countrySelect = document.getElementById("country-select");

// Remember which category and country are selected
let currentCategory = "general";
let currentCountry = "ph";


// Show a message above the cards (set isError to true for red text)
function showStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.className = isError ? "status-message error" : "status-message";
}


// Fetch news from the backend and show it on the page
async function loadNews(category) {
  showStatus("Loading news...");
  newsContainer.innerHTML = "";

  try {
    const response = await fetch(
      `${API_URL}?category=${category}&country=${currentCountry}`
    );
    const data = await response.json();

    if (data.error) {
      showStatus("Error: " + data.error, true);
      return;
    }

    if (data.articles.length === 0) {
      showStatus("No articles found for this category.");
      return;
    }

    showStatus("");
    displayNews(data.articles);
  } catch (error) {
    showStatus("Could not connect to the backend. Is your Flask server running?", true);
    console.error(error);
  }
}


// Turn the list of articles into cards on the page
function displayNews(articles) {
  newsContainer.innerHTML = "";

  articles.forEach((article) => {
    const card = document.createElement("article");
    card.className = "news-card";

    const imageUrl = article.image || "https://via.placeholder.com/400x200?text=No+Image";

    card.innerHTML = `
      <img src="${imageUrl}" alt="Article image"
           onerror="this.onerror=null; this.src='https://via.placeholder.com/400x200?text=No+Image';">
      <div class="card-body">
        <span class="source">${article.source || "Unknown source"}</span>
        <h2>${article.title || "No title"}</h2>
        <p>${article.description || ""}</p>
        <a href="${article.url}" target="_blank">Read more</a>
      </div>
    `;

    newsContainer.appendChild(card);
  });
}


// When a category button is clicked, switch categories
categoryButtons.forEach((button) => {
  button.addEventListener("click", () => {
    categoryButtons.forEach((b) => b.classList.remove("active"));
    button.classList.add("active");

    currentCategory = button.dataset.category;
    loadNews(currentCategory);
  });
});


// When Refresh is clicked, reload the current category
refreshBtn.addEventListener("click", () => {
  loadNews(currentCategory);
});


// When the country dropdown changes, reload the news
countrySelect.addEventListener("change", () => {
  currentCountry = countrySelect.value;
  loadNews(currentCategory);
});


// Load the first batch of news when the page opens
loadNews(currentCategory);