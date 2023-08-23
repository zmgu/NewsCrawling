from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
import pymysql
from datetime import datetime


def moneyToday():
    # MySQL 연결
    conn = pymysql.connect(host='xxx.xxx.xxx.xxx', user='tissue', password='xxxx', db='tissue', charset='utf8mb4')
    cur = conn.cursor()

    # selenium 기본 설정
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    # 최신 데이터 날짜
    date_sql = 'SELECT DATE FROM NEWS_ARTICLES WHERE PRESS = "머니투데이" ORDER BY DATE DESC LIMIT 1'
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

    for page in range(1, 5):
        if already_data is True:
            break

        url = f'https://news.mt.co.kr/newsList.html?type=1&comd=&pDepth=news&pDepth1=politics&pDepth2=Ptotal&page={page}'
        driver.get(url)
        print(f'머니투데이 {page}페이지 이동')

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#content > ul > li')))
        except TimeoutException:
            continue

        news_list = driver.find_elements(
            By.CSS_SELECTOR, '#content > ul')

        for news_article in news_list:
            for index in range(1, 21):
                try:
                    # 뉴스 리스트 URL 추출
                    href = news_article.find_element(
                        By.CSS_SELECTOR, f'li:nth-child({index}) > a').get_attribute('href')

                    # 이미지
                    try:
                        img_url = (news_article.find_element(
                            By.CSS_SELECTOR, f'li:nth-child({index}) > a > img').get_attribute('src'))
                    except NoSuchElementException:
                        img_url = ''

                    # BeautifulSoup
                    resource = requests.get(href)
                    soup = BeautifulSoup(resource.text, 'html.parser')

                    # 날짜
                    date_str = driver.find_element(
                        By.CSS_SELECTOR, f'li:nth-child({index}) > div > p > span').text
                    date_str = date_str[-16:]
                    date = datetime.strptime(date_str, '%Y.%m.%d %H:%M')

                    # 이전 날짜 크롤링 중단
                    if date < already_date:
                        already_data = True
                        break

                    # 기사 제목
                    title = driver.find_element(By.CSS_SELECTOR, f'li:nth-child({index}) > div > strong > a').text

                    # 본문
                    content_full = soup.select_one('#textBody')
                    for tag in content_full.select('table, br, div'):
                        tag.decompose()
                    content = content_full.get_text('\n\n', strip=True)

                    # 크롤링 데이터 리스트
                    insert_list = [date, title, content, '머니투데이', href, img_url]
                    data_list.append(insert_list)

                except NoSuchElementException:
                    continue

    driver.quit()

    return data_list
