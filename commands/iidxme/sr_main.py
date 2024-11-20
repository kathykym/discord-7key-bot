from discord import Embed
import math
import logging
from db.models.Song import Song
import commands.iidxme.iidxme_util as iidx_util
import db.iidxme_db as db
import config.config_reader as config
import utils.display_util as display_util
import utils.string_util as string_util


def get_result_embed(p_arg_str: str) -> Embed:
    logger = logging.getLogger(__name__)

    logger.debug(p_arg_str)

    # elements of Discord embed object to be displayed
    embed_title = config.get('IIDXME_SR', 'title')
    embed_desc = ""
    embed_colour = config.get('IIDXME_SR', 'colour_embed_border')
    embed_footer = ""

    try:
        # 1) parse the command arguments
        username_list, mode, difficulty, level, keywords, flag_exact_keyword_match, flag_display_score_percentage \
            = iidx_util.parse_arguments(num_of_usernames=0, arg_str=p_arg_str)
        
        embed_title += f" ({mode.upper()}) "

        # 2) fetch charts from DB with the search criteria
        # 2.1) limit the result set to the number of songs specified in config file
        result_limit = int(config.get('IIDXME_SR', 'result_limit'))
        num_of_matches = db.get_num_of_matched_songs(mode, difficulty, level, keywords, flag_exact_keyword_match)

        # display message if number of results exceeds limit
        if num_of_matches > result_limit:
            embed_desc += config.get('IIDX', 'msg_too_many_results') + "\n\n"

        # display message if no charts are found
        if num_of_matches == 0:
            embed_desc += config.get('IIDX', 'msg_result_not_found')
        else:
            # 2.2) fetch song & chart info (song_id, chart_id, title, difficulty, level) from DB
            song_list = db.fetch_charts(mode, difficulty, level, keywords, flag_exact_keyword_match, result_limit)
            
            # 3) calculate scores needed for each rank and construct the embed object desc for display
            embed_desc += _cal_score_and_build_embed_desc(song_list)

    except ValueError as ve:
        logger.debug(repr(ve))
        embed_desc = str(ve)
        embed_colour = config.get('COMMAND_ERROR', 'colour_error')
        embed_footer = ""
    except Exception as e:
        logger.error(repr(e))
        embed_desc = str(e)
        embed_colour = config.get('COMMAND_ERROR', 'colour_error')
        embed_footer = ""
    finally:
        return display_util.construct_embed(title=embed_title, desc=embed_desc, colour=embed_colour,
                                    footer=embed_footer, image_url="")


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
            difficulty_emoji = config.get('IIDX', f"emoji_{chart.difficulty}")

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
    padding_spaces = 2
    if (num_of_digits < 4):
        padding_spaces += 3
    
    num_of_ones = str(score).count("1")
    padding_spaces += num_of_ones

    return num_of_digits + padding_spaces