#!/usr/bin/env python3
"""
Test script for BYU Supabase Query module.

This script demonstrates basic usage of the query module.
Make sure you have set up your Supabase credentials before running.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from query import BYUSupabaseQuery


def test_professor_queries(query_tool: BYUSupabaseQuery):
    """Test professor-related queries."""
    print("=" * 60)
    print("Testing Professor Queries")
    print("=" * 60)
    
    # Search for professors by name
    print("\n1. Searching for professors with 'Smith' in name:")
    professors = query_tool.search_professors(name="Smith", limit=5)
    print(f"   Found {len(professors)} professors")
    if professors:
        prof = professors[0]
        print(f"   Example: {prof.get('first_name')} {prof.get('last_name')} "
              f"(Rating: {prof.get('avg_rating')}, Department: {prof.get('department')})")
    
    # Get professor with ratings
    if professors:
        print("\n2. Getting professor with ratings:")
        prof_id = professors[0]['professor_id']
        prof_with_ratings = query_tool.get_professor_with_ratings(prof_id, review_limit=5)
        if prof_with_ratings:
            print(f"   Professor: {prof_with_ratings.get('first_name')} {prof_with_ratings.get('last_name')}")
            print(f"   Average Rating: {prof_with_ratings.get('avg_rating')}")
            print(f"   Number of Ratings: {len(prof_with_ratings.get('ratings', []))}")
            if prof_with_ratings.get('aggregatedTags'):
                print(f"   Top Tags: {', '.join([t['tagName'] for t in prof_with_ratings['aggregatedTags'][:5]])}")


def test_course_queries(query_tool: BYUSupabaseQuery):
    """Test course-related queries."""
    print("\n" + "=" * 60)
    print("Testing Course Queries")
    print("=" * 60)
    
    # Search for courses
    print("\n1. Searching for courses with 'C S' in code:")
    courses = query_tool.search_courses(course_code="C S", limit=5)
    print(f"   Found {len(courses)} courses")
    if courses:
        course = courses[0]
        print(f"   Example: {course.get('dept_name')} {course.get('catalog_number')} - {course.get('title')}")
    
    # Get course with sections
    if courses:
        print("\n2. Getting course with sections:")
        course_id = courses[0]['course_id']
        course_with_sections = query_tool.get_course_with_sections(course_id)
        if course_with_sections:
            print(f"   Course: {course_with_sections.get('dept_name')} {course_with_sections.get('catalog_number')}")
            print(f"   Title: {course_with_sections.get('title')}")
            print(f"   Number of sections: {len(course_with_sections.get('sections', []))}")
            if course_with_sections.get('sections'):
                section = course_with_sections['sections'][0]
                print(f"   Example section: {section.get('section_number')} "
                      f"taught by {section.get('instructor_name')}")


def test_section_queries(query_tool: BYUSupabaseQuery):
    """Test section-related queries."""
    print("\n" + "=" * 60)
    print("Testing Section Queries")
    print("=" * 60)
    
    # Get sections by instructor
    print("\n1. Searching for sections by instructor name:")
    sections = query_tool.get_sections_by_instructor("Smith", limit=5)
    print(f"   Found {len(sections)} sections")
    if sections:
        section = sections[0]
        print(f"   Example: {section.get('course', {}).get('dept_name')} "
              f"{section.get('course', {}).get('catalog_number')} "
              f"Section {section.get('section_number')}")
        print(f"   Instructor: {section.get('instructor_name')}")
        if section.get('times'):
            time = section['times'][0]
            print(f"   Time: {time.get('days')} {time.get('start_time')}-{time.get('end_time')}")


def test_combined_queries(query_tool: BYUSupabaseQuery):
    """Test combined queries."""
    print("\n" + "=" * 60)
    print("Testing Combined Queries")
    print("=" * 60)
    
    # Search courses with instructor filter
    print("\n1. Searching for C S courses with instructor filter:")
    courses = query_tool.search_courses_with_instructor(course_code="C S", instructor="Smith", limit=5)
    print(f"   Found {len(courses)} courses")
    if courses:
        course = courses[0]
        print(f"   Course: {course.get('dept_name')} {course.get('catalog_number')}")
        print(f"   Matching sections: {len(course.get('sections', []))}")


def main():
    """Run all tests."""
    print("BYU Supabase Query Module - Test Script")
    print("=" * 60)
    
    # Load environment variables from .env file if it exists
    # Look for .env in the query/ directory
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=str(env_path))
    
    # Check for environment variables
    # Accept either SUPABASE_URL or SUPABASE_DB_URL (we can derive URL from DB URL)
    has_url = bool(os.getenv('SUPABASE_URL') or os.getenv('SUPABASE_DB_URL'))
    has_key = bool(os.getenv('SUPABASE_KEY'))
    
    if not has_url or not has_key:
        print("\nError: SUPABASE_URL (or SUPABASE_DB_URL) and SUPABASE_KEY environment variables not set.")
        print("Please set them or create a .env file in the query/ directory.")
        print("\nExample .env file:")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_KEY=your-api-key")
        print("\nOr alternatively:")
        print("SUPABASE_DB_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres")
        print("SUPABASE_KEY=your-api-key")
        sys.exit(1)
    
    try:
        # Initialize query tool
        print("\nInitializing Supabase connection...")
        query_tool = BYUSupabaseQuery()
        print("✓ Connected to Supabase")
        
        # Run tests
        test_professor_queries(query_tool)
        test_course_queries(query_tool)
        test_section_queries(query_tool)
        test_combined_queries(query_tool)
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

