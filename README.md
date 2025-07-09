# Iridology Analysis Web Application

A modern web application that performs automated iris analysis using computer vision and machine learning techniques to provide health insights based on iridology principles.

## ⚠️ Important Disclaimer

**This application is for educational and research purposes only. It should not be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare professionals for medical concerns.**

## Features

### 🔍 Advanced Iris Analysis
- **Automated Iris Detection**: Uses Circle Hough Transform to automatically detect and segment the iris from uploaded images
- **Regional Analysis**: Divides the iris into 10 distinct regions corresponding to different organ systems
- **Feature Extraction**: Employs Gray Level Co-occurrence Matrix (GLCM) for texture analysis
- **Machine Learning Classification**: Uses Random Forest classifier to assess each region

### 🎨 Modern Web Interface
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Drag & Drop Upload**: Easy file upload with visual feedback
- **Interactive Visualization**: Shows analyzed iris with region indicators
- **Tabbed Results**: Organized display of overview, regional analysis, and recommendations
- **Real-time Processing**: Live feedback during analysis

### 📊 Comprehensive Results
- **Overall Health Score**: Percentage-based health assessment
- **Regional Status**: Detailed analysis of each organ region
- **Confidence Levels**: Machine learning confidence scores for each prediction
- **Personalized Recommendations**: Tailored health suggestions based on findings
- **Visual Indicators**: Color-coded status indicators for easy interpretation

## Technology Stack

### Backend
- **Flask**: Python web framework
- **OpenCV**: Computer vision and image processing
- **scikit-image**: Advanced image analysis tools
- **scikit-learn**: Machine learning algorithms
- **NumPy**: Numerical computing
- **Pillow**: Image manipulation

### Frontend
- **HTML5/CSS3**: Modern web standards
- **JavaScript**: Interactive functionality
- **Font Awesome**: Professional icons
- **Responsive Grid**: CSS Grid and Flexbox

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone or download the application files**
   ```bash
   # Ensure you have all the required files:
   # - app.py
   # - requirements.txt
   # - templates/index.html
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create necessary directories**
   ```bash
   mkdir -p uploads static/css static/js
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## Usage Guide

### 1. Upload an Iris Image
- Click the upload area or drag and drop an image file
- Supported formats: JPG, PNG, GIF, BMP (max 16MB)
- Ensure the image clearly shows the iris with good lighting
- The system will automatically detect the iris boundary

### 2. Analyze the Image
- Click the "Analyze Iris" button after uploading
- Wait for the analysis to complete (typically 5-10 seconds)
- The system will process the image through multiple stages

### 3. View Results
The results are organized into three tabs:

#### Overview Tab
- **Visualization**: Shows the original image with iris detection overlay
- **Overall Score**: Percentage-based health assessment
- **Status Summary**: General health status classification

#### Regional Analysis Tab
- **10 Region Cards**: Detailed analysis of each organ system
- **Status Indicators**: Normal or "Attention Needed" classifications
- **Confidence Scores**: Machine learning prediction confidence
- **Descriptions**: Specific findings for each region

#### Recommendations Tab
- **Priority Actions**: Most important health recommendations
- **Areas of Concern**: Regions requiring attention
- **Lifestyle Suggestions**: Personalized health advice

## Iris Regions Analyzed

The application analyzes 10 distinct regions of the iris:

1. **Brain** (0°-30°): Neural pathways and cognitive function
2. **Lungs** (30°-60°): Respiratory system health
3. **Heart** (120°-150°): Cardiovascular indicators
4. **Liver** (150°-180°): Detoxification and processing
5. **Kidney** (180°-210°): Filtration and fluid balance
6. **Stomach** (210°-240°): Digestive acid balance
7. **Intestines** (240°-270°): Absorption and elimination
8. **Reproductive** (270°-300°): Hormonal balance
9. **Spine** (300°-330°): Structural integrity
10. **Circulation** (330°-360°): Overall blood flow

## Technical Details

### Image Processing Pipeline

1. **Preprocessing**
   - RGB to grayscale conversion
   - Gaussian blur for noise reduction
   - Image normalization

2. **Iris Detection**
   - Circle Hough Transform for boundary detection
   - Automatic pupil and iris edge identification
   - Segmentation mask creation

3. **Feature Extraction**
   - GLCM texture analysis at multiple angles (0°, 45°, 90°, 135°)
   - Statistical feature computation (contrast, dissimilarity, homogeneity, energy, correlation)
   - Region-specific analysis

4. **Classification**
   - Random Forest ensemble classification
   - Probability-based confidence scoring
   - Binary classification (Normal/Attention Needed)

### File Structure
```
iridology-app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Web interface
├── uploads/              # Uploaded images (created automatically)
└── static/               # Static files (created automatically)
    ├── css/
    └── js/
```

## API Endpoints

### POST /upload
Upload and analyze an iris image.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: Image file

**Response:**
```json
{
  "success": true,
  "circle_detected": [x, y, radius],
  "regional_analysis": {
    "brain": {
      "status": "Normal",
      "confidence": 85.2,
      "features": [0.1, 0.2, 0.8, 0.7, 0.5],
      "description": "Neural pathways appear clear..."
    }
  },
  "overall_assessment": {
    "overall_score": 78.5,
    "overall_status": "Good",
    "normal_regions": 8,
    "total_regions": 10,
    "areas_of_concern": ["heart", "liver"],
    "priority_recommendations": [...],
    "general_recommendation": "...",
    "disclaimer": "..."
  },
  "visualization": "base64_encoded_image",
  "timestamp": "2024-01-15T10:30:00"
}
```

## Troubleshooting

### Common Issues

1. **Iris Not Detected**
   - Ensure the iris is clearly visible in the image
   - Check that lighting is adequate
   - Try images with higher resolution
   - Avoid images with heavy shadows or reflections

2. **Low Accuracy**
   - Use high-quality images with good contrast
   - Ensure the iris fills a significant portion of the image
   - Avoid blurry or low-resolution images

3. **Upload Errors**
   - Check file size (max 16MB)
   - Verify file format (JPG, PNG, GIF, BMP)
   - Ensure stable internet connection

### Error Messages

- **"Could not detect iris"**: Image quality or iris visibility issues
- **"Could not segment iris"**: Processing failure, try different image
- **"File too large"**: Reduce image size below 16MB
- **"Invalid file format"**: Use supported image formats

## Development

### Adding New Features

To extend the application:

1. **New Analysis Regions**: Modify `iris_regions` dictionary in `IrisAnalyzer` class
2. **Additional Features**: Extend GLCM feature extraction in `extract_features` method
3. **Better Models**: Replace synthetic model with trained classifier
4. **New Visualizations**: Enhance `create_visualization` function

### Custom Models

To use your own trained models:

1. Replace the synthetic model initialization in `_initialize_model`
2. Save your model using `joblib` or `pickle`
3. Load the model in the `IrisAnalyzer` constructor
4. Ensure feature extraction matches your training data

## Contributing

This is an educational project demonstrating:
- Computer vision techniques in medical applications
- Modern web development with Flask
- Machine learning integration
- Responsive UI design

Feel free to extend and modify for educational purposes.

## License

This project is for educational use only. The iridology analysis provided is not medically validated and should not be used for actual health decisions.

## References

- Computer-Aided Iridology research papers
- OpenCV documentation for image processing
- scikit-learn for machine learning algorithms
- Flask web framework documentation

---

**Remember: This application is for educational purposes only and should never replace professional medical consultation.**