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
    recommender = MouseRecommendationSystem("Data_Mouse.csv", "static/img")
    logging.info("Mouse Recommendation System initialized successfully!")
except Exception as e:
    logging.error(f"Error initializing recommendation system: {str(e)}")
    recommender = None

# ========== API: IMAGE SERVING ==========
@app.route("/api/images/<filename>")
def serve_image(filename):
    """API endpoint untuk melayani gambar mouse dengan perbaikan"""
    try:
        image_folder = recommender.image_folder if recommender else "static/img"
        
        # Bersihkan nama file
        clean_filename = filename.strip()
        image_path = os.path.join(image_folder, clean_filename)
        
        # Cek apakah file ada
        if os.path.exists(image_path):
            return send_from_directory(image_folder, clean_filename)
        
        # Coba cari file dengan nama serupa (case-insensitive)
        if os.path.exists(image_folder):
            for file in os.listdir(image_folder):
                if file.lower() == clean_filename.lower():
                    return send_from_directory(image_folder, file)
        
        # Return default image
        default_images = ["default.jpg", "default.png", "no-image.jpg", "placeholder.jpg"]
        for default_img in default_images:
            default_path = os.path.join(image_folder, default_img)
            if os.path.exists(default_path):
                return send_from_directory(image_folder, default_img)
        
        # Jika tidak ada default image, return error
        return jsonify({"error": "Image not found"}), 404
        
    except Exception as e:
        logging.error(f"Error serving image {filename}: {str(e)}")
        return jsonify({"error": "Failed to serve image"}), 500

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

# ========== ROUTE UTAMA ==========
@app.route("/")
def serve_index():
    """Route untuk menampilkan halaman utama"""
    try:
        # Cek apakah file index.html ada
        if os.path.exists(os.path.join("static", "index.html")):
            return send_from_directory("static", "index.html")
        else:
            # Jika tidak ada, buat response HTML sederhana
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Mouse Recommendation System</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .status { padding: 20px; background: #f0f0f0; border-radius: 5px; }
                    .success { background: #d4edda; color: #155724; }
                    .error { background: #f8d7da; color: #721c24; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Mouse Recommendation System</h1>
                    <div class="status success">
                        <h2>✅ System Status: Online</h2>
                        <p>The Mouse Recommendation API is running successfully!</p>
                        <h3>Available Endpoints:</h3>
                        <ul>
                            <li><strong>GET /api/options</strong> - Get available filter options</li>
                            <li><strong>POST /api/recommendations</strong> - Get mouse recommendations</li>
                            <li><strong>GET /api/info</strong> - Get system information</li>
                            <li><strong>GET /health</strong> - Health check</li>
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            """
    except Exception as e:
        logging.error(f"Error serving index: {str(e)}")
        return jsonify({"error": "Failed to serve index page"}), 500

# ========== ROUTE STATIC FILES ==========
@app.route("/static/<path:filename>")
def serve_static(filename):
    """Route untuk melayani static files"""
    try:
        return send_from_directory("static", filename)
    except Exception as e:
        logging.error(f"Error serving static file {filename}: {str(e)}")
        return jsonify({"error": "File not found"}), 404

# ========== ROUTE UNTUK CSS DAN JS ==========
@app.route("/<path:filename>")
def serve_files(filename):
    """Route untuk melayani file CSS dan JS dari root directory"""
    try:
        if filename.endswith('.css') or filename.endswith('.js'):
            if os.path.exists(filename):
                return send_from_directory(".", filename)
            else:
                return jsonify({"error": "File not found"}), 404
        return serve_index()
    except Exception as e:
        logging.error(f"Error serving file {filename}: {str(e)}")
        return serve_index()

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

# ========== ENDPOINT UNTUK DEBUG IMAGES ==========
@app.route("/api/debug/images")
def debug_images():
    """Debug endpoint untuk cek gambar yang tersedia"""
    if recommender is None:
        return jsonify({"error": "Recommendation system not initialized"}), 500
    
    try:
        image_folder = recommender.image_folder
        if not os.path.exists(image_folder):
            return jsonify({"error": f"Image folder '{image_folder}' not found"})
        
        # List semua file gambar
        image_files = []
        for file in os.listdir(image_folder):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                image_files.append(file)
        
        # Ambil sample mice dari dataset
        sample_mice = []
        if hasattr(recommender, 'df') and recommender.df is not None:
            for idx, row in recommender.df.head(10).iterrows():
                mouse_info = {
                    'name': row['Name'],
                    'brand': row['Brand'],
                    'image_filename': row['Image'],
                    'image_url': recommender.get_image_url(row['Image']),
                    'image_exists': os.path.exists(os.path.join(image_folder, row['Image']))
                }
                sample_mice.append(mouse_info)
        
        return jsonify({
            "image_folder": image_folder,
            "total_image_files": len(image_files),
            "available_images": image_files[:20],  # First 20 images
            "sample_mice": sample_mice
        })
    except Exception as e:
        logging.error(f"Error in debug_images: {str(e)}")
        return jsonify({"error": "Failed to debug images"}), 500

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
            "system_info": recommender.get_system_info()
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
    port = int(os.environ.get('PORT', 5000))
    
    # Railway requires binding to 0.0.0.0
    app.run(
        debug=False, 
        host='0.0.0.0', 
        port=port,
        threaded=True
    )
