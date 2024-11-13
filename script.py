#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
from flask import Flask, send_from_directory, jsonify

app = Flask(__name__)


class EventScraper:
    def __init__(self, url):
        self.url = url
        self.current_year = datetime.now().year
        self.last_fetch_time = datetime.min

    def fetch_events(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            events = [
                self.process_event(item)
                for item in soup.select(".squares-events .event_item")
            ]
            self.last_fetch_time = datetime.now()
            return [event for event in events if event]
        else:
            print(f"Request failed, status code: {response.status_code}")
            return []

    def process_event(self, item):
        link = item.select_one(".msl_event_name")
        time_str = item.select_one(".msl_event_time").get_text()
        location = item.select_one(".msl_event_location").get_text()
        description = item.select_one(".msl_event_description").get_text()
        types = [x.get_text() for x in item.select(".msl_event_types a")]

        if link and link.get("href"):
            full_url = urljoin(self.url, link.get("href"))
            start_datetime, end_datetime = self.parse_time(time_str)
            dtstamp = start_datetime.strftime("%Y%m%dT%H%M%SZ")
            dtstart = start_datetime.strftime("%Y%m%dT%H%M%S")
            dtend = end_datetime.strftime("%Y%m%dT%H%M%S")
            ics_event = self.create_ics_event(
                types,
                description,
                full_url,
                dtstart,
                dtend,
                dtstamp,
                location,
                link.get_text(),
            )
            print(f"{time_str}: {link.get_text()}")
            self.write_to_file(ics_event, link.get_text())

            return ics_event

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

        return datetime(
            self.current_year,
            datetime.strptime(month, "%B").month,
            int(day),
            hour,
            minute,
            second,
        )

    def parse_single_time(self, dt_str):
        # Separate AM/PM
        period = ""
        if "am" in dt_str.lower() or "pm" in dt_str.lower():
            period = dt_str[-2:]  # Get AM/PM
            time_part = dt_str[:-2].strip()  # Remove AM/PM
        else:
            time_part = dt_str.strip()

        time_components = time_part.split(":")
        hour = int(time_components[0])
        minute = int(time_components[1]) if len(time_components) > 1 else 0
        second = int(time_components[2]) if len(time_components) > 2 else 0

        # Handle AM/PM
        if period.lower() == "pm" and hour != 12:
            hour += 12
        elif period.lower() == "am" and hour == 12:
            hour = 0

        return hour, minute, second

    def create_ics_event(
        self, types, description, full_url, dtstart, dtend, dtstamp, location, summary
    ):
        return f"""BEGIN:VEVENT
CATEGORIES:{', '.join(types)}
DESCRIPTION:{description}\\n\\n{full_url}
DTEND:{dtend}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
LOCATION:{location}
SUMMARY:{summary}
UID:{full_url}
URL:{full_url}
END:VEVENT
"""

    def sanitize_filename(self, name):
        return re.sub(r'[<>:"/\\|?*]', "_", name)

    def write_to_file(self, ics_event, summary):
        directory = "events"
        os.makedirs(directory, exist_ok=True)

        filename = f"{self.sanitize_filename(summary)}.ics"
        file_path = os.path.join(directory, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(ics_event)

    def create_icalendar_file(self):
        events_dir = "events"
        output_file = "output.ics"

        ical_content = "BEGIN:VCALENDAR\nVERSION:2.0\nX-WR-CALNAME:UoBD Events\n"
        ical_content += self.get_timezone_info()

        if os.path.isdir(events_dir):
            for entry in os.listdir(events_dir):
                if entry.endswith(".ics"):
                    with open(os.path.join(events_dir, entry)) as f:
                        ical_content += f.read()

        ical_content += "END:VCALENDAR\n"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(ical_content)

        return output_file

    def get_timezone_info(self):
        return """BEGIN:VTIMEZONE
TZID:Arabian Standard Time
X-LIC-LOCATION:Asia/Dubai
BEGIN:STANDARD
RRULE:FREQ=YEARLY;BYDAY=1TH;BYMONTH=1
TZNAME:+04
TZOFFSETFROM:+0500
TZOFFSETTO:+0400
END:STANDARD
END:VTIMEZONE
"""


scraper = EventScraper("https://dubaievents.bham.ac.uk/whatson/")


@app.route("/", methods=["GET"])
def main_route():
    if (datetime.now() - scraper.last_fetch_time) > timedelta(minutes=5):
        scraper.fetch_events()

    output_file = scraper.create_icalendar_file()
    return send_from_directory(".", output_file, as_attachment=True)


@app.route("/fetch", methods=["GET"])
def fetch_events_route():
    events = scraper.fetch_events()
    if events:
        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"Fetched {len(events)} events.",
                    "events": events,
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "No events fetched or there was an error.",
                }
            ),
            500,
        )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        app.run(host="0.0.0.0", port=5000)
    else:
        scraper.fetch_events()
