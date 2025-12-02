import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Configuration
MAX_WORKERS = 10  # Number of concurrent threads (adjust based on server capacity)
RATE_LIMIT_DELAY = 0.05  # Reduced delay since we're doing parallel requests

# Read the simplified courses JSON
print("Reading simplified_courses.json...")
with open('simplified_courses.json', 'r') as f:
    simplified_courses = json.load(f)

# Read original data to get title_code
print("Reading parsed_classes.json to get title_codes...")
with open('parsed_classes.json', 'r') as f:
    original_data = json.load(f)

# Build curriculum_id to title_code mapping
curriculum_to_titlecode = {}
for course_key, course_data in original_data.items():
    curriculum_id = course_data['curriculum_id']
    title_code = course_data['title_code']
    curriculum_to_titlecode[curriculum_id] = title_code

# API endpoint
base_url = "https://commtech.byu.edu/noauth/classSchedule/ajax/getSections.php"

# Session ID - you may need to update this periodically
session_id = "GH0JQG8JLMJVED9MSNAQ"

# Only process first 10 courses for debugging
courses_to_process = simplified_courses
print(f"Processing {len(courses_to_process)} courses with {MAX_WORKERS} threads")

# Thread-safe progress tracking
progress_lock = Lock()
completed_count = [0]  # Use list to allow modification in nested function

def format_time(time_str):
    """Format time string (0900 -> 9:00 AM)"""
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

def process_course(course):
    """Process a single course to fetch and add schedule times"""
    curriculum_id = course['curriculum_id']
    
    # Get title_code for this curriculum_id
    if curriculum_id not in curriculum_to_titlecode:
        with progress_lock:
            completed_count[0] += 1
            print(f"[{completed_count[0]}/{len(courses_to_process)}] Warning: No title_code found for {course['course_name']}")
        return course
    
    title_code = curriculum_to_titlecode[curriculum_id]
    course_id = f"{curriculum_id}-{title_code}"
    
    # Prepare payload
    payload = {
        'courseId': course_id,
        'sessionId': session_id,
        'yearterm': '20261'
    }
    
    try:
        response = requests.post(base_url, data=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'sections' in data:
                sections_detail = data['sections']
                
                # Match sections by section_number
                for section in course['sections']:
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
                                
                                if day_string and begin and end:
                                    time_ranges.append({
                                        'days': day_string,
                                        'start_time': format_time(begin),
                                        'end_time': format_time(end),
                                        'building': building,
                                        'room': room
                                    })
                            
                            section['times'] = time_ranges if time_ranges else None
                        else:
                            section['times'] = None
                    else:
                        section['times'] = None
        else:
            # If request failed, set times to None for all sections
            for section in course['sections']:
                section['times'] = None
        
        # Small delay to be nice to the server
        time.sleep(RATE_LIMIT_DELAY)
        
    except Exception as e:
        print(f"Error fetching {course['course_name']}: {e}")
        for section in course['sections']:
            section['times'] = None
    
    # Update progress
    with progress_lock:
        completed_count[0] += 1
        if completed_count[0] % 50 == 0 or completed_count[0] == len(courses_to_process):
            print(f"Progress: {completed_count[0]}/{len(courses_to_process)} courses processed ({100*completed_count[0]//len(courses_to_process)}%)")
    
    return course

# Process courses using thread pool
print(f"\nStarting parallel processing with {MAX_WORKERS} workers...")
start_time = time.time()

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # Submit all tasks
    future_to_course = {executor.submit(process_course, course): course for course in courses_to_process}
    
    # Wait for all tasks to complete (results are already stored in course objects)
    for future in as_completed(future_to_course):
        try:
            future.result()  # This will raise any exceptions that occurred
        except Exception as e:
            course = future_to_course[future]
            print(f"Unexpected error processing {course['course_name']}: {e}")

elapsed_time = time.time() - start_time
print(f"\nCompleted in {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")

# Save updated JSON
print("\nSaving results to simplified_courses_with_times_final.json...")
with open('simplified_courses_with_times_final.json', 'w') as f:
    json.dump(courses_to_process, f, indent=2)

print(f"Created simplified_courses_with_times_final.json")
print("\nFirst example with times:")
print(json.dumps(courses_to_process[0], indent=2))