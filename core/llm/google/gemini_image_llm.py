"""Gemini 이미지 생성 LLM - Python 기반"""

import requests
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class GeminiImageLLM:
    """Gemini 이미지 생성 전용 LLM"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-image-preview", **kwargs):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = kwargs.get('timeout', 60)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def generate_image(self, prompt: str, **kwargs) -> str:
        """이미지 생성 및 Base64 데이터 반환"""
        try:
            url = f"{self.base_url}/{self.model_name}:generateContent"
            
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"Generate an image: {prompt}"
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 8192,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_msg = f"API Error {response.status_code}: {response.text}"
                logger.error(f"Gemini API 오류: {error_msg}")
                raise Exception(error_msg)
            
            result = response.json()
            
            # 이미지 데이터 추출
            if "candidates" in result and result["candidates"]:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        if "inlineData" in part and "data" in part["inlineData"]:
                            mime_type = part["inlineData"].get("mimeType", "image/png")
                            image_data = part["inlineData"]["data"]
                            return f"data:{mime_type};base64,{image_data}"
            
            raise Exception("No image data found in response")
            
        except requests.exceptions.Timeout:
            logger.error(f"Gemini 이미지 생성 타임아웃: {self.timeout}초")
            raise Exception(f"Image generation timed out after {self.timeout} seconds")
        except Exception as e:
            logger.error(f"Gemini 이미지 생성 오류: {e}")
            raise
    
    def __call__(self, prompt: str, **kwargs) -> str:
        """호출 가능한 객체로 만들기"""
        return self.generate_image(prompt, **kwargs)
    
    def invoke(self, input_data, config=None, **kwargs) -> str:
        """호환성을 위한 invoke 메서드"""
        if isinstance(input_data, str):
            prompt = input_data
        elif hasattr(input_data, 'content'):
            prompt = input_data.content
        else:
            prompt = str(input_data)
        
        return self.generate_image(prompt, **kwargs)