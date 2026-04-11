from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from .ocr_processor import OCRProcessor
from .rag_engine import RAGEngine
import os
import base64
import cv2
import numpy as np
import logging
from dotenv import load_dotenv   # ← Added for dotenv

# ====================== CONFIG ======================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()   # ← This loads .env file automatically if present in backend/ folder

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = os.urandom(24)

CORS(app)

# ====================== GEMINI API KEY ======================
# Now loaded from .env file (much safer than hardcoding)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    logger.warning("⚠️ GEMINI_API_KEY not found in .env file!")
    logger.warning("Create a .env file in backend/ folder with: GEMINI_API_KEY=your_actual_key_here")

# Initialize processors
logger.info("Initializing OCR Processor...")
ocr_processor = OCRProcessor()

logger.info("Initializing RAG Engine...")
rag_engine = RAGEngine(GEMINI_API_KEY)

if rag_engine.model:
    ocr_processor.set_gemini_model(rag_engine.model)
    logger.info("✓ Gemini model linked to OCR processor")
else:
    logger.error("❌ Gemini model failed to initialize. Check your GEMINI_API_KEY in .env")

# ====================== ROUTES ======================

@app.route('/')
def serve_frontend():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'gemini_configured': rag_engine.model is not None,
        'tesseract_configured': True
    })

@app.route('/api/ocr/image', methods=['POST'])
def process_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        logger.info(f"Processing image: {file.filename}")

        image_data = file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return jsonify({'error': 'Could not decode image'}), 400

        # Gemini OCR (preferred)
        context_text = None
        if rag_engine.model:
            logger.info("Trying Gemini Vision OCR...")
            gemini_text = ocr_processor.extract_with_gemini(image_base64, file.content_type)
            if gemini_text and len(gemini_text.strip()) > 15:
                context_text = gemini_text
                logger.info("✓ Gemini OCR succeeded")

        # Fallback to Tesseract
        if not context_text:
            logger.info("Falling back to Tesseract OCR...")
            context_text = ocr_processor.extract_with_tesseract(image)

        if not context_text or "No text detected" in context_text:
            context_text = "No readable text could be extracted from the image."

        rag_engine.set_context(context_text)
        summary = rag_engine.summarize_text()

        return jsonify({
            'success': True,
            'text': context_text,
            'summary': summary,
            'char_count': len(context_text),
            'word_count': len(context_text.split())
        })

    except Exception as e:
        logger.error(f"Image processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ocr/video', methods=['POST'])
def process_video():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400

        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        logger.info(f"Processing video: {file.filename}")

        # Save temporarily
        temp_path = f"temp_{file.filename}"
        file.save(temp_path)

        # Process video
        context_text = ocr_processor.process_video_ocr(temp_path)

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if "No readable text" in context_text or len(context_text.strip()) < 10:
            context_text = "No readable text could be extracted from the video frames."

        rag_engine.set_context(context_text)
        summary = rag_engine.summarize_text()

        return jsonify({
            'success': True,
            'text': context_text,
            'summary': summary,
            'char_count': len(context_text),
            'word_count': len(context_text.split())
        })

    except Exception as e:
        logger.error(f"Video processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])   # Changed to cleaner /api/chat (removed duplicate route)
def ocr_chat():
    try:
        data = request.get_json()   # Better than request.json for safety
        question = data.get('question', '').strip() if data else ''

        if not question:
            return jsonify({'error': 'Question is required'}), 400

        answer = rag_engine.query(question)

        return jsonify({
            'success': True,
            'answer': answer
        })

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = 5000
    logger.info(f"🚀 Starting OCR + Gemini Chatbot on http://localhost:{port}")
    logger.info(f"Gemini configured: {rag_engine.model is not None}")
    app.run(debug=True, host='0.0.0.0', port=port)
