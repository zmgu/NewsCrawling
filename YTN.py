from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import requests
from bs4 import BeautifulSoup
import pymysql
from datetime import datetime


def ytn():

    # MySQL 연결
    conn = pymysql.connect(host='xxx.xxx.xxx.xxx', user='tissue', password='xxxx', db='tissue_db', charset='utf8mb4')
    cur = conn.cursor()

    # selenium 기본 설정
    driver = webdriver.Chrome()

    # 최신 날짜 불러오기
    date_sql = 'SELECT DATE FROM NEWS_ARTICLES WHERE PRESS = "YTN" ORDER BY DATE DESC LIMIT 1'
    cur.execute(date_sql)
    ck = cur.fetchone()
    if ck is not None:
        already_date = ck[0]
    else:
        already_date = datetime.min
    conn.close()

    # 크롤링 데이터 리스트
    data_list = []

    # 이전 데이터 크롤링 완료 체크
    already_data = False

    for page in range(1, 32):
        if already_data is True:
            break

        url = f'https://www.ytn.co.kr/news/list.php?page={page}&mcd=0102'
        driver.implicitly_wait(10)
        driver.get(url)
        print(f'{page}페이지 이동')

        # 크롤링 시작
        news_list = driver.find_elements(By.CSS_SELECTOR, "#nav_content > div:nth-child(1) > ul")

        for news_article in news_list:
            for index in range(1, 32):
                try:
                    # 뉴스 리스트 URL 추출
                    href = news_article.find_element(
                        By.CSS_SELECTOR, f"li:nth-child({index}) > a").get_attribute("href")

                    # 이미지
                    try:
                        img_url = (news_article.find_element(
                            By.CSS_SELECTOR, f'li:nth-child({index}) > a > div.thumbwrap > div > div > img')
                                   .get_attribute("src"))
                    except NoSuchElementException:
                        img_url = ''

                    # 추출한 URL 크롤링 시작
                    resource = requests.get(href)
                    soup = BeautifulSoup(resource.text, 'html.parser')

                    # 날짜
                    date_str = driver.find_element(
                        By.CSS_SELECTOR, '#nav_content > div.wrap > div.li_1 > span.time').text
                    date = datetime.strptime(date_str, '%Y년 %m월 %d일 %H시 %M분')

                    # 이전 날짜 크롤링 중단
                    if date < already_date:
                        already_data = True
                        break

                    # 기사 제목
                    title = soup.select_one('#nav_content > div:nth-child(1) > h3').get_text()

                    # 본문
                    content_full = soup.select_one('#CmAdContent')
                    for tag in content_full.select('div, br'):
                        tag.decompose()
                    content = content_full.get_text('\n\n', strip=True)

                    # 크롤링 데이터 리스트
                    insert_list = [date, title, content, 'YTN', href, img_url]
                    data_list.append(insert_list)
                except NoSuchElementException:
                    continue

    driver.quit()

    return data_list
