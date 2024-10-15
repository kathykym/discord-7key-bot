from discord import Embed
import re
import requests
import logging
from commands.iidxme.classes.Song import Song
from commands.iidxme.classes.PbInfo import PbInfo
import commands.iidxme.pb_scraper as scraper
import db.iidxme_db_helper as db
import utils.config_reader as config
import utils.display_util as display_util
import utils.string_util as string_util


def get_result_embed(p_args: list) -> Embed:
    logger = logging.getLogger(__name__)

    logger.debug(p_args)

    # elements of Discord embed object to be displayed
    embed_title = config.get('IIDXME_PB', 'title')
    embed_desc = ""
    embed_colour = config.get('IIDXME_PB', 'colour_embed_border')
    embed_footer = ""

    try:
        # 1) parse the command arguments
        username, mode, difficulty, level, keywords = _parse_arguments(p_args)

        # display iidx.me username and play mode
        embed_desc = f"Player: {string_util.escape_special_formatting_characters(username)} ({mode.upper()})\n\n"

        # 2) fetch the IIDX release version the user last played from iidx.me
        request_session = requests.Session()
        last_play_ver = scraper.fetch_last_play_version(request_session, username)

        # 3) fetch charts from DB with the search criteria
        # 3.1) limit the result set to the number of songs specified in config file
        result_limit = int(config.get('IIDXME_PB', 'result_limit'))
        num_of_matches = db.get_num_of_matched_songs(mode, difficulty, level, keywords)

        # display message if number of results exceeds limit
        if num_of_matches > result_limit:
            embed_desc += config.get('IIDXME_PB', 'msg_too_many_results') + "\n\n"

        # display message if no charts are found
        if num_of_matches == 0:
            embed_desc += config.get('IIDXME_PB', 'msg_result_not_found')
        else:
            # 3.2) fetch song & chart info (song_id, chart_id, title, difficulty, level) from DB
            song_list = db.fetch_charts(mode, difficulty, level, keywords, result_limit)

            # 4) fetch personal best records from iidx.me
            pb_dict = scraper.fetch_pb_records(request_session, username, last_play_ver, song_list)

            # 5) construct the embed object desc for display
            # show song level url if both chart difficulty and level are not specified, else show chart level url
            show_song_level_url = ((difficulty == "ALL") and (level == "ALL"))
            embed_desc += _build_embed_desc_for_PB(username, last_play_ver, song_list, pb_dict, show_song_level_url)

            # 6) display footer message if
            # - user achieved MAX in any of searched charts
            # - user achieved full combo in all searched charts
            # - user achieved AAA in all searched charts
            # - user did not play any searched chart
            has_MAX = False
            is_all_FC = True
            is_all_AAA = True
            is_all_no_play = True

            for pb in pb_dict.values():
                if pb.rank == "MAX":
                    has_MAX = True
                    break
                if pb.lamp != config.get('IIDXME_PB', 'abbr_F-COMBO'):
                    is_all_FC = False
                if pb.rank != "AAA":
                    is_all_AAA = False
                # if user has played the chart, it means either
                #  a) the lamp is not NO PLAY nor "--"
                #  or
                #  b) the score is not -1
                if (pb.lamp != config.get('IIDXME_PB', 'abbr_NO PLAY') and pb.lamp != "--") \
                    or (pb.score != -1):
                    is_all_no_play = False

            if has_MAX:
                embed_footer = config.get('IIDXME_PB', 'msg_has_MAX')
            elif is_all_FC and is_all_AAA:
                embed_footer = config.get('IIDXME_PB', 'msg_all_FC_and_AAA')
            elif is_all_FC:
                embed_footer = config.get('IIDXME_PB', 'msg_all_FC')    
            elif is_all_AAA:
                embed_footer = config.get('IIDXME_PB', 'msg_all_AAA')
            elif is_all_no_play:
                embed_footer = config.get('IIDXME_PB', 'msg_all_no_play')

    except ValueError as ve:
        logger.debug(repr(ve))
        embed_desc = str(ve)
        embed_colour = config.get('IIDXME_PB', 'colour_error')
        embed_footer = ""
    except Exception as e:
        logger.error(repr(e))
        embed_desc = str(e)
        embed_colour = config.get('IIDXME_PB', 'colour_error')
        embed_footer = ""
    finally:
        return display_util.construct_embed(title=embed_title, desc=embed_desc, colour=embed_colour,
                                    footer=embed_footer, image_url="")


def _parse_arguments(p_args: list) -> tuple[str, str, str, str, str]:
    logger = logging.getLogger(__name__)

    # list of values to be returned
    username = ""
    mode = "SP"
    difficulty = "ALL"
    level = "ALL"
    keywords = ""
    
    num_of_args = len(p_args)

    # command takes exactly 2 or 3 arguments - iidx.me username, mode/difficulty/level (optional), song title keywords
    if num_of_args < 2:
        raise ValueError(config.get('IIDXME_PB', 'msg_missing_args'))
    elif num_of_args > 3:
        raise ValueError(config.get('IIDXME_PB', 'msg_too_many_args'))
    else:
        username = p_args[0]
        keywords = p_args[-1]

        # handle '%' and '%%' (custom wildcard) in song title keywords
        keywords = re.sub("%%", "<special_handling>", keywords)
        keywords = re.sub("%", "\%", keywords)
        keywords = re.sub("<special_handling>", "%", keywords)

        # iidx.me username should start with alphabet/number and contain no whitespaces
        if not re.search("^[a-zA-Z|\d][^\s]*$", username):
            raise ValueError(config.get('IIDXME_PB', 'msg_empty_username'))
        # keywords should not be an empty string or merely a wildcard '%'
        elif (keywords == "") or (keywords == "%"):
            raise ValueError(config.get('IIDXME_PB', 'msg_empty_keyword'))
        # if any of mode/difficulty/level are specified
        elif num_of_args == 3:
            # check the pattern of second arg to get mode/difficulty/level filters
            match_regex = re.search("^(SP|DP)?(B|N|H|A|L)?([1-9]|10|11|12)?$", p_args[1].upper())
            if match_regex:
                opt_list = re.split("^(SP|DP)?(B|N|H|A|L)?([1-9]|10|11|12)?$", p_args[1].upper())
                if opt_list[1] is not None:
                    mode = opt_list[1]
                if opt_list[2] is not None:
                    difficulty = opt_list[2]
                if opt_list[3] is not None:
                    level = opt_list[3]
            else:
                raise ValueError(config.get('IIDXME_PB', 'msg_wrong_arg_format'))
    
    logger.debug([username, mode, difficulty, level, keywords])

    return username, mode, difficulty, level, keywords


def _build_embed_desc_for_PB(username: str, last_play_ver: str,
                             song_list: list[Song], pb_dict: dict[str, PbInfo], show_song_level_url: bool) -> str:
    embed_desc = ""

    for song in song_list:
        # display song title
        embed_desc += f"**{string_util.escape_special_formatting_characters(song.title)}**\n"

        # display song/chart url
        if show_song_level_url:
            embed_desc += f"https://iidx.me/{last_play_ver}/{username}/music/{song.song_id}\n"
        elif len(song.charts) > 0:
            embed_desc += f"https://iidx.me/{last_play_ver}/{username}/music/{song.song_id}#{song.charts[0].chart_id}\n"

        for chart in song.charts:
            pb = pb_dict[chart.chart_id]
            
            # display chart difficulty, level and PB info
            '''
                sample:
                🟥12: FC／[AAA] 2123 (MAX-109)／BP 0
            '''
            difficulty_emoji = config.get('IIDXME_PB', f"emoji_{chart.difficulty}")

            level_str = "?" if chart.level == -1 else str(chart.level)
            
            rank_and_score_str = "--"
            if pb.score != -1:
                rank_and_score_str = f"__{pb.score_attained_version}__ [{pb.rank}] {pb.score}"
                if pb.rank_diff:
                    rank_and_score_str += f" _({pb.rank_diff})_"

            misscount_str = "--"
            if pb.misscount != 9999:
                misscount_str = f"BP {pb.misscount}"

            embed_desc += f"{difficulty_emoji}{level_str.rjust(2)}：{pb.lamp}／{rank_and_score_str}／{misscount_str}\n"

        embed_desc += "\n"
        
    return embed_desc


def prompt_loading_message() -> Embed:
    embed_title = config.get('IIDXME_PB', 'title')
    embed_desc = config.get('IIDXME_PB', 'msg_loading')
    embed_colour = config.get('IIDXME_PB', 'colour_embed_border')
    embed_footer = ""
    return display_util.construct_embed(title=embed_title, desc=embed_desc, colour=embed_colour,
                                footer=embed_footer, image_url="")