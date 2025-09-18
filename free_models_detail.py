#!/usr/bin/env python3
import requests
import json

def get_free_models_detail():
    """무료 모델들의 상세 정보"""
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
            print(f"Error: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Exception: {e}")
        return []

def print_model_details(model):
    """모델 상세 정보 출력"""
    print(f"\n{'='*80}")
    print(f"🆓 {model['id']}")
    print(f"{'='*80}")
    
    # 기본 정보
    print(f"📝 모델명: {model.get('name', '정보 없음')}")
    print(f"🏢 제공업체: {model.get('provider', '정보 없음')}")
    print(f"📅 생성일: {model.get('created', '정보 없음')}")
    
    # 컨텍스트 길이
    context_length = model.get('context_length', '정보 없음')
    print(f"📏 컨텍스트 길이: {context_length:,} 토큰" if isinstance(context_length, int) else f"📏 컨텍스트 길이: {context_length}")
    
    # 가격 정보
    pricing = model.get('pricing', {})
    print(f"💰 프롬프트 가격: ${pricing.get('prompt', '0')}")
    print(f"💰 완성 가격: ${pricing.get('completion', '0')}")
    
    # 설명
    description = model.get('description', '설명 없음')
    print(f"📖 설명: {description}")
    
    # 아키텍처 정보
    architecture = model.get('architecture', {})
    if architecture:
        print(f"🏗️ 아키텍처:")
        arch_translations = {
            'modality': '모달리티',
            'input_modalities': '입력 모달리티',
            'output_modalities': '출력 모달리티', 
            'tokenizer': '토크나이저',
            'instruct_type': '명령어 타입'
        }
        for key, value in architecture.items():
            korean_key = arch_translations.get(key, key)
            print(f"   {korean_key}: {value}")
    
    # 최대 토큰
    max_tokens = model.get('top_provider', {}).get('max_completion_tokens')
    if max_tokens:
        print(f"🎯 최대 완성 토큰: {max_tokens:,}개")

def main():
    print("🆓 OpenRouter 무료 모델 상세 정보")
    print("="*80)
    
    free_models = get_free_models_detail()
    
    if not free_models:
        print("무료 모델을 가져올 수 없습니다.")
        return
    
    print(f"총 {len(free_models)}개의 무료 모델 발견\n")
    
    # 제공업체별로 그룹화
    providers = {}
    for model in free_models:
        provider = model.get('provider', '알 수 없음')
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(model)
    
    # 제공업체별로 출력
    for provider, models in sorted(providers.items()):
        provider_name = provider if provider != 'N/A' else '기타'
        print(f"\n🏢 {provider_name} ({len(models)}개 모델)")
        print("="*80)
        
        for model in sorted(models, key=lambda x: x['id']):
            print_model_details(model)

if __name__ == "__main__":
    main()