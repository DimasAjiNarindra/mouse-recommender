// ========================================
// KONFIGURASI APLIKASI
// ========================================

// API Configuration
const CONFIG = {
  API: {
    BASE_URL: "",
    ENDPOINTS: {
      OPTIONS: "/api/options",
      RECOMMENDATIONS: "/api/recommendations",
    },
    TIMEOUT: 10000, // 10 seconds
    RETRY_ATTEMPTS: 3,
  },

  // Form Configuration
  FORM: {
    VALIDATION: {
      PRICE_MAX: {
        MIN: 0,
        STEP: 10000,
        PLACEHOLDER: "e.g., 500000",
      },
      DPI_MIN: {
        MIN: 800,
        STEP: 100,
        PLACEHOLDER: "e.g., 12000",
      },
      BUTTONS: {
        MIN: 2,
        MAX: 20,
        PLACEHOLDER: "e.g., 7",
      },
    },
  },

  // UI Configuration
  UI: {
    LOADING_MESSAGES: [
      "Mencari rekomendasi mouse terbaik untuk Anda...",
      "Menganalisis preferensi Anda...",
      "Memproses data mouse...",
    ],
    ERROR_MESSAGES: {
      NETWORK:
        "Tidak dapat terhubung ke server. Periksa koneksi internet Anda.",
      SERVER: "Server sedang mengalami masalah. Silakan coba lagi nanti.",
      NO_DATA: "Tidak ada data yang ditemukan.",
      INVALID_RESPONSE: "Respons server tidak valid.",
      GENERIC: "Terjadi kesalahan. Silakan coba lagi.",
    },
  },

  // Debug Configuration
  DEBUG: {
    ENABLED: true,
    LOG_LEVEL: "info", // "debug", "info", "warn", "error"
  },
};

// Export configuration if using modules
// export default CONFIG;

// For browser compatibility
if (typeof window !== "undefined") {
  window.CONFIG = CONFIG;
}
