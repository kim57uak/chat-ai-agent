#!/usr/bin/env python3
"""
Deep dependency check - finds ALL missing dependencies recursively
"""

import sys
import importlib
import pkgutil
from typing import Set, List

def get_all_submodules(package_name: str) -> Set[str]:
    """Recursively get all submodules of a package"""
    modules = set()
    try:
        package = importlib.import_module(package_name)
        if hasattr(package, '__path__'):
            for importer, modname, ispkg in pkgutil.walk_packages(
                path=package.__path__,
                prefix=package.__name__ + '.',
                onerror=lambda x: None
            ):
                modules.add(modname)
    except Exception:
        pass
    return modules

def check_import_deep(module_name: str, checked: Set[str] = None) -> List[str]:
    """Deep check: try to import and find all missing dependencies"""
    if checked is None:
        checked = set()
    
    if module_name in checked:
        return []
    
    checked.add(module_name)
    missing = []
    
    try:
        mod = importlib.import_module(module_name)
        
        # Check all attributes
        if hasattr(mod, '__all__'):
            for attr in mod.__all__:
                try:
                    getattr(mod, attr)
                except ImportError as e:
                    missing_mod = str(e).split("'")[1] if "'" in str(e) else str(e)
                    if missing_mod not in missing:
                        missing.append(missing_mod)
                except Exception:
                    pass
                    
    except ImportError as e:
        missing_mod = str(e).split("'")[1] if "'" in str(e) else module_name
        if missing_mod not in missing:
            missing.append(missing_mod)
    except Exception:
        pass
    
    return missing

def main():
    print("=" * 80)
    print("🔬 DEEP Dependency Check for sentence_transformers")
    print("=" * 80)
    
    # Core packages to check
    packages = [
        'sentence_transformers',
        'transformers',
        'torch',
        'huggingface_hub',
    ]
    
    all_missing = set()
    
    for pkg in packages:
        print(f"\n📦 Checking {pkg}...")
        print("-" * 80)
        
        # Try basic import
        try:
            importlib.import_module(pkg)
            print(f"✅ {pkg} imports successfully")
        except ImportError as e:
            print(f"❌ {pkg} import failed: {e}")
            continue
        
        # Deep check
        missing = check_import_deep(pkg)
        if missing:
            print(f"⚠️  Found missing dependencies:")
            for m in missing:
                print(f"   - {m}")
                all_missing.add(m)
        else:
            print(f"✅ No missing dependencies detected")
    
    # Test actual usage
    print("\n" + "=" * 80)
    print("🧪 Testing actual sentence_transformers usage...")
    print("=" * 80)
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ SentenceTransformer imported")
        
        # Try to create model instance
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
        print("✅ Model instance created")
        
        # Try encoding
        embedding = model.encode("test", convert_to_numpy=True)
        print(f"✅ Encoding works (dimension: {len(embedding)})")
        
    except ImportError as e:
        missing_mod = str(e).split("'")[1] if "'" in str(e) else str(e)
        print(f"❌ Import error: {e}")
        all_missing.add(missing_mod)
    except Exception as e:
        print(f"❌ Runtime error: {e}")
        # Try to extract module name from error
        error_str = str(e)
        if "No module named" in error_str:
            missing_mod = error_str.split("'")[1] if "'" in error_str else None
            if missing_mod:
                all_missing.add(missing_mod)
    
    # Filter out optional/non-critical dependencies
    optional_modules = {
        'SmolVLMProcessor',  # Vision model (optional)
        'models.smolvlm.processing_smolvlm',  # Vision model (optional)
    }
    
    critical_missing = all_missing - optional_modules
    
    # Summary
    print("\n" + "=" * 80)
    if critical_missing:
        print("❌ CRITICAL DEPENDENCIES MISSING!")
        print("=" * 80)
        print("\n📋 Add these to my_genie.spec:\n")
        for dep in sorted(critical_missing):
            safe_name = dep.replace('.', '_').replace('-', '_')
            print(f"{safe_name}_datas, {safe_name}_binaries, {safe_name}_hiddenimports = collect_all('{dep}')")
        return 1
    else:
        print("✅ ALL CRITICAL DEPENDENCIES OK!")
        if all_missing:
            print("\n⚠️  Optional dependencies missing (safe to ignore):")
            for dep in sorted(all_missing):
                print(f"   - {dep}")
        print("=" * 80)
        print("\n🚀 Ready to build!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
