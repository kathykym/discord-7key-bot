import sqlite3
from pathlib import Path
from contextlib import closing
import logging
from commands.iidxme.classes.Song import Song
from commands.iidxme.classes.Chart import Chart
import utils.config_reader as config
import utils.string_util as string_util


def get_kanji_by_char(char: str) -> str:
    logger = logging.getLogger(__name__)

    try:
        with closing(sqlite3.connect(Path(config.get('BOT', 'iidxme_db_file')))) as dbconn:
            with closing(dbconn.cursor()) as cursor:
                row = cursor.execute(
                            "SELECT jp FROM mapping_kanji WHERE zh_hk = ? ",
                            (char, )
                        ).fetchone()
        
        return row[0] if row else ""
    
    except sqlite3.DatabaseError as e:
        logger.error(repr(e))
        raise
    except Exception as e:
        logger.error(repr(e))
        raise


def get_num_of_matched_songs(mode: str, difficulty: str, level: str, keywords: str) -> int:
    logger = logging.getLogger(__name__)

    try:
        pstmt_dict = _get_chart_conditions_pstmt(mode, difficulty, level, keywords)

        with closing(sqlite3.connect(Path(config.get('BOT', 'iidxme_db_file')))) as dbconn:
            with closing(dbconn.cursor()) as cursor:
                # count and return the number of matched songs in DB
                rows = cursor.execute(
                            " SELECT DISTINCT s.song_id " +
                            " FROM iidxme_song s, iidxme_chart c " +
                            f"WHERE s.song_id = c.song_id AND {pstmt_dict['conditions']} ",
                            pstmt_dict['values']
                        ).fetchall()
        
        return len(rows)
    
    except sqlite3.DatabaseError as e:
        logger.error(repr(e))
        raise Exception(config.get('IIDXME_PB', 'msg_db_error'))
    except Exception as e:
        logger.error(repr(e))
        raise Exception(config.get('COMMAND_ERROR', 'msg_generic_error'))


def fetch_charts(mode: str, difficulty: str, level: str, keywords: str, result_limit: int) -> list[Song]:
    logger = logging.getLogger(__name__)

    rows = []

    try:
        pstmt_dict = _get_chart_conditions_pstmt(mode, difficulty, level, keywords)

        with closing(sqlite3.connect(Path(config.get('BOT', 'iidxme_db_file')))) as dbconn:
            with closing(dbconn.cursor()) as cursor:
                # limit the result set to the number of songs specified in config file
                # sort the result by (1) length of song title, (2) song title (3) chart difficulty 
                '''
                sample:
                    SELECT s.song_id, s.title, c.chart_id, c.mode, c.difficulty, c.level, c.notes
                    FROM iidxme_song s, iidxme_chart c,
                    (
                        SELECT DISTINCT s.song_id
                        FROM iidxme_song s, iidxme_chart c
                        WHERE s.song_id = c.song_id AND mode = 'SP'
                        ORDER BY LENGTH(s.title)
                        LIMIT 5
                    ) resid
                    WHERE s.song_id = c.song_id AND s.song_id = resid.song_id AND mode = 'SP'
                    ORDER BY LENGTH(s.title), s.title, CASE c.difficulty WHEN 'B' THEN 0 WHEN 'N' THEN 1 WHEN 'H' THEN 2 WHEN 'A' THEN 3 WHEN 'L' THEN 4 END;
                '''
                rows = cursor.execute(
                            " SELECT s.song_id, s.title, c.chart_id, c.mode, c.difficulty, c.level, c.notes " +
                            " FROM iidxme_song s, iidxme_chart c, " +
                            " ( " +
                                " SELECT DISTINCT s.song_id " +
                                " FROM iidxme_song s, iidxme_chart c " +
                                f"WHERE s.song_id = c.song_id AND {pstmt_dict['conditions']} " +
                                " ORDER BY LENGTH(s.title) " +
                                f"LIMIT {result_limit} " +
                            " ) resid " +
                            f"WHERE s.song_id = c.song_id AND s.song_id = resid.song_id AND {pstmt_dict['conditions']} " + 
                            " ORDER BY LENGTH(s.title), s.title, CASE c.difficulty WHEN 'B' THEN 0 WHEN 'N' THEN 1 WHEN 'H' THEN 2 WHEN 'A' THEN 3 WHEN 'L' THEN 4 END ",
                            pstmt_dict['values'] + pstmt_dict['values']
                        ).fetchall()
                
        return _build_song_chart_list(rows)
    
    except sqlite3.DatabaseError as e:
        logger.error(repr(e))
        raise Exception(config.get('IIDXME_PB', 'msg_db_error'))
    except Exception as e:
        logger.error(repr(e))
        raise Exception(config.get('COMMAND_ERROR', 'msg_generic_error'))


def _get_chart_conditions_pstmt(mode: str, difficulty: str, level: str, keywords: str) -> dict:
    # mode
    pstmt_conditions = " mode = ? "
    pstmt_values = [mode]

    # difficulty
    if difficulty != "ALL":
        pstmt_conditions += " AND difficulty = ? "
        pstmt_values.append(difficulty)

    # level
    if level != "ALL":
        pstmt_conditions += " AND level = ? "
        pstmt_values.append(level)

    # song keywords
    pstmt_conditions += " AND ( "
    pstmt_conditions += "  title || ' ' || IFNULL(title_alias, '') LIKE ? "
    pstmt_conditions += "  OR title || ' ' || IFNULL(title_alias, '') LIKE ? "
    pstmt_conditions += "  OR lower(title_romaji) = ? OR lower(title_romaji) LIKE ? OR lower(title_romaji) LIKE ? OR lower(title_romaji) LIKE ? "
    pstmt_conditions += " ) "
    pstmt_values.extend(['%'+keywords+'%', '%'+string_util.convert_chi_to_kanji(keywords)+'%',
                         keywords, keywords+' %', '% '+keywords, '% '+keywords+' %'])
    
    return {'conditions': pstmt_conditions, 'values': pstmt_values}


def _build_song_chart_list(db_chart_list: list[str, str, str, str, str, int, int]) -> list[Song]:
    # db_chart_list = [(song_id, title, chart_id, mode, difficulty, level, notes), ...]

    logger = logging.getLogger(__name__)

    song_chart_list = []
    last_song_id = ""

    for chart in db_chart_list:
        song_id = chart[0]
        title = chart[1]
        chart_id = chart[2]
        #mode = chart[3]    # not in use
        difficulty = chart[4]
        level = chart[5]
        notes = chart[6]

        # if current chart is of a different song than the previous chart,
        if (song_id != last_song_id):
            # add the Song dataclass instance storing details of previous song to the result list
            if last_song_id != "":
                song_chart_list.append(song_chart)
                logger.debug(song_chart)
            
            # create a new Song dataclass instance for the current song
            song_chart = Song(song_id=song_id, title=title, charts=[])

        # add the details of current chart in Song dataclass instance
        song_chart.charts.append(Chart(chart_id=chart_id, difficulty=difficulty, level=level, notes=notes))

        # update last_song_id before proceed to next chart
        last_song_id = song_id

    # add the Song dataclass instance storing details of the last song to the result list
    song_chart_list.append(song_chart)
    logger.debug(song_chart)

    return song_chart_list