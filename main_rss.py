import os
import re
from datetime import timedelta, datetime

import feedparser
import requests

# BAD_COUNTRIES = os.environ["BAD_COUNTRIES"].split(",")
# TIME_IN_PAST = timedelta(minutes=int(os.environ["TIME_IN_PAST"]))
# MIN_BUDGET = int(os.environ["MIN_BUDGET"])
# MIN_RANGE_FROM = int(os.environ["MIN_RANGE_VALUE"])
# MAX_RANGE_FROM = int(os.environ["MAX_RANGE_VALUE"])
# #SEARCH_QUERIES = os.environ["SEARCH_QUERIES"].split(",")
# SEARCH_QUERIES = ["data engineer", "airflow"]

TELEGRAM_TOKEN='5531011071:AAGWFFKwFZF0LI4KIA_81GApPzguubXr3ZY'
TELEGRAM_CHAT_ID=[5228302997, 406962410]
BAD_COUNTRIES=['India']
TIME_IN_PAST=timedelta(minutes=1)
MIN_BUDGET=100
MIN_RANGE_VALUE=15
MAX_RANGE_VALUE=35
SEARCH_QUERIES = ["data engineer", "airflow", "scrapy", "terraform"]

def send_msg(text):
    token = TELEGRAM_TOKEN
    chat_id = TELEGRAM_CHAT_ID

    for _id in chat_id:

        url_req = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={_id}&text={text}"
        requests.get(url_req)


def parse(query):
    query = query.replace(' ', '&20')
    feed = feedparser.parse(f"https://www.upwork.com/ab/feed/jobs/rss?q={query}&sort=recency")

    budget = 0
    min_range_value = 0

    for entry in feed.entries:
        article_title = entry.title
        article_desc = entry.description
        country = re.findall('Country<\/b>:(.+)', article_desc)
        if country:
            country = country[0].strip()
        else:
            country = ''


        if country in BAD_COUNTRIES:
            print(f"skipping {article_title}, because of {country}")
            continue

        job_dt = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S +0000')
        if job_dt < datetime.now() - TIME_IN_PAST:
            print(f" skipping because {job_dt} are yearlier then {datetime.now() - TIME_IN_PAST}")
            continue

        print(job_dt)
        if re.search("Budget<br />", article_desc):
            budget = re.findall('Budget<br \/>\n\$(\d+).+\$(\d+)', article_desc)
            budget_min = int(budget[0][0].replace(',', ''))
            if budget_min < MIN_BUDGET:
                print(f"Because budget is lower than {MIN_BUDGET}")
                continue
        elif re.search("Budget<b>;", article_desc):
            budget = re.findall('Budget<\/b>: \$([\d,]+)', article_desc)
            budget_min = int(budget[0].replace(',', ''))
            if budget_min < MIN_BUDGET:
                print(f"Because budget is lower than {MIN_BUDGET}")
                continue
        elif re.search("Hourly Range", article_desc):
            min_range_value, max_range_value = re.findall('Hourly Range<\/b>: \$(\d+)\.00-\$(\d+)\.', article_desc)[0]
            if int(min_range_value) < MIN_RANGE_VALUE or int(max_range_value) < MAX_RANGE_VALUE:
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
