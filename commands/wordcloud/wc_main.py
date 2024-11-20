from discord import Embed
import jieba
import emoji
from PIL import Image
from imojify import imojify
import requests
from io import BytesIO
from pathlib import Path
import re
import datetime
import logging
import commands.wordcloud.wc_generator as generator
import config.config_reader as config
import utils.display_util as display_util


def get_result_embed(p_args: list, msg_list: list) -> Embed:
    logger = logging.getLogger(__name__)

    logger.debug(p_args)

    # elements of Discord embed object to be displayed
    embed_title = config.get('WORD_CLOUD', 'title')
    embed_desc = ""
    embed_colour = config.get('WORD_CLOUD', 'colour_embed_border')
    embed_image_url = ""
    embed_footer = ""

    try:
        # 1) parse the command arguments
        unicode_emoji, custom_emoji_id, user_id = _parse_arguments(p_args)
        
        # 2) extract message content as text source to build the word cloud
        text_source = ""
        # filter messages if a user is specified in argument
        for msg in msg_list:
            if (user_id == -1) or (msg.author.id == user_id):
                if msg.content:
                    text_source += msg.content + " "
                elif msg.embeds and msg.embeds[0].description:
                    text_source += msg.embeds[0].description + " "
            
        # 3) tokenize the text source and remove unwanted strings, e.g. tags
        text_source = " ".join(jieba.cut(text_source))
        text_source = re.sub("<.*>", "", text_source)

        if not text_source:
            raise ValueError(config.get('WORD_CLOUD', 'msg_no_words_found'))
        else:
            # 4) generate the word cloud

            # override custom emoji for testing purpose
            #override_custom_emoji_id = config.get('WORD_CLOUD', 'override_custom_emoji_id')
            #if override_custom_emoji_id:
            #    custom_emoji_id = override_custom_emoji_id

            # 4.1) if an emoji is specified, use the emoji image as word cloud mask and create colouring from the image
            emoji_img = ""
            if unicode_emoji:
                # a) unicode emoji: use emoji image
                emoji_img = Image.open(imojify.get_img_path(unicode_emoji))
            elif custom_emoji_id != -1:
                # b) discord server custom emoji: fetch emoji image from discord
                response = requests.get(f"https://cdn.discordapp.com/emojis/{custom_emoji_id}.webp?quality=lossless")
                emoji_img = Image.open(BytesIO(response.content))

            # 4.2) generate the word cloud output image filename wth timestamp
            embed_image_url = Path(config.get('WORD_CLOUD', 'output_file_path') + "wc_" + "{date:%Y%m%d_%H%M%S%f}".format(date=datetime.datetime.now()) + ".png")
            
            # 4.3) generate the word cloud. save the output image locally which will be attached to the bot's reply
            generator.generate_word_cloud(text_source, emoji_img, embed_image_url)

            # 5) display footer message
            if emoji_img:
                embed_footer = config.get('WORD_CLOUD', 'msg_done')
            else:
                embed_footer = config.get('WORD_CLOUD', 'msg_done_without_emoji')

    except ValueError as ve:
        logger.debug(repr(ve))
        embed_desc = str(ve)
        embed_colour = config.get('WORD_CLOUD', 'colour_error')
        embed_image_url = ""
        embed_footer = ""
    except Exception as e:
        logger.error(repr(e))
        embed_desc = config.get('WORD_CLOUD', 'msg_generic_error')
        embed_colour = config.get('WORD_CLOUD', 'colour_error')
        embed_image_url = ""
        embed_footer = ""
    finally:
        return display_util.construct_embed(title=embed_title, desc=embed_desc, colour=embed_colour,
                                    footer=embed_footer, image_url=embed_image_url)
                                    

def _parse_arguments(p_args: list) -> tuple[str, int, int]:
    
    logger = logging.getLogger(__name__)
    
    # list of values to be returned
    unicode_emoji = ""
    custom_emoji_id = -1
    user_id = -1

    num_of_args = len(p_args)

    # command takes at most 2 arguments - emoji (optional), discord user mention (optional)
    if num_of_args > 2:
        raise ValueError(config.get('WORD_CLOUD', 'msg_too_many_args'))
    elif num_of_args >= 1:
        # check if first argument is a unicode or custom emoji
        if emoji.is_emoji(p_args[0]):
            unicode_emoji = p_args[0]
        else:
            custom_emoji_id = _get_custom_emoji_id(p_args[0])

        # check if last argument is a discord user mention
        user_id = _get_user_id(p_args[-1])

        if num_of_args == 1:
            # either emoji or user has to be specified
            if not((unicode_emoji or custom_emoji_id != -1) or (user_id != -1)):
                raise ValueError(config.get('WORD_CLOUD', 'msg_wrong_arg_format'))
        else:
            # num_of_args == 2. both emoji and user have to be specified
            if not((unicode_emoji or custom_emoji_id != -1) and (user_id != -1)):
                raise ValueError(config.get('WORD_CLOUD', 'msg_wrong_arg_format'))

    logger.debug([unicode_emoji, custom_emoji_id, user_id])

    return unicode_emoji, custom_emoji_id, user_id


def _get_custom_emoji_id(string: str) -> int:
    emoji_id = -1

    # emoji tag pattern
    emoji_tag = re.findall("^<[a]?\:[a-zA-Z\d_-]+\:[\d]+>$", string)
    if emoji_tag:
        emoji_id = int(re.findall("[\d]+", emoji_tag[0])[-1])

    return emoji_id


def _get_user_id(string: str) -> int:
    user_id = -1

    # user tag pattern
    user_tag = re.findall("^<@[\d]+>$", string)
    if user_tag:
        user_id = int(re.search("[\d]+", user_tag[0]).group(0))
        
    return user_id


def prompt_loading_message() -> Embed:
    embed_title = config.get('WORD_CLOUD', 'title')
    embed_desc = config.get('WORD_CLOUD', 'msg_loading')
    embed_colour = config.get('WORD_CLOUD', 'colour_embed_border')
    embed_footer = ""
    return display_util.construct_embed(title=embed_title, desc=embed_desc, colour=embed_colour,
                                footer=embed_footer, image_url="")
    