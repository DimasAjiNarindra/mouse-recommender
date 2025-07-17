// Theme Toggle Functionality
function toggleTheme() {
  const body = document.body;
  const sunIcon = document.querySelector(".sun-icon");
  const moonIcon = document.querySelector(".moon-icon");

  if (body.dataset.theme === "dark") {
    body.dataset.theme = "light";
    sunIcon.style.display = "none";
    moonIcon.style.display = "block";
    window.currentTheme = "light";
  } else {
    body.dataset.theme = "dark";
    sunIcon.style.display = "block";
    moonIcon.style.display = "none";
    window.currentTheme = "dark";
  }
}

// Initialize theme from memory or default to light
function initializeTheme() {
  const savedTheme = window.currentTheme || "light";
  const body = document.body;
  const sunIcon = document.querySelector(".sun-icon");
  const moonIcon = document.querySelector(".moon-icon");

  if (savedTheme === "dark") {
    body.dataset.theme = "dark";
    sunIcon.style.display = "block";
    moonIcon.style.display = "none";
  } else {
    body.dataset.theme = "light";
    sunIcon.style.display = "none";
    moonIcon.style.display = "block";
  }
}

// ========================================
// KONFIGURASI API
// ========================================
const API_BASE_URL = "";

// ========================================
// INISIALISASI HALAMAN
// ========================================
document.addEventListener("DOMContentLoaded", async () => {
  try {
    initializeTheme();
    await loadOptions();
    initializeEventListeners();
  } catch (error) {
    console.error("Error initializing page:", error);
  }
});

// ========================================
// FUNGSI UNTUK MEMUAT OPSI DROPDOWN
// ========================================
async function loadOptions() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/options`);
    const options = await res.json();

    console.log("Options loaded:", options);

    fillSelect("brand", options.brands);
    fillSelect("category", options.categories);
    fillSelect("connection", options.connections);
    fillSelect("size", options.sizes);
    fillSelect("shape", options.shapes);
  } catch (error) {
    console.error("Error loading options:", error);
    showError("Gagal memuat opsi. Pastikan server backend berjalan.");
  }
}

// ========================================
// FUNGSI UNTUK MENGISI DROPDOWN
// ========================================
function fillSelect(id, items) {
  const select = document.getElementById(id);
  if (!select || !items) {
    console.warn(`Element with id '${id}' not found or items is empty`);
    return;
  }

  const defaultOption = select.querySelector('option[value=""]');
  select.innerHTML = "";
  if (defaultOption) {
    select.appendChild(defaultOption.cloneNode(true));
  }

  const uniqueItems = [...new Set(items)];
  uniqueItems.forEach((item) => {
    const option = document.createElement("option");
    option.value = item;
    option.text = item;
    select.appendChild(option);
  });

  console.log(`Filled ${id} with ${uniqueItems.length} items`);
}

// ========================================
// INISIALISASI EVENT LISTENERS
// ========================================
function initializeEventListeners() {
  const form = document.getElementById("preferencesForm");
  if (form) {
    form.addEventListener("submit", handleFormSubmit);
  }

  const formElements = form.querySelectorAll("select, input");
  formElements.forEach((element) => {
    element.addEventListener("change", (e) => {
      console.log(`${e.target.id} changed to:`, e.target.value);
    });
  });
}

// ========================================
// HANDLER UNTUK FORM SUBMIT
// ========================================
async function handleFormSubmit(e) {
  e.preventDefault();

  showLoading();

  const preferences = getFormPreferences();

  console.log("PREFERENSI YANG DIKIRIM:", preferences);

  try {
    const res = await fetch(`${API_BASE_URL}/api/recommendations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(preferences),
    });

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const data = await res.json();
    console.log("HASIL REKOMENDASI:", data.recommendations);
    displayRecommendations(data.recommendations);
  } catch (error) {
    console.error("Error getting recommendations:", error);
    showError(
      "Terjadi kesalahan saat mengambil rekomendasi. Silakan coba lagi."
    );
  }
}

// ========================================
// FUNGSI UNTUK MENGAMBIL PREFERENSI FORM
// ========================================
function getFormPreferences() {
  const preferences = {};

  const stringFields = [
    "brand",
    "category",
    "connection",
    "size",
    "shape",
    "weight_pref",
  ];

  stringFields.forEach((field) => {
    const element = document.getElementById(field);
    if (element) {
      const value = element.value;
      if (value && value !== "") {
        preferences[field] = value;
        console.log(`${field}: ${value}`);
      }
    } else {
      console.warn(`Element with id '${field}' not found`);
    }
  });

  const numberFields = ["price_max", "dpi_min", "buttons"];
  numberFields.forEach((field) => {
    const element = document.getElementById(field);
    if (element) {
      const value = element.value;
      if (value && value !== "" && !isNaN(value)) {
        preferences[field] = parseInt(value);
        console.log(`${field}: ${value}`);
      }
    } else {
      console.warn(`Element with id '${field}' not found`);
    }
  });

  return preferences;
}

// ========================================
// FUNGSI UNTUK MENAMPILKAN LOADING
// ========================================
function showLoading() {
  const container = document.getElementById("recommendations");
  if (container) {
    container.innerHTML = `
      <div class="loading">
          <div class="spinner"></div>
          <p>Mencari rekomendasi mouse terbaik untuk Anda...</p>
      </div>
    `;
  }
}

// ========================================
// FUNGSI UNTUK MENAMPILKAN ERROR
// ========================================
function showError(message) {
  const container = document.getElementById("recommendations");
  if (container) {
    container.innerHTML = `
      <div class="error">
          <strong>Error:</strong> ${message}
      </div>
    `;
  }
}

// ========================================
// FUNGSI UNTUK MENAMPILKAN REKOMENDASI
// ========================================
function displayRecommendations(recs) {
  const container = document.getElementById("recommendations");
  if (!container) return;

  container.innerHTML = "";

  if (!recs || !recs.length) {
    container.innerHTML = `
      <div class="empty-state">
          <h3>Tidak ada rekomendasi ditemukan</h3>
          <p>Coba ubah preferensi Anda atau perluas kriteria pencarian</p>
      </div>
    `;
    return;
  }

  recs.forEach((rec) => {
    const div = document.createElement("div");
    div.classList.add("recommendation-item");
    div.innerHTML = createRecommendationHTML(rec);
    container.appendChild(div);
  });
}

// ========================================
// FUNGSI UNTUK MEMBUAT HTML REKOMENDASI
// ========================================
function createRecommendationHTML(rec) {
  // Get image filename from the data
  let imageFilename = "";

  if (rec.image) {
    imageFilename = rec.image;
  } else if (rec.name) {
    // Create filename from mouse name
    const cleanName = rec.name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")
      .trim();
    imageFilename = `${cleanName}.jpeg`;
  }

  // Try multiple image formats and paths
  const possibleImages = [
    `img/${imageFilename}`,
    `img/${rec.brand?.toLowerCase()}-${rec.name
      ?.toLowerCase()
      .replace(/\s+/g, "-")}.jpeg`,
    `img/${rec.brand?.toLowerCase()}-${rec.name
      ?.toLowerCase()
      .replace(/\s+/g, "")}.jpeg`,
    `img/default-mouse.png`,
  ];

  const imageSrc = possibleImages[0];

  return `
    <div class="mouse-image-container">
      <img
        src="${imageSrc}"
        alt="${rec.name}"
        class="mouse-image"
        onerror="handleImageError(this, '${rec.name}', '${rec.brand}')"
        loading="lazy"
      >
    </div>
    <div class="mouse-info">
      <div class="mouse-rank">${rec.rank}</div>
      <div class="mouse-name">${rec.name}</div>
      <div class="mouse-brand">${rec.brand}</div>
      <div class="mouse-price">${formatPrice(rec.price)}</div>
      <div class="mouse-specs">
        <div class="spec-item">
          <div class="spec-label">Koneksi:</div>
          <div class="spec-value">${rec.specs.connection || "N/A"}</div>
        </div>
        <div class="spec-item">
          <div class="spec-label">DPI:</div>
          <div class="spec-value">${formatDPI(rec.specs.dpi)}</div>
        </div>
        <div class="spec-item">
          <div class="spec-label">Berat:</div>
          <div class="spec-value">${rec.specs.weight || "N/A"}</div>
        </div>
        <div class="spec-item">
          <div class="spec-label">Tombol:</div>
          <div class="spec-value">${rec.specs.buttons || "N/A"}</div>
        </div>
        <div class="spec-item">
          <div class="spec-label">Ukuran:</div>
          <div class="spec-value">${rec.specs.size || "N/A"}</div>
        </div>
        <div class="spec-item">
          <div class="spec-label">Bentuk:</div>
          <div class="spec-value">${rec.specs.shape || "N/A"}</div>
        </div>
        <div class="spec-item">
          <div class="spec-label">Baterai:</div>
          <div class="spec-value">${rec.specs.battery_life || "N/A"}</div>
        </div>
        <div class="spec-item">
          <div class="spec-label">Polling Rate:</div>
          <div class="spec-value">${formatPollingRate(
            rec.specs.polling_rate
          )}</div>
        </div>
      </div>
      <div class="similarity-score">
        Skor Kecocokan: ${rec.similarity_score}
      </div>
      ${
        rec.link
          ? `
      <div style="margin-top: 12px;">
        <a
          href="${rec.link}"
          target="_blank"
          rel="noopener noreferrer"
          class="btn-link"
        >
          Beli Produk
        </a>
      </div>
      `
          : ""
      }
    </div>
  `;
}

// Function to check if Flask app is running
function checkFlaskApp() {
  return fetch("/app", { method: "HEAD" })
    .then((response) => {
      if (response.ok) {
        return true;
      }
      throw new Error("Flask app not ready");
    })
    .catch(() => false);
}

// Function to redirect to Flask app
function redirectToApp() {
  checkFlaskApp().then((isReady) => {
    if (isReady) {
      window.location.href = "/app";
    } else {
      // Try alternative endpoints
      window.location.href = "/";
    }
  });
}

// ========================================
// FUNGSI UNTUK MENANGANI ERROR GAMBAR
// ========================================
function handleImageError(img, mouseName, mouseBrand) {
  console.warn(`Failed to load image: ${img.src}`);

  // Try alternative image names
  const alternatives = [
    `img/${mouseBrand?.toLowerCase()}-${mouseName
      ?.toLowerCase()
      .replace(/\s+/g, "-")}.jpeg`,
    `img/${mouseBrand?.toLowerCase()}-${mouseName
      ?.toLowerCase()
      .replace(/\s+/g, "")}.jpeg`,
    `img/${mouseName?.toLowerCase().replace(/\s+/g, "-")}.jpeg`,
    `img/${mouseName?.toLowerCase().replace(/\s+/g, "")}.jpeg`,
    `img/default-mouse.png`,
  ];

  let currentIndex = 0;

  function tryNextImage() {
    if (currentIndex < alternatives.length) {
      const nextSrc = alternatives[currentIndex];
      currentIndex++;

      // Test if image exists
      const testImg = new Image();
      testImg.onload = function () {
        img.src = nextSrc;
        img.onerror = null;
      };
      testImg.onerror = function () {
        tryNextImage();
      };
      testImg.src = nextSrc;
    } else {
      // All alternatives failed, show placeholder
      img.style.display = "none";
      const container = img.parentElement;
      if (container) {
        container.innerHTML = `
          <div class="image-placeholder">
            <div class="placeholder-icon">🖱️</div>
            <div class="placeholder-text">Gambar tidak tersedia</div>
          </div>
        `;
      }
    }
  }

  tryNextImage();
}

// ========================================
// FUNGSI HELPER UNTUK FORMATTING
// ========================================
function formatPrice(price) {
  if (!price) return "N/A";

  const numericPrice = parseInt(price.toString().replace(/[^0-9]/g, ""));

  if (isNaN(numericPrice)) return price;

  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    minimumFractionDigits: 0,
  }).format(numericPrice);
}

function formatDPI(dpi) {
  if (!dpi) return "N/A";

  const numericDPI = parseInt(dpi.toString().replace(/[^0-9]/g, ""));

  if (isNaN(numericDPI)) return dpi;

  return `${numericDPI.toLocaleString()} DPI`;
}

function formatPollingRate(rate) {
  if (!rate) return "N/A";

  const numericRate = parseInt(rate.toString().replace(/[^0-9]/g, ""));

  if (isNaN(numericRate)) return rate;

  return `${numericRate} Hz`;
}

// ========================================
// FUNGSI UNTUK MENAMBAHKAN ZOOM GAMBAR
// ========================================
function addImageZoom() {
  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("mouse-image")) {
      const modal = document.createElement("div");
      modal.className = "image-modal";
      modal.innerHTML = `
        <div class="modal-content">
          <span class="close-modal">&times;</span>
          <img src="${e.target.src}" alt="${e.target.alt}" class="modal-image">
          <div class="modal-caption">${e.target.alt}</div>
        </div>
      `;

      document.body.appendChild(modal);

      modal.querySelector(".close-modal").onclick = () => {
        document.body.removeChild(modal);
      };

      modal.onclick = (e) => {
        if (e.target === modal) {
          document.body.removeChild(modal);
        }
      };
    }
  });
}

// Initialize image zoom functionality when page loads
document.addEventListener("DOMContentLoaded", () => {
  addImageZoom();
});
