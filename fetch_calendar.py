import os
import json
import urllib.request
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

import icalendar
import recurring_ical_events


TIMEZONE = ZoneInfo("Europe/Paris")
OUTPUT_FILE = "calendar.json"


def get_calendar():
    url = os.environ["CALENDAR_URL"]

    # urllib ne gère pas webcal:// directement
    if url.startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "EDT-Notion-Widget/1.0"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def to_local_datetime(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=TIMEZONE)
        return value.astimezone(TIMEZONE)

    # Les événements "toute la journée" ne nous intéressent pas
    return None


def main():

    raw_calendar = get_calendar()

    calendar = icalendar.Calendar.from_ical(raw_calendar)

    now = datetime.now(TIMEZONE)

    # On récupère aujourd'hui + les prochains jours.
    # Cela permet au widget de toujours avoir les données nécessaires.
    start = datetime.combine(
        now.date(),
        time.min,
        tzinfo=TIMEZONE
    )

    end = start + timedelta(days=14)

    events = recurring_ical_events.of(calendar).between(
        start,
        end
    )

    result = []

    for event in events:

        try:
            title = str(event.get("SUMMARY", "Cours")).strip()

            start_value = event.get("DTSTART").dt
            end_value = event.get("DTEND").dt

            event_start = to_local_datetime(start_value)
            event_end = to_local_datetime(end_value)

            if event_start is None or event_end is None:
                continue

            result.append({
                "title": title,
                "start": event_start.isoformat(),
                "end": event_end.isoformat()
            })

        except Exception:
            continue

    result.sort(key=lambda event: event["start"])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            {
                "updated": now.isoformat(),
                "events": result
            },
            file,
            ensure_ascii=False,
            indent=2
        )


if __name__ == "__main__":
    main()
