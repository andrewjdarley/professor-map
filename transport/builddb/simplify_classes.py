import json

# Read the original JSON file
with open('parsed_classes.json', 'r') as f:
    courses = json.load(f)

# Create simplified course list
simplified_courses = []

for course_id, course_data in courses.items():
    # Build course name
    dept = course_data['dept_name']
    catalog_num = course_data['catalog_number']
    suffix = course_data['catalog_suffix'] if course_data['catalog_suffix'] else ''
    course_name = f"{dept} {catalog_num}{suffix}".strip()
    
    # Get course-level info
    full_title = course_data['full_title']
    curriculum_id = course_data['curriculum_id']
    
    # Build sections array with instructor, mode, and section_number
    sections = []
    for section in course_data['sections']:
        sections.append({
            "section_number": section['section_number'],
            "instructor_name": section['instructor_name'],
            "mode": section['mode']
        })
    
    simplified_course = {
        "course_name": course_name,
        "full_title": full_title,
        "curriculum_id": curriculum_id,
        "credit_hours": course_data['sections'][0]['credit_hours'] if course_data['sections'] else None,
        "sections": sections
    }
    simplified_courses.append(simplified_course)

# Write to new JSON file
with open('simplified_courses.json', 'w') as f:
    json.dump(simplified_courses, f, indent=2)

print(f"Created simplified_courses.json with {len(simplified_courses)} courses")
print("\nFirst 2 examples:")
for i in range(min(2, len(simplified_courses))):
    print(f"\n{i+1}. {json.dumps(simplified_courses[i], indent=2)}")