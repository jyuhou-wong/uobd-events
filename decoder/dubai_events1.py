#!/usr/bin/python
# -*- coding: utf-8 -*-
import pytz
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta


class EventFetcher:
    def __init__(self, url="https://www.birmingham.ac.uk/dubai/events"):
        self.url = url
        self.current_year = datetime.now().year

    def fetch_events(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            events = [self.process_event(item) for item in soup.select("article.event")]
            return events
        else:
            print(f"Request failed, status code: {response.status_code}")
            return []

    def process_event(self, item):
        # 获取链接和名称
        link = item.select_one("a:nth-child(1)")
        name = link.get_text()

        # 初始化一个字典来存储提取的信息
        event_info = {"name": name, "full_url": urljoin(self.url, link.get("href"))}

        # 查找所有 dt 标签
        dt_tags = item.find_all("dt")

        # 遍历 dt 标签，提取需要的信息
        for dt in dt_tags:
            dt_text = dt.get_text()
            dd = dt.find_next_sibling("dd")
            if dd:
                dd_text = dd.get_text()
                # 将信息存储到字典中
                event_info[dt_text] = dd_text

        time_str = event_info.get("Dates", "")

        dtstart, dtend = self.parse_time(time_str)

        ics_event = self.create_ics_event(
            event_info.get("Description", ""),
            event_info["full_url"],
            dtstart,
            dtend,
            event_info.get("Location", ""),
            name,
        )

        return [name, ics_event]

    def parse_time(self, time_str):
        # 定义时区
        local_tz = pytz.timezone("Etc/GMT-4")  # GMT-4 对应 UTC+4
        utc_tz = pytz.utc

        # 处理时间范围
        if " - " in time_str:
            # 处理带有范围的时间字符串
            parts = time_str.split(" - ")
            start_part = parts[0].strip()
            end_part = parts[1].strip()

            # 处理开始时间
            if len(start_part.split()) == 4:  # 例如: "Thursday 14 November (00:00)"
                # 没有年份，使用结束时间的年份
                end_year = int(end_part.split()[3])  # 获取结束时间的年份
                start_dt = datetime.strptime(
                    start_part + f" {end_year}", "%A %d %B (%H:%M) %Y"
                )
            else:
                start_dt = datetime.strptime(start_part, "%A %d %B %Y (%H:%M)")

            start_dt = local_tz.localize(start_dt)  # 本地化到 GMT-4

            # 处理结束时间
            if len(end_part.split()) == 5:  # 例如: "Friday 20 December 2024 (23:59)"
                end_dt = datetime.strptime(end_part, "%A %d %B %Y (%H:%M)")
            else:  # 只有日期和时间，没有年份
                end_dt = datetime.strptime(end_part, "%A %d %B (%H:%M)")
                end_dt = end_dt.replace(year=start_dt.year)  # 使用开始时间的年份

            end_dt = local_tz.localize(end_dt)  # 本地化到 GMT-4

        else:
            # 处理单个时间
            if "(" in time_str and "-" in time_str:
                dt_part, time_range = time_str.split(" (")
                start_time_str, end_time_str = time_range[:-1].split("-")
                dt = datetime.strptime(dt_part.strip(), "%A %d %B %Y")
                start_dt = datetime.combine(
                    dt.date(), datetime.strptime(start_time_str.strip(), "%H:%M").time()
                )
                end_dt = datetime.combine(
                    dt.date(), datetime.strptime(end_time_str.strip(), "%H:%M").time()
                )

                start_dt = local_tz.localize(start_dt)  # 本地化到 GMT-4
                end_dt = local_tz.localize(end_dt)  # 本地化到 GMT-4

        # 转换为 UTC
        start_dt = start_dt.astimezone(utc_tz)
        end_dt = end_dt.astimezone(utc_tz)

        # 格式化为 %Y%m%dT%H%M%SZ
        dtstart = start_dt.strftime("%Y%m%dT%H%M%SZ")
        dtend = end_dt.strftime("%Y%m%dT%H%M%SZ")

        return dtstart, dtend

    def create_ics_event(
        self, description, full_url, dtstart, dtend, location, summary
    ):
        return f"""BEGIN:VEVENT
DESCRIPTION:{description}\\n\\n{full_url}
DTEND:{dtend}
DTSTART:{dtstart}
LOCATION:{location}
SUMMARY:{summary}
UID:{full_url}
URL:{full_url}
END:VEVENT
"""


if __name__ == "__main__":
    EventFetcher().fetch_events()
