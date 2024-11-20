from discord import Embed
import re
import logging
import db.bot_db as db
import config.config_reader as config
import utils.display_util as display_util


def get_result_embed(input_str: str, channel_id: int) -> Embed:
    logger = logging.getLogger(__name__)

    # elements of Discord embed object to be displayed
    embed_title = config.get('VOLUME', 'title')
    embed_desc = config.get('VOLUME', 'subtitle')
    embed_colour = config.get('VOLUME', 'colour_embed_border')
    embed_footer = ""

    try:
        if (channel_id != config.get('SERVER', 'iidx_channel_id')):
            embed_desc = config.get('VOLUME', 'msg_wrong_channel')
            embed_colour = config.get('VOLUME', 'colour_error')
        else:
            if input_str:
                # parse the command arguments
                volume = _parse_arguments(input_str)

                # update the volume value in database
                db.update_bot_param('on_message', 'iidx_result_comment_volume', str(volume))
            else:
                # if there is no argument, display the current volume value
                #fetch the volume value in database
                volume = int(db.get_bot_param('on_message', 'iidx_result_comment_volume'))

            # construct the volume bar for display
            vol_bar_length = config.get('VOLUME', 'vol_bar_length')
            vol_upper_bound = config.get('VOLUME', 'vol_upper_bound')
            vol_on_length = round(volume / vol_upper_bound * vol_bar_length)

            embed_footer += config.get('VOLUME', 'emoji_vol_on') * vol_on_length
            embed_footer += config.get('VOLUME', 'emoji_vol_handler')
            embed_footer += config.get('VOLUME', 'emoji_vol_off') * (vol_bar_length - vol_on_length)

            # display the volume bar in footer as there is not enough horizontal space to display the bar in embed desc
            if volume == 0:
                embed_footer += "\n\n" + config.get('VOLUME', 'msg_muted')
            elif 0 < volume <= 50:
                embed_footer += "\n\n" + config.get('VOLUME', 'msg_low_vol_1_footer')
            elif 50 < volume < 100:
                embed_footer += "\n\n" + config.get('VOLUME', 'msg_low_vol_2_footer')
            elif volume == 100:
                embed_footer += "\n\n" + config.get('VOLUME', 'msg_normal_vol_footer')
            elif 100 < volume <= 150:
                embed_footer += "\n\n" + config.get('VOLUME', 'msg_high_vol_1_footer')
            elif 150 < volume < vol_upper_bound:
                embed_footer += "\n\n" + config.get('VOLUME', 'msg_high_vol_2_footer')
            elif volume == vol_upper_bound:
                embed_footer += "\n\n" + config.get('VOLUME', 'msg_max_vol')

    except (TypeError, ValueError) as e:
        logger.debug(repr(e))
        embed_desc = str(e)
        embed_colour = config.get('VOLUME', 'colour_error')
        embed_footer = config.get('VOLUME', 'msg_arg_error_footer')
    except Exception as e:
        logger.error(repr(e))
        embed_desc = config.get('VOLUME', 'msg_generic_error')
        embed_colour = config.get('VOLUME', 'colour_error')
        embed_footer = ""
    finally:
        return display_util.construct_embed(title=embed_title, desc=embed_desc, colour=embed_colour,
                                    footer=embed_footer, image_url="")


def _parse_arguments(input_str: str) -> int:
    # command takes only one integer argument
    if not re.search("^[-+]?[\d]+$", input_str):
        raise TypeError(config.get('VOLUME', 'msg_not_integer_input'))
    # the integer should be between 0 and the volume upper bound (inclusive) defined in config file
    elif int(input_str) < 0:
        raise ValueError(config.get('VOLUME', 'msg_negative_vol'))
    elif int(input_str) > config.get('VOLUME', 'vol_upper_bound'):
        raise ValueError(config.get('VOLUME', 'msg_vol_exceeds_limit'))
    
    return int(input_str)