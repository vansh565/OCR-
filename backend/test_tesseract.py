import pytesseract
import cv2
import numpy as np
from PIL import Image
import subprocess

# Check if tesseract is installed
try:
    result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
    print("✓ Tesseract is installed")
    print(result.stdout.split('\n')[0])
except FileNotFoundError:
    print("✗ Tesseract not found in PATH")
    print("Please install from: https://github.com/UB-Mannheim/tesseract/wiki")

# Check pytesseract
print(f"✓ pytesseract version: {pytesseract.__version__}")

# Create a simple test image with text
img = np.ones((100, 300), dtype=np.uint8) * 255
cv2.putText(img, "Test Text 123", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

# Try OCR
text = pytesseract.image_to_string(img)
print(f"Test OCR result: '{text.strip()}'")

if text.strip() == "Test Text 123":
    print("✓ OCR is working correctly!")
else:
    print("⚠️ OCR may not be configured correctly")