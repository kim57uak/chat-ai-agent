#!/usr/bin/env python3
import requests
import json

def get_free_models_korean():
    """무료 모델들의 한글 설명"""
    api_key = "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"
    
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code == 200:
            models = response.json()['data']
            
            # 무료 모델 필터링
            free_models = []
            for model in models:
                model_id = model['id']
                pricing = model.get('pricing', {})
                prompt_price = pricing.get('prompt', '0')
                
                if prompt_price == '0' or ':free' in model_id:
                    free_models.append(model)
            
            return free_models
        else:
            print(f"오류: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"예외 발생: {e}")
        return []

def print_korean_summary(models):
    """한글로 모델 요약 출력"""
    
    categories = {
        '🧠 추론 특화': [
            'deepseek/deepseek-r1:free',
            'deepseek/deepseek-r1-0528:free', 
            'deepseek/deepseek-r1-distill-llama-70b:free',
            'deepseek/deepseek-r1-distill-qwen-14b:free',
            'nvidia/llama-3.1-nemotron-ultra-253b-v1:free',
            'qwen/qwq-32b:free'
        ],
        '💻 코딩 특화': [
            'qwen/qwen3-coder:free',
            'qwen/qwen-2.5-coder-32b-instruct:free',
            'moonshotai/kimi-dev-72b:free',
            'mistralai/devstral-small-2505:free'
        ],
        '🖼️ 멀티모달': [
            'google/gemini-2.0-flash-exp:free',
            'google/gemma-3-27b-it:free',
            'google/gemma-3-12b-it:free',
            'google/gemma-3-4b-it:free',
            'meta-llama/llama-4-maverick:free',
            'meta-llama/llama-4-scout:free',
            'qwen/qwen2.5-vl-72b-instruct:free',
            'qwen/qwen2.5-vl-32b-instruct:free',
            'mistralai/mistral-small-3.2-24b-instruct:free',
            'moonshotai/kimi-vl-a3b-thinking:free'
        ],
        '🦙 Meta Llama': [
            'meta-llama/llama-3.1-405b-instruct:free',
            'meta-llama/llama-3.3-70b-instruct:free',
            'meta-llama/llama-3.3-8b-instruct:free',
            'meta-llama/llama-3.2-3b-instruct:free'
        ],
        '🔍 Google 모델': [
            'google/gemma-2-9b-it:free',
            'google/gemma-3n-e4b-it:free',
            'google/gemma-3n-e2b-it:free'
        ],
        '🌪️ Mistral': [
            'mistralai/mistral-7b-instruct:free',
            'mistralai/mistral-nemo:free',
            'mistralai/mistral-small-24b-instruct-2501:free',
            'mistralai/mistral-small-3.1-24b-instruct:free'
        ],
        '🇨🇳 중국 모델': [
            'qwen/qwen-2.5-72b-instruct:free',
            'qwen/qwen3-235b-a22b:free',
            'qwen/qwen3-30b-a3b:free',
            'qwen/qwen3-14b:free',
            'qwen/qwen3-8b:free',
            'qwen/qwen3-4b:free',
            'tencent/hunyuan-a13b-instruct:free',
            'z-ai/glm-4.5-air:free'
        ],
        '🤖 OpenAI 오픈소스': [
            'openai/gpt-oss-120b:free',
            'openai/gpt-oss-20b:free'
        ],
        '🔬 실험 모델': [
            'openrouter/sonoma-dusk-alpha',
            'openrouter/sonoma-sky-alpha'
        ],
        '🌐 다국어/특수': [
            'shisa-ai/shisa-v2-llama3.3-70b:free',
            'microsoft/mai-ds-r1:free',
            'nvidia/nemotron-nano-9b-v2',
            'rekaai/reka-flash-3:free',
            'nousresearch/deephermes-3-llama-3-8b-preview:free'
        ]
    }
    
    descriptions = {
        # 추론 특화
        'deepseek/deepseek-r1:free': '🏆 OpenAI o1과 동등한 성능을 가진 671B 파라미터 모델로, 추론 패스당 37B가 활성화됩니다. 오픈소스이며 완전히 공개된 추론 토큰을 제공합니다. MIT 라이선스로 자유롭게 증류 및 상용화가 가능하며, 163,840 토큰 컨텍스트를 지원합니다.',
        'deepseek/deepseek-r1-0528:free': '🔥 원래 DeepSeek R1의 5월 28일 업데이트 버전으로, 더 많은 컴퓨팅 자원과 스마트한 후처리 기법을 활용하여 추론과 추론 능력을 O3와 Gemini 2.5 Pro 같은 플래그십 모델 수준으로 끌어올렸습니다. 수학, 프로그래밍, 논리 리더보드에서 1위를 차지하며 사고의 깊이에서 단계적 변화를 보여줍니다.',
        'deepseek/deepseek-r1-distill-llama-70b:free': '📚 Llama-3.3-70B-Instruct를 기반으로 DeepSeek R1의 출력을 사용하여 증류한 대형 언어 모델입니다. 고급 증류 기법을 결합하여 여러 벤치마크에서 높은 성능을 달성했습니다: AIME 2024 pass@1 70.0, MATH-500 pass@1 94.5, CodeForces 레이팅 1633. 더 큰 프론티어 모델과 경쟁할 수 있는 성능을 가능하게 합니다.',
        'deepseek/deepseek-r1-distill-qwen-14b:free': '⚡ Qwen 2.5 14B를 기반으로 DeepSeek R1의 출력을 사용하여 증류한 모델로, 다양한 벤치마크에서 OpenAI의 o1-mini를 능가하며 덴스 모델에서 새로운 최고 성능을 달성했습니다. AIME 2024 pass@1 69.7, MATH-500 pass@1 93.9, CodeForces 레이팅 1481을 기록했습니다. 64,000 토큰 컨텍스트를 지원합니다.',
        'nvidia/llama-3.1-nemotron-ultra-253b-v1:free': '🚀 Meta의 Llama-3.1-405B-Instruct에서 파생된 대형 언어 모델로, 고급 추론, 인간 상호작용 채팅, RAG, 도구 호출 작업에 최적화되었습니다. Neural Architecture Search(NAS)를 사용하여 효율성 향상, 메모리 사용량 감소, 추론 지연 시간 개선을 이루었습니다. 128K 토큰 컨텍스트를 지원하며 8x NVIDIA H100 노드에서 효율적으로 작동합니다.',
        'qwen/qwq-32b:free': '🤔 Qwen 시리즈의 추론 모델로, 기존 명령어 튜닝 모델과 비교하여 사고하고 추론할 수 있는 능력을 가지고 있어 다운스트림 작업, 특히 어려운 문제에서 크게 향상된 성능을 달성할 수 있습니다. 32B 크기의 중간 규모 추론 모델로 DeepSeek-R1, o1-mini 같은 최고 수준의 추론 모델과 경쟁할 수 있는 성능을 발휘합니다.',
        
        # 코딩 특화  
        'qwen/qwen3-coder:free': '💻 Qwen 팀이 개발한 480B 총 파라미터의 MoE 코딩 모델로, 35B가 활성화됩니다(160개 전문가 중 8개). 함수 호출, 도구 사용, 저장소에 대한 긴 컨텍스트 추론과 같은 에이전트 코딩 작업에 최적화되었습니다. 262K 컨텍스트를 지원하며, 128K 입력 토큰 초과 시 높은 가격이 적용됩니다.',
        'qwen/qwen-2.5-coder-32b-instruct:free': '🔧 Qwen2.5-Coder 시리즈의 코드 전용 대형 언어 모델입니다. CodeQwen1.5 대비 코드 생성, 코드 추론, 코드 수정에서 크게 개선되었습니다. 코드 에이전트와 같은 실제 애플리케이션을 위한 포괄적인 기반을 제공하며, 코딩 능력뿐만 아니라 수학과 일반 역량도 유지합니다.',
        'moonshotai/kimi-dev-72b:free': '🛠️ Qwen2.5-72B를 기반으로 소프트웨어 엔지니어링과 이슈 해결 작업에 특화된 오픈소스 모델입니다. 실제 저장소에서 코드 패치를 적용하고 전체 테스트 스위트 실행으로 검증하는 대규모 강화학습으로 최적화되었습니다. SWE-bench Verified에서 60.4%를 달성하여 오픈소스 모델 중 소프트웨어 버그 수정과 코드 추론에서 새로운 벤치마크를 설정했습니다.',
        'mistralai/devstral-small-2505:free': '⚙️ Mistral AI와 All Hands AI가 공동 개발한 24B 파라미터 에이전트 LLM으로, Mistral-Small-3.1에서 고급 소프트웨어 엔지니어링 작업을 위해 파인튜닝되었습니다. 코드베이스 탐색, 다중 파일 편집, 코딩 에이전트 통합에 최적화되어 SWE-Bench Verified에서 46.8%의 최고 성능을 달성했습니다. 128K 컨텍스트와 커스텀 Tekken 토크나이저를 지원합니다.',
        
        # 멀티모달
        'google/gemini-2.0-flash-exp:free': '🌟 Google 최신 멀티모달. 1M 컨텍스트, 텍스트+이미지 입력 지원',
        'google/gemma-3-27b-it:free': '🎨 Google 최신 오픈소스. 멀티모달, 140개 언어, 함수 호출 지원',
        'google/gemma-3-12b-it:free': '📱 Gemma 3 중간 크기. 32K 컨텍스트, 비전-언어 입력',
        'google/gemma-3-4b-it:free': '⚡ Gemma 3 경량 버전. 모바일/저사양 기기 최적화',
        'meta-llama/llama-4-maverick:free': '🦄 Meta Llama 4 멀티모달. 17B 활성 파라미터, 1M 토큰 컨텍스트',
        'meta-llama/llama-4-scout:free': '🔍 Llama 4 효율 버전. 17B 활성, 10M 토큰 컨텍스트',
        'qwen/qwen2.5-vl-72b-instruct:free': '👁️ Qwen 비전-언어 모델. 이미지 분석, 차트 해석 뛰어남',
        'qwen/qwen2.5-vl-32b-instruct:free': '📊 수학적 추론, 시각적 문제 해결에 특화된 32B 모델',
        'mistralai/mistral-small-3.2-24b-instruct:free': '🖼️ Mistral 멀티모달. 함수 호출, 구조화된 출력 개선',
        'moonshotai/kimi-vl-a3b-thinking:free': '🧮 경량 MoE 비전 모델. 수학, 시각 추론에 특화',
        
        # Meta Llama
        'meta-llama/llama-3.1-405b-instruct:free': '👑 Meta 최대 모델 405B. GPT-4o, Claude 3.5와 경쟁 가능',
        'meta-llama/llama-3.3-70b-instruct:free': '🌍 8개 언어 지원 70B 모델. 다국어 대화 최적화',
        'meta-llama/llama-3.3-8b-instruct:free': '⚡ Llama 3.3 경량 버전. 빠른 응답 시간',
        'meta-llama/llama-3.2-3b-instruct:free': '📱 3B 다국어 모델. 8개 언어, 효율성과 정확성 균형',
        
        # Google 모델
        'google/gemma-2-9b-it:free': '🔥 Google 9B 효율 모델. 크기 대비 뛰어난 성능',
        'google/gemma-3n-e4b-it:free': '📱 모바일 최적화 4B. 동적 파라미터 활성화로 메모리 효율',
        'google/gemma-3n-e2b-it:free': '⚡ 초경량 2B 모델. 저사양 기기용',
        
        # Mistral
        'mistralai/mistral-7b-instruct:free': '🏛️ Mistral 클래식 7B. 속도와 컨텍스트 길이 최적화',
        'mistralai/mistral-nemo:free': '🤝 NVIDIA 협업 12B. 128K 컨텍스트, 다국어 지원',
        'mistralai/mistral-small-24b-instruct-2501:free': '🚀 Mistral Small 3. 81% MMLU, Llama 70B급 성능을 3배 빠르게',
        'mistralai/mistral-small-3.1-24b-instruct:free': '🎯 24B 멀티모달. 128K 컨텍스트, 함수 호출 지원',
        
        # 중국 모델
        'qwen/qwen-2.5-72b-instruct:free': '🇨🇳 Qwen 2.5 최대 모델. 코딩, 수학 대폭 개선, 29개 언어',
        'qwen/qwen3-235b-a22b:free': '🎯 235B MoE 모델. 22B 활성, 추론/비추론 모드 전환',
        'qwen/qwen3-30b-a3b:free': '⚖️ 30B MoE 균형 모델. 3.3B 활성, 다양한 작업 지원',
        'qwen/qwen3-14b:free': '🔄 14B 듀얼 모드. 추론/대화 모드 전환 가능',
        'qwen/qwen3-8b:free': '💬 8B 다목적. 32K 컨텍스트, 100개 언어',
        'qwen/qwen3-4b:free': '📱 4B 경량. 멀티턴 채팅, 에이전트 워크플로우',
        'tencent/hunyuan-a13b-instruct:free': '🐧 텐센트 13B MoE. 80B 총 파라미터, 추론 지원',
        'z-ai/glm-4.5-air:free': '🌬️ GLM 경량 버전. MoE 아키텍처, 추론/비추론 모드',
        
        # OpenAI 오픈소스
        'openai/gpt-oss-120b:free': '🔓 OpenAI 오픈소스 120B MoE. 단일 H100에서 실행 가능',
        'openai/gpt-oss-20b:free': '🔓 OpenAI 오픈소스 20B MoE. 소비자 하드웨어 최적화',
        
        # 실험 모델
        'openrouter/sonoma-dusk-alpha': '🌅 실험적 프론티어 모델. 2M 컨텍스트, 빠르고 지능적',
        'openrouter/sonoma-sky-alpha': '☁️ 최대 지능 실험 모델. 2M 컨텍스트, 최고 성능',
        
        # 다국어/특수
        'shisa-ai/shisa-v2-llama3.3-70b:free': '🇯🇵 일본어-영어 특화 70B. Llama 3.3 기반',
        'microsoft/mai-ds-r1:free': '🛡️ Microsoft 안전성 강화 R1. 차단된 주제 응답 개선',
        'nvidia/nemotron-nano-9b-v2': '🔬 NVIDIA 9B 통합 모델. 추론/비추론 작업 모두 지원',
        'rekaai/reka-flash-3:free': '⚡ Reka 21B 범용 모델. 저지연, 온디바이스 배포 최적화',
        'nousresearch/deephermes-3-llama-3-8b-preview:free': '🔮 Nous 8B 프리뷰. 추론/일반 응답 통합'
    }
    
    print("🆓 OpenRouter 무료 모델 59개 완전 가이드")
    print("="*80)
    
    for category, model_ids in categories.items():
        print(f"\n{category}")
        print("-" * 60)
        
        for model_id in model_ids:
            if model_id in descriptions:
                print(f"• {model_id}")
                print(f"  {descriptions[model_id]}")
                print()

def main():
    print_korean_summary([])

if __name__ == "__main__":
    main()