"""
Dynamic Import Resolver for PyInstaller compatibility.
Centralizes all dynamic imports to avoid runtime import failures.
"""

import sys
import importlib
from typing import Dict, Any, Optional, Callable
from core.logging import get_logger

logger = get_logger(__name__)

class DynamicImportResolver:
    """Centralized dynamic import resolver for PyInstaller compatibility."""
    
    def __init__(self):
        self._cached_modules: Dict[str, Any] = {}
        self._import_strategies: Dict[str, Callable] = {}
        self._register_strategies()
    
    def _register_strategies(self):
        """Register import strategies for different module types."""
        self._import_strategies.update({
            'langchain': self._import_langchain,
            'transformers': self._import_transformers,
            'sentence_transformers': self._import_sentence_transformers,
            'huggingface_hub': self._import_huggingface_hub,
            'torch': self._import_torch,
            'pygments': self._import_pygments,
            'pandas': self._import_pandas,
            'numpy': self._import_numpy,
            'matplotlib': self._import_matplotlib,
        })
    
    def get_module(self, module_name: str, fallback: Optional[Any] = None) -> Optional[Any]:
        """Get module with caching and fallback support."""
        if module_name in self._cached_modules:
            return self._cached_modules[module_name]
        
        try:
            # Try direct import first
            module = importlib.import_module(module_name)
            self._cached_modules[module_name] = module
            return module
        except ImportError as e:
            logger.warning(f"Direct import failed for {module_name}: {e}")
            
            # Try strategy-based import
            for strategy_key, strategy_func in self._import_strategies.items():
                if strategy_key in module_name:
                    try:
                        module = strategy_func(module_name)
                        if module:
                            self._cached_modules[module_name] = module
                            return module
                    except Exception as strategy_error:
                        logger.warning(f"Strategy {strategy_key} failed for {module_name}: {strategy_error}")
            
            logger.error(f"All import strategies failed for {module_name}")
            return fallback
    
    def _import_langchain(self, module_name: str) -> Optional[Any]:
        """Import LangChain modules with fallback."""
        try:
            if 'langchain_core' in module_name:
                import langchain_core
                return self._get_nested_attr(langchain_core, module_name.replace('langchain_core.', ''))
            elif 'langchain_community' in module_name:
                import langchain_community
                return self._get_nested_attr(langchain_community, module_name.replace('langchain_community.', ''))
            elif 'langchain' in module_name:
                import langchain
                return self._get_nested_attr(langchain, module_name.replace('langchain.', ''))
        except ImportError:
            pass
        return None
    
    def _import_transformers(self, module_name: str) -> Optional[Any]:
        """Import transformers modules with fallback."""
        try:
            import transformers
            if module_name == 'transformers':
                return transformers
            return self._get_nested_attr(transformers, module_name.replace('transformers.', ''))
        except ImportError:
            pass
        return None
    
    def _import_sentence_transformers(self, module_name: str) -> Optional[Any]:
        """Import sentence_transformers modules with fallback."""
        try:
            # Pre-import ALL transformers dependencies
            import torch
            import torch.nn
            import transformers
            import transformers.generation
            import transformers.generation.utils
            import transformers.modeling_utils
            import transformers.models.auto.modeling_auto
            import transformers.models.auto.tokenization_auto
            import transformers.models.auto.configuration_auto
            
            import sentence_transformers
            if module_name == 'sentence_transformers':
                return sentence_transformers
            return self._get_nested_attr(sentence_transformers, module_name.replace('sentence_transformers.', ''))
        except ImportError as e:
            logger.error(f"sentence_transformers import failed: {e}")
        return None
    
    def _import_huggingface_hub(self, module_name: str) -> Optional[Any]:
        """Import huggingface_hub modules with fallback."""
        try:
            import huggingface_hub
            if module_name == 'huggingface_hub':
                return huggingface_hub
            return self._get_nested_attr(huggingface_hub, module_name.replace('huggingface_hub.', ''))
        except ImportError:
            pass
        return None
    
    def _import_torch(self, module_name: str) -> Optional[Any]:
        """Import torch modules with fallback."""
        try:
            import torch
            if module_name == 'torch':
                return torch
            return self._get_nested_attr(torch, module_name.replace('torch.', ''))
        except ImportError:
            pass
        return None
    
    def _import_pygments(self, module_name: str) -> Optional[Any]:
        """Import pygments modules with fallback."""
        try:
            import pygments
            if module_name == 'pygments':
                return pygments
            return self._get_nested_attr(pygments, module_name.replace('pygments.', ''))
        except ImportError:
            pass
        return None
    
    def _import_pandas(self, module_name: str) -> Optional[Any]:
        """Import pandas modules with fallback."""
        try:
            import pandas
            if module_name == 'pandas':
                return pandas
            return self._get_nested_attr(pandas, module_name.replace('pandas.', ''))
        except ImportError:
            pass
        return None
    
    def _import_numpy(self, module_name: str) -> Optional[Any]:
        """Import numpy modules with fallback."""
        try:
            import numpy
            if module_name == 'numpy':
                return numpy
            return self._get_nested_attr(numpy, module_name.replace('numpy.', ''))
        except ImportError:
            pass
        return None
    
    def _import_matplotlib(self, module_name: str) -> Optional[Any]:
        """Import matplotlib modules with fallback."""
        try:
            import matplotlib
            if module_name == 'matplotlib':
                return matplotlib
            return self._get_nested_attr(matplotlib, module_name.replace('matplotlib.', ''))
        except ImportError:
            pass
        return None
    
    def _get_nested_attr(self, obj: Any, attr_path: str) -> Optional[Any]:
        """Get nested attribute from object."""
        try:
            for attr in attr_path.split('.'):
                obj = getattr(obj, attr)
            return obj
        except AttributeError:
            return None
    
    def safe_import(self, module_name: str, attr_name: Optional[str] = None, fallback: Optional[Any] = None) -> Optional[Any]:
        """Safe import with attribute access and fallback."""
        module = self.get_module(module_name, fallback)
        if module is None:
            return fallback
        
        if attr_name:
            try:
                return getattr(module, attr_name)
            except AttributeError:
                logger.warning(f"Attribute {attr_name} not found in {module_name}")
                return fallback
        
        return module

# Global instance
dynamic_import_resolver = DynamicImportResolver()