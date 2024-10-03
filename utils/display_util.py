from discord import Embed
import utils.config_reader as config


def construct_embed(title: str, desc: str, colour: int, footer: str, image_url: str) -> Embed: 
    if (not colour) or (not isinstance(colour, int)):
        colour = config.get('BOT', 'default_embed_colour')
    
    embedObj = Embed(title=title, description=desc, colour=colour)
    
    if footer:
        embedObj.set_footer(text=footer)
    
    if image_url:
        embedObj.set_image(url=image_url)
        
    return embedObj