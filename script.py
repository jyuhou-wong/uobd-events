#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import sys
from datetime import datetime, timedelta
from flask import Flask, send_from_directory, jsonify
import threading
import time

from decoder import uob_events, dubai_events1

app = Flask(__name__)


class EventScraper:
    def __init__(self):
        self.last_fetch_time = datetime.min

    def fetch_events(self):
        events = [
            *uob_events.EventFetcher(
                "https://studentevents.bham.ac.uk/whatson/", "Europe/London", True
            ).fetch_events(),
            *uob_events.EventFetcher(
                "https://dubaievents.bham.ac.uk/whatson/", "Asia/Dubai", False
            ).fetch_events(),
            *dubai_events1.EventFetcher().fetch_events(),
        ]

        for name, event in events:
            print(name)
            self.write_to_file(event, name)

        self.last_fetch_time = datetime.now()
        return events

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


scraper = EventScraper()


def fetch_events_periodically(interval=3600):
    while True:
        scraper.fetch_events()
        time.sleep(interval)


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
        # Start the background thread for periodic fetching
        threading.Thread(
            target=fetch_events_periodically, args=(900,), daemon=True
        ).start()
        app.run(host="0.0.0.0", port=5000)
    else:
        scraper.fetch_events()
