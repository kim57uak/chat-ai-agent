# 🎨 무료 이미지 생성 API 테스트 가이드

## 📋 준비사항

### 1. 필수 패키지 설치
```bash
pip install requests replicate
```

### 2. API 토큰 발급

#### Hugging Face (무료)
1. [huggingface.co](https://huggingface.co) 회원가입
2. [Settings > Access Tokens](https://huggingface.co/settings/tokens) 이동
3. "New token" 클릭
4. 토큰 생성 후 복사

#### Replicate (무료 크레딧)
1. [replicate.com](https://replicate.com) 회원가입
2. [Account > API Tokens](https://replicate.com/account/api-tokens) 이동
3. 토큰 생성 후 복사

## 🧪 테스트 실행

### 1. 전체 테스트 (추천)
```bash
python test_image_generation.py
```

### 2. 개별 서비스 테스트

#### Pollinations (API 키 불필요)
```bash
python test_pollinations.py
```

#### Hugging Face
```bash
# 토큰 설정 후
python test_huggingface.py
```

#### Replicate
```bash
# 토큰 설정 후
python test_replicate.py
```

## ⚙️ 토큰 설정 방법

### 방법 1: 스크립트 직접 수정
```python
# test_huggingface.py
HF_TOKEN = "hf_your_actual_token_here"

# test_replicate.py
REPLICATE_TOKEN = "r8_your_actual_token_here"
```

### 방법 2: 환경변수 사용
```bash
export HF_TOKEN="hf_your_actual_token_here"
export REPLICATE_TOKEN="r8_your_actual_token_here"

python test_image_generation.py
```

## 📊 예상 결과

### ✅ 성공 시
```
🎨 Pollinations 테스트: 'a cute cat wearing a space helmet, digital art'
📡 요청 URL: https://image.pollinations.ai/prompt/a%20cute%20cat%20wearing%20a%20space%20helmet%2C%20digital%20art
✅ 이미지 저장됨: generated_images/pollinations_20241221_143022.png

🤗 Hugging Face 테스트: 'a cute cat wearing a space helmet, digital art'
📡 API 호출 중...
✅ 이미지 저장됨: generated_images/huggingface_20241221_143045.png

🔄 Replicate 테스트: 'a cute cat wearing a space helmet, digital art'
📡 API 호출 중...
✅ 이미지 저장됨: generated_images/replicate_20241221_143112.png
```

### ❌ 실패 시 해결방법

#### Pollinations 실패
- 인터넷 연결 확인
- 프롬프트가 너무 길지 않은지 확인

#### Hugging Face 실패
- 토큰이 올바른지 확인
- 모델 로딩 중이면 잠시 대기
- 월 1,000회 제한 확인

#### Replicate 실패
- `pip install replicate` 실행
- 토큰이 올바른지 확인
- 무료 크레딧 잔액 확인

## 🎯 테스트 프롬프트 예시

### 간단한 프롬프트
```
"a cute cat"
"beautiful sunset"
"red car"
```

### 상세한 프롬프트
```
"a cute cat wearing a space helmet, digital art, high quality"
"beautiful sunset over mountains, realistic, golden hour"
"red sports car in cyberpunk city, neon lights, night scene"
```

### 스타일 지정
```
"portrait of a woman, oil painting style"
"landscape, watercolor style"
"robot, anime style"
```

## 📁 생성된 파일

테스트 실행 후 다음 폴더에서 이미지 확인:
- `generated_images/` (전체 테스트)
- `images/` (개별 테스트)

## 🔧 문제 해결

### 1. 패키지 설치 오류
```bash
pip install --upgrade pip
pip install requests replicate
```

### 2. 토큰 오류
- 토큰 앞뒤 공백 제거
- 토큰 유효성 확인
- 새 토큰 재발급

### 3. 네트워크 오류
- 방화벽 설정 확인
- VPN 사용 시 해제 후 테스트

### 4. 이미지 저장 오류
- 폴더 쓰기 권한 확인
- 디스크 용량 확인

## 🎉 성공 후 다음 단계

1. **Chat-AI-Agent 통합**: 성공한 서비스를 MCP 도구로 추가
2. **프롬프트 최적화**: 더 나은 결과를 위한 프롬프트 개선
3. **UI 통합**: 채팅 인터페이스에서 이미지 생성 기능 사용

## 💡 팁

- **Pollinations**: 가장 빠르고 간단, API 키 불필요
- **Hugging Face**: 다양한 모델, 월 1,000회 무료
- **Replicate**: 최고 품질, 무료 크레딧 제한적

**추천 순서**: Pollinations → Hugging Face → Replicate