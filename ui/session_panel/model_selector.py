"""
Model Selector
모델 선택 전담 클래스 - SRP (Single Responsibility Principle)
"""

from PyQt6.QtWidgets import QMenu
from PyQt6.QtCore import QPoint
from core.file_utils import load_config, save_last_model, load_last_model
from core.logging import get_logger

logger = get_logger("model_selector")


class ModelSelector:
    """모델 선택 전담 클래스"""

    def __init__(self, parent):
        self.parent = parent

    def show(self, button):
        """모델 선택 메뉴 표시"""
        try:
            config = load_config()
            models = config.get("models", {})
            if not models:
                return

            menu = self._create_menu()
            current_model = load_last_model()
            categorized = self._categorize_models(models)

            self._populate_menu(menu, categorized, current_model)
            self._show_menu(menu, button)

        except Exception as e:
            logger.debug(f"모델 선택기 표시 오류: {e}")

    def _create_menu(self):
        """메뉴 생성"""
        menu = QMenu(self.parent)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: rgb(163,135,215);
            }
        """)
        return menu

    def _categorize_models(self, models):
        """모델 카테고리 분류"""
        categories = {
            "openrouter": {},
            "google": {},
            "perplexity": {},
            "pollinations": {},
            "other": {},
        }

        for model_name, model_config in models.items():
            api_key = model_config.get("api_key", "")
            if not (api_key and api_key != "none"):
                continue

            provider = model_config.get("provider", "")
            if provider in categories:
                categories[provider][model_name] = model_config
            else:
                categories["other"][model_name] = model_config

        return categories

    def _populate_menu(self, menu, categorized, current_model):
        """메뉴 채우기"""
        category_info = {
            "openrouter": {"emoji": "🔀", "name": "OpenRouter"},
            "google": {"emoji": "🔍", "name": "Google Gemini"},
            "perplexity": {"emoji": "🔬", "name": "Perplexity"},
            "pollinations": {"emoji": "🌸", "name": "Pollinations"},
            "other": {"emoji": "🤖", "name": "기타 모델"},
        }

        for category, models in categorized.items():
            if not models:
                continue

            info = category_info[category]
            submenu = menu.addMenu(f"{info['emoji']} {info['name']} ({len(models)}개)")
            submenu.setStyleSheet(menu.styleSheet())

            for model_name, model_config in sorted(models.items()):
                display_name = self._get_display_name(model_name, model_config)
                action = submenu.addAction(f"🤖 {display_name}")
                
                if model_name == current_model:
                    action.setText(f"✅ {display_name} (현재)")

                action.triggered.connect(lambda checked, m=model_name: self._select_model(m))

    def _get_display_name(self, model_name, model_config):
        """모델 표시명 생성"""
        description = model_config.get("description", "")
        if description:
            clean_desc = description.split(" - ")[-1] if " - " in description else description
            return f"{model_name.split('/')[-1]} - {clean_desc[:30]}..."
        return model_name

    def _select_model(self, model_name):
        """모델 선택"""
        try:
            save_last_model(model_name)
            display_name = model_name[:12] + "..." if len(model_name) > 15 else model_name
            
            if hasattr(self.parent, 'model_button'):
                self.parent.model_button.setText(f"🤖 {display_name}")
                self.parent.model_button.setToolTip(f"현재 모델: {model_name}")
            
            logger.debug(f"모델 선택됨: {model_name}")
        except Exception as e:
            logger.debug(f"모델 선택 오류: {e}")

    def _show_menu(self, menu, button):
        """메뉴 표시"""
        button_pos = button.mapToGlobal(QPoint(0, 0))
        menu.exec(QPoint(button_pos.x(), button_pos.y() + button.height()))
