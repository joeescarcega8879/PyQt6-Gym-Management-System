"""
Configuration package.
Re-exports Config and config from settings module.
"""
from src.config.settings import Config, config

__all__ = ['Config', 'config']
