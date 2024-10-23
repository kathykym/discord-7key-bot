import re
import logging
import utils.config_reader as config


def parse_arguments(num_of_usernames: int, arg_str: str) -> tuple[list[str], str, str, str, str, bool, bool]:
    logger = logging.getLogger(__name__)

    # values to be returned
    username_list = []
    mode = "SP"
    difficulty = "ALL"
    level = "ALL"
    keywords = ""
    flag_exact_keyword_match = False
    flag_display_score_percentage = False

    '''
        format of argument string:
            <optional flag: -%> <usernames (0..n)> <optional filters: mode|difficulty|level> <song title keywords>
        where
            mode = "SP" / "DP"
            difficulty = "B/N/H/A/L"
            level = 1-12
            song title keywords can be enclosed by double quotes to indicate an exact match
        
        samples of argument string:
        a) song title
        b) userA dp10 "exact song title"
        c) -% userA song title
        d) userA userB spa12 "exact song title"
    '''

    # 1) check if argument string is not empty
    if not arg_str:
        if num_of_usernames == 0:
            raise ValueError(config.get('IIDX', 'msg_empty_keyword'))
        else:
            raise ValueError(config.get('IIDX', 'msg_missing_args'))
    
    # 2) split the argument string into list of arguments
    arg_list = arg_str.split()

    # 3) check if any flag is indicated. ignore checking if there is only one argument as the flag is optional
    if (len(arg_list) > 1) and (arg_list[0] == "-%"):
        flag_display_score_percentage = True
        arg_list.pop(0)
    
    # 4) check the number of remaining arguments
    # there should be at least (num_of_usernames + 1) arguments, specifying usernames and song title keywords
    if len(arg_list) < num_of_usernames + 1:
        raise ValueError(config.get('IIDX', 'msg_missing_args'))

    # 5) check the format of usernames
    for i in range(0, num_of_usernames):
        if _is_valid_username_format(arg_list[0]):
            username_list.append(arg_list.pop(0))
        else:
            raise ValueError(config.get('IIDX', 'msg_invalid_username'))

    # 6) check if any chart filter (mode/difficulty/level) is specified
    # if more than one arguments remain and the first argument matches the pattern of chart filters,
    if (len(arg_list) > 1) and _is_valid_chart_filters_format(arg_list[0]):
        # parse the filters
        mode, difficulty, level = _parse_chart_filters(arg_list[0].upper())
        # and remove the first argument from list
        arg_list.pop(0)

    # 7) check if using exact match mode for song title keywords
    keywords = ' '.join(arg_list)
    if _is_enclosed_by_double_quotes(keywords):
        if re.match("^\s*$", keywords[1:-1]):
            raise ValueError(config.get('IIDX', 'msg_empty_keyword'))
        else:
            flag_exact_keyword_match = True

    # 8) contruct the query string of song title keyword
    keywords = _construct_keywords_query_string(keywords, flag_exact_keyword_match)

    logger.debug(f"Username: {username_list}")
    logger.debug(f"Mode: {mode}, Difficulty: {difficulty}, Level: {level}")
    logger.debug(f"Keywords: [{keywords}], Exact match: {flag_exact_keyword_match}")
    logger.debug(f"Display %: {flag_display_score_percentage}")

    # 9) return the command arguments
    return username_list, mode, difficulty, level, keywords, flag_exact_keyword_match, flag_display_score_percentage


def _is_valid_username_format(string: str) -> bool:
    is_valid_format = False
    
    # username should start with alphabet/number and contain no whitespaces
    if string and re.match("^[a-zA-Z|\d][^\s]*$", string):
        is_valid_format = True
    
    return is_valid_format


def _is_valid_chart_filters_format(string: str) -> bool:
    is_valid_format = False

    # format of chart filters = <SP/DP><B/N/H/A/L><1-12>
    # each block is optional and case-insensitive
    if re.search("^(SP|DP)?(B|N|H|A|L)?([1-9]|10|11|12)?$", string.upper()):
        is_valid_format = True
    
    return is_valid_format


def _parse_chart_filters(string: str) -> tuple[str, str, str]:
    # values to be returned
    mode = "SP"
    difficulty = "ALL"
    level = "ALL"

    filter_list = re.split("^(SP|DP)?(B|N|H|A|L)?([1-9]|10|11|12)?$", string.upper())
    if filter_list[1] is not None:
        mode = filter_list[1]
    if filter_list[2] is not None:
        difficulty = filter_list[2]
    if filter_list[3] is not None:
        level = filter_list[3]

    return (mode, difficulty, level)


def _is_enclosed_by_double_quotes(string: str) -> bool:
    is_enclosed = False

    # accept “ ” " as valid double quotes
    string = string.replace('“', '"', 0)
    string = string.replace('”', '"', 0)
    string = string.replace('“', '"', -1)
    string = string.replace('”', '"', -1)

    if len(string) > 1 and string.startswith('"') and string.endswith('"'):
        is_enclosed = True

    return is_enclosed


def _construct_keywords_query_string(keywords: str, flag_exact_match: bool) -> str:
    # if using exact match mode, remove the first and the last double quotes from keyword string
    if flag_exact_match:
        keywords = keywords[1:-1]
    # else add wildcard characters to keyword string
    else:
        keywords = keywords.replace("%", "\%")
        keywords = re.sub("\s+", "%", keywords)
    
    return keywords