import json
import os
from typing import Dict, List, Optional
from presets.defaults import PRESETS


class PresetManager:
    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = config_path
        self._presets: Dict = {}
        self._custom_presets: Dict = {}
        self._active_preset: str = "streaming"
        
        self.load_defaults()
        self._load_custom_presets()
    
    def load_defaults(self) -> None:
        self._presets = PRESETS.copy()
    
    def _load_custom_presets(self) -> None:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    if 'presets' in config and isinstance(config['presets'], dict):
                        self._custom_presets = config['presets']
                    if 'active_preset' in config:
                        self._active_preset = config['active_preset']
            except (json.JSONDecodeError, IOError):
                self._custom_presets = {}
    
    def _save_config(self) -> None:
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {"presets": {}, "active_preset": "streaming"}
        except (json.JSONDecodeError, IOError):
            config = {"presets": {}, "active_preset": "streaming"}
        
        config['presets'] = self._custom_presets
        config['active_preset'] = self._active_preset
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def save_preset(self, name: str, params: dict) -> bool:
        if name in PRESETS:
            return False
        
        self._custom_presets[name] = params
        self._save_config()
        return True
    
    def load_preset(self, name: str) -> Optional[dict]:
        if name in PRESETS:
            return self._presets[name].copy()
        elif name in self._custom_presets:
            return self._custom_presets[name].copy()
        return None
    
    def delete_preset(self, name: str) -> bool:
        if name in PRESETS:
            return False
        
        if name in self._custom_presets:
            del self._custom_presets[name]
            self._save_config()
            return True
        
        return False
    
    def list_presets(self) -> List[Dict]:
        result = []
        
        for name in PRESETS:
            result.append({
                'name': name,
                'display_name': self._presets[name].get('name', name),
                'description': self._presets[name].get('description', ''),
                'is_builtin': True,
                'is_custom': False
            })
        
        for name in self._custom_presets:
            display_name = name.replace('_', ' ').title()
            result.append({
                'name': name,
                'display_name': display_name,
                'description': 'Custom preset',
                'is_builtin': False,
                'is_custom': True
            })
        
        return result
    
    def set_active_preset(self, name: str) -> bool:
        if name in PRESETS or name in self._custom_presets:
            self._active_preset = name
            self._save_config()
            return True
        return False
    
    def get_active_preset(self) -> str:
        return self._active_preset
    
    def get_preset_names(self) -> List[str]:
        names = list(PRESETS.keys())
        names.extend(list(self._custom_presets.keys()))
        return names
