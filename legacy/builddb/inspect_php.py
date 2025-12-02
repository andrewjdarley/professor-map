import json
import random

# Read the JSON file
with open('parsed_classes.json', 'r') as f:
    courses = json.load(f)

# Get all course keys
course_keys = list(courses.keys())

# Select a random course
random_key = random.choice(course_keys)
random_course = courses[random_key]

# Extract course-level features
course_level_features = [key for key in random_course.keys() if key != 'sections']

# Extract section-level features (from first section if available)
section_level_features = []
if random_course['sections'] and len(random_course['sections']) > 0:
    section_level_features = list(random_course['sections'][0].keys())

# Print results
print("=== COURSE DATA STRUCTURE ===\n")

print("COURSE-LEVEL FEATURES:")
for i, feature in enumerate(course_level_features, 1):
    print(f"  {i}. {feature}")

print("\nSECTION-LEVEL FEATURES:")
for i, feature in enumerate(section_level_features, 1):
    print(f"  {i}. {feature}")

print("\n=== RANDOM COURSE EXAMPLE ===\n")
print(f"Course ID: {random_key}")
print(f"Department: {random_course['dept_name']}")
catalog_suffix = random_course['catalog_suffix'] if random_course['catalog_suffix'] else ''
print(f"Course Number: {random_course['catalog_number']}{catalog_suffix}")
print(f"Title: {random_course['title']}")
print(f"Full Title: {random_course['full_title']}")
print(f"Number of Sections: {len(random_course['sections'])}")

if random_course['sections']:
    random_section = random.choice(random_course['sections'])
    print("\nRandom Section Details:")
    print(f"  Section Number: {random_section['section_number']}")
    instructor = random_section['instructor_name'] if random_section['instructor_name'] else 'TBA'
    print(f"  Instructor: {instructor}")
    print(f"  Credit Hours: {random_section['credit_hours']}")
    print(f"  Mode: {random_section['mode']}")
    print(f"  Section Type: {random_section['section_type']}")
    print(f"  Honors: {random_section['honors']}")

print("\n=== COMPLETE RANDOM COURSE DATA ===")
print(json.dumps({random_key: random_course}, indent=2))