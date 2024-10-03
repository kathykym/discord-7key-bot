from discord import Embed
import re
import math
import logging
from commands.iidxme.classes.Song import Song
import db.iidxme_db_helper as db
import utils.config_reader as config
import utils.display_util as display_util
import utils.string_util as string_util


def get_result_embed(p_args: list) -> Embed:
    logger = logging.getLogger(__name__)

    logger.debug(p_args)

    # elements of Discord embed object to be displayed
    embed_title = config.get('IIDXME_SR', 'title')
    embed_desc = ""
    embed_colour = config.get('IIDXME_SR', 'colour_embed_border')
    embed_footer = ""

    try:
        # 1) parse the command arguments
        mode, difficulty, level, keywords = _parse_arguments(p_args)
        
        embed_title += f" ({mode.upper()}) "

        # 2) fetch charts from DB with the search criteria
        # 2.1) limit the result set to the number of songs specified in config file
        result_limit = int(config.get('IIDXME_SR', 'result_limit'))
        num_of_matches = db.get_num_of_matched_songs(mode, difficulty, level, keywords)

        # display message if number of results exceeds limit
        if num_of_matches > result_limit:
            embed_desc += config.get('IIDXME_SR', 'msg_too_many_results') + "\n\n"

        # display message if no charts are found
        if num_of_matches == 0:
            embed_desc += config.get('IIDXME_SR', 'msg_result_not_found')
        else:
            # 2.2) fetch song & chart info (song_id, chart_id, title, difficulty, level) from DB
            song_list = db.fetch_charts(mode, difficulty, level, keywords, result_limit)
            
            # 3) calculate scores needed for each rank and construct the embed object desc for display
            embed_desc += _cal_score_and_build_embed_desc(song_list)

    except ValueError as ve:
        logger.debug(repr(ve))
        embed_desc = str(ve)
        embed_colour = config.get('IIDXME_SR', 'colour_error')
        embed_footer = ""
    except Exception as e:
        logger.error(repr(e))
        embed_desc = str(e)
        embed_colour = config.get('IIDXME_SR', 'colour_error')
        embed_footer = ""
    finally:
        return display_util.construct_embed(title=embed_title, desc=embed_desc, colour=embed_colour,
                                    footer=embed_footer, image_url="")
    

def _parse_arguments(p_args: list) -> tuple[str, str, str, str]:
    logger = logging.getLogger(__name__)

    # list of values to be returned
    mode = "SP"
    difficulty = "ALL"
    level = "ALL"
    keywords = ""
    
    num_of_args = len(p_args)

    # command takes exactly 1 or 2 arguments - mode/difficulty/level (optional), song title keywords
    if num_of_args == 0:
        raise ValueError(config.get('IIDXME_SR', 'msg_empty_keyword'))
    elif num_of_args > 2:
        raise ValueError(config.get('IIDXME_SR', 'msg_too_many_args'))
    else:
        keywords = p_args[-1]

        # handle '%' and '%%' (custom wildcard) in song title keywords
        keywords = re.sub("%%", "<special_handling>", keywords)
        keywords = re.sub("%", "\%", keywords)
        keywords = re.sub("<special_handling>", "%", keywords)

        # keywords should not be an empty string or merely a wildcard '%'
        if (keywords == "") or (keywords == "%"):
            raise ValueError(config.get('IIDXME_SR', 'msg_empty_keyword'))
        # if any of mode/difficulty/level are specified
        elif num_of_args == 2:
            # check the pattern of second arg to get mode/difficulty/level filters
            match_regex = re.search("^(SP|DP)?(B|N|H|A|L)?([1-9]|10|11|12)?$", p_args[0].upper())
            if match_regex:
                opt_list = re.split("^(SP|DP)?(B|N|H|A|L)?([1-9]|10|11|12)?$", p_args[0].upper())
                if opt_list[1] is not None:
                    mode = opt_list[1]
                if opt_list[2] is not None:
                    difficulty = opt_list[2]
                if opt_list[3] is not None:
                    level = opt_list[3]
            else:
                raise ValueError(config.get('IIDXME_SR', 'msg_wrong_arg_format'))
    
    logger.debug([mode, difficulty, level, keywords])

    return mode, difficulty, level, keywords


def _cal_score_and_build_embed_desc(song_list: list[Song]) -> str:
    embed_desc = ""

    # display the header
    rank_str_format = "{0:^6}／{1:^4}／{2:^5}／{3:^5}\n"
    embed_desc += f"Rank  :  {rank_str_format.format('AAA-', 'AAA', 'MAX-', 'MAX')}"
    embed_desc += f"{'¯' * 56}\n"

    for song in song_list:
        # display song title
        embed_desc += f"**{string_util.escape_special_formatting_characters(song.title)}**\n"

        for chart in song.charts:
            # display the chart info and scores needed for each rank
            '''
                sample:
                🟪12： 3462 ／ 3270 ／ 3078 ／ 2885
            '''
            difficulty_emoji = config.get('IIDXME_PB', f"emoji_{chart.difficulty}")

            level_str = "?" if chart.level == -1 else str(chart.level)
            
            if chart.notes != -1:
                # calculate the scores needed for each rank
                # MAX : = number of notes * 2
                # AAA : >= 8/9 of MAX score
                # AA  : >= 7/9 of MAX score
                # MAX-: >= average of AAA and MAX scores
                # AAA-: >= average of AA and AAA scores
                score_max = chart.notes * 2
                score_aaa = math.ceil(score_max * 8 / 9)
                score_aa  = math.ceil(score_max * 7 / 9)
                score_max_minus = math.ceil((score_aaa + score_max) / 2)
                score_aaa_minus = math.ceil((score_aa  + score_aaa) / 2)

                score_str = "{num:{field_size}}".format(num = score_aaa_minus, field_size = _get_score_display_width(score_aaa_minus)) + "  ／" + \
                            "{num:{field_size}}".format(num = score_aaa, field_size = _get_score_display_width(score_aaa)) + "  ／" + \
                            "{num:{field_size}}".format(num = score_max_minus, field_size = _get_score_display_width(score_max_minus)) + "  ／" + \
                            "{num:{field_size}}".format(num = score_max, field_size = _get_score_display_width(score_max))

                embed_desc += f"{difficulty_emoji}{level_str.rjust(2)}：{score_str}\n"
            else:
                embed_desc += f"{difficulty_emoji}{level_str.rjust(2)}： {config.get('IIDXME_SR', 'msg_notes_TBD')}\n"
                
        embed_desc += "\n"
        
    return embed_desc


def _get_score_display_width(score: str) -> int:
    # adjust number of padding spaces based on the number of digits and number of 1's in the score
    num_of_digits = len(str(score))
    padding_spaces = 0
    if (num_of_digits < 4):
        padding_spaces += 3
    
    num_of_ones = str(score).count("1")
    padding_spaces += num_of_ones

    return num_of_digits + padding_spaces