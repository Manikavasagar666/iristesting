import os
import cv2
import numpy as np
import json
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from skimage.feature import graycomatrix, graycoprops
from sklearn.ensemble import RandomForestClassifier
import joblib
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'iridology_analysis_key'

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class IrisAnalyzer:
    def __init__(self):
        self.iris_regions = {
            'brain': (0, 30),
            'lungs': (30, 60),
            'heart': (120, 150),  # 2:00-3:00 position
            'liver': (150, 180),
            'kidney': (180, 210),
            'stomach': (210, 240),
            'intestines': (240, 270),
            'reproductive': (270, 300),
            'spine': (300, 330),
            'circulation': (330, 360)
        }
        
        # Initialize a simple classifier (in real application, this would be pre-trained)
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize a demo model with synthetic data"""
        # Generate synthetic training data for demonstration
        np.random.seed(42)
        n_samples = 1000
        
        # Feature names: contrast, dissimilarity, homogeneity, energy, correlation
        features = np.random.rand(n_samples, 5)
        
        # Create synthetic labels (0: normal, 1: abnormal)
        labels = np.random.choice([0, 1], n_samples, p=[0.7, 0.3])
        
        # Train the model
        self.classifier.fit(features, labels)
    
    def detect_iris(self, image):
        """Detect iris using Circle Hough Transform"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Detect circles using HoughCircles
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=int(gray.shape[0]/8),
            param1=200,
            param2=100,
            minRadius=int(gray.shape[0]/8),
            maxRadius=int(gray.shape[0]/3)
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            # Return the largest circle (likely the iris)
            largest_circle = max(circles, key=lambda x: x[2])
            return largest_circle
        return None
    
    def segment_iris(self, image, circle):
        """Segment iris from the image"""
        if circle is None:
            return None
        
        x, y, r = circle
        
        # Create a mask for the iris
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), r, 255, -1)
        
        # Create inner mask for pupil (approximate)
        pupil_radius = int(r * 0.3)
        cv2.circle(mask, (x, y), pupil_radius, 0, -1)
        
        # Apply mask to extract iris
        iris = cv2.bitwise_and(image, image, mask=mask)
        
        # Crop to iris bounding box
        x1, y1 = max(0, x - r), max(0, y - r)
        x2, y2 = min(image.shape[1], x + r), min(image.shape[0], y + r)
        
        iris_cropped = iris[y1:y2, x1:x2]
        mask_cropped = mask[y1:y2, x1:x2]
        
        return iris_cropped, mask_cropped, (x, y, r)
    
    def extract_features(self, iris_image, mask):
        """Extract GLCM features from iris image"""
        if iris_image is None:
            return None
        
        # Convert to grayscale if needed
        if len(iris_image.shape) == 3:
            gray = cv2.cvtColor(iris_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = iris_image
        
        # Apply mask
        masked_iris = cv2.bitwise_and(gray, gray, mask=mask)
        
        # Calculate GLCM
        distances = [1]
        angles = [0, np.pi/4, np.pi/2, 3*np.pi/4]
        
        # Ensure we have valid pixel values
        valid_pixels = masked_iris[mask > 0]
        if len(valid_pixels) == 0:
            return np.zeros(5)
        
        # Normalize to 0-255 and convert to uint8
        normalized = cv2.normalize(masked_iris, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        
        try:
            glcm = graycomatrix(normalized, distances, angles, levels=256, symmetric=True, normed=True)
            
            # Extract features
            contrast = graycoprops(glcm, 'contrast')[0, 0]
            dissimilarity = graycoprops(glcm, 'dissimilarity')[0, 0]
            homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
            energy = graycoprops(glcm, 'energy')[0, 0]
            correlation = graycoprops(glcm, 'correlation')[0, 0]
            
            return np.array([contrast, dissimilarity, homogeneity, energy, correlation])
        except:
            # Return default values if GLCM calculation fails
            return np.array([0.1, 0.1, 0.9, 0.8, 0.5])
    
    def analyze_regions(self, iris_image, mask, circle):
        """Analyze different regions of the iris"""
        if iris_image is None or circle is None:
            return {}
        
        cx, cy, radius = circle
        results = {}
        
        for region_name, (start_angle, end_angle) in self.iris_regions.items():
            # Create sector mask
            sector_mask = self.create_sector_mask(mask.shape, cx, cy, radius, start_angle, end_angle)
            
            # Combine with iris mask
            combined_mask = cv2.bitwise_and(mask, sector_mask)
            
            # Extract features for this region
            features = self.extract_features(iris_image, combined_mask)
            
            if features is not None:
                # Predict health status for this region
                prediction = self.classifier.predict([features])[0]
                probability = self.classifier.predict_proba([features])[0]
                
                results[region_name] = {
                    'status': 'Normal' if prediction == 0 else 'Attention Needed',
                    'confidence': float(max(probability)) * 100,
                    'features': features.tolist(),
                    'description': self.get_region_description(region_name, prediction)
                }
        
        return results
    
    def create_sector_mask(self, shape, cx, cy, radius, start_angle, end_angle):
        """Create a sector mask for iris region analysis"""
        mask = np.zeros(shape, dtype=np.uint8)
        
        # Convert angles to radians
        start_rad = np.radians(start_angle)
        end_rad = np.radians(end_angle)
        
        # Create points for the sector
        angles = np.linspace(start_rad, end_rad, 50)
        inner_radius = int(radius * 0.3)  # Inner boundary (pupil edge)
        
        # Outer arc points
        outer_points = []
        for angle in angles:
            x = int(cx + radius * np.cos(angle))
            y = int(cy + radius * np.sin(angle))
            outer_points.append([x, y])
        
        # Inner arc points (reverse order)
        inner_points = []
        for angle in reversed(angles):
            x = int(cx + inner_radius * np.cos(angle))
            y = int(cy + inner_radius * np.sin(angle))
            inner_points.append([x, y])
        
        # Combine points
        all_points = np.array(outer_points + inner_points, dtype=np.int32)
        
        # Fill the sector
        cv2.fillPoly(mask, [all_points], 255)
        
        return mask
    
    def get_region_description(self, region_name, prediction):
        """Get description for each iris region"""
        descriptions = {
            'brain': {
                0: "Neural pathways appear clear with good circulation patterns.",
                1: "Some congestion patterns suggest stress or tension. Consider relaxation techniques."
            },
            'heart': {
                0: "Cardiovascular indicators show good circulation and rhythm patterns.",
                1: "Cardiovascular stress indicators present. Consider heart-healthy lifestyle changes."
            },
            'lungs': {
                0: "Respiratory patterns indicate good oxygenation and clear airways.",
                1: "Respiratory stress patterns. Deep breathing exercises may be beneficial."
            },
            'liver': {
                0: "Liver processing patterns appear optimal with good detoxification signs.",
                1: "Liver stress indicators. Consider reducing processed foods and increasing hydration."
            },
            'kidney': {
                0: "Kidney filtration patterns show good fluid balance and processing.",
                1: "Kidney stress patterns. Ensure adequate hydration and reduce sodium intake."
            },
            'stomach': {
                0: "Digestive patterns indicate good acid balance and processing capability.",
                1: "Digestive stress indicators. Consider smaller, more frequent meals."
            },
            'intestines': {
                0: "Intestinal patterns show good absorption and elimination processes.",
                1: "Intestinal stress patterns. Increase fiber intake and consider probiotics."
            },
            'reproductive': {
                0: "Reproductive system patterns indicate good hormonal balance.",
                1: "Reproductive stress indicators. Consider lifestyle balance and stress reduction."
            },
            'spine': {
                0: "Spinal alignment patterns show good structural integrity.",
                1: "Spinal stress indicators. Consider posture improvement and gentle exercise."
            },
            'circulation': {
                0: "Overall circulation patterns indicate good blood flow throughout the body.",
                1: "Circulation stress patterns. Regular exercise and movement recommended."
            }
        }
        
        return descriptions.get(region_name, {}).get(prediction, "Analysis complete.")

# Initialize the analyzer
analyzer = IrisAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Process the image
            result = process_iris_image(filepath)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': f'Processing failed: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file format'}), 400

def process_iris_image(filepath):
    """Process the uploaded iris image and return analysis results"""
    # Load image
    image = cv2.imread(filepath)
    if image is None:
        raise ValueError("Could not load image")
    
    original_image = image.copy()
    
    # Detect iris
    circle = analyzer.detect_iris(image)
    if circle is None:
        raise ValueError("Could not detect iris in the image")
    
    # Segment iris
    iris_result = analyzer.segment_iris(image, circle)
    if iris_result is None:
        raise ValueError("Could not segment iris")
    
    iris_image, mask, circle_coords = iris_result
    
    # Analyze different regions
    regional_analysis = analyzer.analyze_regions(iris_image, mask, circle_coords)
    
    # Create visualization
    visualization = create_visualization(original_image, circle_coords, regional_analysis)
    
    # Generate overall assessment
    overall_assessment = generate_overall_assessment(regional_analysis)
    
    return {
        'success': True,
        'circle_detected': circle.tolist() if circle is not None else None,
        'regional_analysis': regional_analysis,
        'overall_assessment': overall_assessment,
        'visualization': visualization,
        'timestamp': datetime.now().isoformat()
    }

def create_visualization(image, circle, regional_analysis):
    """Create visualization of the iris analysis"""
    vis_image = image.copy()
    
    if circle is not None:
        cx, cy, radius = circle
        
        # Draw iris circle
        cv2.circle(vis_image, (cx, cy), radius, (0, 255, 0), 2)
        
        # Draw pupil circle
        pupil_radius = int(radius * 0.3)
        cv2.circle(vis_image, (cx, cy), pupil_radius, (255, 0, 0), 2)
        
        # Draw region indicators
        for i, (region_name, analysis) in enumerate(regional_analysis.items()):
            if region_name in analyzer.iris_regions:
                start_angle, end_angle = analyzer.iris_regions[region_name]
                
                # Calculate position for label
                mid_angle = np.radians((start_angle + end_angle) / 2)
                label_radius = radius + 30
                label_x = int(cx + label_radius * np.cos(mid_angle))
                label_y = int(cy + label_radius * np.sin(mid_angle))
                
                # Color based on status
                color = (0, 255, 0) if analysis['status'] == 'Normal' else (0, 165, 255)
                
                # Draw sector indicator
                sector_radius = radius + 10
                sector_x = int(cx + sector_radius * np.cos(mid_angle))
                sector_y = int(cy + sector_radius * np.sin(mid_angle))
                cv2.circle(vis_image, (sector_x, sector_y), 3, color, -1)
    
    # Convert to base64 for web display
    _, buffer = cv2.imencode('.png', vis_image)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return img_base64

def generate_overall_assessment(regional_analysis):
    """Generate overall health assessment from regional analysis"""
    total_regions = len(regional_analysis)
    normal_regions = sum(1 for analysis in regional_analysis.values() if analysis['status'] == 'Normal')
    
    overall_score = (normal_regions / total_regions) * 100 if total_regions > 0 else 0
    
    if overall_score >= 80:
        overall_status = "Excellent"
        recommendation = "Your iris patterns suggest excellent overall health. Continue maintaining your healthy lifestyle."
    elif overall_score >= 60:
        overall_status = "Good"
        recommendation = "Your iris patterns suggest generally good health with some areas that may benefit from attention."
    elif overall_score >= 40:
        overall_status = "Fair"
        recommendation = "Your iris patterns suggest several areas that may benefit from lifestyle improvements."
    else:
        overall_status = "Needs Attention"
        recommendation = "Your iris patterns suggest multiple areas that may benefit from health improvements. Consider consulting with healthcare professionals."
    
    # Key areas of concern
    concerns = [region for region, analysis in regional_analysis.items() 
               if analysis['status'] != 'Normal']
    
    # Priority recommendations
    priority_areas = []
    if 'heart' in concerns:
        priority_areas.append("Cardiovascular health - consider regular exercise and heart-healthy diet")
    if 'liver' in concerns:
        priority_areas.append("Liver health - reduce toxin exposure and support detoxification")
    if 'kidney' in concerns:
        priority_areas.append("Kidney health - ensure adequate hydration and reduce sodium")
    
    return {
        'overall_score': round(overall_score, 1),
        'overall_status': overall_status,
        'normal_regions': normal_regions,
        'total_regions': total_regions,
        'areas_of_concern': concerns,
        'priority_recommendations': priority_areas,
        'general_recommendation': recommendation,
        'disclaimer': "This analysis is for educational purposes only and should not replace professional medical advice."
    }

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)