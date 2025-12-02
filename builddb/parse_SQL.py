#!/usr/bin/env python3
"""
Parse JSON data from build_courses.py and get_reviews.py into SQL tables.
Handles inconsistent professor name formatting across datasets using fuzzy matching.
"""

import json
import sqlite3
import re
import csv
import sys
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime

# SQLite database file
DB_FILE = "byu_courses.db"

# Common nickname mappings
NICKNAME_MAP = {
    'mike': 'michael',
    'mikey': 'michael',
    'mick': 'michael',
    'bob': 'robert',
    'bobby': 'robert',
    'rob': 'robert',
    'robby': 'robert',
    'dick': 'richard',
    'rick': 'richard',
    'rich': 'richard',
    'bill': 'william',
    'will': 'william',
    'billy': 'william',
    'jim': 'james',
    'jimmy': 'james',
    'tom': 'thomas',
    'tommy': 'thomas',
    'dave': 'david',
    'davey': 'david',
    'dan': 'daniel',
    'danny': 'daniel',
    'chris': 'christopher',
    'chuck': 'charles',
    'charlie': 'charles',
    'ed': 'edward',
    'eddie': 'edward',
    'ted': 'edward',
    'teddy': 'edward',
    'joe': 'joseph',
    'joey': 'joseph',
    'johnny': 'john',
    'jon': 'john',
    'jack': 'john',
    'pat': 'patrick',
    'patty': 'patrick',
    'pete': 'peter',
    'steve': 'steven',
    'steven': 'stephen',
    'steve': 'stephen',
    'al': 'alan',
    'al': 'allen',
    'al': 'albert',
    'alex': 'alexander',
    'andy': 'andrew',
    'drew': 'andrew',
    'ben': 'benjamin',
    'bennie': 'benjamin',
    'frank': 'franklin',
    'frank': 'francis',
    'fred': 'frederick',
    'greg': 'gregory',
    'jeff': 'jeffrey',
    'jeff': 'jeffery',
    'ken': 'kenneth',
    'kenny': 'kenneth',
    'larry': 'lawrence',
    'matt': 'matthew',
    'nate': 'nathan',
    'nate': 'nathaniel',
    'nick': 'nicholas',
    'paul': 'paul',
    'phil': 'philip',
    'phil': 'phillip',
    'ray': 'raymond',
    'ron': 'ronald',
    'ronny': 'ronald',
    'sam': 'samuel',
    'scott': 'scott',
    'sean': 'sean',
    'shawn': 'sean',
    'tim': 'timothy',
    'timmy': 'timothy',
    'tony': 'anthony',
    'vince': 'vincent',
}


def normalize_name(name: str) -> str:
    """Normalize a name for comparison."""
    if not name:
        return ""
    # Convert to lowercase, strip whitespace
    name = name.lower().strip()
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name)
    # Remove common suffixes
    name = re.sub(r'\s+(jr|sr|ii|iii|iv|v|esq|phd|md)\.?$', '', name)
    # Remove periods from initials
    name = re.sub(r'\.', '', name)
    return name


def expand_nickname(name: str) -> List[str]:
    """Return possible variations of a name including nicknames."""
    name_lower = name.lower().strip()
    variations = [name_lower]
    
    # Check if it's a nickname
    if name_lower in NICKNAME_MAP:
        variations.append(NICKNAME_MAP[name_lower])
    
    # Check if it's a full name that has a nickname
    for nickname, full_name in NICKNAME_MAP.items():
        if full_name == name_lower:
            variations.append(nickname)
    
    return list(set(variations))


def parse_name(full_name: str) -> Dict[str, str]:
    """Parse a full name into components."""
    if not full_name or not full_name.strip():
        return {'first': '', 'last': '', 'middle': '', 'suffix': ''}
    
    # Normalize
    name = normalize_name(full_name)
    parts = name.split()
    
    if len(parts) == 0:
        return {'first': '', 'last': '', 'middle': '', 'suffix': ''}
    elif len(parts) == 1:
        return {'first': parts[0], 'last': '', 'middle': '', 'suffix': ''}
    elif len(parts) == 2:
        return {'first': parts[0], 'last': parts[1], 'middle': '', 'suffix': ''}
    else:
        # Handle middle names and suffixes
        first = parts[0]
        last = parts[-1]
        middle = ' '.join(parts[1:-1]) if len(parts) > 2 else ''
        suffix = ''
        
        # Check if last part is a suffix
        suffix_pattern = r'^(jr|sr|ii|iii|iv|v|esq|phd|md)$'
        if re.match(suffix_pattern, last):
            suffix = last
            last = parts[-2] if len(parts) > 2 else ''
            middle = ' '.join(parts[1:-2]) if len(parts) > 3 else ''
        
        return {'first': first, 'last': last, 'middle': middle, 'suffix': suffix}


def name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two names (0.0 to 1.0)."""
    if not name1 or not name2:
        return 0.0
    
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    
    # Exact match after normalization
    if norm1 == norm2:
        return 1.0
    
    # Use SequenceMatcher for fuzzy matching
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Boost similarity if they share significant parts
    parts1 = set(norm1.split())
    parts2 = set(norm2.split())
    if parts1 and parts2:
        common_parts = parts1.intersection(parts2)
        if common_parts:
            # If they share words, boost the similarity
            similarity = max(similarity, 0.7)
    
    return similarity


def match_professor_name(instructor_name: str, professors: List[Dict]) -> Optional[int]:
    """
    Match an instructor name from courses.json to a professor in byu_professors.json.
    Returns the professor's internal ID (index) or None if no good match.
    """
    if not instructor_name or not instructor_name.strip():
        return None
    
    instructor_parsed = parse_name(instructor_name)
    instructor_first = instructor_parsed['first']
    instructor_last = instructor_parsed['last']
    
    if not instructor_first or not instructor_last:
        return None
    
    best_match_idx = None
    best_similarity = 0.0
    
    for idx, prof in enumerate(professors):
        prof_first = normalize_name(prof.get('firstName', ''))
        prof_last = normalize_name(prof.get('lastName', ''))
        
        if not prof_first or not prof_last:
            continue
        
        # Try exact match first
        if prof_first == instructor_first and prof_last == instructor_last:
            return idx
        
        # Try with nickname expansion
        instructor_first_variations = expand_nickname(instructor_first)
        prof_first_variations = expand_nickname(prof_first)
        
        for inst_first_var in instructor_first_variations:
            for prof_first_var in prof_first_variations:
                if inst_first_var == prof_first_var and prof_last == instructor_last:
                    return idx
        
        # Calculate similarity scores
        first_sim = name_similarity(instructor_first, prof_first)
        last_sim = name_similarity(instructor_last, prof_last)
        
        # Combined similarity (weight last name more heavily)
        combined_sim = (first_sim * 0.4 + last_sim * 0.6)
        
        # If first name matches well and last name matches well, it's a good match
        if first_sim > 0.7 and last_sim > 0.7:
            combined_sim = max(combined_sim, 0.85)
        
        if combined_sim > best_similarity and combined_sim >= 0.75:
            best_similarity = combined_sim
            best_match_idx = idx
    
    return best_match_idx


def create_tables(conn: sqlite3.Connection):
    """Create all SQL tables."""
    cursor = conn.cursor()
    
    # Professors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professors (
            professor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rmp_id TEXT UNIQUE,
            rmp_legacy_id INTEGER,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            department TEXT,
            school TEXT,
            avg_rating REAL,
            avg_difficulty REAL,
            num_ratings INTEGER,
            would_take_again_percent REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Courses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_key TEXT UNIQUE NOT NULL,
            year_term TEXT,
            curriculum_id TEXT,
            title_code TEXT,
            dept_name TEXT,
            catalog_number TEXT,
            catalog_suffix TEXT,
            title TEXT,
            full_title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Sections table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            section_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            section_number TEXT NOT NULL,
            fixed_or_variable TEXT,
            credit_hours TEXT,
            minimum_credit_hours TEXT,
            honors TEXT,
            credit_type TEXT,
            section_type TEXT,
            instructor_name TEXT,
            instructor_id TEXT,
            professor_id INTEGER,
            mode TEXT,
            mode_desc TEXT,
            FOREIGN KEY (course_id) REFERENCES courses(course_id),
            FOREIGN KEY (professor_id) REFERENCES professors(professor_id),
            UNIQUE(course_id, section_number)
        )
    """)
    
    # Section times table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS section_times (
            time_id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id INTEGER NOT NULL,
            days TEXT,
            start_time TEXT,
            end_time TEXT,
            building TEXT,
            room TEXT,
            FOREIGN KEY (section_id) REFERENCES sections(section_id)
        )
    """)
    
    # Ratings table (from ratings.json)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_id INTEGER NOT NULL,
            rmp_rating_id TEXT UNIQUE,
            rmp_legacy_id INTEGER,
            date TEXT,
            class_name TEXT,
            clarity_rating INTEGER,
            helpful_rating INTEGER,
            difficulty_rating INTEGER,
            comment TEXT,
            grade TEXT,
            attendance_mandatory TEXT,
            would_take_again INTEGER,
            textbook_use INTEGER,
            is_for_credit INTEGER,
            is_for_online_class INTEGER,
            flag_status TEXT,
            admin_reviewed_at TEXT,
            thumbs_up_total INTEGER,
            thumbs_down_total INTEGER,
            created_by_user INTEGER,
            FOREIGN KEY (professor_id) REFERENCES professors(professor_id)
        )
    """)
    
    # Rating tags table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rating_tags (
            tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating_id INTEGER NOT NULL,
            tag_name TEXT NOT NULL,
            FOREIGN KEY (rating_id) REFERENCES ratings(rating_id)
        )
    """)
    
    # Professor name variants table (for tracking matches)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor_name_variants (
            variant_id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_id INTEGER NOT NULL,
            variant_name TEXT NOT NULL,
            source TEXT,
            match_confidence REAL,
            FOREIGN KEY (professor_id) REFERENCES professors(professor_id)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_professors_rmp_id ON professors(rmp_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_professors_name ON professors(first_name, last_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sections_course ON sections(course_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sections_professor ON sections(professor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_section_times_section ON section_times(section_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratings_professor ON ratings(professor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rating_tags_rating ON rating_tags(rating_id)")
    
    conn.commit()
    print("✓ Created all tables and indexes")


def load_professors(professors_file: str) -> List[Dict]:
    """Load professors from byu_professors.json."""
    print(f"Loading professors from {professors_file}...")
    with open(professors_file, 'r', encoding='utf-8') as f:
        professors = json.load(f)
    print(f"  Loaded {len(professors)} professors")
    return professors


def load_courses(courses_file: str) -> Dict:
    """Load courses from courses.json."""
    print(f"Loading courses from {courses_file}...")
    with open(courses_file, 'r', encoding='utf-8') as f:
        courses = json.load(f)
    print(f"  Loaded {len(courses)} courses")
    return courses


def load_ratings(ratings_file: str) -> List[Dict]:
    """Load ratings from ratings.json."""
    print(f"Loading ratings from {ratings_file}...")
    with open(ratings_file, 'r', encoding='utf-8') as f:
        ratings = json.load(f)
    print(f"  Loaded {len(ratings)} rating entries")
    return ratings


def insert_professors(conn: sqlite3.Connection, professors: List[Dict]) -> Dict[str, int]:
    """
    Insert professors into database.
    Returns a mapping from (rmp_id) to (database professor_id).
    """
    cursor = conn.cursor()
    rmp_id_to_db_id = {}
    
    print("Inserting professors...")
    total = len(professors)
    for i, prof in enumerate(professors, 1):
        if i % 100 == 0 or i == total:
            print(f"  Progress: {i}/{total} ({100*i//total}%)", end='\r')
            sys.stdout.flush()
        rmp_id = prof.get('id')
        if not rmp_id:
            continue
        
        cursor.execute("""
            INSERT OR IGNORE INTO professors 
            (rmp_id, rmp_legacy_id, first_name, last_name, department, school,
             avg_rating, avg_difficulty, num_ratings, would_take_again_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rmp_id,
            prof.get('legacyId'),
            prof.get('firstName', ''),
            prof.get('lastName', ''),
            prof.get('department'),
            prof.get('school'),
            prof.get('avgRating'),
            prof.get('avgDifficulty'),
            prof.get('numRatings'),
            prof.get('wouldTakeAgainPercent')
        ))
        
        # Get the database ID
        cursor.execute("SELECT professor_id FROM professors WHERE rmp_id = ?", (rmp_id,))
        result = cursor.fetchone()
        if result:
            rmp_id_to_db_id[rmp_id] = result[0]
    
    conn.commit()
    print(f"\n  Inserted {len(rmp_id_to_db_id)} professors")
    return rmp_id_to_db_id


def insert_courses_and_sections(conn: sqlite3.Connection, courses: Dict, professors: List[Dict], 
                                rmp_id_to_db_id: Dict[str, int]) -> Dict[str, int]:
    """
    Insert courses and sections into database.
    Returns a mapping from (course_key) to (database course_id).
    """
    cursor = conn.cursor()
    course_key_to_db_id = {}
    
    # Build a mapping from instructor names to professor IDs
    instructor_to_prof_id = {}
    
    print("Inserting courses and sections...")
    sections_inserted = 0
    times_inserted = 0
    name_matches = 0
    name_misses = 0
    total_courses = len(courses)
    processed = 0
    
    for course_key, course_data in courses.items():
        processed += 1
        if processed % 50 == 0 or processed == total_courses:
            print(f"  Progress: {processed}/{total_courses} courses ({100*processed//total_courses}%)", end='\r')
            sys.stdout.flush()
        # Insert course
        cursor.execute("""
            INSERT OR IGNORE INTO courses
            (course_key, year_term, curriculum_id, title_code, dept_name,
             catalog_number, catalog_suffix, title, full_title)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            course_key,
            course_data.get('year_term'),
            course_data.get('curriculum_id'),
            course_data.get('title_code'),
            course_data.get('dept_name'),
            course_data.get('catalog_number'),
            course_data.get('catalog_suffix'),
            course_data.get('title'),
            course_data.get('full_title')
        ))
        
        # Get course database ID
        cursor.execute("SELECT course_id FROM courses WHERE course_key = ?", (course_key,))
        result = cursor.fetchone()
        if not result:
            continue
        course_db_id = result[0]
        course_key_to_db_id[course_key] = course_db_id
        
        # Insert sections
        sections = course_data.get('sections', [])
        for section in sections:
            instructor_name = section.get('instructor_name')
            professor_db_id = None
            
            # Try to match instructor name to a professor
            if instructor_name and instructor_name.strip():
                # Check cache first
                if instructor_name in instructor_to_prof_id:
                    professor_db_id = instructor_to_prof_id[instructor_name]
                else:
                    # Try to match
                    prof_idx = match_professor_name(instructor_name, professors)
                    if prof_idx is not None:
                        prof = professors[prof_idx]
                        rmp_id = prof.get('id')
                        if rmp_id and rmp_id in rmp_id_to_db_id:
                            professor_db_id = rmp_id_to_db_id[rmp_id]
                            instructor_to_prof_id[instructor_name] = professor_db_id
                            name_matches += 1
                            
                            # Store name variant
                            cursor.execute("""
                                INSERT OR IGNORE INTO professor_name_variants
                                (professor_id, variant_name, source, match_confidence)
                                VALUES (?, ?, ?, ?)
                            """, (professor_db_id, instructor_name, 'courses.json', 0.9))
                    else:
                        name_misses += 1
            
            # Insert section
            cursor.execute("""
                INSERT OR IGNORE INTO sections
                (course_id, section_number, fixed_or_variable, credit_hours,
                 minimum_credit_hours, honors, credit_type, section_type,
                 instructor_name, instructor_id, professor_id, mode, mode_desc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                course_db_id,
                section.get('section_number'),
                section.get('fixed_or_variable'),
                section.get('credit_hours'),
                section.get('minimum_credit_hours'),
                section.get('honors'),
                section.get('credit_type'),
                section.get('section_type'),
                instructor_name,
                section.get('instructor_id'),
                professor_db_id,
                section.get('mode'),
                section.get('mode_desc')
            ))
            
            # Get section database ID
            cursor.execute("""
                SELECT section_id FROM sections 
                WHERE course_id = ? AND section_number = ?
            """, (course_db_id, section.get('section_number')))
            result = cursor.fetchone()
            if not result:
                continue
            section_db_id = result[0]
            sections_inserted += 1
            
            # Insert section times
            times = section.get('times')
            if times and isinstance(times, list):
                for time_block in times:
                    cursor.execute("""
                        INSERT INTO section_times
                        (section_id, days, start_time, end_time, building, room)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        section_db_id,
                        time_block.get('days'),
                        time_block.get('start_time'),
                        time_block.get('end_time'),
                        time_block.get('building'),
                        time_block.get('room')
                    ))
                    times_inserted += 1
    
    conn.commit()
    print(f"\n  Inserted {len(course_key_to_db_id)} courses")
    print(f"  Inserted {sections_inserted} sections")
    print(f"  Inserted {times_inserted} section times")
    print(f"  Matched {name_matches} instructor names to professors")
    print(f"  Could not match {name_misses} instructor names")
    
    return course_key_to_db_id


def insert_ratings(conn: sqlite3.Connection, ratings: List[Dict], 
                  rmp_id_to_db_id: Dict[str, int]) -> int:
    """Insert ratings into database."""
    cursor = conn.cursor()
    
    print("Inserting ratings...")
    ratings_inserted = 0
    tags_inserted = 0
    total = len(ratings)
    
    for i, rating_entry in enumerate(ratings, 1):
        if i % 10 == 0 or i == total:
            print(f"  Progress: {i}/{total} entries ({100*i//total}%) - {ratings_inserted} ratings inserted", end='\r')
            sys.stdout.flush()
        teacher_node = rating_entry.get('data', {}).get('node', {})
        if teacher_node.get('__typename') != 'Teacher':
            continue
        
        rmp_id = teacher_node.get('id')
        if not rmp_id or rmp_id not in rmp_id_to_db_id:
            continue
        
        professor_db_id = rmp_id_to_db_id[rmp_id]
        
        # Get ratings edges
        ratings_data = teacher_node.get('ratings', {})
        edges = ratings_data.get('edges', [])
        
        for edge in edges:
            rating_node = edge.get('node', {})
            if rating_node.get('__typename') != 'Rating':
                continue
            
            rmp_rating_id = rating_node.get('id')
            if not rmp_rating_id:
                continue
            
            # Insert rating
            cursor.execute("""
                INSERT OR IGNORE INTO ratings
                (professor_id, rmp_rating_id, rmp_legacy_id, date, class_name,
                 clarity_rating, helpful_rating, difficulty_rating, comment, grade,
                 attendance_mandatory, would_take_again, textbook_use,
                 is_for_credit, is_for_online_class, flag_status, admin_reviewed_at,
                 thumbs_up_total, thumbs_down_total, created_by_user)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                professor_db_id,
                rmp_rating_id,
                rating_node.get('legacyId'),
                rating_node.get('date'),
                rating_node.get('class'),
                rating_node.get('clarityRating'),
                rating_node.get('helpfulRating'),
                rating_node.get('difficultyRating'),
                rating_node.get('comment'),
                rating_node.get('grade'),
                rating_node.get('attendanceMandatory'),
                rating_node.get('wouldTakeAgain'),
                rating_node.get('textbookUse'),
                1 if rating_node.get('isForCredit') else 0,
                1 if rating_node.get('isForOnlineClass') else 0,
                rating_node.get('flagStatus'),
                rating_node.get('adminReviewedAt'),
                rating_node.get('thumbsUpTotal', 0),
                rating_node.get('thumbsDownTotal', 0),
                1 if rating_node.get('createdByUser') else 0
            ))
            
            # Get rating database ID
            cursor.execute("SELECT rating_id FROM ratings WHERE rmp_rating_id = ?", (rmp_rating_id,))
            result = cursor.fetchone()
            if not result:
                continue
            rating_db_id = result[0]
            ratings_inserted += 1
            
            # Insert rating tags
            rating_tags = rating_node.get('ratingTags', '')
            if rating_tags:
                tags = [tag.strip() for tag in rating_tags.split('--') if tag.strip()]
                for tag in tags:
                    cursor.execute("""
                        INSERT INTO rating_tags (rating_id, tag_name)
                        VALUES (?, ?)
                    """, (rating_db_id, tag))
                    tags_inserted += 1
    
    conn.commit()
    print(f"\n  Inserted {ratings_inserted} ratings")
    print(f"  Inserted {tags_inserted} rating tags")
    
    return ratings_inserted


def main():
    """Main function to parse all JSON files into SQL database."""
    print("=" * 60)
    print("BYU Courses SQL Parser")
    print("=" * 60)
    print()
    
    # File paths
    professors_file = "byu_professors.json"
    courses_file = "courses.json"
    ratings_file = "ratings.json"
    
    # Load data
    professors = load_professors(professors_file)
    courses = load_courses(courses_file)
    ratings = load_ratings(ratings_file)
    
    # Create database
    print(f"\nCreating database: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    create_tables(conn)
    
    # Insert data
    print("\n" + "=" * 60)
    print("Inserting data...")
    print("=" * 60)
    
    # Insert professors first
    rmp_id_to_db_id = insert_professors(conn, professors)
    
    # Insert courses and sections (with name matching)
    course_key_to_db_id = insert_courses_and_sections(conn, courses, professors, rmp_id_to_db_id)
    
    # Insert ratings
    ratings_inserted = insert_ratings(conn, ratings, rmp_id_to_db_id)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM professors")
    print(f"Professors: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM courses")
    print(f"Courses: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM sections")
    print(f"Sections: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM section_times")
    print(f"Section Times: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM ratings")
    print(f"Ratings: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM rating_tags")
    print(f"Rating Tags: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM professor_name_variants")
    print(f"Name Variants: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM sections WHERE professor_id IS NOT NULL")
    print(f"Sections with matched professors: {cursor.fetchone()[0]}")
    
    # Export to PostgreSQL SQL and CSV
    print("\n" + "=" * 60)
    print("Exporting data...")
    print("=" * 60)
    
    export_to_postgresql(conn)
    export_to_csv(conn)
    
    conn.close()
    print(f"\n✓ Database created: {DB_FILE}")
    print("\n" + "=" * 60)
    print("Export Summary")
    print("=" * 60)
    print("✓ Supabase import file: sql_export/supabase_import.sql")
    print("  → Upload this file directly to Supabase SQL Editor")
    print("✓ Schema file: sql_export/schema.sql")
    print("✓ CSV files created in 'csv_export/' directory")
    print("\nTo import into Supabase:")
    print("  1. Open Supabase Dashboard → SQL Editor")
    print("  2. Copy and paste contents of sql_export/supabase_import.sql")
    print("  3. Run the query")


def escape_sql_string(value):
    """Escape a value for PostgreSQL SQL insertion."""
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    if isinstance(value, (int, float)):
        # Handle NaN and Infinity
        if isinstance(value, float):
            if value != value:  # NaN
                return 'NULL'
            if value == float('inf'):
                return "'Infinity'"
            if value == float('-inf'):
                return "'-Infinity'"
        return str(value)
    # Handle strings - escape single quotes and backslashes for PostgreSQL
    value_str = str(value)
    # PostgreSQL uses single quotes, so escape them by doubling
    value_str = value_str.replace("'", "''")
    # Escape backslashes
    value_str = value_str.replace("\\", "\\\\")
    # Wrap in single quotes
    return f"'{value_str}'"


def export_to_postgresql(conn: sqlite3.Connection):
    """Export SQLite database to Supabase/PostgreSQL-compatible SQL files."""
    import os
    
    os.makedirs("sql_export", exist_ok=True)
    cursor = conn.cursor()
    
    print("Exporting to Supabase/PostgreSQL SQL...")
    
    # Get table names in dependency order (tables with foreign keys last)
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    all_tables = [row[0] for row in cursor.fetchall()]
    
    # Define table order for proper foreign key handling
    # Tables without foreign keys first, then dependent tables
    table_order = [
        'professors',
        'courses',
        'sections',
        'section_times',
        'ratings',
        'rating_tags',
        'professor_name_variants'
    ]
    
    # Reorder tables according to dependencies
    ordered_tables = []
    for table in table_order:
        if table in all_tables:
            ordered_tables.append(table)
    # Add any remaining tables
    for table in all_tables:
        if table not in ordered_tables:
            ordered_tables.append(table)
    
    # Create a single combined SQL file for Supabase
    combined_file = "sql_export/supabase_import.sql"
    
    with open(combined_file, 'w', encoding='utf-8') as combined:
        combined.write("-- ============================================\n")
        combined.write("-- BYU Courses Database - Supabase Import\n")
        combined.write(f"-- Generated: {datetime.now().isoformat()}\n")
        combined.write("-- ============================================\n\n")
        combined.write("-- This file can be run directly in Supabase SQL Editor\n")
        combined.write("-- It will drop existing tables and recreate them with data\n\n")
        
        # Step 1: Drop all tables in reverse dependency order
        combined.write("-- ============================================\n")
        combined.write("-- Step 1: Drop existing tables\n")
        combined.write("-- ============================================\n\n")
        for table in reversed(ordered_tables):
            combined.write(f"DROP TABLE IF EXISTS {table} CASCADE;\n")
        combined.write("\n")
        
        # Step 2: Create tables with PostgreSQL syntax
        combined.write("-- ============================================\n")
        combined.write("-- Step 2: Create tables\n")
        combined.write("-- ============================================\n\n")
        
        for table in ordered_tables:
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
            result = cursor.fetchone()
            if not result:
                continue
            sql = result[0]
            
            # Convert SQLite syntax to PostgreSQL
            # Replace AUTOINCREMENT with SERIAL
            sql = re.sub(r'INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT', 'SERIAL PRIMARY KEY', sql, flags=re.IGNORECASE)
            sql = re.sub(r'\s+AUTOINCREMENT', '', sql, flags=re.IGNORECASE)
            
            # Convert REAL to DOUBLE PRECISION
            sql = re.sub(r'\bREAL\b', 'DOUBLE PRECISION', sql, flags=re.IGNORECASE)
            
            # Remove IF NOT EXISTS (we're dropping first)
            sql = re.sub(r'\s+IF\s+NOT\s+EXISTS', '', sql, flags=re.IGNORECASE)
            
            # Fix TIMESTAMP DEFAULT CURRENT_TIMESTAMP for PostgreSQL
            sql = re.sub(
                r'TIMESTAMP\s+DEFAULT\s+CURRENT_TIMESTAMP',
                'TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP',
                sql,
                flags=re.IGNORECASE
            )
            
            combined.write(f"-- Table: {table}\n")
            combined.write(f"{sql};\n\n")
        
        # Step 3: Create indexes
        combined.write("-- ============================================\n")
        combined.write("-- Step 3: Create indexes\n")
        combined.write("-- ============================================\n\n")
        
        index_definitions = [
            ("idx_professors_rmp_id", "professors", "rmp_id"),
            ("idx_professors_name", "professors", "first_name, last_name"),
            ("idx_sections_course", "sections", "course_id"),
            ("idx_sections_professor", "sections", "professor_id"),
            ("idx_section_times_section", "section_times", "section_id"),
            ("idx_ratings_professor", "ratings", "professor_id"),
            ("idx_rating_tags_rating", "rating_tags", "rating_id"),
        ]
        
        for idx_name, table_name, columns in index_definitions:
            combined.write(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({columns});\n")
        combined.write("\n")
        
        # Step 4: Insert data
        combined.write("-- ============================================\n")
        combined.write("-- Step 4: Insert data\n")
        combined.write("-- ============================================\n\n")
        
        for table in ordered_tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if not rows:
                continue
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            combined.write(f"-- Table: {table} ({len(rows)} rows)\n")
            
            # Batch inserts (500 rows at a time for better Supabase compatibility)
            batch_size = 500
            for batch_start in range(0, len(rows), batch_size):
                batch = rows[batch_start:batch_start + batch_size]
                combined.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n")
                
                values_list = []
                for row in batch:
                    values = [escape_sql_string(val) for val in row]
                    values_list.append(f"({', '.join(values)})")
                
                combined.write(",\n".join(values_list))
                combined.write(";\n\n")
            
            print(f"  Exported {table}: {len(rows)} rows")
    
    print(f"✓ Created combined Supabase import file: {combined_file}")
    
    # Also create separate files for schema and data (optional)
    schema_file = "sql_export/schema.sql"
    with open(schema_file, 'w', encoding='utf-8') as f:
        f.write("-- BYU Courses Database Schema (Supabase/PostgreSQL)\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}\n\n")
        f.write("-- Drop tables\n")
        for table in reversed(ordered_tables):
            f.write(f"DROP TABLE IF EXISTS {table} CASCADE;\n")
        f.write("\n-- Create tables\n")
        
        for table in ordered_tables:
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
            result = cursor.fetchone()
            if not result:
                continue
            sql = result[0]
            
            sql = re.sub(r'INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT', 'SERIAL PRIMARY KEY', sql, flags=re.IGNORECASE)
            sql = re.sub(r'\s+AUTOINCREMENT', '', sql, flags=re.IGNORECASE)
            sql = re.sub(r'\bREAL\b', 'DOUBLE PRECISION', sql, flags=re.IGNORECASE)
            sql = re.sub(r'\s+IF\s+NOT\s+EXISTS', '', sql, flags=re.IGNORECASE)
            sql = re.sub(
                r'TIMESTAMP\s+DEFAULT\s+CURRENT_TIMESTAMP',
                'TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP',
                sql,
                flags=re.IGNORECASE
            )
            
            f.write(f"{sql};\n\n")
    
    print(f"  Created schema file: {schema_file}")
    print("✓ Supabase/PostgreSQL SQL export complete")


def export_to_csv(conn: sqlite3.Connection):
    """Export all tables to CSV files."""
    import os
    
    os.makedirs("csv_export", exist_ok=True)
    cursor = conn.cursor()
    
    print("Exporting to CSV...")
    
    # Get table names
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        csv_file = f"csv_export/{table}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)
        
        print(f"  Created {csv_file} ({len(rows)} rows)")
    
    print("✓ CSV export complete")


if __name__ == "__main__":
    main()

