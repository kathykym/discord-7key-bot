import discord
import random
import logging
import db.bot_db_helper as db
import utils.config_reader as config


async def follow_suit(bot_user_id: discord.ClientUser, message: discord.Message) -> str:
    logger = logging.getLogger(__name__)

    ping_msg = ""
    last_follow_msg = db.get_bot_param('on_message', 'follow_suit_last_sent_msg')
    
    # if the message is different from what the bot posted when it last followed suit,
    # reset the last sent message in database
    if last_follow_msg and (last_follow_msg != message.content):
        last_follow_msg = ""
        db.update_bot_param('on_message', 'follow_suit_last_sent_msg', "")

    # follow suit to send the same text message if all of below conditions are met:
    # a) the text message is not a command
    if message.content and (message.content[0] not in config.get('SERVER', 'cmd_prefixes')):
        # get the latest N messages in the channel, where N is the "number of same message" defined in config file
        num_of_same_msg = config.get('ON_MESSAGE_FOLLOW_SUIT', 'num_of_same_msg')
        past_msg_list = [(msg.author.id, msg.content) async for msg in message.channel.history(limit=num_of_same_msg)]
        
        # b) there are at least N messages in the channel, where N is the "number of same message" defined in config file
        if len(past_msg_list) >= num_of_same_msg:
            # c) all messages have different authors
            author_list = [item[0] for item in past_msg_list]
            is_diff_authors = len(set(author_list)) == len(author_list)

            # d) the exact same text message is sent in a row
            content_list = [item[1] for item in past_msg_list]
            is_same_content = all(item == content_list[0] for item in content_list)
            
            logger.debug(f"content_list = {content_list}")
            logger.debug(f"is_same_content = {is_same_content}")
            logger.debug(f"author_list = {author_list}")
            logger.debug(f"is_diff_authors = {is_diff_authors}")

            # e) the text messages are sent by different users/bots, excluding the bot itself
            if is_same_content and is_diff_authors and (bot_user_id not in author_list):
                # f) the text message is different from what the bot sent when it last followed suit
                if last_follow_msg != content_list[0]:
                    # follow suit to send the message and update the database
                    ping_msg = content_list[0]
                    db.update_bot_param('on_message', 'follow_suit_last_sent_msg', ping_msg)

    return ping_msg


async def iidx_result_comment(message: discord.Message) -> str:
    ping_msg = ""
    
    attachment_ext_list = tuple(config.get('ON_MESSAGE_IIDX_RESULT_COMMENT', 'attachment_ext_list').split("|"))

    # randomly send comment in iidx-bms channel if all of below conditions are met:
    # a) it is currently in iidx-bms channel
    # b) the message is sent by a human user
    # c) the message has an attachment which is an image or a video, or the message contains a youtube link
    if (message.channel.id == config.get('SERVER', 'iidx_channel_id')) \
        and (message.author.bot == False) \
        and (
                (message.attachments and message.attachments[0].filename.lower().endswith(attachment_ext_list)) \
                or ("https://www.youtube.com/" in message.content) \
                or ("https://youtu.be/" in message.content)
            ):
        
        # fetch the volume value from database and calculate the probability to comment
        comment_chance = int(db.get_bot_param('on_message', 'iidx_result_comment_volume'))

        if random.randrange(0, config.get('VOLUME', 'vol_upper_bound')) < comment_chance:
            # retrieve comments from config file
            comment_list = config.get('ON_MESSAGE_IIDX_RESULT_COMMENT', 'msg_comment_list').split("|")
            
            # retrieve a role-based comment from config file
            dan_role_list = config.get('SERVER', 'dan_role_id_dict')
            author_role_list = [role.id for role in message.author.roles]
            author_dan = ""

            for dan, role_id in dan_role_list.items():
                if role_id in author_role_list:
                    author_dan = dan
                    break
            
            if author_dan:
                comment_list.append(config.get('ON_MESSAGE_IIDX_RESULT_COMMENT', 'msg_next_dan_dict').get(author_dan))
            
            # randomly pick a comment to send
            ping_msg = f"{random.choice(comment_list)}"

    return ping_msg