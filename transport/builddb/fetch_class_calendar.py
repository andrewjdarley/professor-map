#!/usr/bin/env python3
"""
Convert iCal feeds and files to JSON format.
Reads calendar sources from icals.txt and outputs to calendar.json
"""

import json
import requests
from datetime import datetime
from pathlib import Path
from icalendar import Calendar
from typing import Dict, List, Any


def parse_icals_file(filename: str = "icals.txt") -> Dict[str, str]:
    """Parse the icals.txt file to get course names and their sources."""
    sources = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                # Split on the last occurrence of http:// or https:// or ./
                if 'http://' in line:
                    idx = line.index('http://')
                    course_name = line[:idx].strip()
                    source = line[idx:].strip()
                elif 'https://' in line:
                    idx = line.index('https://')
                    course_name = line[:idx].strip()
                    source = line[idx:].strip()
                elif './' in line:
                    idx = line.index('./')
                    course_name = line[:idx].strip()
                    source = line[idx:].strip()
                else:
                    continue
                sources[course_name] = source
    return sources


def fetch_ical_content(source: str) -> str:
    """Fetch iCal content from a URL or read from a local file."""
    if source.startswith('http://') or source.startswith('https://'):
        response = requests.get(source)
        response.raise_for_status()
        return response.text
    else:
        # Local file
        with open(source, 'r', encoding='utf-8') as f:
            return f.read()


def convert_datetime(dt) -> str:
    """Convert datetime object to ISO format string."""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def parse_event(event: Any) -> Dict[str, Any]:
    """Parse an iCal event into a dictionary."""
    event_dict = {}
    
    # Common fields
    fields = ['SUMMARY', 'DTSTART', 'DTEND', 'DESCRIPTION', 'LOCATION', 
              'STATUS', 'UID', 'CREATED', 'LAST-MODIFIED', 'SEQUENCE']
    
    for field in fields:
        if field in event:
            value = event[field]
            if field in ['DTSTART', 'DTEND', 'CREATED', 'LAST-MODIFIED']:
                event_dict[field.lower()] = convert_datetime(value.dt)
            else:
                event_dict[field.lower()] = str(value)
    
    # Handle recurrence rules
    if 'RRULE' in event:
        event_dict['rrule'] = str(event['RRULE'])
    
    return event_dict


def process_calendar(course_name: str, ical_content: str) -> List[Dict[str, Any]]:
    """Process an iCal calendar and extract events."""
    cal = Calendar.from_ical(ical_content)
    events = []
    
    for component in cal.walk():
        if component.name == "VEVENT":
            event = parse_event(component)
            event['course'] = course_name
            events.append(event)
    
    return events


def main():
    """Main function to convert all iCal sources to JSON."""
    print("Reading icals.txt...")
    sources = parse_icals_file()
    
    all_events = []
    
    for course_name, source in sources.items():
        print(f"Processing {course_name}...")
        try:
            ical_content = fetch_ical_content(source)
            events = process_calendar(course_name, ical_content)
            all_events.extend(events)
            print(f"  Found {len(events)} events")
        except Exception as e:
            print(f"  Error processing {course_name}: {e}")
    
    # Process events: calculate due_date and simplify structure
    processed_events = []
    for event in all_events:
        # Calculate due_date
        if 'dtend' in event:
            # Parse dtend and subtract one day
            dtend_str = event['dtend']
            if 'T' in dtend_str:
                # Has time component
                dtend = datetime.fromisoformat(dtend_str)
            else:
                # Date only
                dtend = datetime.fromisoformat(dtend_str)
            
            from datetime import timedelta
            due_date = dtend - timedelta(days=1)
            due_date_str = due_date.date().isoformat()
        elif 'dtstart' in event:
            dtstart_str = event['dtstart']
            if 'T' in dtstart_str:
                dtstart = datetime.fromisoformat(dtstart_str)
                due_date_str = dtstart.date().isoformat()
            else:
                due_date_str = dtstart_str
        else:
            due_date_str = None
        
        # Clean up course name - remove "Canvas" wrapper
        course = event.get('course', '')
        if course.startswith('Canvas (') and course.endswith(')'):
            course = course[8:-1]  # Remove "Canvas (" and ")"
        
        # Create simplified event
        processed_events.append({
            'assignment': event.get('summary', ''),
            'due_date': due_date_str,
            'course': course
        })
    
    # Sort events by due date
    processed_events.sort(key=lambda x: x.get('due_date', ''))
    
    # Create output structure
    output = {
        'generated_at': datetime.now().isoformat(),
        'total_events': len(processed_events),
        'courses': [c if not c.startswith('Canvas (') else c[8:-1] for c in sources.keys()],
        'events': processed_events
    }
    
    # Write to JSON file
    output_file = 'schedule.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nSuccessfully exported {len(processed_events)} events to {output_file}")


if __name__ == "__main__":
    main()