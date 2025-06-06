import pytesseract
import cv2
import numpy as np
from PIL import Image
import re
from typing import List, Dict, Tuple


class ShotChartOCR:
    """OCR extractor for basketball shot chart images."""
    
    def __init__(self):
        # Configure pytesseract if needed (adjust path for your system)
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'  # macOS
        pass
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for better OCR results."""
        # Read image
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Apply morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def is_basketball_stat(self, text: str) -> bool:
        """Check if text looks like basketball statistics."""
        text = text.strip()
        
        # Pattern for made/attempts (e.g., "27/70", "5/12")
        made_attempts_pattern = r'^\d+/\d+$'
        
        # Pattern for percentages (e.g., "38.6%", "45%")
        percentage_pattern = r'^\d+\.?\d*%$'
        
        # Pattern for simple numbers that could be stats
        number_pattern = r'^\d+$'
        
        return (re.match(made_attempts_pattern, text) or 
                re.match(percentage_pattern, text) or
                (re.match(number_pattern, text) and len(text) <= 3))
    
    def extract_text_with_positions(self, image_path: str) -> List[Dict]:
        """Extract text and their positions from shot chart image."""
        # Preprocess image
        processed_img = self.preprocess_image(image_path)
        
        # Use pytesseract to get data
        data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
        
        extracted_data = []
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            confidence = int(data['conf'][i])
            
            # Filter out low confidence and non-basketball stats
            if confidence > 30 and text and self.is_basketball_stat(text):
                x = data['left'][i]
                y = data['top'][i]
                width = data['width'][i]
                height = data['height'][i]
                
                extracted_data.append({
                    'text': text,
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height,
                    'confidence': confidence,
                    'center_x': x + width // 2,
                    'center_y': y + height // 2
                })
        
        return extracted_data
    
    def extract_from_original_image(self, image_path: str) -> List[Dict]:
        """Extract text directly from original image without preprocessing."""
        # Read original image
        img = Image.open(image_path)
        
        # Use pytesseract to get data
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        extracted_data = []
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            confidence = int(data['conf'][i])
            
            # Filter out low confidence and non-basketball stats
            if confidence > 20 and text and self.is_basketball_stat(text):
                x = data['left'][i]
                y = data['top'][i]
                width = data['width'][i]
                height = data['height'][i]
                
                extracted_data.append({
                    'text': text,
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height,
                    'confidence': confidence,
                    'center_x': x + width // 2,
                    'center_y': y + height // 2
                })
        
        return extracted_data
    
    def extract_basketball_stats(self, image_path: str) -> List[Dict]:
        """Main method to extract basketball statistics from shot chart."""
        # Try both preprocessed and original image
        preprocessed_results = self.extract_text_with_positions(image_path)
        original_results = self.extract_from_original_image(image_path)
        
        # Combine results and remove duplicates
        all_results = preprocessed_results + original_results
        
        # Remove duplicates based on position and text
        unique_results = []
        seen = set()
        
        for result in all_results:
            key = (result['text'], result['center_x'], result['center_y'])
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return sorted(unique_results, key=lambda x: (x['center_y'], x['center_x']))


if __name__ == "__main__":
    # Test the OCR extractor
    ocr = ShotChartOCR()
    results = ocr.extract_basketball_stats("shot_charts/marina_mabrey.jpeg")
    
    print("Extracted Basketball Statistics:")
    for result in results:
        print(f"Text: {result['text']}, Position: ({result['center_x']}, {result['center_y']}), Confidence: {result['confidence']}") 