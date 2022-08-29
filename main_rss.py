import os
import re
from datetime import timedelta, datetime

import feedparser
import requests

BAD_COUNTRIES = os.environ["BAD_COUNTRIES"].split(",")
TIME_IN_PAST = timedelta(minutes=int(os.environ["TIME_IN_PAST"]))
MIN_BUDGET = int(os.environ["MIN_BUDGET"])
MIN_RANGE_FROM = int(os.environ["MIN_RANGE_VALUE"])
MAX_RANGE_FROM = int(os.environ["MAX_RANGE_VALUE"])
#SEARCH_QUERIES = os.environ["SEARCH_QUERIES"].split(",")
SEARCH_QUERIES = ["data engineer", "airflow"]

def send_msg(text):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url_req = "https://api.telegram.org/bot" + token + "/sendMessage" + "?chat_id=" + chat_id + "&text=" + text
    requests.get(url_req)


def parse(query):
    query = query.replace(' ', '&20')
    feed = feedparser.parse(f"https://www.upwork.com/ab/feed/jobs/rss?q={query}&sort=recency")

    budget = 0
    min_range_value = 0

    for entry in feed.entries:
        article_title = entry.title
        article_desc = entry.description
        country = re.findall('Country<\/b>:(.+)', article_desc)[0].strip()

        if country in BAD_COUNTRIES:
            print(f"skipping {article_title}, because of {country}")
            continue

        job_dt = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S +0000')
        if job_dt < datetime.now() - TIME_IN_PAST:
            print(f" skipping because {job_dt} are yearlier then {datetime.now() - TIME_IN_PAST}")
            continue

        print(job_dt)
        if re.search("Budget", article_desc):
            budget = int(re.findall('Budget<\/b>:\s\$(.+)', article_desc)[0].replace(",", ""))
            if int(budget) < MIN_BUDGET:
                print(f"Because budget is lower than {MIN_BUDGET}")
                continue
        elif re.search("Hourly Range", article_desc):
            min_range_value, max_range_value = re.findall('Hourly Range<\/b>: \$(\d+)\.00-\$(\d+)\.', article_desc)[0]
            if int(min_range_value) < MIN_RANGE_FROM or int(max_range_value) < MAX_RANGE_FROM:
                print(f"skipping because hourly range)\n")

                continue
        skills = ', '.join(re.findall('Skills<\/b>:(.+)<br', article_desc)[0].strip().split(",                     "))
        title = article_title.split(' - Upwork')[0].strip()
        country = re.findall('Country<\/b>:(.+)', article_desc)[0].strip()
        link = re.findall('a href="(.+)"', article_desc)[0].strip()

        if min_range_value:
            print(
                f"{title}\nSkills: {skills}\nCountry: {country}\nHourly Range: {min_range_value}$-{max_range_value}$\n{link}\n")
            send_msg(
                f"{title}\nSkills: {skills}\nCountry: {country}\nHourly Range: {min_range_value}$-{max_range_value}$\n{link}\n")
            min_range_value, max_range_value = None, None

        elif budget:
            print(f"{title}\nSkills: {skills}\nCountry: {country}\nBudget: {budget}$\n{link}\n")
            send_msg(f"{title}\nSkills: {skills}\nCountry: {country}\nBudget: {budget}$\n{link}\n")


def main():
    for query in SEARCH_QUERIES:
        parse(query)


if __name__ == '__main__':
    main()
