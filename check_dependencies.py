#!/usr/bin/env python3
"""
Check all dependencies for sentence_transformers before packaging
"""

import sys
import importlib
from typing import List, Tuple

def check_import(module_name: str) -> Tuple[bool, str]:
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_name)
        return True, f"✅ {module_name}"
    except ImportError as e:
        return False, f"❌ {module_name}: {str(e)}"
    except Exception as e:
        return False, f"⚠️  {module_name}: {str(e)}"

def main():
    print("=" * 80)
    print("🔍 Checking sentence_transformers dependencies...")
    print("=" * 80)
    
    # Core dependencies
    core_deps = [
        'sentence_transformers',
        'transformers',
        'torch',
        'torchgen',
        'huggingface_hub',
        'filelock',
        'tokenizers',
        'safetensors',
        'numpy',
        'scipy',
        'tqdm',
        'requests',
    ]
    
    # Optional but recommended
    optional_deps = [
        'Pillow',
        'scikit-learn',
    ]
    
    print("\n📦 Core Dependencies:")
    print("-" * 80)
    
    all_ok = True
    failed = []
    
    for dep in core_deps:
        ok, msg = check_import(dep)
        print(msg)
        if not ok:
            all_ok = False
            failed.append(dep)
    
    print("\n📦 Optional Dependencies:")
    print("-" * 80)
    
    for dep in optional_deps:
        ok, msg = check_import(dep)
        print(msg)
    
    # Test actual sentence_transformers import chain
    print("\n🧪 Testing sentence_transformers import chain:")
    print("-" * 80)
    
    test_imports = [
        'sentence_transformers',
        'sentence_transformers.backend',
        'sentence_transformers.models',
        'sentence_transformers.SentenceTransformer',
        'transformers.configuration_utils',
        'transformers.utils',
        'huggingface_hub.hf_api',
        'huggingface_hub.file_download',
    ]
    
    for imp in test_imports:
        ok, msg = check_import(imp)
        print(msg)
        if not ok:
            all_ok = False
            if imp.split('.')[0] not in failed:
                failed.append(imp.split('.')[0])
    
    # Test model loading
    print("\n🤖 Testing model loading:")
    print("-" * 80)
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ SentenceTransformer class imported")
        
        # Try to load a small model (won't download, just check if it can be initialized)
        try:
            model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
            print("✅ Model initialization successful")
            
            # Test encoding
            embedding = model.encode("test", convert_to_numpy=True)
            print(f"✅ Encoding test successful (dimension: {len(embedding)})")
            
        except Exception as e:
            print(f"⚠️  Model loading test: {str(e)}")
            
    except Exception as e:
        print(f"❌ SentenceTransformer import failed: {str(e)}")
        all_ok = False
    
    # Summary
    print("\n" + "=" * 80)
    if all_ok:
        print("✅ All core dependencies are available!")
        print("✅ Ready for packaging!")
        return 0
    else:
        print("❌ Missing dependencies detected!")
        print(f"❌ Failed modules: {', '.join(failed)}")
        print("\n💡 Add these to my_genie.spec:")
        for dep in failed:
            print(f"   {dep}_datas, {dep}_binaries, {dep}_hiddenimports = collect_all('{dep}')")
        return 1

if __name__ == "__main__":
    sys.exit(main())
