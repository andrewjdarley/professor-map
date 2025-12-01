import json
import requests
import time

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
print(f"Processing first {len(courses_to_process)} courses for debugging")

# Process each course
for i, course in enumerate(courses_to_process):
    curriculum_id = course['curriculum_id']
    
    # Get title_code for this curriculum_id
    if curriculum_id not in curriculum_to_titlecode:
        print(f"Warning: No title_code found for {course['course_name']}")
        continue
    
    title_code = curriculum_to_titlecode[curriculum_id]
    course_id = f"{curriculum_id}-{title_code}"
    
    print(f"Fetching {i+1}/{len(courses_to_process)}: {course['course_name']}")
    
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
                                    # Format time nicely (0900 -> 9:00 AM)
                                    def format_time(time_str):
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
            
        # Small delay to be nice to the server
        time.sleep(0.13)
        
    except Exception as e:
        print(f"Error fetching {course['course_name']}: {e}")
        for section in course['sections']:
            section['times'] = None

# Save updated JSON (only first 10 for debugging)
with open('simplified_courses_with_times_final.json', 'w') as f:
    json.dump(courses_to_process, f, indent=2)

print(f"\nCreated simplified_courses_with_times_debug.json")
print("\nFirst example with times:")
print(json.dumps(courses_to_process[0], indent=2))