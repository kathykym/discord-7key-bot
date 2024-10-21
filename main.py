import discord
from discord.ext import commands
import logging.config
from pathlib import Path
import commands.iidxme.pb_main as iidxpb_main
import commands.iidxme.sr_main as iidxsr_main
import commands.wordcloud.wc_main as wordcloud_main
import commands.volume.vl_main as volume_main
import events.on_message as ping_functions
import utils.config_reader as config


def main():
    # BOT AND LOGGER SETUP
    bot_token = config.get('ENV', 'token')
    command_prefix = config.get('ENV', 'command_prefix')
    log_level = config.get('ENV', 'log_level')

    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    bot = commands.Bot(command_prefix=commands.when_mentioned_or(command_prefix), intents=intents)

    log_level_dict = {
        'logging.DEBUG': logging.DEBUG,
        'logging.INFO': logging.INFO,
        'logging.WARNING': logging.WARNING,
        'logging.ERROR': logging.ERROR
    }

    logger_handler = logging.FileHandler(filename=Path(config.get('BOT', 'log_file')), encoding='utf-8', mode='a')


    # BOT EVENTS - start
    @bot.event
    async def on_ready():
        logger = logging.getLogger(__name__)
        logger.info("Bot is now running")


    @bot.event
    async def on_command_error(ctx, error):
        # respond to command input errors
        if isinstance(error, commands.errors.InvalidEndOfQuotedStringError):
            await ctx.reply(embed=discord.Embed(description=config.get('COMMAND_ERROR', 'msg_double_quote_misplaced'),
                                                color=config.get('COMMAND_ERROR', 'colour_error')))
        if isinstance(error, commands.errors.ExpectedClosingQuoteError):
            await ctx.reply(embed=discord.Embed(description=config.get('COMMAND_ERROR', 'msg_double_quote_misplaced'),
                                                color=config.get('COMMAND_ERROR', 'colour_error')))


    @bot.event
    async def on_message(message):
        # ignore messages sent by the bot itself
        bot_user = bot.user
        if message.author != bot_user:
            # ping function: follow suit
            # - if an exact same text message is sent by several users in a row, join the party
            ping_msg = await ping_functions.follow_suit(bot_user.id, message)
            if ping_msg:
                await message.channel.send(ping_msg)
            
            # ping function: iidx result comment
            # - randomly comment on images/videos sent by users in iidx-bms channel
            ping_msg = await ping_functions.iidx_result_comment(message)
            if ping_msg:
                await message.channel.send(ping_msg)

            # replace ’ with ' in message content as the bot fails to process command when argument contains ’
            message.content = message.content.replace('’', '\'')
            # process the message/command further
            await bot.process_commands(message)
   
    # BOT EVENTS - end


    # BOT COMMANDS - start
    @bot.command(brief=config.get('IIDXME_PB', 'title'), help=config.get('IIDXME_PB', 'usage'))
    async def iidxpb(ctx, *, arg_str: str = ""):
        # reply with a loading message
        bot_message = await ctx.reply(embed=iidxpb_main.prompt_loading_message(), mention_author=False)
        # get personal best records from iidx.me and update the reply
        await bot_message.edit(embed=iidxpb_main.get_result_embed(arg_str))


    @bot.command(brief=config.get('IIDXME_SR', 'title'), help=config.get('IIDXME_SR', 'usage'))
    async def iidxsr(ctx, *, arg_str: str = ""):
        # get the calculated scores needed for different ranks and reply
        await ctx.reply(embed=iidxsr_main.get_result_embed(arg_str), mention_author=False)


    @bot.command(brief=config.get('WORD_CLOUD', 'title'), help=config.get('WORD_CLOUD', 'usage'))
    async def wordcloud(ctx, *args: str):
        # reply with a loading message
        bot_message = await ctx.reply(embed=wordcloud_main.prompt_loading_message(), mention_author=False)
        # read message history in the channel and use the messages as text source
        msg_list = [msg async for msg in ctx.channel.history(limit=config.get('WORD_CLOUD', 'message_history_limit'))]
        # generate the word cloud
        embedObj = wordcloud_main.get_result_embed(args, msg_list)
        
        # if the word cloud image is generated successfully
        if embedObj.image:
            # attach the word cloud image and update the bot reply
            img_file = discord.File(embedObj.image.url, filename="image.png")
            embedObj.set_image(url="attachment://image.png")
            await bot_message.edit(embed=embedObj, attachments=[img_file])
        # else, update the bot reply with error message
        else:
            await bot_message.edit(embed=embedObj)


    @bot.command(brief=config.get('VOLUME', 'title'), help=config.get('VOLUME', 'usage'))
    async def volume(ctx, *args: str):
        arg_str = " ".join(args)
        # get the result of "bot volume" adjustment and reply
        await ctx.reply(embed=volume_main.get_result_embed(arg_str, ctx.message.channel.id), mention_author=False)
    
    # BOT COMMANDS - end


    # START THE BOT
    bot.run(bot_token,
            log_handler=logger_handler,
            log_level=log_level_dict.get(log_level),
            root_logger=True)


if __name__ == '__main__':
    main()