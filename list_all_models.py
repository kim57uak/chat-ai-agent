#!/usr/bin/env python3
import requests
import json

def get_all_models():
    """OpenRouter의 모든 모델 리스트 가져오기"""
    api_key = "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"
    
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if response.status_code == 200:
            return response.json()['data']
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"Exception: {e}")
        return []

def categorize_models(models):
    """모델을 카테고리별로 분류"""
    categories = {
        'free': [],
        'openai': [],
        'google': [],
        'anthropic': [],
        'meta': [],
        'microsoft': [],
        'cohere': [],
        'mistral': [],
        'other': []
    }
    
    for model in models:
        model_id = model['id']
        pricing = model.get('pricing', {})
        prompt_price = pricing.get('prompt', '0')
        
        # 무료 모델
        if prompt_price == '0' or ':free' in model_id:
            categories['free'].append(model)
        # 제공업체별 분류
        elif 'openai/' in model_id:
            categories['openai'].append(model)
        elif 'google/' in model_id:
            categories['google'].append(model)
        elif 'anthropic/' in model_id:
            categories['anthropic'].append(model)
        elif 'meta/' in model_id or 'llama' in model_id.lower():
            categories['meta'].append(model)
        elif 'microsoft/' in model_id:
            categories['microsoft'].append(model)
        elif 'cohere/' in model_id:
            categories['cohere'].append(model)
        elif 'mistral/' in model_id:
            categories['mistral'].append(model)
        else:
            categories['other'].append(model)
    
    return categories

def print_models(models, title, show_pricing=True):
    """모델 리스트 출력"""
    print(f"\n{'='*60}")
    print(f"{title} ({len(models)}개)")
    print(f"{'='*60}")
    
    for model in models:
        model_id = model['id']
        pricing = model.get('pricing', {})
        prompt_price = pricing.get('prompt', 'N/A')
        completion_price = pricing.get('completion', 'N/A')
        
        if show_pricing:
            print(f"- {model_id}")
            print(f"  Prompt: ${prompt_price} | Completion: ${completion_price}")
        else:
            print(f"- {model_id}")

def main():
    print("OpenRouter 모든 텍스트 모델 리스트 조회 중...")
    
    models = get_all_models()
    if not models:
        print("모델 리스트를 가져올 수 없습니다.")
        return
    
    print(f"총 {len(models)}개 모델 발견")
    
    # 카테고리별 분류
    categories = categorize_models(models)
    
    # 무료 모델 (가장 중요)
    print_models(categories['free'], "🆓 무료 모델", show_pricing=False)
    
    # 무료 모델 59개 리스트 출력
    print(f"\n{'='*60}")
    print(f"🆓 무료 모델 59개 리스트")
    print(f"{'='*60}")
    free_models = categories['free'][:59]  # 최대 59개만
    for i, model in enumerate(free_models, 1):
        print(f"{i:2d}. {model['id']}")
    
    # 주요 제공업체별
    print_models(categories['openai'], "🤖 OpenAI 모델")
    print_models(categories['google'], "🔍 Google 모델") 
    print_models(categories['anthropic'], "🧠 Anthropic 모델")
    print_models(categories['meta'], "🦙 Meta/Llama 모델")
    print_models(categories['mistral'], "🌪️ Mistral 모델")
    print_models(categories['cohere'], "💬 Cohere 모델")
    print_models(categories['microsoft'], "🪟 Microsoft 모델")
    print_models(categories['other'], "🔧 기타 모델")
    
    # 요약 통계
    print(f"\n{'='*60}")
    print("📊 카테고리별 통계")
    print(f"{'='*60}")
    for category, models in categories.items():
        if models:
            print(f"{category.upper()}: {len(models)}개")

if __name__ == "__main__":
    main()