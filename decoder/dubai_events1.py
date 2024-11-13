#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime


class EventFetcher:
    def __init__(self, url="https://www.birmingham.ac.uk/dubai/events"):
        self.url = url
        self.current_year = datetime.now().year

    def fetch_events(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            event_urls = [
                [item.get_text(), urljoin(self.url, item.get("href") + "?ical=true")]
                for item in soup.select("article.event a:nth-child(1)")
            ]

            events = [
                [name, self.process_event(response.text)]
                for name, response in [
                    [name, requests.get(url)] for name, url in event_urls
                ]
                if response.status_code == 200
            ]

            return events
        else:
            print(f"Request failed, status code: {response.status_code}")
            return []

    def process_event(self, item):
        match = re.search(r"BEGIN:VEVENT.*END:VEVENT", item, re.DOTALL | re.I)
        if match is not None:
            event = re.sub(
                r"(DTSTART:\w*|DTEND:\w*)Z", r"\1", match.group(), flags=re.I
            )
        return event
