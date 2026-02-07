#!/usr/bin/env python3
"""
Clean everything and start fresh
"""
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_all():
    """Clean everything"""
    # Clean vector store
    store_path = Path("vector_store")
    if store_path.exists():
        for item in store_path.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                    logger.info(f"🗑️ Deleted: {item.name}")
            except:
                pass
        logger.info("✅ Vector store cleaned")
    
    # Clean backups
    for ext in ['.backup', '.bak', '.old', '.tmp']:
        for backup in Path(".").glob(f"*{ext}"):
            try:
                backup.unlink()
                logger.info(f"🗑️ Deleted backup: {backup.name}")
            except:
                pass
    
    # Clean __pycache__
    for pycache in Path(".").rglob("__pycache__"):
        try:
            shutil.rmtree(pycache)
            logger.info(f"🗑️ Deleted: {pycache}")
        except:
            pass
    
    logger.info("✨ Everything cleaned and ready for fresh start!")

if __name__ == "__main__":
    clean_all()
