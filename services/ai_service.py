import requests
import json
import time
from helpers.config import Config
from helpers.logger import Logger

class AIService:
    """Service for interacting with AI providers (Gemini)"""

    def __init__(self):
        self.provider = Config.get('AI_PROVIDER', 'gemini')
        self.api_key = Config.get('AI_API_KEY', '')
        self.model = Config.get('AI_MODEL', 'gemini-1.5-pro')

        if not self.api_key:
            Logger.warning('AI API Key not configured')

    def ask_question(self, prompt):
        """Send prompt to AI and get response"""
        if not self.api_key:
            Logger.error('AI API Key not configured')
            return {'success': False, 'error': 'AI service not configured'}

        try:
            response = self.call_gemini_api(prompt)
            return response
        except Exception as e:
            Logger.error('AI API error', {'error': str(e)})
            return {'success': False, 'error': f'Failed to get response from AI service: {str(e)}'}

    def call_gemini_api(self, prompt):
        """Call Gemini API with complete document text and retry logic"""
        # Try v1 endpoint first, then v1beta
        endpoints = [
            f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent?key={self.api_key}",
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        ]

        payload = {
            'contents': [
                {
                    'parts': [
                        {'text': prompt}
                    ]
                }
            ],
            'generationConfig': {
                'temperature': 0.7,
                'topP': 0.95,
                'topK': 64,
                'maxOutputTokens': 8096,
            }
        }

        headers = {
            'Content-Type': 'application/json'
        }

        last_error = None
        for url in endpoints:
            # Retry logic with exponential backoff
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    Logger.info(f'Attempting API call (attempt {attempt+1}/{max_retries}): {url[:80]}...')
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    response.raise_for_status()
                    
                    try:
                        decoded = response.json()
                    except json.JSONDecodeError as e:
                        raise Exception(f'Invalid JSON response from Gemini API: {str(e)}')

                    if 'error' in decoded:
                        error_msg = decoded['error'].get('message', 'Unknown error')
                        raise Exception(f"Gemini API error: {error_msg}")

                    try:
                        answer = decoded['candidates'][0]['content']['parts'][0]['text']
                    except (KeyError, IndexError, TypeError):
                        raise Exception('Unexpected API response format')

                    Logger.info('AI response generated successfully')
                    return {'success': True, 'answer': answer}
                    
                except requests.exceptions.HTTPError as e:
                    # Handle 503 Service Unavailable with retry
                    if e.response.status_code == 503:
                        if attempt < max_retries - 1:
                            Logger.warning(f'API temporarily unavailable (503). Retrying in {retry_delay} seconds...')
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                    last_error = str(e)
                    Logger.warning(f'API endpoint failed (attempt {attempt+1}): {str(e)}')
                    break
                    
                except requests.exceptions.RequestException as e:
                    last_error = str(e)
                    Logger.warning(f'API endpoint failed (attempt {attempt+1}): {str(e)}')
                    break
                    
                except Exception as e:
                    last_error = str(e)
                    Logger.warning(f'API call failed (attempt {attempt+1}): {str(e)}')
                    break
        
        # If we got here, all endpoints and retries failed
        raise Exception(f'All API endpoints failed after retries. Last error: {last_error}')
