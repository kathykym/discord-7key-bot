import re
import logging
from discord import Guild
import db.iidxme_db_helper as iidxme_db


def escape_special_formatting_characters(string: str) -> str:
    string = string.replace("_", "\_")
    string = string.replace("*", "\*")
    return string


# convert traditional chinese characters in input string to kanji
def convert_chi_to_kanji(string: str) -> str:
    for char in string:
        converted_char = iidxme_db.get_kanji_by_char(char)
        if converted_char:
            string = string.replace(char, converted_char)

    return string