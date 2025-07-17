# app.py - Flask Application (Fixed for Railway Deployment)
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging
import pandas as pd

# Import the ML system
from mouse_recomender import MouseRecommendationSystem

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, static_folder="static")
CORS(app)

# Initialize the ML recommendation system
try:
    # PERBAIKAN 1: Gunakan path yang sama seperti program pertama
    recommender = MouseRecommendationSystem("Data_Mouse.csv", "img")
    logging.info("Mouse Recommendation System initialized successfully!")
except Exception as e:
    logging.error(f"Error initializing recommendation system: {str(e)}")
    recommender = None

# ========== ROUTE UTAMA ==========
@app.route("/")
def serve_index():
    """Route untuk menampilkan halaman utama"""
    try:
        return send_from_directory("static", "index.html")
    except Exception as e:
        logging.error(f"Error serving index: {str(e)}")
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mouse Recommendation System</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .error { padding: 20px; background: #f8d7da; color: #721c24; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Mouse Recommendation System</h1>
                <div class="error">
                    <h2> Error: Frontend files not found</h2>
                    <p>Please make sure index.html is in the static folder</p>
                </div>
            </div>
        </body>
        </html>
        """

# ========== ROUTE STATIC FILES ==========
@app.route("/static/<path:filename>")
def serve_static(filename):
    """Route untuk melayani static files"""
    try:
        return send_from_directory("static", filename)
    except Exception as e:
        logging.error(f"Error serving static file {filename}: {str(e)}")
        return jsonify({"error": "File not found"}), 404

# ========== ROUTE UNTUK CSS DAN JS (BACKWARD COMPATIBILITY) ==========
@app.route("/style.css")
def serve_css():
    """Route untuk melayani CSS file"""
    try:
        return send_from_directory("static", "style.css")
    except Exception as e:
        logging.error(f"Error serving CSS: {str(e)}")
        return jsonify({"error": "CSS file not found"}), 404

@app.route("/script.js")
def serve_js():
    """Route untuk melayani JS file"""
    try:
        return send_from_directory("static", "script.js")
    except Exception as e:
        logging.error(f"Error serving JS: {str(e)}")
        return jsonify({"error": "JS file not found"}), 404

# ========== PERBAIKAN 2: API IMAGE SERVING - SAMA SEPERTI PROGRAM PERTAMA ==========
@app.route("/api/images/<filename>")
def serve_image(filename):
    """API endpoint untuk melayani gambar mouse dengan perbaikan"""
    try:
        # PERBAIKAN: Gunakan path yang sama seperti program pertama
        image_folder = "img"  # Langsung ke folder img
        
        # Bersihkan nama file
        clean_filename = filename.strip()
        
        # PERBAIKAN: Cek apakah file ada di folder img
        image_path = os.path.join(image_folder, clean_filename)
        if os.path.exists(image_path):
            return send_from_directory(image_folder, clean_filename)
        
        # PERBAIKAN: Jika tidak ada di img, coba di static/img
        static_image_folder = "static/img"
        static_image_path = os.path.join(static_image_folder, clean_filename)
        if os.path.exists(static_image_path):
            return send_from_directory(static_image_folder, clean_filename)
        
        # Coba cari file dengan nama serupa (case-insensitive)
        for folder in [image_folder, static_image_folder]:
            if os.path.exists(folder):
                for file in os.listdir(folder):
                    if file.lower() == clean_filename.lower():
                        return send_from_directory(folder, file)
        
        # Return default image
        default_images = ["default.jpg", "default.png", "no-image.jpg", "placeholder.jpg"]
        for folder in [image_folder, static_image_folder]:
            for default_img in default_images:
                default_path = os.path.join(folder, default_img)
                if os.path.exists(default_path):
                    return send_from_directory(folder, default_img)
        
        # Jika tidak ada default image, return error
        logging.warning(f"Image not found: {filename}")
        return jsonify({"error": "Image not found"}), 404
        
    except Exception as e:
        logging.error(f"Error serving image {filename}: {str(e)}")
        return jsonify({"error": "Failed to serve image"}), 500

# ========== PERBAIKAN 3: ROUTE TAMBAHAN UNTUK COMPATIBILITY ==========
@app.route("/img/<filename>")
def serve_image_direct(filename):
    """Route langsung untuk gambar (compatibility dengan program pertama)"""
    return serve_image(filename)

# ========== API: OPTIONS ==========
@app.route("/api/options")
def get_options():
    """API endpoint untuk mendapatkan opsi yang tersedia"""
    if recommender is None:
        return jsonify({"error": "Recommendation system not initialized"}), 500
    
    try:
        options = recommender.get_available_options()
        
        # Convert the options to match the frontend format
        formatted_options = {
            'brands': options.get('brands', []),
            'categories': options.get('categories', []),
            'connections': options.get('connections', []),
            'sizes': options.get('sizes', []),
            'shapes': options.get('shapes', [])
        }
        
        logging.info(f"Options sent to frontend: {formatted_options}")
        return jsonify(formatted_options)
        
    except Exception as e:
        logging.error(f"Error in get_options: {str(e)}")
        return jsonify({"error": "Failed to get options"}), 500

# ========== API: RECOMMENDATIONS ==========
@app.route("/api/recommendations", methods=["POST"])
def recommend():
    """API endpoint untuk mendapatkan rekomendasi mouse"""
    if recommender is None:
        return jsonify({"error": "Recommendation system not initialized"}), 500
    
    try:
        user_preferences = request.json
        logging.info(f"User preferences received: {user_preferences}")
        
        # Get recommendations using the ML system
        recommendations = recommender.get_recommendations(user_preferences, top_n=5)
        
        logging.info(f"Recommendations generated: {len(recommendations)} items")
        
        # PERBAIKAN 4: Debug logging untuk image URLs
        for i, rec in enumerate(recommendations):
            if 'image' in rec:
                logging.info(f"Recommendation {i+1}: {rec.get('name', 'Unknown')} - Image: {rec['image']}")
        
        if not recommendations:
            return jsonify({
                "recommendations": [],
                "message": "No recommendations found matching your criteria. Try adjusting your preferences."
            })
        
        return jsonify({"recommendations": recommendations})
    
    except Exception as e:
        logging.error(f"Error in recommend: {str(e)}")
        return jsonify({"error": f"Failed to get recommendations: {str(e)}"}), 500

# ========== API: SYSTEM INFO ==========
@app.route("/api/info")
def get_info():
    """API endpoint untuk mendapatkan informasi sistem"""
    if recommender is None:
        return jsonify({"error": "Recommendation system not initialized"}), 500
    
    try:
        info = recommender.get_system_info()
        return jsonify(info)
    except Exception as e:
        logging.error(f"Error in get_info: {str(e)}")
        return jsonify({"error": "Failed to get system info"}), 500

# ========== HEALTH CHECK ==========
@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Mouse Recommendation System is running",
        "recommendation_system": "initialized" if recommender else "not initialized",
        "dataset_size": recommender.get_system_info().get('total_data', 0) if recommender else 0,
        "model_name": recommender.model_name if recommender else "N/A",
        "image_support": True if recommender else False,
        "image_folder": recommender.image_folder if recommender else "N/A",
        "port": os.environ.get('PORT', '5000'),
        "environment": "production" if os.environ.get('RAILWAY_ENVIRONMENT') else "development"
    })

# ========== PERBAIKAN 5: ENDPOINT DEBUG IMAGES - DITINGKATKAN ==========
@app.route("/api/debug/images")
def debug_images():
    """Debug endpoint untuk cek gambar yang tersedia"""
    if recommender is None:
        return jsonify({"error": "Recommendation system not initialized"}), 500
    
    try:
        # Check multiple possible image folders
        possible_folders = ["img", "static/img", "static/images"]
        folder_info = {}
        
        for folder in possible_folders:
            if os.path.exists(folder):
                image_files = []
                for file in os.listdir(folder):
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                        image_files.append(file)
                
                folder_info[folder] = {
                    "exists": True,
                    "total_images": len(image_files),
                    "sample_images": image_files[:5]
                }
            else:
                folder_info[folder] = {
                    "exists": False,
                    "total_images": 0,
                    "sample_images": []
                }
        
        # Ambil sample mice dari dataset
        sample_mice = []
        if hasattr(recommender, 'df') and recommender.df is not None:
            for idx, row in recommender.df.head(5).iterrows():
                image_filename = row.get('Image', 'no-image.jpg')
                mouse_info = {
                    'name': row.get('Name', 'Unknown'),
                    'brand': row.get('Brand', 'Unknown'),
                    'image_filename': image_filename,
                    'image_url': f"/api/images/{image_filename}",
                    'image_exists_img': os.path.exists(os.path.join("img", image_filename)),
                    'image_exists_static': os.path.exists(os.path.join("static/img", image_filename))
                }
                sample_mice.append(mouse_info)
        
        return jsonify({
            "folders": folder_info,
            "recommender_folder": recommender.image_folder if recommender else "N/A",
            "sample_mice": sample_mice,
            "current_working_directory": os.getcwd(),
            "directory_contents": os.listdir(".")
        })
        
    except Exception as e:
        logging.error(f"Error in debug_images: {str(e)}")
        return jsonify({"error": f"Failed to debug images: {str(e)}"}), 500

# ========== TEST ENDPOINT ==========
@app.route("/api/test")
def test_system():
    """Test endpoint untuk memastikan sistem berjalan"""
    if recommender is None:
        return jsonify({
            "status": "error",
            "message": "Recommendation system not initialized"
        }), 500
    
    try:
        # Test get options
        options = recommender.get_available_options()
        
        # Test sample recommendation
        sample_prefs = {"brand": "Logitech", "category": "Gaming"}
        sample_recs = recommender.get_recommendations(sample_prefs, top_n=2)
        
        return jsonify({
            "status": "success",
            "message": "System is working properly",
            "options_available": len(options),
            "sample_recommendations": len(sample_recs),
            "system_info": recommender.get_system_info(),
            "sample_image_urls": [rec.get('image', 'no-image') for rec in sample_recs[:2]]
        })
        
    except Exception as e:
        logging.error(f"Error in test_system: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": f"System test failed: {str(e)}"
        }), 500

# ========== ERROR HANDLERS ==========
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logging.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

# ========== JALANKAN APP ==========
if __name__ == '__main__':
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get('PORT', 8080))
    
    logging.info("Starting Mouse Recommendation System...")
    logging.info(f"Web interface available at: http://0.0.0.0:{port}")
    logging.info("Debug images at: /api/debug/images")
    logging.info("Test system at: /api/test")
    
    # Railway requires binding to 0.0.0.0
    app.run(
        debug=False, 
        host='0.0.0.0', 
        port=port,
        threaded=True
    )
