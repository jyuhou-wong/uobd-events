# Event Scraper

This project is a Python-based web scraper that fetches event information from the University of Birmingham's Dubai campus website. It organizes the events into an iCalendar format (.ics) for easy import into calendar applications. The application is built using Flask and BeautifulSoup.

### iCalendar Subscribe URL:
[https://uobd.hyh.ltd:2053/events](https://uobd.hyh.ltd:2053/events)

## Features

- Scrapes event data from a specified URL.
- Generates .ics files for each event.
- Combines individual event files into a single iCalendar file.
- Provides a web interface to fetch events and download the iCalendar file.
- Includes a dedicated route to manually trigger event fetching.

## Requirements

- Python 3.x
- Flask
- Requests
- BeautifulSoup4

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/jyuhou-wong/uobd-events.git
   cd uobd-events
   ```

2. **Install the required packages:**

   You can use `pip` to install the necessary libraries:

   ```bash
   pip install Flask requests beautifulsoup4
   ```

   or
   
   ```bash
   pip install -r ./requirements.txt
   ```

## Usage

### Running the Application

To start the Flask server, run the following command:

```bash
python script.py server
```

Replace `script.py` with the name of your Python file.

### Accessing the Application

- Open your web browser and go to `http://localhost:5000/` to fetch events and download the iCalendar file.
- Access `http://localhost:5000/fetch` to manually trigger the event fetching process and receive a JSON response indicating the success or failure of the operation.

### Subscribing to the iCalendar Feed (Need to configurate nginx proxy for http://127.0.0.1:5000)

below example: `https://uobd.hyh.ltd:2053/events` proxy `http://127.0.0.1:5000`

You can subscribe to the iCalendar feed to receive updates automatically:

1. **Using Google Calendar:**
   - Open Google Calendar.
   - On the left side, click the `+` next to "Other calendars."
   - Select "From URL."
   - Paste the iCalendar subscribe URL: `https://uobd.hyh.ltd:2053/events`
   - Click "Add Calendar." The events will now appear in your calendar.

2. **Using Apple Calendar:**
   - Open Apple Calendar.
   - From the menu bar, select `File` > `New Calendar Subscription...`
   - Paste the iCalendar subscribe URL: `https://uobd.hyh.ltd:2053/events`
   - Click "Subscribe."
   - Adjust the settings as desired and click "OK."

3. **Using Microsoft Outlook:**
   - Open Outlook.
   - Go to the Calendar view.
   - Click on "Add Calendar" > "From Internet."
   - Paste the iCalendar subscribe URL: `https://uobd.hyh.ltd:2053/events`
   - Click "OK" to add the calendar.

### Directory Structure

- `events/` - Directory where individual event .ics files are saved.
- `output.ics` - Combined iCalendar file containing all events.

## Customization

You can modify the `EventScraper` class to change the URL from which events are scraped or adjust the parsing logic based on the structure of the target website.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - A micro web framework for Python.
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - A library for parsing HTML and XML documents.
- [Requests](https://requests.readthedocs.io/en/latest/) - A simple, yet elegant HTTP library for Python.