import os
from pathlib import Path
from dotenv import load_dotenv
import yaml
import logging


def get(section: str, key: str):
    logger = logging.getLogger(__name__)

    try:
        if section == 'ENV':
            # load config in .env
            dotenv_path = Path("config/.env")
            load_dotenv(dotenv_path=dotenv_path)
            value = os.getenv(key.upper())
        else:
            # load config in config.yaml
            with open(Path("config/config.yaml"), 'r', encoding='utf8') as file:
                config = yaml.safe_load(file)
                value = config[section][key]
                
        return value
    
    except yaml.YAMLError as e:
        logger.error(repr(e))
        raise
    except Exception as e:
        logger.error(repr(e))
        raise