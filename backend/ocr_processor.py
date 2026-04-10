
import cv2
import numpy as np
import pytesseract
import base64
import os
import re

class OCRProcessor:
    def __init__(self):
        # Configure Tesseract path for Render (Linux)
        if os.name == 'posix':  # Linux (Render)
            pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        elif os.name == 'nt':  # Windows (local)
            tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        self.gemini_model = None
        print("✓ OCR Processor initialized")
    
    # ... rest of your methods stay the same ...

class OCRProcessor:
    def __init__(self):
        # Configure Tesseract path for Windows
        if os.name == 'nt':
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            found = False
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    print(f"✓ Tesseract found at: {path}")
                    found = True
                    break
            if not found:
                print(f"✗ Tesseract not found. Please install from: https://github.com/UB-Mannheim/tesseract/wiki")
        
        self.gemini_model = None
    
    def set_gemini_model(self, model):
        self.gemini_model = model
    
    def preprocess_for_ocr(self, image):
        """Advanced preprocessing to improve text detection"""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Resize image if too small (improves OCR)
        height, width = gray.shape
        if height < 300 or width < 300:
            scale_factor = max(2, 600 / min(height, width))
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            print(f"✓ Resized image from {width}x{height} to {new_width}x{new_height}")
        
        # Apply different preprocessing techniques
        processed_images = []
        
        # Method 1: Simple threshold
        _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(('otsu', thresh1))
        
        # Method 2: Adaptive threshold
        thresh2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY, 11, 2)
        processed_images.append(('adaptive', thresh2))
        
        # Method 3: Denoise first
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        _, thresh3 = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(('denoised', thresh3))
        
        # Method 4: Increase contrast
        contrasted = cv2.convertScaleAbs(gray, alpha=1.5, beta=30)
        _, thresh4 = cv2.threshold(contrasted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(('contrast', thresh4))
        
        # Method 5: Morphological operations
        kernel = np.ones((2,2), np.uint8)
        dilated = cv2.dilate(gray, kernel, iterations=1)
        _, thresh5 = cv2.threshold(dilated, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(('dilated', thresh5))
        
        # Try each preprocessing method and get the best result
        best_text = ""
        best_method = None
        
        for method_name, proc_img in processed_images:
            try:
                # Try different PSM modes
                for psm in [3, 6, 7, 8, 11, 12, 13]:
                    config = f'--oem 3 --psm {psm}'
                    text = pytesseract.image_to_string(proc_img, config=config)
                    text = text.strip()
                    if len(text) > len(best_text):
                        best_text = text
                        best_method = f"{method_name}_psm{psm}"
            except:
                continue
        
        if best_text:
            print(f"✓ Best OCR result using {best_method}, {len(best_text)} chars")
        
        return best_text, best_method
    
    def extract_with_tesseract(self, image):
        """Extract text with multiple attempts"""
        try:
            # First attempt: direct OCR with default settings
            direct_text = pytesseract.image_to_string(image)
            if len(direct_text.strip()) > 20:
                print(f"✓ Direct OCR successful: {len(direct_text)} chars")
                return direct_text.strip()
            
            # Second attempt: enhanced preprocessing
            print("Running enhanced preprocessing...")
            enhanced_text, method = self.preprocess_for_ocr(image)
            
            if enhanced_text and len(enhanced_text.strip()) > 10:
                print(f"✓ Enhanced OCR successful: {len(enhanced_text)} chars")
                return enhanced_text.strip()
            
            # Third attempt: try with just alphanumeric characters
            print("Trying alphanumeric only mode...")
            config = r'-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?@#$% '
            text = pytesseract.image_to_string(image, config=config)
            if len(text.strip()) > 5:
                return text.strip()
            
            return "No text detected in the image. Please ensure the image contains clear, readable text."
            
        except Exception as e:
            print(f"Tesseract error: {str(e)}")
            return f"OCR Error: {str(e)}"
    
    def extract_with_gemini(self, image_base64, mime_type="image/jpeg"):
        """Extract text using Gemini API"""
        if not self.gemini_model:
            return None
        
        try:
            prompt = """Extract ALL text from this image. 
            Return ONLY the extracted text, no explanations.
            If you see any words, numbers, or characters, extract them exactly.
            If no text is found, return 'NO_TEXT_FOUND'."""
            
            response = self.gemini_model.generate_content([
                prompt,
                {"mime_type": mime_type, "data": image_base64}
            ])
            
            result = response.text.strip()
            if result and result != 'NO_TEXT_FOUND':
                print(f"✓ Gemini extracted {len(result)} characters")
                return result
            return None
        except Exception as e:
            print(f"Gemini error: {str(e)}")
            return None
    
    def extract_frames_from_video(self, video_path, num_frames=5):
        """Extract frames from video"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return []
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames == 0:
            cap.release()
            return []
        
        frame_indices = np.linspace(0, total_frames - 1, min(num_frames, total_frames), dtype=int)
        
        frames = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret and frame is not None:
                frames.append(frame)
        
        cap.release()
        return frames
    
    def process_video_ocr(self, video_path):
        """Process video and extract text"""
        frames = self.extract_frames_from_video(video_path, num_frames=5)
        
        if not frames:
            return "Could not extract frames from video."
        
        all_text = []
        for i, frame in enumerate(frames, 1):
            text = self.extract_with_tesseract(frame)
            if text and "No text detected" not in text and "OCR Error" not in text:
                all_text.append(f"Frame {i}:\n{text}")
        
        if not all_text:
            return "No readable text found in any video frame."
        
        return "\n\n".join(all_text)
