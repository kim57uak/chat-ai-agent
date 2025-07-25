"""이미지 처리를 담당하는 모듈"""
from abc import ABC, abstractmethod
from langchain.schema import HumanMessage
import logging
import re
import base64

logger = logging.getLogger(__name__)


class ImageProcessor(ABC):
    """이미지 처리를 위한 추상 클래스"""
    
    @abstractmethod
    def contains_image_data(self, user_input: str) -> bool:
        """이미지 데이터 포함 여부 확인"""
        pass
    
    @abstractmethod
    def process_image_input(self, user_input: str, model_name: str):
        """이미지 데이터 처리"""
        pass


class StandardImageProcessor(ImageProcessor):
    """표준 이미지 처리기"""
    
    def contains_image_data(self, user_input: str) -> bool:
        """이미지 데이터 포함 여부 확인"""
        return "[IMAGE_BASE64]" in user_input and "[/IMAGE_BASE64]" in user_input
    
    def process_image_input(self, user_input: str, model_name: str):
        """이미지 데이터를 처리하여 LangChain 메시지로 변환"""
        image_match = re.search(
            r"\[IMAGE_BASE64\](.*?)\[/IMAGE_BASE64\]", user_input, re.DOTALL
        )
        if not image_match:
            return HumanMessage(content=user_input)

        image_data = image_match.group(1).strip()
        text_content = user_input.replace(image_match.group(0), "").strip()

        try:
            base64.b64decode(image_data)
        except Exception as e:
            logger.error(f"잘못된 Base64 이미지 데이터: {e}")
            return HumanMessage(content="잘못된 이미지 데이터입니다.")

        if not text_content:
            text_content = self._get_default_image_analysis_prompt()

        try:
            if 'gemini' in model_name.lower():
                return HumanMessage(
                    content=[
                        {"type": "text", "text": text_content},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{image_data}",
                        },
                    ]
                )
            else:
                return HumanMessage(
                    content=[
                        {"type": "text", "text": text_content},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            },
                        },
                    ]
                )
        except Exception as e:
            logger.error(f"이미지 처리 오류: {e}")
            return HumanMessage(
                content=f"{text_content}\n\n[이미지 처리 오류: {str(e)}]"
            )
    
    def _get_default_image_analysis_prompt(self) -> str:
        """기본 이미지 분석 프롬프트"""
        return """Analyze this image comprehensively and extract all information.

**Analysis Tasks:**
1. **Complete Text Extraction**: Extract all visible text with perfect accuracy
2. **Content Understanding**: Identify the type and purpose of the document/image
3. **Structure Analysis**: Describe layout, organization, and visual hierarchy
4. **Context Interpretation**: Explain what the image represents and its significance

**Response Requirements:**
- Extract ALL text without any omissions
- Organize information logically and clearly
- Use appropriate formatting (tables, lists, headings) based on content
- Provide context and interpretation where helpful
- Respond in Korean unless the content suggests otherwise

**Quality Standards:**
- Accuracy: 100% faithful text extraction
- Completeness: Cover all visible information
- Clarity: Well-organized, easy to understand presentation
- Intelligence: Apply appropriate formatting based on content type"""