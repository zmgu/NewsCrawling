import time
import pymysql
from pymysql import IntegrityError
from YTN import ytn
from Hankyoreh import hankyoreh

# MySQL 연결
conn = pymysql.connect(host='xxx.xxx.xxx.xxxx', user='tissue', password='xxxx', db='tissue_db', charset='utf8mb4')
cur = conn.cursor()

if __name__ == "__main__":

    while True:
        commit_cnt = 0
        data_list = [[] for _ in range(0)]

        data_list += hankyoreh()

        data_list = sorted(data_list, key=lambda x: x[0])
        for data in data_list:
            try:
                # DB에 저장
                sql = ('INSERT INTO NEWS_ARTICLES(DATE, TITLE, CONTENT, PRESS, URL, IMG_URL) '
                       'VALUES(%s, %s, %s, %s, %s, %s)')
                cur.execute(sql, data)
                commit_cnt += 1

            except IntegrityError as e:
                if e.args[0] == 1062:  # MySQL 에러 코드 1062인 경우 처리
                    continue

            conn.commit()
        print(f'{commit_cnt}개 커밋 완료')
        time.sleep(3600)

conn.close()
