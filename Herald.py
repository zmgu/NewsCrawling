from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import requests
from bs4 import BeautifulSoup
import pymysql
from datetime import datetime


def herald():

    # MySQL 연결
    conn = pymysql.connect(host='xxx.xxx.xxx.xxx', user='tissue', password='xxxx', db='tissue_db', charset='utf8mb4')
    cur = conn.cursor()

    # selenium 기본 설정
    driver = webdriver.Chrome()

    # 최신 날짜 불러오기
    date_sql = 'SELECT DATE FROM NEWS_ARTICLES WHERE PRESS = "헤럴드" ORDER BY DATE DESC LIMIT 1'
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

    for page in range(1, 1001):
        if already_data is True:
            break
        url = f'https://biz.heraldcorp.com/list.php?ct=010104000000&ctv=&np={page}'
        driver.implicitly_wait(10)
        driver.get(url)
        print(f'헤럴드 {page}페이지 이동')

        # 크롤링 시작
        news_list = driver.find_elements(
            By.CSS_SELECTOR, 'body > div > div.list_wrap > div.list_l > div.list > ul')

        for news_article in news_list:
            for index in range(1, 11):
                try:
                    # 뉴스 리스트 URL 추출
                    href = news_article.find_element(
                        By.CSS_SELECTOR, f'li:nth-child({index}) > a').get_attribute('href')

                    # 이미지
                    try:
                        img_url = (news_article.find_element(
                            By.CSS_SELECTOR, f'li:nth-child({index}) > a > div.list_img > img')
                                   .get_attribute('src'))
                    except NoSuchElementException:
                        img_url = ''

                    # 추출한 URL 크롤링 시작
                    resource = requests.get(href)
                    soup = BeautifulSoup(resource.text, 'html.parser')

                    # 날짜
                    date_str = driver.find_element(
                        By.CSS_SELECTOR, f'li:nth-child({index}) > div.l_date').text
                    date = datetime.strptime(date_str, '%Y.%m.%d %H:%M')

                    # 이전 날짜 크롤링 중단
                    if date < already_date:
                        already_data = True
                        break

                    # 기사 제목
                    title = soup.select_one(
                        'body > div.wrap > div.view_bg > div.view_area > div.article_wrap > div.article_top > ul > li.article_title.ellipsis2').get_text()

                    # 본문
                    content_full = soup.select_one('#articleText')
                    for tag in content_full.select('table, br'):
                        tag.decompose()
                    content = content_full.get_text('\n\n', strip=True)

                    # 크롤링 데이터 리스트
                    insert_list = [date, title, content, '헤럴드', href, img_url]
                    data_list.append(insert_list)
                except NoSuchElementException:
                    continue

    driver.quit()

    return data_list
