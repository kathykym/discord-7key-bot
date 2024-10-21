from bs4 import BeautifulSoup
import re
import requests
import logging
import utils.config_reader as config
from commands.iidxme.classes.Song import Song
from commands.iidxme.classes.PbInfo import PbInfo


def fetch_last_play_version(request_session: requests.Session, username: str) -> str:
    logger = logging.getLogger(__name__)
    
    # 'c' = current version
    last_play_version = 'c'
    
    try:
        # send a GET request and parse the response content
        url = f"https://iidx.me/c/{username}"
        response = request_session.get(url, params='content')

        status_code = response.status_code
        # case 1: 200 OK
        if status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml', from_encoding='utf-8')
            h2_title = soup.select_one('h2')
            # user exists but no play data in current version
            if h2_title and re.search("VERSION DATA NOT FOUND", h2_title.get_text()):
                # get last play version and return the value
                li_version = soup.select_one("ul > li")
                last_play_version = re.search("^\d+", str(li_version.get_text())).group()
        # case 2: 400 bad request due to username not found
        elif status_code == 400:
            raise ValueError(config.get('IIDX', 'msg_user_not_found'))
        # case 3: other status code due to server issues
        else:
            raise Exception(config.get('IIDX', 'msg_iidxme_conn_failed'))
            
        return last_play_version
        
    except requests.exceptions.RequestException as e:
        logger.error(repr(e))
        raise Exception(config.get('IIDX', 'msg_iidxme_conn_failed'))
    except ValueError as ve:
        logger.debug(repr(ve))
        raise
    except (KeyError, AttributeError) as e:
        logger.error(repr(e))
        raise Exception(config.get('IIDX', 'msg_parse_page_error'))


def fetch_pb_records(request_session: requests.Session, username:str, last_play_ver: str, song_list: list[Song]) -> dict[str, PbInfo]:
    logger = logging.getLogger(__name__)

    chart_pb_dict = {}

    try:
        for song in song_list:
            # fetch the song page content: send a GET request and parse the response content
            url = f"https://iidx.me/{last_play_ver}/{username}/music/{song.song_id}"
            response = request_session.get(url, params='content')

            if response.status_code == 200:
                logger.debug(f"fetching {url}")
                logger.debug(f"-- song id: {song.song_id} / {song.title}")

                song_page_content = BeautifulSoup(response.content, 'lxml', from_encoding='utf-8')

                for chart in song.charts:
                    logger.debug(f"-- chart id: {chart.chart_id} / {chart.difficulty}")

                    # extract personal best info of current chart from song page content and add to the result dictionary
                    chart_pb_dict[chart.chart_id] = _extract_pb_info_of_chart(chart.chart_id, song_page_content)
            else:
                raise Exception(config.get('IIDX', 'msg_iidxme_conn_failed'))

        return chart_pb_dict
        
    except requests.exceptions.RequestException as e:
        logger.error(repr(e))
        raise Exception(config.get('IIDX', 'msg_iidxme_conn_failed'))
    except Exception as e:
        raise


def _extract_pb_info_of_chart(chart_id: str, page_content: BeautifulSoup) -> PbInfo:
    logger = logging.getLogger(__name__)

    # PB info to be returned
    pb_lamp = "--"
    pb_score = -1
    pb_score_attained_version = ""
    pb_rank = "?"
    pb_rank_diff = ""
    pb_rate = "?"
    pb_misscount = 9999

    try:
        # get the div object of the chart and extract PB info
        div_chart_data = page_content.find('div', attrs={'name': f"tabview_{chart_id}"})

        # 1) find all div objects containing the clear lamp info
        div_td_clear = div_chart_data.find_all('div', class_="div_td clear")
        for td in div_td_clear:
            # get the best clear lamp, which can be found in the most recent record
            if td.get_text() != "":
                pb_lamp = config.get('IIDX', f"abbr_{td.get_text()}")
                break

        # 2) find all div objects containing the score info
        # loop through the table containing score history
        div_tr_hist = div_chart_data.find('div', class_="table_scrollcol music").find_all('div', class_="div_tr")
        pb_row = -1
        for idx, div_row in enumerate(div_tr_hist):
            p_score = div_row.find('p', class_="score")
            
            if p_score and re.search("^[0-9]+$", p_score.get_text()):
                # get the best score, rank and score rate
                if int(p_score.get_text()) > pb_score:
                    pb_row = idx
                    pb_score = int(p_score.get_text())
                    pb_rank = p_score.find_previous('p', class_="rank").get_text()
                    span_rank_diff = p_score.find_next("span", "pri_border")
                    if span_rank_diff:
                        pb_rank_diff = f"{span_rank_diff.get_text().lstrip()}"
                    pb_rate = p_score.find_next('div', class_="rate_wrapper").get_text()
                # if there is a tie for best score, update pb_row index to display earlier release version title
                elif int(p_score.get_text()) == pb_score:
                    pb_row = idx

        if pb_row != -1:
            # from the table containing release version titles,
            div_tr_ver = div_chart_data.find('div', class_="table_fixcol music").find_all('div', class_="div_tr")
            # get the version in which the best score was attained
            span_ver = div_tr_ver[pb_row].find('span', class_="short")
            if span_ver and span_ver.get_text():
                pb_score_attained_version = span_ver.get_text().split(" ")[-1]
            
        # 3) find all div objects containing the miss count
        span_miss = div_chart_data.find_all('span', class_="miss")
        for span in span_miss:
            # get the lowest miss count
            if re.search("^[0-9]+$", span.get_text()) and (int(span.get_text()) < pb_misscount):
                pb_misscount = int(span.get_text())

        return PbInfo(pb_lamp, pb_score, pb_score_attained_version, pb_rank, pb_rank_diff, pb_rate, pb_misscount)
    
    except (KeyError, AttributeError) as e:
        logger.error(repr(e))
        raise Exception(config.get('IIDX', 'msg_parse_page_error'))
    except Exception as e:
        logger.error(repr(e))
        raise Exception(config.get('IIDX', 'msg_generic_error'))