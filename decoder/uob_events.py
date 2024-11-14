#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytz
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta


class EventFetcher:
    def __init__(
        self,
        url,
        timezone,
        online_only=False,
    ):
        self.url = url
        self.timezone = timezone
        self.online_only = online_only
        self.current_year = datetime.now().year

    def fetch_events(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            events = []
            for item in soup.select(".squares-events .event_item"):
                event = self.process_event(item)
                if event:
                    events.append(event)
            return events
        else:
            print(f"Request failed, status code: {response.status_code}")
            return []

    def process_event(self, item):
        link = item.select_one(".msl_event_name")
        name = link.get_text()
        time_str = item.select_one(".msl_event_time").get_text()
        location = item.select_one(".msl_event_location").get_text()
        description = item.select_one(".msl_event_description").get_text()
        types = [x.get_text() for x in item.select(".msl_event_types a")]

        if self.online_only and location != "Online":
            return

        if link and link.get("href"):
            full_url = urljoin(self.url, link.get("href"))

        start_datetime, end_datetime = self.parse_time(time_str)
        dtstart = start_datetime.strftime("%Y%m%dT%H%M%SZ")
        dtend = end_datetime.strftime("%Y%m%dT%H%M%SZ")
        ics_event = self.create_ics_event(
            types, description, full_url, dtstart, dtend, location, name
        )

        return [name, ics_event]

    def parse_time(self, time_str):
        start_time_str, end_time_str = time_str.split(" - ")
        day, month, start_time_part = start_time_str.split(" ")

        start_datetime = self.convert_to_datetime(day, month, start_time_part)
        end_datetime = self.convert_to_datetime(day, month, end_time_str)

        # Adjust for overnight events
        if end_datetime < start_datetime:
            end_datetime += timedelta(days=1)

        return start_datetime, end_datetime

    def convert_to_datetime(self, day, month, time_part):
        day = "".join(filter(str.isdigit, day))  # Keep only digits
        month = month.strip()  # Keep month as is

        hour, minute, second = self.parse_single_time(time_part.strip())

        # Create a naive datetime (without timezone)
        naive_datetime = datetime(
            self.current_year,
            datetime.strptime(month, "%B").month,
            int(day),
            hour,
            minute,
            second,
        )

        local_tz = pytz.timezone(self.timezone)
        localized_datetime = local_tz.localize(naive_datetime)

        # Convert to UTC
        utc_datetime = localized_datetime.astimezone(pytz.utc)

        return utc_datetime

    def parse_single_time(self, dt_str):
        # Separate AM/PM
        period = ""
        if "am" in dt_str.lower() or "pm" in dt_str.lower():
            period = dt_str[-2:]  # Get AM/PM
            time_part = dt_str[:-2].strip()  # Remove AM/PM
        else:
            time_part = dt_str.strip()

        time_components = time_part.split(":")
        hour = int(time_components[0]) if time_components[0] != "noon" else 12
        minute = int(time_components[1]) if len(time_components) > 1 else 0
        second = int(time_components[2]) if len(time_components) > 2 else 0

        # Handle AM/PM
        if period.lower() == "pm" and hour != 12:
            hour += 12
        elif period.lower() == "am" and hour == 12:
            hour = 0

        return hour, minute, second

    def create_ics_event(
        self, types, description, full_url, dtstart, dtend, location, summary
    ):
        return f"""BEGIN:VEVENT
CATEGORIES:{', '.join(types)}
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
    EventFetcher(
        "https://studentevents.bham.ac.uk/whatson/", "Europe/London", True
    ).fetch_events()
    EventFetcher(
        "https://dubaievents.bham.ac.uk/whatson/", "Asia/Dubai", False
    ).fetch_events()
