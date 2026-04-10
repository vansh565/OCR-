import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model = None
        self.context = ""
        self.setup_gemini()

    def setup_gemini(self):
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3-flash-preview')
            logger.info("RAG Engine: Gemini model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.model = None

    def set_context(self, text: str):
        self.context = text.strip()
        logger.info(f"Context set with {len(self.context)} characters")

    def summarize_text(self):
        if not self.model or not self.context:
            return "No content available to summarize."

        try:
            prompt = f"""
Summarize the following document in a clear and concise way:

{self.context}

Summary:
"""
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return "Could not generate summary."

    def query(self, question: str):
        if not self.model:
            return "Gemini model is not available. Please check API key."
        if not self.context:
            return "No document has been processed yet. Please upload an image first."

        try:
            prompt = f"""
You are a helpful assistant. Answer the question based ONLY on the following document.

Document:
{self.context}

Question: {question}

Answer clearly and accurately. If the answer is not in the document, say "Not mentioned in the document."
"""
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Query error: {e}")
            return f"Error generating answer: {str(e)}"