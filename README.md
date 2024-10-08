
# 💿🎹 7-Key Discord Bot 🎹💿

This bot is designed to enhance the Discord experience for a rhythm game community in Hong Kong by providing useful commands to track personal best records in the rhythm game [Beatmania IIDX](https://p.eagate.573.jp/game/2dx/) and creating fun interactions among server members.

## Commands
### 🎵 Game Related Commands

> **$iidxpb**

![bot_iidxpb](https://github.com/user-attachments/assets/f0391c38-a577-4120-8323-9b545a8aa321)

Retrieves the all-time personal best scores, clear lamp and miss count of specific song charts for the given user. Play data is retrieved from [iidx.me](https://iidx.me/).

Usage: ``$iidxpb <username> <mode><difficulty><level> <song_title_keywords>``

  * ``<username>`` = Username on iidx.me.
  * ``<mode>`` _(optional)_ = Play mode: ``SP`` for single play, ``DP`` for double play. Default is set to ``SP``.
  * ``<difficulty>`` _(optional)_ = Difficulty of song chart: ``B`` for beginner, ``N`` for normal, ``H`` for hyper, ``A`` for another, ``L`` for leggendaria.
  * ``<level>`` _(optional)_ = Level of song chart: ``1``-``12``.
  * ``<song_title_keywords>`` = Keywords of the song title.

_All arguments are case-insensitive._

> **$iidxsr**

![bot_iidxsr](https://github.com/user-attachments/assets/2007cfec-8e13-4b9d-9d74-b745b46d743a)

Retrieves the scores required for the ranks AAA-, AAA, MAX- and MAX of specific song charts. 

Usage: ``$iidxsr <mode><difficulty><level> <song_title_keywords>``

  * ``<mode>`` _(optional)_ = Play mode: ``SP`` for single play, ``DP`` for double play. Default is set to ``SP``.
  * ``<difficulty>`` _(optional)_ = Difficulty of song chart: ``B`` for beginner, ``N`` for normal, ``H`` for hyper, ``A`` for another, ``L`` for leggendaria.
  * ``<level>`` _(optional)_ = Level of song chart: ``1``-``12``.
  * ``<song_title_keywords>`` = Keywords of the song title.

_All arguments are case-insensitive._

### 📜 Misc Commands

> **$wordcloud**

![bot_wordcloud](https://github.com/user-attachments/assets/c268f469-4c67-4937-8491-5ec2af5e8d15)

Generates a word cloud from the message history in the channel.

Usage: ``$wordcloud <emoji> <server_member>``

  * ``<emoji>`` _(optional)_ = Emoji character. The specified emoji will be used as the mask for the word cloud.
  * ``<server_member>`` _(optional)_ = Discord user tag. Only the messages posted by the specified server member will be used to generate the word cloud.

> **$volume**

![bot_volume](https://github.com/user-attachments/assets/2f1c93c4-e35e-4cf0-bb15-bd3a2c10cf72)

Adjusts the probability that the bot sends a comment after an image is posted in a score-posting channel.

Usage: ``$volume <bot_volume>``

  * ``<bot_volume>`` = User volume of the bot: ``0``-``200``.

## ✨ Other Features

> **Follow suit**

![bot_followsuit](https://github.com/user-attachments/assets/38912b2f-a091-42c2-bd00-8c24a6e047d1)

When the same message is sent by three server members consecutively, the bot will echo that message.

## 🙇🏻‍♀️ Credits

> **iidx.me** - https://iidx.me/

The site from which the bot retrieves all-time play data for Beatmania IIDX.

> **NaikaiFont** - https://github.com/max32002/naikaifont

The font used to generate word clouds with Chinese characters.

<br />

AND special thanks to the Discord community for their support and feedback!
