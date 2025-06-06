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
    
    def preprocess_image_enhanced(self, image_path: str) -> List[np.ndarray]:
        """Create multiple preprocessed versions for better OCR results."""
        # Read image
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        processed_images = []
        
        # Original grayscale
        processed_images.append(gray)
        
        # Binary threshold (Otsu)
        _, thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(thresh_otsu)
        
        # Adaptive threshold
        thresh_adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        processed_images.append(thresh_adaptive)
        
        # Gaussian blur + threshold
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh_blur = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(thresh_blur)
        
        return processed_images
    
    def is_basketball_stat(self, text: str) -> bool:
        """Check if text looks like basketball statistics."""
        text = text.strip()
        
        # Handle empty text
        if not text:
            return False
        
        # Pattern for made/attempts (e.g., "27/70", "5/12")
        made_attempts_pattern = r'^\d+/\d+$'
        
        # Pattern for percentages (e.g., "38.6%", "45%")
        percentage_pattern = r'^\d+\.?\d*%$'
        
        # Pattern for simple numbers that could be stats
        number_pattern = r'^\d+$'
        
        # Pattern for "NA" or "N/A" (not available)
        na_pattern = r'^(NA|N/A|na|n/a)$'
        
        # Pattern for decimal numbers without %
        decimal_pattern = r'^\d+\.\d+$'
        
        return (re.match(made_attempts_pattern, text) or 
                re.match(percentage_pattern, text) or
                re.match(na_pattern, text) or
                re.match(decimal_pattern, text) or
                (re.match(number_pattern, text) and len(text) <= 3))
    
    def extract_text_with_positions(self, image_path: str) -> List[Dict]:
        """Extract text and their positions from shot chart image."""
        # Get multiple preprocessed versions
        processed_images = self.preprocess_image_enhanced(image_path)
        
        all_extractions = []
        
        for i, processed_img in enumerate(processed_images):
            # Use pytesseract to get data
            data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
            
            for j in range(len(data['text'])):
                text = data['text'][j].strip()
                confidence = int(data['conf'][j])
                
                # Lower confidence threshold and improve filtering
                min_confidence = 20 if i == 0 else 30  # Lower threshold for original image
                
                if confidence > min_confidence and text and self.is_basketball_stat(text):
                    x = data['left'][j]
                    y = data['top'][j]
                    width = data['width'][j]
                    height = data['height'][j]
                    
                    all_extractions.append({
                        'text': text,
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height,
                        'confidence': confidence,
                        'center_x': x + width // 2,
                        'center_y': y + height // 2,
                        'method': f'preprocessed_{i}'
                    })
        
        return all_extractions
    
    def extract_from_original_image(self, image_path: str) -> List[Dict]:
        """Extract text directly from original image without preprocessing."""
        # Read original image
        img = Image.open(image_path)
        
        # Use pytesseract to get data with custom config
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz./% '
        data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)
        
        extracted_data = []
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            confidence = int(data['conf'][i])
            
            # Lower confidence threshold for original image
            if confidence > 15 and text and self.is_basketball_stat(text):
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
                    'center_y': y + height // 2,
                    'method': 'original'
                })
        
        return extracted_data
    
    def remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate detections based on position and text similarity."""
        if not results:
            return results
        
        unique_results = []
        tolerance = 20  # pixels tolerance for considering positions similar
        
        for result in results:
            is_duplicate = False
            
            for existing in unique_results:
                # Check if positions are close and text is similar
                x_diff = abs(result['center_x'] - existing['center_x'])
                y_diff = abs(result['center_y'] - existing['center_y'])
                
                if (x_diff <= tolerance and y_diff <= tolerance and 
                    result['text'] == existing['text']):
                    # Keep the one with higher confidence
                    if result['confidence'] > existing['confidence']:
                        unique_results.remove(existing)
                        unique_results.append(result)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_results.append(result)
        
        return unique_results
    
    def detect_missing_zones(self, image_path: str, detected_stats: List[Dict]) -> List[Dict]:
        """Detect zones that might have N/A values by looking for missing data and faint text."""
        from PIL import Image, ImageEnhance
        
        # Load image for enhanced OCR
        img = Image.open(image_path)
        
        # Try with extreme contrast enhancement for faint N/A text
        enhancer = ImageEnhance.Contrast(img)
        high_contrast = enhancer.enhance(3.0)
        brightness_enhancer = ImageEnhance.Brightness(high_contrast)
        bright_img = brightness_enhancer.enhance(1.5)
        
        # Very aggressive OCR settings for N/A detection
        na_candidates = []
        configs = [
            r'--oem 3 --psm 8 -c tessedit_char_whitelist=NAna/',
            r'--oem 3 --psm 7 -c tessedit_char_whitelist=NAna/',
        ]
        
        for config in configs:
            try:
                data = pytesseract.image_to_data(bright_img, config=config, output_type=pytesseract.Output.DICT)
                
                for i in range(len(data['text'])):
                    text = data['text'][i].strip()
                    confidence = int(data['conf'][i])
                    
                    if confidence > 5 and text:  # Very low threshold
                        text_upper = text.upper()
                        if (text_upper in ['N/A', 'NA', 'N', 'A', '/'] or 
                            ('N' in text_upper and 'A' in text_upper)):
                            
                            x = data['left'][i]
                            y = data['top'][i]
                            width = data['width'][i]
                            height = data['height'][i]
                            
                            na_candidates.append({
                                'text': text,
                                'x': x,
                                'y': y,
                                'width': width,
                                'height': height,
                                'confidence': confidence,
                                'center_x': x + width // 2,
                                'center_y': y + height // 2,
                                'method': 'na_detection'
                            })
            except Exception:
                continue
        
        # Define expected zones based on typical shot chart layout
        expected_zones = [
            {'name': 'Left Mid Range', 'x_range': (100, 280), 'y_range': (220, 340)},
            {'name': 'Right Mid Range', 'x_range': (470, 650), 'y_range': (220, 340)},
            {'name': 'Free Throw Line Center', 'x_range': (300, 450), 'y_range': (180, 280)},
        ]
        
        inferred_nas = []
        
        for zone in expected_zones:
            # Check if we have any stats in this zone
            stats_in_zone = []
            for stat in detected_stats:
                if (zone['x_range'][0] <= stat['center_x'] <= zone['x_range'][1] and
                    zone['y_range'][0] <= stat['center_y'] <= zone['y_range'][1]):
                    stats_in_zone.append(stat)
            
            if not stats_in_zone:
                # Look for N/A candidates in this zone
                candidates_in_zone = []
                for candidate in na_candidates:
                    if (zone['x_range'][0] <= candidate['center_x'] <= zone['x_range'][1] and
                        zone['y_range'][0] <= candidate['center_y'] <= zone['y_range'][1]):
                        candidates_in_zone.append(candidate)
                
                if candidates_in_zone:
                    # Found actual N/A text in this zone
                    best_candidate = max(candidates_in_zone, key=lambda x: x['confidence'])
                    best_candidate['text'] = 'N/A'  # Normalize to standard format
                    inferred_nas.append(best_candidate)
                else:
                    # No stats and no N/A text found - infer N/A at zone center
                    center_x = (zone['x_range'][0] + zone['x_range'][1]) // 2
                    center_y = (zone['y_range'][0] + zone['y_range'][1]) // 2
                    
                    inferred_nas.append({
                        'text': 'N/A',
                        'x': center_x - 10,
                        'y': center_y - 5,
                        'width': 20,
                        'height': 10,
                        'confidence': 50,  # Medium confidence for inferred
                        'center_x': center_x,
                        'center_y': center_y,
                        'method': 'inferred_na'
                    })
        
        return inferred_nas
    
    def extract_basketball_stats(self, image_path: str) -> List[Dict]:
        """Main method to extract basketball statistics from shot chart."""
        # Try both preprocessed and original image
        preprocessed_results = self.extract_text_with_positions(image_path)
        original_results = self.extract_from_original_image(image_path)
        
        # Combine results
        all_results = preprocessed_results + original_results
        
        # Remove duplicates
        unique_results = self.remove_duplicates(all_results)
        
        # Detect missing zones and N/A values
        na_results = self.detect_missing_zones(image_path, unique_results)
        
        # Combine all results
        final_results = unique_results + na_results
        
        # Sort by position (top to bottom, left to right)
        return sorted(final_results, key=lambda x: (x['center_y'], x['center_x']))


if __name__ == "__main__":
    # Test the OCR extractor
    ocr = ShotChartOCR()
    results = ocr.extract_basketball_stats("shot_charts/marina_mabrey.jpeg")
    
    print("Extracted Basketball Statistics:")
    for result in results:
        print(f"Text: {result['text']}, Position: ({result['center_x']}, {result['center_y']}), Confidence: {result['confidence']}, Method: {result['method']}") 