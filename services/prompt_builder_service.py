class PromptBuilderService:
    """Service for building prompts for AI"""

    @staticmethod
    def build_prompt(document_text, user_question):
        """Build complete prompt for AI"""
        system_instruction = """You are a document question-answering assistant.
Answer only from the provided document.
If the answer is not clearly stated in the document, say:
"This is not clearly stated in the uploaded document."
Keep answers clear, concise, and professional."""

        prompt = system_instruction + "\n\n"
        prompt += "DOCUMENT CONTENT:\n"
        prompt += "==================================================\n"
        prompt += document_text + "\n"
        prompt += "==================================================\n\n"
        prompt += "USER QUESTION:\n"
        prompt += user_question + "\n\n"
        prompt += "ANSWER:\n"

        return prompt
