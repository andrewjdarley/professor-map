#!/usr/bin/env python3
"""
Consolidated script to download, parse, and add section times to BYU course data.
This script combines the functionality of:
- download_classes.sh (downloads raw course data)
- parse_classes.py (parses JSON)
- add_times.py (adds detailed schedule times)

Output: courses.json with all course data including section times.
"""

import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import os

# Configuration
MAX_WORKERS = 10  # Number of concurrent threads for fetching section times
RATE_LIMIT_DELAY = 0.05  # Delay between requests (seconds)
SESSION_ID = "GH0JQG8JLMJVED9MSNAQ"  # Update this if it expires
YEARTERM = "20261"  # Update for different semesters

# API endpoints
GET_CLASSES_URL = "https://commtech.byu.edu/noauth/classSchedule/ajax/getClasses.php"
GET_SECTIONS_URL = "https://commtech.byu.edu/noauth/classSchedule/ajax/getSections.php"

# Output file
OUTPUT_FILE = "courses.json"


def download_classes(session_id=SESSION_ID, yearterm=YEARTERM):
    """Download all classes from BYU's class schedule API."""
    print("Downloading classes from BYU API...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://commtech.byu.edu",
        "Referer": "https://commtech.byu.edu/noauth/classSchedule/index.php"
    }
    
    data = {
        "searchObject[yearterm]": yearterm,
        "sessionId": session_id
    }
    
    try:
        response = requests.post(GET_CLASSES_URL, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        
        classes_data = response.json()
        print(f"Downloaded {len(classes_data)} courses")
        return classes_data
    except requests.exceptions.RequestException as e:
        print(f"Error downloading classes: {e}")
        raise


def parse_classes(classes_data):
    """Parse classes data (already in correct format, just validate)."""
    print(f"Parsing {len(classes_data)} courses...")
    # Data is already organized by course code (curriculum_id-title_code)
    # Just return it as-is
    return classes_data


def format_time(time_str):
    """Format time string (0900 -> 9:00 AM)."""
    if len(time_str) == 4:
        hour = int(time_str[:2])
        minute = time_str[2:]
        period = 'AM' if hour < 12 else 'PM'
        if hour > 12:
            hour -= 12
        elif hour == 0:
            hour = 12
        return f"{hour}:{minute} {period}"
    return time_str


def add_times_to_course(course_key, course_data, session_id=SESSION_ID, yearterm=YEARTERM):
    """Fetch and add schedule times to a single course's sections."""
    curriculum_id = course_data['curriculum_id']
    title_code = course_data['title_code']
    course_id = f"{curriculum_id}-{title_code}"
    
    # Prepare payload
    payload = {
        'courseId': course_id,
        'sessionId': session_id,
        'yearterm': yearterm
    }
    
    try:
        response = requests.post(GET_SECTIONS_URL, data=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'sections' in data:
                sections_detail = data['sections']
                
                # Match sections by section_number and add times
                for section in course_data['sections']:
                    section_num = section['section_number']
                    
                    # Find matching section in API response
                    matching_section = next(
                        (s for s in sections_detail if s['section_number'] == section_num),
                        None
                    )
                    
                    if matching_section and 'times' in matching_section:
                        times = matching_section['times']
                        if times:
                            # Format time ranges
                            time_ranges = []
                            for time_block in times:
                                # Build day string from individual day fields
                                days = []
                                if time_block.get('mon'): days.append('M')
                                if time_block.get('tue'): days.append('T')
                                if time_block.get('wed'): days.append('W')
                                if time_block.get('thu'): days.append('Th')
                                if time_block.get('fri'): days.append('F')
                                if time_block.get('sat'): days.append('Sa')
                                if time_block.get('sun'): days.append('Su')
                                
                                day_string = ' '.join(days)
                                begin = time_block.get('begin_time', '')
                                end = time_block.get('end_time', '')
                                building = time_block.get('building', '')
                                room = time_block.get('room', '')
                                
                                # Only add time block if we have at least days and times
                                # But always include all fields (with None for missing)
                                if day_string and begin and end:
                                    time_ranges.append({
                                        'days': day_string,
                                        'start_time': format_time(begin),
                                        'end_time': format_time(end),
                                        'building': building if building else None,
                                        'room': room if room else None
                                    })
                            
                            section['times'] = time_ranges if time_ranges else None
                        else:
                            section['times'] = None
                    else:
                        section['times'] = None
        else:
            # If request failed, set times to None for all sections
            for section in course_data['sections']:
                section['times'] = None
        
        # Small delay to be nice to the server
        time.sleep(RATE_LIMIT_DELAY)
        
    except Exception as e:
        print(f"Error fetching times for {course_key}: {e}")
        for section in course_data['sections']:
            section['times'] = None
    
    return course_key, course_data


def normalize_schema(courses_data):
    """Normalize schema to ensure all fields are present everywhere (with nulls where missing)."""
    print("\nNormalizing schema to ensure all fields are present...")
    
    # Define complete schema
    course_fields = [
        'catalog_number', 'catalog_suffix', 'curriculum_id', 'dept_name', 
        'full_title', 'sections', 'title', 'title_code', 'year_term'
    ]
    
    section_fields = [
        'credit_hours', 'credit_type', 'fixed_or_variable', 'honors', 
        'instructor_id', 'instructor_name', 'minimum_credit_hours', 'mode', 
        'mode_desc', 'section_number', 'section_type', 'times'
    ]
    
    time_fields = [
        'building', 'days', 'end_time', 'room', 'start_time'
    ]
    
    normalized_count = 0
    
    for course_key, course_data in courses_data.items():
        # Normalize course-level fields
        for field in course_fields:
            if field not in course_data:
                course_data[field] = None
                normalized_count += 1
        
        # Normalize section-level fields
        if 'sections' in course_data and course_data['sections']:
            for section in course_data['sections']:
                for field in section_fields:
                    if field not in section:
                        section[field] = None
                        normalized_count += 1
                
                # Normalize time-level fields
                if section.get('times'):
                    if isinstance(section['times'], list):
                        for time_block in section['times']:
                            if isinstance(time_block, dict):
                                for field in time_fields:
                                    if field not in time_block:
                                        time_block[field] = None
                                        normalized_count += 1
    
    if normalized_count > 0:
        print(f"  Added {normalized_count} missing fields with null values")
    else:
        print("  Schema already consistent")
    
    return courses_data


def add_times_to_all_courses(courses_data, session_id=SESSION_ID, yearterm=YEARTERM, max_workers=MAX_WORKERS):
    """Add schedule times to all courses using multi-threading."""
    print(f"\nAdding section times to {len(courses_data)} courses using {max_workers} threads...")
    
    # Thread-safe progress tracking
    progress_lock = Lock()
    completed_count = [0]
    total_courses = len(courses_data)
    
    def process_course_wrapper(item):
        """Wrapper to process course and update progress."""
        course_key, course_data = item
        result = add_times_to_course(course_key, course_data, session_id, yearterm)
        
        # Update progress
        with progress_lock:
            completed_count[0] += 1
            if completed_count[0] % 50 == 0 or completed_count[0] == total_courses:
                print(f"Progress: {completed_count[0]}/{total_courses} courses processed ({100*completed_count[0]//total_courses}%)")
        
        return result
    
    # Process courses using thread pool
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_course = {
            executor.submit(process_course_wrapper, item): item[0]
            for item in courses_data.items()
        }
        
        # Wait for all tasks to complete and update the original dict
        for future in as_completed(future_to_course):
            try:
                course_key, updated_course_data = future.result()
                courses_data[course_key] = updated_course_data
            except Exception as e:
                course_key = future_to_course[future]
                print(f"Unexpected error processing {course_key}: {e}")
    
    elapsed_time = time.time() - start_time
    print(f"\nCompleted in {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
    
    return courses_data


def main():
    """Main function to orchestrate the entire process."""
    print("=" * 60)
    print("BYU Course Data Builder")
    print("=" * 60)
    print()
    
    # Step 1: Download classes
    try:
        classes_data = download_classes()
    except Exception as e:
        print(f"Failed to download classes: {e}")
        print("\nTip: You may need to update SESSION_ID in the script.")
        print("Visit https://commtech.byu.edu/noauth/classSchedule/index.php")
        print("Open browser developer tools (F12) → Network tab")
        print("Make a search request and copy the sessionId from the request")
        return
    
    # Step 2: Parse classes (already in correct format)
    courses_data = parse_classes(classes_data)
    
    # Step 3: Add section times
    courses_data = add_times_to_all_courses(courses_data)
    
    # Step 4: Normalize schema
    courses_data = normalize_schema(courses_data)
    
    # Step 5: Save final output
    print(f"\nSaving results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(courses_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created {OUTPUT_FILE} with {len(courses_data)} courses")
    
    # Show example
    if courses_data:
        first_course_key = next(iter(courses_data))
        first_course = courses_data[first_course_key]
        print(f"\nExample course ({first_course_key}):")
        print(json.dumps({first_course_key: first_course}, indent=2)[:500] + "...")


if __name__ == "__main__":
    main()

