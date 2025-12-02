# Building Demo JSONs - Step-by-Step Walkthrough

This guide walks you through using the tools in the `builddb` folder to build demo JSON files for testing.

## Overview

The builddb tools create three main JSON files:
1. **`teacher_ratings.json`** - Professor ratings from Rate My Professors
2. **`professor_reviews.json`** - Detailed reviews (note: script not included, file may already exist)
3. **`courses.json`** - Course catalog with sections, instructors, and schedules

## Prerequisites

### 1. Install Python Dependencies

```bash
cd /home/andrew/Desktop/CS452/final/transport/builddb
pip install requests icalendar
```

### 2. Check Current Directory

All scripts should be run from the `builddb` directory:
```bash
cd /home/andrew/Desktop/CS452/final/transport/builddb
```

---

## Part 1: Building Course Data (`courses.json`)

The course data pipeline has 4 steps that transform raw BYU API data into a clean, structured format.

### Step 1: Download Raw Course Data

**Script**: `download_classes.sh`

**What it does**: Downloads all courses from BYU's class schedule API for a specific term.

**Command**:
```bash
bash download_classes.sh
```

**Output**: `classes_full.json`

**Notes**:
- The script uses a session ID (`GH0JQG8JLMJVED9MSNAQ`) and term (`20261`) that may expire
- If it fails, you may need to:
  1. Visit https://commtech.byu.edu/noauth/classSchedule/index.php
  2. Open browser developer tools (F12) → Network tab
  3. Make a search request and copy the `sessionId` from the request
  4. Update `sessionId` in `download_classes.sh`
  5. Update `yearterm` to match the current/upcoming semester

**Testing**:
```bash
# Check if file was created
ls -lh classes_full.json

# View first few lines (should be JSON)
head -20 classes_full.json
```

---

### Step 2: Parse Course Structure

**Script**: `parse_classes.py`

**What it does**: Reads the raw JSON and organizes it by course code. This step mainly validates and reformats the data.

**Command**:
```bash
python parse_classes.py
```

**Input**: `classes_full.json` (from Step 1)

**Output**: `parsed_classes.json`

**Testing**:
```bash
# Check output
ls -lh parsed_classes.json

# Count courses
python -c "import json; data = json.load(open('parsed_classes.json')); print(f'Total courses: {len(data)}')"
```

---

### Step 3: Simplify Course Data

**Script**: `simplify_classes.py`

**What it does**: Extracts essential fields and creates a cleaner structure with:
- Course name (e.g., "C S 142")
- Full title
- Curriculum ID
- Credit hours
- Sections with instructor names and modes

**Command**:
```bash
python simplify_classes.py
```

**Input**: `parsed_classes.json` (from Step 2)

**Output**: `simplified_courses.json`

**Testing**:
```bash
# Check output
ls -lh simplified_courses.json

# View first course example
python -c "import json; data = json.load(open('simplified_courses.json')); print(json.dumps(data[0], indent=2))"
```

---

### Step 4: Add Schedule Times

**Script**: `add_times.py`

**What it does**: For each course, fetches detailed section times from BYU's API and adds:
- Days of week (M, T, W, Th, F, Sa, Su)
- Start/end times (formatted as "9:00 AM")
- Building and room numbers

**Command**:
```bash
python add_times.py
```

**Input**: 
- `simplified_courses.json` (from Step 3)
- `parsed_classes.json` (from Step 2, for title_code mapping)

**Output**: `simplified_courses_with_times_final.json`

**Notes**:
- This script makes many API calls (one per course)
- Includes a 0.13 second delay between requests
- May take 10-30 minutes depending on number of courses
- The script currently processes ALL courses (see line 29 in `add_times.py`)

**Testing**:
```bash
# Check output
ls -lh simplified_courses_with_times_final.json

# View first course with times
python -c "import json; data = json.load(open('simplified_courses_with_times_final.json')); print(json.dumps(data[0], indent=2))"
```

**To create a smaller demo file** (for faster testing):
```python
# Edit add_times.py, line 29:
# Change from:
courses_to_process = simplified_courses

# To:
courses_to_process = simplified_courses[:10]  # Only first 10 courses
```

---

### Step 5: Copy to Final Location

After Step 4, copy the final file to the transport directory:

```bash
cp simplified_courses_with_times_final.json ../courses.json
```

Or if you want to use it directly:
```bash
# The application may expect courses.json in the transport/ directory
# Check query.py to see what filename it expects
```

---

## Part 2: Building Professor Ratings (`teacher_ratings.json`)

### Step 1: Scrape Rate My Professors

**Script**: `scrape_rmp.py`

**What it does**: Fetches all BYU professors from Rate My Professors GraphQL API with:
- Average rating
- Average difficulty
- Number of ratings
- Would take again percentage
- Department
- Name

**Command**:
```bash
python scrape_rmp.py
```

**Output**: 
- `byu_professors.json` (JSON format)
- `byu_professors.csv` (CSV format)

**Notes**:
- Uses pagination to fetch all professors (100 per page)
- Includes 1 second delay between pages
- May take 5-10 minutes depending on number of professors
- Uses GraphQL API which may require authentication updates

**Testing**:
```bash
# Check outputs
ls -lh byu_professors.json byu_professors.csv

# View first professor
python -c "import json; data = json.load(open('byu_professors.json')); print(json.dumps(data[0], indent=2))"

# Count professors
python -c "import json; data = json.load(open('byu_professors.json')); print(f'Total professors: {len(data)}')"
```

---

### Step 2: Copy to Final Location

```bash
cp byu_professors.json ../teacher_ratings.json
```

---

## Part 3: Professor Reviews (`professor_reviews.json`)

**Note**: The script to generate detailed reviews is **not included** in the builddb folder. The `professor_reviews.json` file may already exist in the `transport/` directory.

If you need to recreate it, you would need to:
1. Use professor IDs from `teacher_ratings.json`
2. Query Rate My Professors GraphQL API with `TeacherRatingsPageQuery` for each professor
3. Collect all ratings with comments, tags, grades, etc.

For now, if the file exists, you can use it as-is for testing.

---

## Quick Test Workflow

Here's a minimal workflow to test with just a few courses:

### 1. Download Course Data
```bash
cd /home/andrew/Desktop/CS452/final/transport/builddb
bash download_classes.sh
```

### 2. Parse and Simplify (Quick)
```bash
python parse_classes.py
python simplify_classes.py
```

### 3. Create Small Demo (Edit add_times.py first)
```python
# In add_times.py, line 29, change to:
courses_to_process = simplified_courses[:5]  # Only 5 courses for testing
```

Then run:
```bash
python add_times.py
cp simplified_courses_with_times_final.json ../courses.json
```

### 4. Test Professor Ratings (Optional)
```bash
python scrape_rmp.py
cp byu_professors.json ../teacher_ratings.json
```

### 5. Verify with Query Tool
```bash
cd ..
python query.py courses --course-code "C S" --limit 5
python query.py ratings --teacher-name "Smith" --limit 5
```

---

## Troubleshooting

### BYU API Issues

**Problem**: `download_classes.sh` or `add_times.py` fails with authentication errors

**Solution**:
1. Visit https://commtech.byu.edu/noauth/classSchedule/index.php
2. Open browser developer tools (F12) → Network tab
3. Make a search request
4. Find the request to `getClasses.php` or `getSections.php`
5. Copy the `sessionId` from the request payload
6. Update `sessionId` in the scripts:
   - `download_classes.sh` (line 11)
   - `add_times.py` (line 26)

**Problem**: Wrong semester data

**Solution**: Update `yearterm` parameter:
- `20261` = Fall 2026
- `20264` = Winter 2027
- `20268` = Spring 2027
- Format: `YYYYT` where T = term (1=Fall, 4=Winter, 8=Spring)

### Rate My Professors Issues

**Problem**: `scrape_rmp.py` fails with authentication errors

**Solution**: The GraphQL API may have changed. Check:
1. Visit Rate My Professors website
2. Open developer tools → Network tab
3. Search for a BYU professor
4. Find the GraphQL request
5. Copy the authorization header
6. Update `scrape_rmp.py` line 11

**Problem**: Rate limiting / blocked requests

**Solution**: Increase the delay in `scrape_rmp.py`:
```python
# Line 206, increase delay:
professors = scraper.scrape_all_professors(batch_size=100, delay=2.0)  # 2 seconds instead of 1
```

### File Not Found Errors

**Problem**: Scripts can't find input files

**Solution**: Make sure you're running scripts from the `builddb` directory:
```bash
cd /home/andrew/Desktop/CS452/final/transport/builddb
```

---

## Expected File Sizes

After running all scripts, you should see files like:

- `classes_full.json`: ~5-20 MB (raw BYU data)
- `parsed_classes.json`: ~5-20 MB (same data, reformatted)
- `simplified_courses.json`: ~1-5 MB (simplified structure)
- `simplified_courses_with_times_final.json`: ~2-10 MB (with schedule times)
- `byu_professors.json`: ~500 KB - 2 MB (professor ratings)
- `courses.json` (final): ~2-10 MB
- `teacher_ratings.json` (final): ~500 KB - 2 MB

---

## Next Steps

After building the JSON files:

1. **Test with query.py**:
   ```bash
   cd /home/andrew/Desktop/CS452/final/transport
   python query.py courses --course-code "C S 142"
   python query.py ratings --teacher-name "Smith"
   ```

2. **Verify data structure**:
   ```bash
   python -c "import json; data = json.load(open('courses.json')); print(f'Courses: {len(data)}'); print(json.dumps(data[0], indent=2))"
   ```

3. **Check for missing data**:
   - Some courses may not have times (online courses, TBA sections)
   - Some professors may not have ratings
   - This is normal and expected

---

## Summary

**Course Data Pipeline**:
```
download_classes.sh → classes_full.json
    ↓
parse_classes.py → parsed_classes.json
    ↓
simplify_classes.py → simplified_courses.json
    ↓
add_times.py → simplified_courses_with_times_final.json
    ↓
Copy to ../courses.json
```

**Professor Ratings Pipeline**:
```
scrape_rmp.py → byu_professors.json
    ↓
Copy to ../teacher_ratings.json
```

**Total Time**: 
- Course data: 15-30 minutes (mostly waiting for API calls)
- Professor ratings: 5-10 minutes
- **Total: ~20-40 minutes for full dataset**

For testing, you can limit the number of courses processed in `add_times.py` to speed things up!

