# mouse_recomender.py - Machine Learning System
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import os
import logging

class MouseRecommendationSystem:
    """
    Mouse Recommendation System menggunakan Cosine Similarity
    """
    
    def __init__(self, csv_path, image_folder="img"):
        self.df = None
        self.processed_df = None
        self.feature_matrix = None
        self.scaler = MinMaxScaler()
        self.label_encoders = {}
        self.model_name = "Cosine Similarity"
        self.feature_columns = []
        self.image_folder = image_folder
        self.load_and_preprocess_data(csv_path)

    def load_and_preprocess_data(self, csv_path):
        """Memuat dan memproses data dari file CSV"""
        try:
            self.df = pd.read_csv(csv_path)
            logging.info(f"Dataset loaded: {len(self.df)} mice")

            # Clean column names
            self.df.columns = self.df.columns.str.strip()
            self.processed_df = self.df.copy()

            # Handle missing values
            self.processed_df['Power'] = self.processed_df['Power'].fillna('Unknown')
            self.processed_df['Battery Life'] = self.processed_df['Battery Life'].fillna('Unknown')
            
            # Perbaikan untuk gambar - pastikan semua mouse memiliki gambar
            self.processed_df['Image'] = self.processed_df['Image'].fillna('default.jpg')
            
            # Bersihkan nama file gambar dari spasi dan karakter khusus
            self.processed_df['Image'] = self.processed_df['Image'].astype(str).str.strip()
            
            # Validasi dan standarisasi format gambar
            self.processed_df['Image'] = self.processed_df['Image'].apply(self._standardize_image_name)

            # Clean numerical data
            numerical_cols = ['Price', 'Weight', 'DPI', 'Polling Rate', 'Buttons']
            for col in numerical_cols:
                if col in self.processed_df.columns:
                    self.processed_df[col] = pd.to_numeric(self.processed_df[col], errors='coerce')
                    self.processed_df[col] = self.processed_df[col].fillna(self.processed_df[col].median())

            # Clean categorical data
            categorical_cols = ['Brand', 'Connection', 'Power', 'Battery Life',
                              'Buttons Type', 'Size', 'Shape', 'Category']
            for col in categorical_cols:
                if col in self.processed_df.columns:
                    self.processed_df[col] = self.processed_df[col].astype(str).str.strip()

            # Encode categorical variables
            for col in categorical_cols:
                if col in self.processed_df.columns:
                    le = LabelEncoder()
                    self.processed_df[col + '_encoded'] = le.fit_transform(self.processed_df[col])
                    self.label_encoders[col] = le

            # Store original values
            self.original_numerical = self.processed_df[numerical_cols].copy()

            # Normalize numerical features
            available_numerical = [col for col in numerical_cols if col in self.processed_df.columns]
            if available_numerical:
                self.processed_df[available_numerical] = self.scaler.fit_transform(self.processed_df[available_numerical])

            # Create feature matrix
            feature_cols = ([col + '_encoded' for col in categorical_cols if col in self.df.columns] +
                           available_numerical)
            self.feature_matrix = self.processed_df[feature_cols].values
            self.feature_cols = feature_cols
            self.feature_columns = feature_cols

            # Validate images
            self.validate_and_fix_images()

            logging.info("Data preprocessing completed")
            logging.info(f"Feature matrix shape: {self.feature_matrix.shape}")
            logging.info(f"Available columns: {list(self.df.columns)}")

        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
            raise

    def _standardize_image_name(self, image_name):
        """Standardisasi nama file gambar"""
        if pd.isna(image_name) or str(image_name).lower() in ['nan', 'none', '']:
            return 'default.jpg'
        
        image_name = str(image_name).strip()
        
        # Pastikan ada ekstensi
        if not image_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            image_name += '.jpg'
        
        return image_name

    def validate_and_fix_images(self):
        """Validasi dan perbaiki path gambar"""
        if not os.path.exists(self.image_folder):
            logging.warning(f"Image folder '{self.image_folder}' tidak ditemukan")
            return

        # Buat mapping semua file gambar yang ada
        available_images = {}
        for file in os.listdir(self.image_folder):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                clean_name = file.lower().replace(' ', '_').replace('-', '_')
                available_images[clean_name] = file

        # Perbaiki referensi gambar untuk setiap mouse
        for idx, row in self.processed_df.iterrows():
            image_name = row['Image']
            image_path = os.path.join(self.image_folder, image_name)
            
            if not os.path.exists(image_path):
                # Coba cari dengan nama yang mirip
                mouse_name = str(row['Name']).lower().replace(' ', '_').replace('-', '_')
                brand_name = str(row['Brand']).lower().replace(' ', '_').replace('-', '_')
                
                # Coba beberapa kemungkinan nama file
                possible_names = [
                    f"{mouse_name}.jpg",
                    f"{brand_name}_{mouse_name}.jpg",
                    f"{mouse_name}.png",
                    f"{brand_name}.jpg"
                ]
                
                found = False
                for possible_name in possible_names:
                    if possible_name in available_images:
                        self.processed_df.loc[idx, 'Image'] = available_images[possible_name]
                        self.df.loc[idx, 'Image'] = available_images[possible_name]
                        found = True
                        break
                
                if not found:
                    # Gunakan default image
                    self.processed_df.loc[idx, 'Image'] = 'default.jpg'
                    self.df.loc[idx, 'Image'] = 'default.jpg'

        logging.info("Image validation completed")

    def get_image_url(self, image_filename):
        """Dapatkan URL gambar dengan validasi"""
        if not image_filename or pd.isna(image_filename):
            return "/api/images/default.jpg"
        
        # Bersihkan nama file
        clean_filename = str(image_filename).strip()
        image_path = os.path.join(self.image_folder, clean_filename)
        
        if os.path.exists(image_path):
            return f"/api/images/{clean_filename}"
        else:
            # Coba cari file dengan nama serupa
            if os.path.exists(self.image_folder):
                for file in os.listdir(self.image_folder):
                    if file.lower() == clean_filename.lower():
                        return f"/api/images/{file}"
            return "/api/images/default.jpg"

    def create_user_profile(self, user_preferences):
        """Membuat user profile vector berdasarkan preferensi"""
        feature_cols = self.feature_cols
        user_profile = {}

        logging.info(f"Creating user profile for: {user_preferences}")

        # Handle categorical preferences
        categorical_mappings = {
            'brand': 'Brand',
            'connection': 'Connection',
            'size': 'Size',
            'shape': 'Shape',
            'category': 'Category'
        }

        for pref_key, col_name in categorical_mappings.items():
            if pref_key in user_preferences and user_preferences[pref_key]:
                value = user_preferences[pref_key].strip()
                if value and col_name in self.label_encoders:
                    if value in self.label_encoders[col_name].classes_:
                        encoded_value = self.label_encoders[col_name].transform([value])[0]
                        user_profile[col_name + '_encoded'] = encoded_value
                        logging.info(f"Encoded {col_name}: {value} -> {encoded_value}")

        # Handle numerical preferences
        if 'price_max' in user_preferences and user_preferences['price_max']:
            try:
                original_price = float(user_preferences['price_max'])
                price_min = self.original_numerical['Price'].min()
                price_max = self.original_numerical['Price'].max()
                price_normalized = (original_price - price_min) / (price_max - price_min)
                user_profile['Price'] = min(1.0, max(0.0, price_normalized))
                logging.info(f"Normalized price: {original_price} -> {user_profile['Price']}")
            except (ValueError, TypeError):
                logging.warning(f"Invalid price value: {user_preferences['price_max']}")

        # Weight preference handling
        if 'weight_pref' in user_preferences and user_preferences['weight_pref']:
            weight_min = self.original_numerical['Weight'].min()
            weight_max = self.original_numerical['Weight'].max()
            weight_range = weight_max - weight_min
            
            weight_pref = user_preferences['weight_pref'].lower()
            if weight_pref == 'light':
                target_weight = weight_min + (weight_range * 0.2)
            elif weight_pref == 'medium':
                target_weight = weight_min + (weight_range * 0.5)
            else:  # heavy
                target_weight = weight_min + (weight_range * 0.8)
            
            weight_normalized = (target_weight - weight_min) / (weight_max - weight_min)
            user_profile['Weight'] = min(1.0, max(0.0, weight_normalized))
            logging.info(f"Weight preference: {weight_pref} -> {user_profile['Weight']}")

        # DPI preference
        if 'dpi_min' in user_preferences and user_preferences['dpi_min']:
            try:
                original_dpi = float(user_preferences['dpi_min'])
                dpi_min = self.original_numerical['DPI'].min()
                dpi_max = self.original_numerical['DPI'].max()
                dpi_normalized = (original_dpi - dpi_min) / (dpi_max - dpi_min)
                user_profile['DPI'] = min(1.0, max(0.0, dpi_normalized))
                logging.info(f"Normalized DPI: {original_dpi} -> {user_profile['DPI']}")
            except (ValueError, TypeError):
                logging.warning(f"Invalid DPI value: {user_preferences['dpi_min']}")

        # Buttons preference
        if 'buttons' in user_preferences and user_preferences['buttons']:
            try:
                buttons_original = float(user_preferences['buttons'])
                buttons_min = self.original_numerical['Buttons'].min()
                buttons_max = self.original_numerical['Buttons'].max()
                buttons_normalized = (buttons_original - buttons_min) / (buttons_max - buttons_min)
                user_profile['Buttons'] = min(1.0, max(0.0, buttons_normalized))
                logging.info(f"Normalized buttons: {buttons_original} -> {user_profile['Buttons']}")
            except (ValueError, TypeError):
                logging.warning(f"Invalid buttons value: {user_preferences['buttons']}")

        # Convert to vector
        user_vector = np.zeros(len(feature_cols))
        for i, col in enumerate(feature_cols):
            if col in user_profile:
                user_vector[i] = user_profile[col]
            else:
                user_vector[i] = np.median(self.processed_df[col])

        logging.info(f"User vector created with {len(user_vector)} features")
        return user_vector.reshape(1, -1)

    def get_recommendations(self, user_preferences, top_n=5):
        """Mendapatkan rekomendasi mouse dengan gambar"""
        try:
            logging.info(f"Getting recommendations for: {user_preferences}")
            
            user_vector = self.create_user_profile(user_preferences)
            similarities = cosine_similarity(user_vector, self.feature_matrix)[0]

            recommendations = self.df.copy()
            recommendations['similarity_score'] = similarities

            # Apply filters
            if 'price_max' in user_preferences and user_preferences['price_max']:
                try:
                    max_price = float(user_preferences['price_max'])
                    recommendations = recommendations[recommendations['Price'] <= max_price]
                    logging.info(f"Applied price filter: <= {max_price}")
                except (ValueError, TypeError):
                    logging.warning(f"Invalid price filter: {user_preferences['price_max']}")

            # Apply other filters
            filter_mappings = {
                'category': 'Category',
                'brand': 'Brand',
                'connection': 'Connection',
                'size': 'Size',
                'shape': 'Shape'
            }

            for pref_key, col_name in filter_mappings.items():
                if pref_key in user_preferences and user_preferences[pref_key]:
                    filter_value = user_preferences[pref_key].strip()
                    if filter_value and col_name in recommendations.columns:
                        mask = recommendations[col_name].str.strip().str.lower() == filter_value.lower()
                        recommendations = recommendations[mask]
                        logging.info(f"Applied {col_name} filter: {filter_value}")

            # Weight preference filter
            if 'weight_pref' in user_preferences and user_preferences['weight_pref']:
                weight_pref = user_preferences['weight_pref'].lower()
                weight_min = recommendations['Weight'].min()
                weight_max = recommendations['Weight'].max()
                weight_range = weight_max - weight_min
                
                if weight_pref == 'light':
                    weight_threshold = weight_min + (weight_range * 0.4)
                    recommendations = recommendations[recommendations['Weight'] <= weight_threshold]
                elif weight_pref == 'medium':
                    weight_lower = weight_min + (weight_range * 0.3)
                    weight_upper = weight_min + (weight_range * 0.7)
                    recommendations = recommendations[(recommendations['Weight'] >= weight_lower) & (recommendations['Weight'] <= weight_upper)]
                else:  # heavy
                    weight_threshold = weight_min + (weight_range * 0.6)
                    recommendations = recommendations[recommendations['Weight'] >= weight_threshold]
                    
                logging.info(f"Applied weight filter: {weight_pref}")

            # DPI filter
            if 'dpi_min' in user_preferences and user_preferences['dpi_min']:
                try:
                    min_dpi = float(user_preferences['dpi_min'])
                    recommendations = recommendations[recommendations['DPI'] >= min_dpi]
                    logging.info(f"Applied DPI filter: >= {min_dpi}")
                except (ValueError, TypeError):
                    logging.warning(f"Invalid DPI filter: {user_preferences['dpi_min']}")

            # Buttons filter
            if 'buttons' in user_preferences and user_preferences['buttons']:
                try:
                    buttons_count = int(user_preferences['buttons'])
                    recommendations = recommendations[recommendations['Buttons'] == buttons_count]
                    logging.info(f"Applied buttons filter: = {buttons_count}")
                except (ValueError, TypeError):
                    logging.warning(f"Invalid buttons filter: {user_preferences['buttons']}")

            # Sort by similarity
            recommendations = recommendations.sort_values('similarity_score', ascending=False)
            top_recommendations = recommendations.head(top_n)

            logging.info(f"Found {len(top_recommendations)} recommendations")

            # Format output
            result = []
            for idx, row in top_recommendations.iterrows():
                mouse_info = {
                    'rank': len(result) + 1,
                    'name': row['Name'],
                    'brand': row['Brand'],
                    'price': f"Rp {row['Price']:,.0f}",
                    'similarity_score': f"{row['similarity_score']:.3f}",
                    'image': row['Image'],  # Add this for the frontend
                    'image_url': self.get_image_url(row['Image']),
                    'specs': {
                        'connection': row['Connection'],
                        'dpi': f"{row['DPI']:,.0f}",
                        'weight': f"{row['Weight']:.0f}g",
                        'buttons': int(row['Buttons']),
                        'size': row['Size'],
                        'shape': row['Shape'],
                        'battery_life': row['Battery Life'],
                        'polling_rate': f"{row['Polling Rate']:.0f}",
                        'button_type': row['Buttons Type']
                    },
                    'category': row['Category'],
                    'link': row['Link'] if 'Link' in row and pd.notna(row['Link']) else None
                }
                result.append(mouse_info)

            logging.info(f"Returning {len(result)} recommendations")
            return result

        except Exception as e:
            logging.error(f"Error getting recommendations: {str(e)}")
            return []

    def get_available_options(self):
        """Mendapatkan opsi yang tersedia"""
        try:
            def clean_options(series):
                cleaned = series.dropna().astype(str).str.strip()
                cleaned = cleaned[cleaned != '']
                cleaned = cleaned[cleaned.str.lower() != 'nan']
                return sorted(list(set(cleaned.tolist())))

            options = {
                'brands': clean_options(self.df['Brand']),
                'connections': clean_options(self.df['Connection']),
                'sizes': clean_options(self.df['Size']),
                'shapes': clean_options(self.df['Shape']),
                'categories': clean_options(self.df['Category']),
                'price_range': {
                    'min': int(self.df['Price'].min()),
                    'max': int(self.df['Price'].max())
                },
                'dpi_range': {
                    'min': int(self.df['DPI'].min()),
                    'max': int(self.df['DPI'].max())
                },
                'weight_range': {
                    'min': int(self.df['Weight'].min()),
                    'max': int(self.df['Weight'].max())
                },
                'buttons_range': {
                    'min': int(self.df['Buttons'].min()),
                    'max': int(self.df['Buttons'].max())
                }
            }
            
            logging.info(f"Available options: {options}")
            return options
            
        except Exception as e:
            logging.error(f"Error getting options: {str(e)}")
            return {}

    def get_system_info(self):
        """Mendapatkan informasi sistem"""
        try:
            return {
                'model_name': self.model_name,
                'total_data': len(self.df) if self.df is not None else 0,
                'feature_columns': self.feature_columns,
                'dataset_shape': {
                    'rows': len(self.df) if self.df is not None else 0,
                    'columns': len(self.df.columns) if self.df is not None else 0
                },
                'original_columns': list(self.df.columns) if self.df is not None else [],
                'image_folder': self.image_folder,
                'image_support': True
            }
        except Exception as e:
            logging.error(f"Error getting system info: {str(e)}")
            return {}