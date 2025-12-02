# BYU Query Tool

This directory contains extracted functionality for querying BYU professor ratings, reviews, and course information.

## Directory Structure

- **Data Files**: `teacher_ratings.json`, `professor_reviews.json`, `courses.json`
- **Query Tool**: `query.py` - Python script for querying the data
- **Scraping Scripts**: `builddb/` - All web scraping scripts used to generate the datasets (see `builddb/SCRAPING_README.md` for details)

## Files

- `teacher_ratings.json` - Rate My Professor ratings data (5,603 professors)
- `professor_reviews.json` - Detailed professor reviews with student comments (5,603 entries)
- `courses.json` - Course catalog with sections, instructors, and schedules (3,265 courses)
- `query.py` - Python script for querying the data
- `builddb/` - Directory containing all web scraping scripts

## Usage

### Python API

```python
from query import BYUQueryTool

# Initialize the tool
tool = BYUQueryTool()

# Query teacher ratings
ratings = tool.get_teacher_ratings("Smith")
print(f"Found {len(ratings)} teachers named Smith")

# Query teacher ratings with reviews
ratings_with_reviews = tool.get_teacher_ratings_with_reviews("John Smith")
for teacher in ratings_with_reviews:
    print(f"{teacher['firstName']} {teacher['lastName']}")
    print(f"  Rating: {teacher['avgRating']}/5.0")
    print(f"  Difficulty: {teacher['avgDifficulty']}/5.0")
    print(f"  Reviews: {len(teacher['reviews'])}")
    for review in teacher['reviews']:
        print(f"    - {review['class']}: {review['comment'][:50]}...")

# Search courses
courses = tool.search_courses(course_code="C S 142")
print(f"Found {len(courses)} courses matching 'C S 142'")

# Search courses by instructor
instructor_courses = tool.get_courses_by_instructor("Smith")
print(f"Found {len(instructor_courses)} courses taught by Smith")
```

### Command Line Interface

```bash
# Query teacher ratings
python query.py ratings --teacher-name "Smith"

# Query teacher ratings with reviews
python query.py ratings --teacher-name "John Smith" --with-reviews

# Search courses by code
python query.py courses --course-code "C S 142"

# Search courses by instructor
python query.py courses --instructor "Smith"

# Search courses with both filters
python query.py courses --course-code "MATH" --instructor "Johnson" --limit 10
```

## Features

### Teacher Ratings Query (`get_teacher_ratings`)
- Fuzzy name matching (supports partial matches, multi-word names)
- Returns: firstName, lastName, department, avgRating, avgDifficulty, numRatings, wouldTakeAgainPercent

### Teacher Ratings with Reviews (`get_teacher_ratings_with_reviews`)
- Same as above, plus:
- Aggregated tags (common tags from all reviews)
- Individual reviews (up to 10) with:
  - Course code
  - Student comment
  - Grade received
  - Individual ratings (clarity, helpfulness, difficulty)
  - Tags
  - Attendance requirement

### Course Search (`search_courses`)
- Search by course code or title
- Filter by instructor name
- Returns: course_name, full_title, sections with times, locations, and instructors

## Data Structure

### Teacher Ratings
```json
{
  "firstName": "John",
  "lastName": "Smith",
  "department": "Computer Science",
  "avgRating": 4.5,
  "avgDifficulty": 3.2,
  "numRatings": 42,
  "wouldTakeAgainPercent": 85.7
}
```

### Reviews (when merged)
```json
{
  "aggregatedTags": [
    {"tagName": "Clear explanations", "tagCount": 15},
    {"tagName": "Helpful", "tagCount": 12}
  ],
  "reviews": [
    {
      "class": "C S 142",
      "comment": "Great professor!",
      "grade": "A",
      "clarityRating": 5,
      "helpfulRating": 5,
      "difficultyRating": 3,
      "wouldTakeAgain": true,
      "tags": ["Clear explanations", "Helpful"],
      "attendanceMandatory": "mandatory"
    }
  ]
}
```

### Courses
```json
{
  "course_name": "C S 142",
  "full_title": "Introduction to Computer Science",
  "curriculum_id": "12345",
  "credit_hours": "3",
  "sections": [
    {
      "section_number": "001",
      "instructor_name": "John Smith",
      "mode": "Classroom",
      "times": [
        {
          "days": "M W F",
          "start_time": "10:00 AM",
          "end_time": "10:50 AM",
          "building": "TMCB",
          "room": "1170"
        }
      ]
    }
  ]
}
```

