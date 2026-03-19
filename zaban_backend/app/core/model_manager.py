import gc
import time
import asyncio
import torch
from typing import Dict, Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages AI models to support lazy loading and idle-based unloading.
    Tracks the last time a model was used and unloads it after a TTL.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance.models = {}  # service_name -> {unload_fn, last_used}
            cls._instance.lock = asyncio.Lock()
        return cls._instance

    def register_service(self, name: str, unload_fn: Callable):
        """Register a service's unload function."""
        self.models[name] = {
            "unload_fn": unload_fn,
            "last_used": time.time(),
            "is_loaded": False
        }
        logger.info(f"Registered service for lazy management: {name}")

    def touch(self, name: str):
        """Update the last used timestamp for a service."""
        if name in self.models:
            self.models[name]["last_used"] = time.time()
            self.models[name]["is_loaded"] = True

    def mark_unloaded(self, name: str):
        """Mark a service as explicitly unloaded."""
        if name in self.models:
            self.models[name]["is_loaded"] = False

    async def unload_model(self, name: str):
        """Explicitly unload a specific model."""
        if name in self.models and self.models[name]["is_loaded"]:
            logger.info(f"Unloading model: {name}")
            unload_fn = self.models[name]["unload_fn"]
            if asyncio.iscoroutinefunction(unload_fn):
                await unload_fn()
            else:
                unload_fn()
            self.models[name]["is_loaded"] = False
            self.clear_vram()

    def clear_vram(self):
        """Force Python GC and Torch to release GPU memory."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("GPU VRAM Cache cleared.")

    async def cleanup_loop(self, ttl_seconds: int = 300):
        """Background loop to unload models that have been idle for longer than TTL."""
        logger.info(f"Starting model cleanup background task (TTL: {ttl_seconds}s)")
        while True:
            await asyncio.sleep(60)  # Check every minute
            current_time = time.time()
            
            for name, info in self.models.items():
                if info["is_loaded"] and (current_time - info["last_used"] > ttl_seconds):
                    logger.info(f"Model '{name}' was idle for >{ttl_seconds}s. Auto-unloading.")
                    try:
                        await self.unload_model(name)
                    except Exception as e:
                        logger.error(f"Failed to auto-unload {name}: {e}")

# Global singleton instance
model_manager = ModelManager()
