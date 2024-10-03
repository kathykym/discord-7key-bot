import sqlite3
from pathlib import Path
from contextlib import closing
import logging
import utils.config_reader as config


def get_bot_param(module: str, key: str) -> str:
    logger = logging.getLogger(__name__)

    try:
        with closing(sqlite3.connect(Path(config.get('BOT', 'bot_db_file')))) as dbconn:
            with closing(dbconn.cursor()) as cursor:
                row = cursor.execute(
                            "SELECT value FROM bot_param WHERE module = ? AND key = ?",
                            (module, key)
                        ).fetchone()
        
        return row[0] if row else ""
    
    except sqlite3.DatabaseError as e:
        logger.error(repr(e))
        raise
    except Exception as e:
        logger.error(repr(e))
        raise


def update_bot_param(module: str, key: str, value: str):
    logger = logging.getLogger(__name__)

    try:
        with closing(sqlite3.connect(Path(config.get('BOT', 'bot_db_file')))) as dbconn:
            with closing(dbconn.cursor()) as cursor:
                cursor.execute(
                    "UPDATE bot_param SET value = ? WHERE module = ? AND key = ?",
                    (value, module, key)
                )
            dbconn.commit()
            
    except sqlite3.DatabaseError as e:
        logger.error(repr(e))
        raise
    except Exception as e:
        logger.error(repr(e))
        raise