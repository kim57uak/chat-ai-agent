from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import os
import base64
import logging

logger = logging.getLogger(__name__)


class FileProcessor(ABC):
    """파일 처리를 위한 추상 클래스"""
    
    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """파일 처리 가능 여부 확인"""
        pass
    
    @abstractmethod
    def process(self, file_path: str) -> str:
        """파일 처리"""
        pass


class TextFileProcessor(FileProcessor):
    """텍스트 파일 처리기"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith('.txt')
    
    def process(self, file_path: str) -> str:
        # 다양한 encoding 시도
        for encoding in ['utf-8', 'cp949', 'euc-kr', 'latin-1', 'utf-8-sig']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return f"텍스트 파일: {os.path.basename(file_path)}\n인코딩을 읽을 수 없습니다."


class PDFFileProcessor(FileProcessor):
    """PDF 파일 처리기"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith('.pdf')
    
    def process(self, file_path: str) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            return "\n".join(page.extract_text() or '' for page in reader.pages)
        except ImportError:
            return f"PDF 파일: {os.path.basename(file_path)}\n(PyPDF2 라이브러리가 필요합니다)"
        except Exception as e:
            return f"PDF 파일 처리 오류: {str(e)}"


class WordFileProcessor(FileProcessor):
    """Word 파일 처리기"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.docx', '.doc'))
    
    def process(self, file_path: str) -> str:
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        except ImportError:
            return f"Word 파일: {os.path.basename(file_path)}\n(python-docx 라이브러리가 필요합니다)"
        except Exception as e:
            return f"Word 파일 처리 오류: {str(e)}"


class ExcelFileProcessor(FileProcessor):
    """Excel 파일 처리기"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.xlsx', '.xls'))
    
    def process(self, file_path: str) -> str:
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            return f"파일 정보: {os.path.basename(file_path)}\n열 수: {len(df.columns)}, 행 수: {len(df)}\n\n데이터 미리보기:\n{df.head(10).to_string()}"
        except ImportError:
            return f"Excel 파일: {os.path.basename(file_path)}\n(pandas 라이브러리가 필요합니다. pip install pandas openpyxl)"
        except Exception as e:
            return f"Excel 파일 처리 오류: {str(e)}"


class ImageFileProcessor(FileProcessor):
    """이미지 파일 처리기"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))
    
    def process(self, file_path: str) -> str:
        try:
            # 이미지를 base64로 인코딩
            with open(file_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            # 이미지 정보 추가 (선택사항)
            img_info = ""
            try:
                from PIL import Image
                img = Image.open(file_path)
                img_info = f"\n이미지 정보: {img.size[0]}x{img.size[1]} 픽셀, 모드: {img.mode}"
            except (ImportError, ModuleNotFoundError):
                pass
            
            return f"[IMAGE_BASE64]{img_data}[/IMAGE_BASE64]\n이미지 파일: {os.path.basename(file_path)}{img_info}"
            
        except Exception as e:
            file_size = os.path.getsize(file_path)
            return f"이미지 파일: {os.path.basename(file_path)}\n파일 크기: {file_size:,} bytes\n이미지 처리 오류: {str(e)}"


class JSONFileProcessor(FileProcessor):
    """JSON 파일 처리기"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith('.json')
    
    def process(self, file_path: str) -> str:
        import json
        # JSON 파일도 다중 인코딩 지원
        for encoding in ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    data = json.load(f)
                return f"JSON 파일 내용:\n{json.dumps(data, indent=2, ensure_ascii=False)}"
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        return f"JSON 파일: {os.path.basename(file_path)}\n파일을 읽을 수 없습니다."


class FileProcessorChain:
    """파일 처리기 체인 (Chain of Responsibility 패턴)"""
    
    def __init__(self):
        self.processors = [
            TextFileProcessor(),
            PDFFileProcessor(),
            WordFileProcessor(),
            ExcelFileProcessor(),
            ImageFileProcessor(),
            JSONFileProcessor(),
        ]
    
    def process_file(self, file_path: str) -> str:
        """파일 처리"""
        for processor in self.processors:
            if processor.can_process(file_path):
                return processor.process(file_path)
        
        # 지원하지 않는 파일도 기본 텍스트로 읽기 시도
        return self._process_unknown_file(file_path)
    
    def _process_unknown_file(self, file_path: str) -> str:
        """알 수 없는 파일 형식 처리"""
        for encoding in ['utf-8', 'cp949', 'euc-kr', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                return f"파일: {os.path.basename(file_path)}\n파일 읽기 오류: {str(e)}"
        
        return f"파일: {os.path.basename(file_path)}\n지원하지 않는 파일 형식입니다."