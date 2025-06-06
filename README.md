# 🏀 Basketball Shot Chart Analyzer

A Python-based web application that extracts shot zone statistics from basketball shot chart images using OCR and visualizes this data through interactive radar charts.

![Basketball Shot Chart Analyzer](https://img.shields.io/badge/Basketball-Shot%20Chart%20Analyzer-orange?style=for-the-badge&logo=python)

## ✨ Features

| Feature                              | Description                                                                           |
| ------------------------------------ | ------------------------------------------------------------------------------------- |
| 🧾 **OCR-based Data Extraction**     | Extract shooting statistics like "27/70" and "38.6%" with positions using pytesseract |
| 🧭 **Zone Inference**                | Map coordinates to known court zones (Left Corner 3, Paint, etc.)                     |
| 📈 **Radar Chart Visualization**     | Generate interactive radar charts from per-zone shot percentages                      |
| ⚔️ **Player Comparison**             | Compare multiple players on the same radar chart                                      |
| 🧠 **Similar Player Identification** | Find the most similar player using cosine similarity                                  |
| 🌐 **Web Interface**                 | Easy-to-use Streamlit interface with three main tabs                                  |

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Tesseract OCR installed on your system

#### Installing Tesseract

**macOS:**

```bash
brew install tesseract
```

**Ubuntu/Debian:**

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### Installation

1. **Clone the repository:**

```bash
git clone <repository-url>
cd chart2radar
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Run the application:**

```bash
streamlit run app.py
```

4. **Open your browser:**
   The app will automatically open at `http://localhost:8501`

## 📖 Usage Guide

### 1. 📤 Upload & Extract Tab

1. **Choose Image Source:**

   - Use sample shot charts (included in `shot_charts/` folder)
   - Or upload your own shot chart image

2. **Extract Data:**
   - Click "🔍 Extract Shot Data"
   - The app will use OCR to extract shooting statistics
   - View extracted zone statistics and quick radar preview

### 2. 📊 Radar Charts Tab

**Single Player Analysis:**

- Select a player from the database
- View detailed player analysis (strengths, weaknesses, playing style)
- See an interactive radar chart visualization

**Compare Players:**

- Select 2-4 players to compare
- View side-by-side radar chart comparison
- See comparison table with zone-by-zone statistics

**Detailed Comparison:**

- Choose 2-3 players for detailed analysis
- View both radar and bar chart comparisons

### 3. 🔍 Similarity Search Tab

- **Find Similar Players:** Select a target player and find the most similar players
- **Similarity Methods:** Choose between Cosine Similarity or Euclidean Distance
- **Visual Comparison:** See radar chart comparisons with similar players
- **Similarity Matrix:** View heatmap of all player similarities

## 📂 Project Structure

```
chart2radar/
├── app.py                 # Main Streamlit application
├── ocr_extractor.py      # OCR extraction module
├── zone_mapper.py        # Shot zone mapping module
├── radar_chart.py        # Radar chart visualization module
├── similarity_finder.py  # Player similarity analysis module
├── requirements.txt      # Python dependencies
├── shot_charts/         # Sample shot chart images
│   ├── marina_mabrey.jpeg
│   ├── kellsey_mitchell.jpeg
│   ├── ariel_atkins.jpeg
│   └── allisha_gray.jpeg
└── README.md            # This file
```

## 🧭 Shot Zones

The application recognizes the following basketball shot zones:

- **Three-Point Zones:**

  - Left Corner 3
  - Left Wing 3
  - Top of Key 3
  - Right Wing 3
  - Right Corner 3
  - Above Break 3

- **Mid-Range & Paint:**
  - Left Mid Range
  - Right Mid Range
  - Free Throw Line
  - Paint

## 🔧 Technical Details

### OCR Processing

- Uses `pytesseract` for text extraction
- Applies image preprocessing for better accuracy
- Filters extracted text to identify basketball statistics
- Maps text positions to court zones

### Zone Mapping

- Defines bounding boxes for each shot zone
- Groups nearby OCR results
- Pairs made/attempts with percentages
- Handles missing or incomplete data

### Similarity Analysis

- Normalizes player data to consistent format
- Computes cosine similarity or Euclidean distance
- Identifies playing style characteristics
- Creates similarity matrices for multiple players

### Visualization

- Uses `matplotlib` for radar charts
- Supports single player and comparison views
- Interactive Streamlit interface
- Professional styling and color schemes

## 🎯 Sample Data

The application includes sample shot charts for:

- Marina Mabrey
- Kellsey Mitchell
- Ariel Atkins
- Allisha Gray

These can be used to test the application's functionality.

## ⚙️ Configuration

### Zone Boundaries

Zone boundaries can be adjusted in `zone_mapper.py` based on your shot chart image dimensions:

```python
self.shot_zones = {
    'Left Corner 3': {'x_range': (0, 150), 'y_range': (300, 500)},
    'Right Corner 3': {'x_range': (650, 800), 'y_range': (300, 500)},
    # ... more zones
}
```

### OCR Settings

OCR confidence thresholds and text patterns can be modified in `ocr_extractor.py`:

```python
# Adjust confidence threshold
if confidence > 30 and text and self.is_basketball_stat(text):
    # Process text
```

## 🔍 Troubleshooting

**OCR Not Extracting Text:**

- Ensure Tesseract is properly installed
- Check image quality and contrast
- Adjust OCR confidence thresholds

**Zone Mapping Issues:**

- Verify zone boundary coordinates match your shot chart layout
- Check image dimensions and coordinate system

**Performance Issues:**

- Reduce image size for faster processing
- Clear player database periodically
- Close matplotlib figures properly

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the web interface
- Uses [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text extraction
- Visualization powered by [Matplotlib](https://matplotlib.org/)
- Similarity analysis using [scikit-learn](https://scikit-learn.org/)

---

🏀 **Ready to analyze some shot charts?** Run `streamlit run app.py` and start exploring!
