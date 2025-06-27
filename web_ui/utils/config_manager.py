"""
Configuration Management Utilities for Grid Trading Bot Web UI

Handles configuration export, import, and file management.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import base64

logger = logging.getLogger(__name__)


class UIConfigManager:
    """Manages configuration files for the Web UI."""
    
    def __init__(self):
        """Initialize the config manager."""
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        
        # Templates directory
        self.templates_dir = self.config_dir / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
        # User configs directory
        self.user_configs_dir = self.config_dir / "user_configs"
        self.user_configs_dir.mkdir(exist_ok=True)
    
    def save_config(self, config: Dict[str, Any], filename: Optional[str] = None) -> Tuple[bool, str]:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary
            filename: Optional filename, auto-generated if not provided
            
        Returns:
            Tuple of (success, message/filepath)
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"grid_config_{timestamp}.json"
            
            # Ensure .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            filepath = self.user_configs_dir / filename
            
            # Add metadata
            config_with_metadata = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "created_by": "Grid Trading Bot Web UI",
                    "version": "1.0",
                    "description": f"Grid trading configuration saved on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                },
                "config": config
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config_with_metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {filepath}")
            return True, str(filepath)
            
        except Exception as e:
            error_msg = f"Failed to save configuration: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def load_config(self, filepath: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Load configuration from file.
        
        Args:
            filepath: Path to configuration file
            
        Returns:
            Tuple of (success, config_dict, message)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both old format (direct config) and new format (with metadata)
            if "config" in data and "metadata" in data:
                config = data["config"]
                metadata = data["metadata"]
                message = f"Loaded configuration created on {metadata.get('created_at', 'unknown date')}"
            else:
                config = data
                message = "Loaded configuration (legacy format)"
            
            logger.info(f"Configuration loaded from {filepath}")
            return True, config, message
            
        except FileNotFoundError:
            error_msg = f"Configuration file not found: {filepath}"
            logger.error(error_msg)
            return False, {}, error_msg
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in configuration file: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
        except Exception as e:
            error_msg = f"Failed to load configuration: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
    
    def export_config_for_download(self, config: Dict[str, Any], filename: str = None) -> Tuple[bool, str, str]:
        """
        Export configuration for browser download.
        
        Args:
            config: Configuration dictionary
            filename: Optional filename
            
        Returns:
            Tuple of (success, base64_data, filename)
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"grid_config_{timestamp}.json"
            
            # Ensure .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            # Add metadata
            config_with_metadata = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "created_by": "Grid Trading Bot Web UI",
                    "version": "1.0",
                    "description": f"Grid trading configuration exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "export_type": "browser_download"
                },
                "config": config
            }
            
            # Convert to JSON string
            json_str = json.dumps(config_with_metadata, indent=2, ensure_ascii=False)
            
            # Encode to base64 for download
            base64_data = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            
            logger.info(f"Configuration prepared for download as {filename}")
            return True, base64_data, filename
            
        except Exception as e:
            error_msg = f"Failed to export configuration: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
    
    def import_config_from_upload(self, file_content: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Import configuration from uploaded file content.
        
        Args:
            file_content: JSON string content of uploaded file
            
        Returns:
            Tuple of (success, config_dict, message)
        """
        try:
            data = json.loads(file_content)
            
            # Handle both old format (direct config) and new format (with metadata)
            if "config" in data and "metadata" in data:
                config = data["config"]
                metadata = data["metadata"]
                message = f"Imported configuration created on {metadata.get('created_at', 'unknown date')}"
            else:
                config = data
                message = "Imported configuration (legacy format)"
            
            # Basic validation
            required_sections = ["exchange", "pair", "trading_settings", "grid_strategy"]
            missing_sections = [section for section in required_sections if section not in config]
            
            if missing_sections:
                error_msg = f"Configuration missing required sections: {', '.join(missing_sections)}"
                return False, {}, error_msg
            
            logger.info("Configuration imported successfully")
            return True, config, message
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
        except Exception as e:
            error_msg = f"Failed to import configuration: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
    
    def list_saved_configs(self) -> List[Dict[str, Any]]:
        """
        List all saved configuration files.
        
        Returns:
            List of config file information
        """
        try:
            configs = []
            
            for filepath in self.user_configs_dir.glob("*.json"):
                try:
                    stat = filepath.stat()
                    
                    # Try to read metadata
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if "metadata" in data:
                        metadata = data["metadata"]
                        description = metadata.get("description", "No description")
                        created_at = metadata.get("created_at", "Unknown")
                    else:
                        description = "Legacy configuration file"
                        created_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    
                    configs.append({
                        "filename": filepath.name,
                        "filepath": str(filepath),
                        "size": stat.st_size,
                        "created_at": created_at,
                        "description": description,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                    
                except Exception as e:
                    logger.warning(f"Error reading config file {filepath}: {e}")
                    continue
            
            # Sort by creation date (newest first)
            configs.sort(key=lambda x: x["created_at"], reverse=True)
            return configs
            
        except Exception as e:
            logger.error(f"Failed to list configurations: {e}")
            return []
    
    def delete_config(self, filename: str) -> Tuple[bool, str]:
        """
        Delete a saved configuration file.
        
        Args:
            filename: Name of file to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            filepath = self.user_configs_dir / filename
            
            if not filepath.exists():
                return False, f"Configuration file not found: {filename}"
            
            filepath.unlink()
            logger.info(f"Deleted configuration file: {filename}")
            return True, f"Configuration '{filename}' deleted successfully"
            
        except Exception as e:
            error_msg = f"Failed to delete configuration: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def create_template_configs(self):
        """Create template configuration files for common strategies."""
        templates = {
            "conservative_grid.json": {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "created_by": "Grid Trading Bot Web UI",
                    "version": "1.0",
                    "description": "Conservative grid strategy with tight range and many grids"
                },
                "config": {
                    "exchange": {"name": "coinbase", "trading_fee": 0.005, "trading_mode": "paper_trading"},
                    "pair": {"base_currency": "BTC", "quote_currency": "USDT"},
                    "trading_settings": {"timeframe": "1h", "initial_balance": 10000},
                    "grid_strategy": {"type": "simple_grid", "spacing": "arithmetic", "num_grids": 20, "range": {"top": 105000, "bottom": 95000}},
                    "risk_management": {"take_profit": {"enabled": True, "threshold": 110000}, "stop_loss": {"enabled": True, "threshold": 90000}}
                }
            },
            "aggressive_grid.json": {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "created_by": "Grid Trading Bot Web UI",
                    "version": "1.0",
                    "description": "Aggressive grid strategy with wide range and fewer grids"
                },
                "config": {
                    "exchange": {"name": "coinbase", "trading_fee": 0.005, "trading_mode": "paper_trading"},
                    "pair": {"base_currency": "BTC", "quote_currency": "USDT"},
                    "trading_settings": {"timeframe": "6h", "initial_balance": 25000},
                    "grid_strategy": {"type": "simple_grid", "spacing": "geometric", "num_grids": 8, "range": {"top": 120000, "bottom": 80000}},
                    "risk_management": {"take_profit": {"enabled": False, "threshold": 0}, "stop_loss": {"enabled": False, "threshold": 0}}
                }
            }
        }
        
        for filename, template in templates.items():
            filepath = self.templates_dir / filename
            if not filepath.exists():
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(template, f, indent=2, ensure_ascii=False)
                    logger.info(f"Created template: {filename}")
                except Exception as e:
                    logger.error(f"Failed to create template {filename}: {e}")


# Global instance
ui_config_manager = UIConfigManager()
