"""
Utility module for loading prompts from YAML files.
"""
import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PromptLoader:
    """Load and manage prompts from YAML configuration files."""
    
    def __init__(self, prompts_file: Optional[str] = None):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_file: Path to the prompts YAML file. If None, uses default location.
        """
        if prompts_file is None:
            # Default to prompts.yaml in the same directory as this file
            current_dir = Path(__file__).parent
            prompts_file = current_dir / "prompts.yaml"
        
        self.prompts_file = Path(prompts_file)
        self._prompts: Optional[Dict[str, Any]] = None
        self._load_prompts()
    
    def _load_prompts(self):
        """Load prompts from YAML file."""
        try:
            if not self.prompts_file.exists():
                logger.warning(f"Prompts file not found: {self.prompts_file}")
                self._prompts = {}
                return
            
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                self._prompts = yaml.safe_load(f) or {}
            
            logger.info(f"Loaded prompts from: {self.prompts_file}")
            
        except Exception as e:
            logger.error(f"Error loading prompts file: {e}")
            self._prompts = {}
    
    def get_prompt(
        self,
        category: str,
        prompt_name: str,
        **kwargs
    ) -> str:
        """
        Get a formatted prompt by category and name.
        
        Args:
            category: Category of the prompt (e.g., 'multihop')
            prompt_name: Name of the prompt (e.g., 'extract_entities_and_facts')
            **kwargs: Variables to format into the prompt template
            
        Returns:
            Formatted prompt string
        """
        if not self._prompts:
            logger.warning("Prompts not loaded, returning empty string")
            return ""
        
        try:
            prompt_config = self._prompts.get(category, {}).get(prompt_name)
            if not prompt_config:
                logger.warning(f"Prompt not found: {category}.{prompt_name}")
                return ""
            
            template = prompt_config.get("template", "")
            if not template:
                logger.warning(f"Template not found for: {category}.{prompt_name}")
                return ""
            
            # Format the template with provided kwargs
            formatted = template.format(**kwargs)
            return formatted
            
        except KeyError as e:
            logger.error(f"Missing key in prompt template: {e}")
            return ""
        except Exception as e:
            logger.error(f"Error formatting prompt: {e}")
            return ""
    
    def get_prompt_config(
        self,
        category: str,
        prompt_name: str
    ) -> Dict[str, Any]:
        """
        Get the full prompt configuration (template, temperature, model, etc.).
        
        Args:
            category: Category of the prompt
            prompt_name: Name of the prompt
            
        Returns:
            Dictionary with prompt configuration
        """
        if not self._prompts:
            return {}
        
        try:
            return self._prompts.get(category, {}).get(prompt_name, {})
        except Exception as e:
            logger.error(f"Error getting prompt config: {e}")
            return {}
    
    def reload(self):
        """Reload prompts from the YAML file."""
        self._load_prompts()


# Global prompt loader instance
_default_loader: Optional[PromptLoader] = None


def get_prompt_loader(prompts_file: Optional[str] = None) -> PromptLoader:
    """
    Get or create the default prompt loader instance.
    
    Args:
        prompts_file: Optional path to prompts file
        
    Returns:
        PromptLoader instance
    """
    global _default_loader
    if _default_loader is None or prompts_file is not None:
        _default_loader = PromptLoader(prompts_file)
    return _default_loader
