#!/usr/bin/env python3
"""
Query tool for BYU professor ratings, reviews, and course information using Supabase.

This module provides functionality to:
1. Query professor ratings from Rate My Professor data
2. Query professor reviews (merged with ratings)
3. Query course/class information by course code, title, or instructor
4. Query sections and section times
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from supabase import create_client, Client
from dotenv import load_dotenv


class BYUSupabaseQuery:
    """Main query tool for BYU data using Supabase."""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """
        Initialize the query tool with Supabase connection.
        
        Args:
            supabase_url: Supabase project URL. If None, reads from SUPABASE_URL env var.
            supabase_key: Supabase API key. If None, reads from SUPABASE_KEY env var.
        """
        # Load environment variables from .env file if it exists
        # Look for .env in the query/ directory (where this file is located)
        env_path = Path(__file__).parent / '.env'
        load_dotenv(dotenv_path=str(env_path))
        
        # Get URL - check SUPABASE_URL first, or derive from SUPABASE_DB_URL if available
        if supabase_url:
            self.supabase_url = supabase_url
        elif os.getenv('SUPABASE_URL'):
            self.supabase_url = os.getenv('SUPABASE_URL')
        elif os.getenv('SUPABASE_DB_URL'):
            # Extract API URL from database URL (e.g., db.xxxxx.supabase.co -> https://xxxxx.supabase.co)
            db_url = os.getenv('SUPABASE_DB_URL')
            import re
            match = re.search(r'@db\.([^.]+)\.supabase\.co', db_url)
            if match:
                project_ref = match.group(1)
                self.supabase_url = f'https://{project_ref}.supabase.co'
            else:
                self.supabase_url = None
        else:
            self.supabase_url = None
        
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Supabase credentials not provided. "
                "Set SUPABASE_URL and SUPABASE_KEY environment variables, "
                "or pass them as arguments."
            )
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    # ==================== Professor Queries ====================
    
    def get_professor_by_id(self, professor_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a professor by their ID.
        
        Args:
            professor_id: The professor's ID
            
        Returns:
            Professor dictionary or None if not found
        """
        response = self.client.table('professors').select('*').eq('professor_id', professor_id).execute()
        if response.data:
            return response.data[0]
        return None
    
    def search_professors(self, name: Optional[str] = None, 
                         department: Optional[str] = None,
                         min_rating: Optional[float] = None,
                         limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for professors by name, department, or rating.
        
        Args:
            name: Professor name to search for (searches first_name and last_name)
            department: Department to filter by
            min_rating: Minimum average rating
            limit: Maximum number of results
            
        Returns:
            List of professor dictionaries
        """
        query = self.client.table('professors').select('*')
        
        if name:
            # Search in both first_name and last_name
            name_lower = name.lower()
            # Use or_ with proper PostgREST filter syntax (ilike uses % for wildcards)
            query = query.or_(f'first_name.ilike.%{name_lower}%,last_name.ilike.%{name_lower}%')
        
        if department:
            query = query.eq('department', department)
        
        if min_rating is not None:
            query = query.gte('avg_rating', min_rating)
        
        query = query.limit(limit)
        response = query.execute()
        
        return response.data
    
    def get_professor_ratings(self, professor_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all ratings for a specific professor.
        
        Args:
            professor_id: The professor's ID
            limit: Maximum number of ratings to return
            
        Returns:
            List of rating dictionaries
        """
        response = self.client.table('ratings')\
            .select('*')\
            .eq('professor_id', professor_id)\
            .order('date', desc=True)\
            .limit(limit)\
            .execute()
        
        return response.data
    
    def get_professor_with_ratings(self, professor_id: int, 
                                   include_reviews: bool = True,
                                   review_limit: int = 10) -> Optional[Dict[str, Any]]:
        """
        Get a professor with their ratings and reviews.
        
        Args:
            professor_id: The professor's ID
            include_reviews: Whether to include individual reviews
            review_limit: Maximum number of reviews to include
            
        Returns:
            Professor dictionary with ratings and reviews, or None if not found
        """
        professor = self.get_professor_by_id(professor_id)
        if not professor:
            return None
        
        # Get ratings
        ratings = self.get_professor_ratings(professor_id, limit=review_limit)
        
        # Get tags for each rating
        if include_reviews and ratings:
            rating_ids = [r['rating_id'] for r in ratings]
            
            # Get all tags for these ratings
            tags_response = self.client.table('rating_tags')\
                .select('*')\
                .in_('rating_id', rating_ids)\
                .execute()
            
            # Group tags by rating_id
            tags_by_rating = {}
            for tag in tags_response.data:
                rating_id = tag['rating_id']
                if rating_id not in tags_by_rating:
                    tags_by_rating[rating_id] = []
                tags_by_rating[rating_id].append(tag['tag_name'])
            
            # Attach tags to ratings
            for rating in ratings:
                rating['tags'] = tags_by_rating.get(rating['rating_id'], [])
        
        professor['ratings'] = ratings
        
        # Calculate aggregated tags (most common tags)
        if include_reviews and ratings:
            all_tags = []
            for rating in ratings:
                all_tags.extend(rating.get('tags', []))
            
            # Count tag occurrences
            tag_counts = {}
            for tag in all_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Convert to list of dicts sorted by count
            aggregated_tags = [
                {'tagName': tag, 'tagCount': count}
                for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            ]
            professor['aggregatedTags'] = aggregated_tags
        
        return professor
    
    # ==================== Course Queries ====================
    
    def get_course_by_id(self, course_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a course by its ID.
        
        Args:
            course_id: The course's ID
            
        Returns:
            Course dictionary or None if not found
        """
        response = self.client.table('courses').select('*').eq('course_id', course_id).execute()
        if response.data:
            return response.data[0]
        return None
    
    def get_course_by_key(self, course_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a course by its course_key (e.g., "20255-CS-142-001").
        
        Args:
            course_key: The course key
            
        Returns:
            Course dictionary or None if not found
        """
        response = self.client.table('courses').select('*').eq('course_key', course_key).execute()
        if response.data:
            return response.data[0]
        return None
    
    def search_courses(self, course_code: Optional[str] = None,
                      title: Optional[str] = None,
                      department: Optional[str] = None,
                      limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for courses by code, title, or department.
        
        Args:
            course_code: Course code to search for (e.g., "CS 142")
            title: Title keywords to search for
            department: Department name to filter by
            limit: Maximum number of results
            
        Returns:
            List of course dictionaries
        """
        query = self.client.table('courses').select('*')
        
        if course_code:
            # Search in catalog_number and catalog_suffix
            # Use or_ with proper PostgREST filter syntax (ilike uses % for wildcards)
            query = query.or_(f'catalog_number.ilike.%{course_code}%,catalog_suffix.ilike.%{course_code}%')
        
        if title:
            # Use or_ with proper PostgREST filter syntax (ilike uses % for wildcards)
            query = query.or_(f'title.ilike.%{title}%,full_title.ilike.%{title}%')
        
        if department:
            query = query.eq('dept_name', department)
        
        query = query.limit(limit)
        response = query.execute()
        
        return response.data
    
    def get_course_sections(self, course_id: int) -> List[Dict[str, Any]]:
        """
        Get all sections for a specific course.
        
        Args:
            course_id: The course's ID
            
        Returns:
            List of section dictionaries with times
        """
        # Get sections
        sections_response = self.client.table('sections')\
            .select('*')\
            .eq('course_id', course_id)\
            .execute()
        
        sections = sections_response.data
        
        # Get times for each section
        if sections:
            section_ids = [s['section_id'] for s in sections]
            
            times_response = self.client.table('section_times')\
                .select('*')\
                .in_('section_id', section_ids)\
                .execute()
            
            # Group times by section_id
            times_by_section = {}
            for time in times_response.data:
                section_id = time['section_id']
                if section_id not in times_by_section:
                    times_by_section[section_id] = []
                times_by_section[section_id].append(time)
            
            # Attach times to sections
            for section in sections:
                section['times'] = times_by_section.get(section['section_id'], [])
        
        return sections
    
    def get_course_with_sections(self, course_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a course with all its sections and times.
        
        Args:
            course_id: The course's ID
            
        Returns:
            Course dictionary with sections and times, or None if not found
        """
        course = self.get_course_by_id(course_id)
        if not course:
            return None
        
        course['sections'] = self.get_course_sections(course_id)
        return course
    
    # ==================== Section Queries ====================
    
    def get_sections_by_instructor(self, instructor_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all sections taught by a specific instructor.
        
        Args:
            instructor_name: Name of the instructor
            limit: Maximum number of results
            
        Returns:
            List of section dictionaries with course and time information
        """
        # Search sections by instructor_name
        sections_response = self.client.table('sections')\
            .select('*')\
            .ilike('instructor_name', f'%{instructor_name}%')\
            .limit(limit)\
            .execute()
        
        sections = sections_response.data
        
        # Get course info and times for each section
        if sections:
            course_ids = list(set([s['course_id'] for s in sections]))
            section_ids = [s['section_id'] for s in sections]
            
            # Get courses
            courses_response = self.client.table('courses')\
                .select('*')\
                .in_('course_id', course_ids)\
                .execute()
            
            courses_by_id = {c['course_id']: c for c in courses_response.data}
            
            # Get times
            times_response = self.client.table('section_times')\
                .select('*')\
                .in_('section_id', section_ids)\
                .execute()
            
            times_by_section = {}
            for time in times_response.data:
                section_id = time['section_id']
                if section_id not in times_by_section:
                    times_by_section[section_id] = []
                times_by_section[section_id].append(time)
            
            # Enrich sections with course and time info
            for section in sections:
                section['course'] = courses_by_id.get(section['course_id'])
                section['times'] = times_by_section.get(section['section_id'], [])
        
        return sections
    
    def get_sections_by_professor_id(self, professor_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all sections taught by a professor (using professor_id).
        
        Args:
            professor_id: The professor's ID
            limit: Maximum number of results
            
        Returns:
            List of section dictionaries with course and time information
        """
        sections_response = self.client.table('sections')\
            .select('*')\
            .eq('professor_id', professor_id)\
            .limit(limit)\
            .execute()
        
        sections = sections_response.data
        
        # Get course info and times
        if sections:
            course_ids = list(set([s['course_id'] for s in sections]))
            section_ids = [s['section_id'] for s in sections]
            
            courses_response = self.client.table('courses')\
                .select('*')\
                .in_('course_id', course_ids)\
                .execute()
            
            courses_by_id = {c['course_id']: c for c in courses_response.data}
            
            times_response = self.client.table('section_times')\
                .select('*')\
                .in_('section_id', section_ids)\
                .execute()
            
            times_by_section = {}
            for time in times_response.data:
                section_id = time['section_id']
                if section_id not in times_by_section:
                    times_by_section[section_id] = []
                times_by_section[section_id].append(time)
            
            for section in sections:
                section['course'] = courses_by_id.get(section['course_id'])
                section['times'] = times_by_section.get(section['section_id'], [])
        
        return sections
    
    # ==================== Combined Queries ====================
    
    def get_courses_by_instructor(self, instructor_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all courses taught by a specific instructor.
        
        Args:
            instructor_name: Name of the instructor
            limit: Maximum number of results
            
        Returns:
            List of course dictionaries with matching sections
        """
        sections = self.get_sections_by_instructor(instructor_name, limit=limit)
        
        # Group sections by course
        courses_by_id = {}
        for section in sections:
            course_id = section['course_id']
            if course_id not in courses_by_id:
                course = section.get('course', {})
                course['sections'] = []
                courses_by_id[course_id] = course
            
            # Remove course from section to avoid duplication
            section_copy = {k: v for k, v in section.items() if k != 'course'}
            courses_by_id[course_id]['sections'].append(section_copy)
        
        return list(courses_by_id.values())[:limit]
    
    def search_courses_with_instructor(self, course_code: Optional[str] = None,
                                      instructor: Optional[str] = None,
                                      limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for courses, optionally filtered by instructor.
        
        Args:
            course_code: Course code to search for
            instructor: Instructor name to filter by
            limit: Maximum number of results
            
        Returns:
            List of course dictionaries with sections filtered by instructor
        """
        # First, get courses matching the course code
        courses = self.search_courses(course_code=course_code, limit=limit * 2)
        
        if not instructor:
            # Just return courses with all sections
            for course in courses:
                course['sections'] = self.get_course_sections(course['course_id'])
            return courses[:limit]
        
        # Filter by instructor
        result = []
        for course in courses:
            sections = self.get_course_sections(course['course_id'])
            matching_sections = [
                s for s in sections
                if instructor.lower() in s.get('instructor_name', '').lower()
            ]
            
            if matching_sections:
                course_copy = course.copy()
                course_copy['sections'] = matching_sections
                result.append(course_copy)
            
            if len(result) >= limit:
                break
        
        return result


def main():
    """Example usage of the query tool."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Query BYU professor ratings, reviews, and courses from Supabase')
    parser.add_argument('--supabase-url', type=str, help='Supabase project URL')
    parser.add_argument('--supabase-key', type=str, help='Supabase API key')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Professor queries
    prof_parser = subparsers.add_parser('professor', help='Query professors')
    prof_parser.add_argument('--name', type=str, help='Professor name to search for')
    prof_parser.add_argument('--id', type=int, help='Professor ID')
    prof_parser.add_argument('--department', type=str, help='Department filter')
    prof_parser.add_argument('--min-rating', type=float, help='Minimum rating')
    prof_parser.add_argument('--with-ratings', action='store_true', help='Include ratings')
    
    # Course queries
    course_parser = subparsers.add_parser('course', help='Query courses')
    course_parser.add_argument('--code', type=str, help='Course code to search')
    course_parser.add_argument('--title', type=str, help='Title keywords')
    course_parser.add_argument('--id', type=int, help='Course ID')
    course_parser.add_argument('--instructor', type=str, help='Instructor name filter')
    course_parser.add_argument('--with-sections', action='store_true', help='Include sections')
    
    # Section queries
    section_parser = subparsers.add_parser('section', help='Query sections')
    section_parser.add_argument('--instructor', type=str, help='Instructor name')
    section_parser.add_argument('--professor-id', type=int, help='Professor ID')
    
    args = parser.parse_args()
    
    # Initialize tool
    try:
        tool = BYUSupabaseQuery(
            supabase_url=args.supabase_url,
            supabase_key=args.supabase_key
        )
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Execute command
    try:
        if args.command == 'professor':
            if args.id:
                if args.with_ratings:
                    result = tool.get_professor_with_ratings(args.id)
                else:
                    result = tool.get_professor_by_id(args.id)
            else:
                result = tool.search_professors(
                    name=args.name,
                    department=args.department,
                    min_rating=args.min_rating
                )
            
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        
        elif args.command == 'course':
            if args.id:
                if args.with_sections:
                    result = tool.get_course_with_sections(args.id)
                else:
                    result = tool.get_course_by_id(args.id)
            else:
                result = tool.search_courses_with_instructor(
                    course_code=args.code,
                    instructor=args.instructor
                )
            
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        
        elif args.command == 'section':
            if args.professor_id:
                result = tool.get_sections_by_professor_id(args.professor_id)
            elif args.instructor:
                result = tool.get_sections_by_instructor(args.instructor)
            else:
                print("Error: Must provide --instructor or --professor-id")
                return
            
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error executing query: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

