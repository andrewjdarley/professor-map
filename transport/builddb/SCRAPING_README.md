# Web Scraping Scripts

This directory contains all the web scraping scripts used to generate the datasets for professor ratings, reviews, and course information.

## Files Overview

### Rate My Professor Scraping

#### `scrape_rmp.py`
**Purpose**: Scrapes professor ratings from Rate My Professors using their GraphQL API.

**What it does**:
- Fetches all BYU professors from Rate My Professors
- Gets basic ratings: avgRating, avgDifficulty, numRatings, wouldTakeAgainPercent
- Saves to JSON and CSV formats

**Usage**:
```bash
python scrape_rmp.py
```

**Output**: `byu_professors.json` and `byu_professors.csv`

**Note**: This script only fetches basic ratings. To get detailed reviews with comments, you would need to use a different GraphQL query (TeacherRatingsPage) for each professor's ID. The `professor_reviews.json` file in this directory contains the full review data that was fetched separately.

### Course/Class Scraping

#### `download_classes.sh`
**Purpose**: Downloads the full course schedule from BYU's class schedule API.

**What it does**:
- Makes a POST request to BYU's class schedule endpoint
- Downloads all courses for a specific term (20261 in the script)
- Saves raw JSON response

**Usage**:
```bash
bash download_classes.sh
```

**Output**: `classes_full.json`

**Note**: You may need to update the `sessionId` and `yearterm` parameters in the script if they expire.

#### `getClasses.php`
**Purpose**: PHP endpoint reference (shows the API structure BYU uses).

**Note**: This is the actual PHP endpoint that BYU uses. The script shows the expected request format.

#### `parse_classes.py`
**Purpose**: Parses the raw classes JSON file.

**What it does**:
- Reads `classes_full.json`
- Organizes data by course code
- Saves parsed structure

**Usage**:
```bash
python parse_classes.py
```

**Output**: `parsed_classes.json`

#### `simplify_classes.py`
**Purpose**: Simplifies the parsed course data structure.

**What it does**:
- Reads `parsed_classes.json`
- Extracts essential fields: course_name, full_title, curriculum_id, credit_hours, sections
- Creates a cleaner, simplified structure

**Usage**:
```bash
python simplify_classes.py
```

**Output**: `simplified_courses.json`

#### `add_times.py`
**Purpose**: Adds detailed schedule times to simplified courses.

**What it does**:
- Reads `simplified_courses.json` and `parsed_classes.json`
- For each course, fetches detailed section times from BYU's API
- Adds building, room, days, and time information to each section
- Formats times in readable format (e.g., "9:00 AM")

**Usage**:
```bash
python add_times.py
```

**Output**: `simplified_courses_with_times_final.json`

**Note**: This script makes many API calls (one per course). It includes a delay (0.13 seconds) between requests to be respectful to the server. The script processes all courses, which may take a while.

#### `fetch_class_calendar.py`
**Purpose**: Converts iCal calendar feeds to JSON format.

**What it does**:
- Reads course calendar sources from `icals.txt`
- Fetches iCal data (from URLs or local files)
- Converts to JSON format with assignment information
- Calculates due dates

**Usage**:
```bash
python fetch_class_calendar.py
```

**Requirements**: 
- `icalendar` Python package: `pip install icalendar`
- `icals.txt` file with course names and their calendar sources

**Output**: `schedule.json`

#### `inspect_php.py`
**Purpose**: Utility script to inspect the structure of course data.

**What it does**:
- Reads `parsed_classes.json`
- Analyzes and displays the data structure
- Shows course-level and section-level features
- Prints a random course example

**Usage**:
```bash
python inspect_php.py
```

## Data Pipeline

The typical workflow for scraping course data:

1. **Download raw data**: `download_classes.sh` → `classes_full.json`
2. **Parse structure**: `parse_classes.py` → `parsed_classes.json`
3. **Simplify**: `simplify_classes.py` → `simplified_courses.json`
4. **Add times**: `add_times.py` → `simplified_courses_with_times_final.json`

The final `courses.json` file used by the application is based on the output from step 4.

## Rate My Professor Data Pipeline

1. **Fetch ratings**: `scrape_rmp.py` → `teacher_ratings.json`
2. **Fetch detailed reviews**: (Separate script needed) → `professor_reviews.json`

**Note**: The `professor_reviews.json` file contains detailed review data with comments, but the script to generate it is not in the legacy folder. It would require a GraphQL query like `TeacherRatingsPageQuery` that fetches the full teacher page including all ratings with comments for each professor ID.

## API Endpoints Used

### BYU Class Schedule
- **Base URL**: `https://commtech.byu.edu/noauth/classSchedule/`
- **Get Classes**: `ajax/getClasses.php`
- **Get Sections**: `ajax/getSections.php`

### Rate My Professors
- **GraphQL Endpoint**: `https://www.ratemyprofessors.com/graphql`
- **School ID**: `U2Nob29sLTEzNQ==` (BYU)

## Important Notes

1. **Session IDs**: BYU's API uses session IDs that may expire. You may need to update these in the scripts.

2. **Rate Limiting**: The scripts include delays to be respectful to servers. Don't remove these delays.

3. **Data Freshness**: Course data is term-specific. Update the `yearterm` parameter for different semesters.

4. **Authentication**: Rate My Professors may require authentication headers. The current script uses a basic auth header, but this may need updating.

5. **GraphQL Queries**: Rate My Professors uses GraphQL. The queries in `scrape_rmp.py` may need updating if their API changes.

## Dependencies

### Python Packages
- `requests` - HTTP requests
- `icalendar` - iCal parsing (for `fetch_class_calendar.py`)
- Standard library: `json`, `time`, `csv`

Install with:
```bash
pip install requests icalendar
```

## Troubleshooting

### BYU API Issues
- Check if session ID is still valid
- Verify the yearterm parameter matches current/upcoming semester
- Check if BYU has changed their API structure

### Rate My Professors Issues
- Verify the GraphQL query structure hasn't changed
- Check if authentication headers are still valid
- Rate My Professors may block requests if too many are made too quickly

### Missing Review Data
The `professor_reviews.json` file contains detailed reviews, but the script to generate it is not present. To recreate it, you would need to:
1. Use the professor IDs from `teacher_ratings.json`
2. Make GraphQL queries to `TeacherRatingsPageQuery` for each professor
3. Collect all ratings with comments, tags, grades, etc.

