import pymysql
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from pymysql import IntegrityError
import requests
from bs4 import BeautifulSoup
from datetime import datetime


def hankyoreh():
    # selenium 기본 설정
    driver = webdriver.Chrome()

    # MySQL 연결
    conn = pymysql.connect(host='xxx.xxx.xxx.xxx', user='tissue', password='xxxx', db='tissue_db', charset='utf8mb4')
    cur = conn.cursor()

    # 최신 날짜 불러오기
    date_sql = 'SELECT DATE FROM NEWS_ARTICLES WHERE PRESS = "한겨레" ORDER BY DATE DESC LIMIT 1'
    cur.execute(date_sql)
    ck = cur.fetchone()
    if ck is not None:
        already_date = ck[0]
    else:
        already_date = datetime.min
    conn.close()

    # 이전 데이터 크롤링 완료 체크
    already_data = False

    # 크롤링 데이터 리스트
    data_list = []

    for page in range(1, 61):
        if already_data is True:
            break

        url = f'https://www.hani.co.kr/arti/economy/economy_general/list{page}.html'
        driver.implicitly_wait(15)
        driver.get(url)

        # 크롤링 시작
        for index in range(2, 17):
            if page == 1 and index == 2:  # 가장 최근에 올라온 기사 날짜 태크 에러 제외
                continue
            try:
                if index == 2:
                    a_tag = driver.find_element(
                        By.CSS_SELECTOR,
                        '#section-left-scroll-in > div.section-list-area > div.list.first > div > span > a')
                else:
                    a_tag = driver.find_element(
                        By.CSS_SELECTOR,
                        f'#section-left-scroll-in > div.section-list-area > div:nth-child({index}) > div > span > a')

                href = a_tag.get_attribute('href')
                resource = requests.get(href)
                soup = BeautifulSoup(resource.text, 'html.parser')

                # 이미지
                try:
                    img_url = (driver.find_element(
                        By.CSS_SELECTOR, f'#section-left-scroll-in > div.section-list-area > div:nth-child({index}) > div > span > a > img')
                               .get_attribute('src'))
                except NoSuchElementException:
                    img_url = ''

                # 날짜
                date_str = soup.select_one('#article_view_headline > p.date-time > span:nth-child(1)')
                for tag in date_str.select('em'):
                    tag.decompose()
                date_str = date_str.get_text(strip=True)
                date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')

                # 이전 날짜 크롤링 중단
                if date < already_date:
                    already_data = True
                    break

                # 기사 제목
                title = soup.select_one('#article_view_headline > h4 > span').get_text()

                # 본문
                content_full = soup.select_one('#a-left-scroll-in > div.article-text > div > div.text')
                for tag in content_full.select('div, a'):
                    tag.decompose()
                content = content_full.get_text('\n\n', strip=True)

                # 크롤링 데이터 리스트
                insert_list = [date, title, content, '한겨레', href, img_url]
                data_list.append(insert_list)
            except NoSuchElementException:  # 태그 못 찾는 경우 예외
                continue
            except AttributeError:  # 사진만 있는 기사
                continue
            except IntegrityError:
                continue

    driver.quit()

    return data_list
