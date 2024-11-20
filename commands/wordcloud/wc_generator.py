from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image
import numpy
import matplotlib.pyplot as plt
from pathlib import Path
import logging
import config.config_reader as config


def generate_word_cloud(text_source: str, emoji_img: Image, filename: str) -> None:
    logger = logging.getLogger(__name__)

    try:
        font_file = Path(config.get('WORD_CLOUD', 'font_file'))
        wc_image_size = config.get('WORD_CLOUD', 'wc_image_size')
        plt_figsize = config.get('WORD_CLOUD', 'plt_figsize')
                
        # if an emoji is specified,
        if emoji_img:
            # enlarge the emoji image and use it as word cloud mask
            emoji_img = emoji_img.resize((wc_image_size, wc_image_size))
            mask = numpy.array(emoji_img)
            # generate word cloud image. use default font size as mask is applied
            bg_colour = config.get('WORD_CLOUD', 'with_emoji_bgcolour')
            wc = WordCloud(font_path=font_file,
                           collocations=False, max_words=1000,
                           width=wc_image_size, height=wc_image_size, background_color=bg_colour, mask=mask
                           ).generate(text_source)
        # if NO emoji is specified,
        else:
            # set custom font size for word cloud. generate font colours with colormap in matplotlib
            max_font_size = config.get('WORD_CLOUD', 'no_emoji_max_font_size')
            min_font_size = config.get('WORD_CLOUD', 'no_emoji_min_font_size')
            font_colours = config.get('WORD_CLOUD', 'no_emoji_colour_map')
            bg_colour = config.get('WORD_CLOUD', 'no_emoji_bgcolour')
            # generate word cloud image without mask
            wc = WordCloud(font_path=font_file, max_font_size=max_font_size, min_font_size=min_font_size,
                           collocations=False, max_words=1000,
                           width=wc_image_size, height=wc_image_size, background_color=bg_colour, colormap=font_colours
                           ).generate(text_source)
        
        # set output image size
        plt.figure(figsize=[plt_figsize, plt_figsize])

        # if an emoji is specified, create colouring from the emoji image
        if emoji_img:
            image_colors = ImageColorGenerator(mask)
            plt.imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
        else:
            plt.imshow(wc)
        
        # save output image as png
        plt.axis("off")
        plt.savefig(filename, format="png", bbox_inches="tight", pad_inches=0)
        plt.close()

    except ValueError as ve:
        logger.debug(repr(ve))
        raise ValueError(config.get('WORD_CLOUD', 'msg_no_space_to_display_text'))
    except Exception as e:
        logger.error(repr(e))
        raise