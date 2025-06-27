"""
Unified Configuration Service for Grid Trading Bot

This service consolidates the dual configuration management systems into a single,
consistent interface that can be used by both the backend and web UI components.
"""

import json
import logging
import os
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from abc import ABC, abstractmethod

from .config_validator import ConfigValidator
from .exceptions import ConfigFileNotFoundError, ConfigParseError, ConfigValidationError
from .trading_mode import TradingMode
from strategies.strategy_type import StrategyType
from core.error_handling import (
    ErrorContext, ErrorCategory, ErrorSeverity,
    ConfigurationError, error_handler
)


class ConfigurationAdapter(ABC):
    """Abstract adapter for different configuration sources and formats."""
    
    @abstractmethod
    def load_config(self, source: str) -> Dict[str, Any]:
        """Load configuration from a source."""
        pass
    
    @abstractmethod
    def save_config(self, config: Dict[str, Any], destination: str) -> bool:
        """Save configuration to a destination."""
        pass


class FileConfigurationAdapter(ConfigurationAdapter):
    """Adapter for file-based configuration management."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load_config(self, source: str) -> Dict[str, Any]:
        """Load configuration from a JSON file."""
        if not os.path.exists(source):
            raise ConfigFileNotFoundError(source)
        
        try:
            with open(source, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both old format (direct config) and new format (with metadata)
            if "config" in data and "metadata" in data:
                return data["config"]
            else:
                return data
                
        except json.JSONDecodeError as e:
            raise ConfigParseError(source, e)
    
    def save_config(self, config: Dict[str, Any], destination: str) -> bool:
        """Save configuration to a JSON file with metadata."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            # Add metadata wrapper
            config_with_metadata = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "created_by": "Grid Trading Bot Unified Config Service",
                    "version": "2.0",
                    "description": f"Grid trading configuration saved on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                },
                "config": config
            }
            
            with open(destination, 'w', encoding='utf-8') as f:
                json.dump(config_with_metadata, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration to {destination}: {e}")
            return False


class UnifiedConfigurationService:
    """
    Unified configuration service that consolidates backend and UI configuration management.
    
    This service provides a single interface for configuration operations while maintaining
    compatibility with existing code through adapters.
    """
    
    def __init__(self, validator: Optional[ConfigValidator] = None):
        """
        Initialize the unified configuration service.
        
        Args:
            validator: Optional ConfigValidator instance. If None, creates a new one.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.validator = validator or ConfigValidator()
        self.file_adapter = FileConfigurationAdapter()
        
        # Configuration directories
        self.config_dir = Path("config")
        self.templates_dir = self.config_dir / "templates"
        self.user_configs_dir = self.config_dir / "user_configs"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        self.config_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        self.user_configs_dir.mkdir(exist_ok=True)
    
    def load_configuration(self, config_path: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Load configuration from file with validation.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Tuple of (success, config_dict, message)
        """
        try:
            config = self.file_adapter.load_config(config_path)
            
            # Validate the configuration
            self.validator.validate(config)
            
            message = f"Configuration loaded and validated successfully from {config_path}"
            self.logger.info(message)
            return True, config, message
            
        except (ConfigFileNotFoundError, ConfigParseError, ConfigValidationError) as e:
            error_msg = f"Failed to load configuration: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
        except Exception as e:
            error_msg = f"Unexpected error loading configuration: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, {}, error_msg
    
    def save_configuration(self, config: Dict[str, Any], filename: Optional[str] = None) -> Tuple[bool, str]:
        """
        Save configuration to file with validation.
        
        Args:
            config: Configuration dictionary to save
            filename: Optional filename. Auto-generated if not provided.
            
        Returns:
            Tuple of (success, filepath_or_error_message)
        """
        try:
            # Validate configuration before saving
            self.validator.validate(config)
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"grid_config_{timestamp}.json"
            
            # Ensure .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            filepath = self.user_configs_dir / filename
            
            # Save configuration
            if self.file_adapter.save_config(config, str(filepath)):
                message = f"Configuration saved successfully to {filepath}"
                self.logger.info(message)
                return True, str(filepath)
            else:
                error_msg = f"Failed to save configuration to {filepath}"
                return False, error_msg
                
        except ConfigValidationError as e:
            error_msg = f"Configuration validation failed: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error saving configuration: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def export_configuration(self, config: Dict[str, Any], filename: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Export configuration for download (base64 encoded).
        
        Args:
            config: Configuration dictionary to export
            filename: Optional filename for the export
            
        Returns:
            Tuple of (success, base64_data_or_error, filename_or_error_message)
        """
        try:
            # Validate configuration
            self.validator.validate(config)
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"grid_config_export_{timestamp}.json"
            
            # Ensure .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            # Create export data with metadata
            export_data = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "exported_by": "Grid Trading Bot Unified Config Service",
                    "version": "2.0",
                    "description": f"Exported grid trading configuration on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                },
                "config": config
            }
            
            # Convert to JSON string and encode to base64
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            base64_data = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            
            self.logger.info(f"Configuration exported successfully as {filename}")
            return True, base64_data, filename
            
        except ConfigValidationError as e:
            error_msg = f"Configuration validation failed: {str(e)}"
            self.logger.error(error_msg)
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Failed to export configuration: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, "", error_msg
    
    def import_configuration(self, file_content: str) -> Tuple[bool, Dict[str, Any], str]:
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
            
            # Validate the imported configuration
            self.validator.validate(config)
            
            self.logger.info(f"Configuration imported successfully: {message}")
            return True, config, message
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
        except ConfigValidationError as e:
            error_msg = f"Configuration validation failed: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
        except Exception as e:
            error_msg = f"Failed to import configuration: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, {}, error_msg
    
    def list_user_configurations(self) -> List[Dict[str, Any]]:
        """
        List all user configuration files with metadata.
        
        Returns:
            List of configuration file information dictionaries
        """
        configs = []
        
        try:
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
                    self.logger.warning(f"Error reading config file {filepath}: {e}")
                    continue
            
            # Sort by creation date (newest first)
            configs.sort(key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error listing user configurations: {e}")
        
        return configs


# Global instance for easy access
unified_config_service = UnifiedConfigurationService()
