# Scraping Scripts Summary

## All Scraping Scripts Collected

### ✅ Rate My Professor
- **`scrape_rmp.py`** - Fetches professor ratings from Rate My Professors GraphQL API

### ✅ Course/Class Data
- **`download_classes.sh`** - Downloads raw course data from BYU API
- **`getClasses.php`** - Reference PHP endpoint (shows API structure)
- **`parse_classes.py`** - Parses raw course JSON
- **`simplify_classes.py`** - Simplifies course data structure
- **`add_times.py`** - Adds detailed schedule times to courses
- **`fetch_class_calendar.py`** - Converts iCal feeds to JSON
- **`inspect_php.py`** - Utility to inspect course data structure

## Data Files

### Generated Datasets
- **`teacher_ratings.json`** - 5,603 professor ratings (from `scrape_rmp.py`)
- **`professor_reviews.json`** - 5,603 detailed review entries with comments
- **`courses.json`** - 3,265 courses with sections, instructors, and schedules

## Missing Script

**Note**: The script to generate `professor_reviews.json` (detailed reviews with comments) is not present in the legacy folder. This file contains full review data including:
- Student comments
- Individual ratings (clarity, helpfulness, difficulty)
- Tags
- Grades
- Attendance requirements

To recreate this file, you would need to:
1. Use professor IDs from `teacher_ratings.json`
2. Query Rate My Professors GraphQL API with `TeacherRatingsPageQuery` for each professor
3. Collect all ratings with full details

## Query Tool

**`query.py`** - Python tool to query all the datasets (see README.md for usage)

