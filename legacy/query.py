#!/usr/bin/env python3
"""
Query tool for BYU professor ratings, reviews, and course information.

This script provides functionality to:
1. Query professor ratings from Rate My Professor data
2. Query professor reviews (merged with ratings)
3. Query course/class information by course code, title, or instructor
"""

import json
import os
from typing import List, Dict, Optional, Any
from pathlib import Path


class BYUQueryTool:
    """Main query tool for BYU data."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the query tool.
        
        Args:
            data_dir: Directory containing the data files. Defaults to the directory
                     containing this script.
        """
        if data_dir is None:
            data_dir = Path(__file__).parent
        
        self.data_dir = Path(data_dir)
        self.ratings_path = self.data_dir / "teacher_ratings.json"
        self.reviews_path = self.data_dir / "professor_reviews.json"
        self.courses_path = self.data_dir / "courses.json"
        
        # Load data files
        self._load_data()
    
    def _load_data(self):
        """Load all data files into memory."""
        print(f"Loading data from {self.data_dir}...")
        
        with open(self.ratings_path, 'r', encoding='utf-8') as f:
            self.ratings_data = json.load(f)
        print(f"Loaded {len(self.ratings_data)} teacher ratings")
        
        with open(self.reviews_path, 'r', encoding='utf-8') as f:
            self.reviews_data = json.load(f)
        print(f"Loaded {len(self.reviews_data)} professor review entries")
        
        with open(self.courses_path, 'r', encoding='utf-8') as f:
            self.courses_data = json.load(f)
        print(f"Loaded {len(self.courses_data)} courses")
        print()
    
    def _match_teacher_name(self, teacher: Dict[str, Any], search_terms: List[str]) -> bool:
        """
        Check if a teacher matches the search terms using fuzzy matching.
        
        This replicates the exact matching logic from the TypeScript code.
        
        Args:
            teacher: Teacher object with firstName and lastName
            search_terms: List of search terms (lowercase)
        
        Returns:
            True if teacher matches all search terms
        """
        full_name = f"{teacher.get('firstName', '')} {teacher.get('lastName', '')}".lower()
        first_name = teacher.get('firstName', '').lower()
        last_name = teacher.get('lastName', '').lower()
        
        # Check if all search terms are found
        for term in search_terms:
            matched = False
            
            # First try exact full name match
            if term in full_name:
                matched = True
            
            # Then try partial matches - check if term is a substring of first or last name
            elif term in first_name or term in last_name:
                matched = True
            
            # For multi-word terms, check if they span across first and last names
            # e.g., "Riley Nelson" should match "Charles Riley Nelson"
            elif ' ' in term:
                term_parts = term.split(' ')
                if len(term_parts) == 2:
                    first_part, last_part = term_parts
                    if ((first_part in first_name and last_part in last_name) or
                        (first_part in last_name and last_part in first_name)):
                        matched = True
            
            if not matched:
                return False
        
        return True
    
    def get_teacher_ratings(self, teacher_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query teacher ratings by name.
        
        Args:
            teacher_name: Name of the teacher to search for. If None, returns all teachers.
        
        Returns:
            List of teacher rating dictionaries
        """
        if teacher_name is None:
            return self.ratings_data
        
        # Split search query into terms
        search_terms = [term for term in teacher_name.lower().split() if term]
        
        if not search_terms:
            return []
        
        # Filter teachers using fuzzy matching
        filtered = [
            teacher for teacher in self.ratings_data
            if self._match_teacher_name(teacher, search_terms)
        ]
        
        return filtered
    
    def get_teacher_ratings_with_reviews(self, teacher_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query teacher ratings and merge with review data.
        
        This replicates the exact functionality from the TypeScript code that merges
        ratings with reviews, including aggregated tags and individual reviews.
        
        Args:
            teacher_name: Name of the teacher to search for. If None, returns all teachers.
        
        Returns:
            List of enriched teacher dictionaries with ratings and reviews
        """
        # Get filtered ratings
        filtered = self.get_teacher_ratings(teacher_name)
        
        # Merge review data with ratings
        enriched = []
        for teacher in filtered:
            # Find matching review entry
            review_entry = None
            for review in self.reviews_data:
                prof = review.get('data', {}).get('node', {})
                if (prof.get('firstName', '').lower() == teacher.get('firstName', '').lower() and
                    prof.get('lastName', '').lower() == teacher.get('lastName', '').lower()):
                    review_entry = review
                    break
            
            if review_entry:
                prof = review_entry['data']['node']
                
                # Extract aggregated tags
                aggregated_tags = []
                if prof.get('teacherRatingTags'):
                    aggregated_tags = [
                        {
                            'tagName': tag.get('tagName'),
                            'tagCount': tag.get('tagCount')
                        }
                        for tag in prof['teacherRatingTags']
                    ]
                
                # Extract reviews (limit to 10)
                reviews = []
                if prof.get('ratings', {}).get('edges'):
                    reviews = [
                        {
                            'class': r.get('node', {}).get('class'),
                            'comment': r.get('node', {}).get('comment'),
                            'grade': r.get('node', {}).get('grade'),
                            'date': r.get('node', {}).get('date'),
                            'clarityRating': r.get('node', {}).get('clarityRating'),
                            'helpfulRating': r.get('node', {}).get('helpfulRating'),
                            'difficultyRating': r.get('node', {}).get('difficultyRating'),
                            'wouldTakeAgain': r.get('node', {}).get('wouldTakeAgain'),
                            'tags': [
                                t.strip() for t in r.get('node', {}).get('ratingTags', '').split('--')
                                if t.strip()
                            ] if r.get('node', {}).get('ratingTags') else [],
                            'attendanceMandatory': r.get('node', {}).get('attendanceMandatory'),
                        }
                        for r in prof['ratings']['edges'][:10]
                    ]
                
                enriched_teacher = {
                    **teacher,
                    'aggregatedTags': aggregated_tags,
                    'reviews': reviews
                }
            else:
                enriched_teacher = {
                    **teacher,
                    'aggregatedTags': [],
                    'reviews': []
                }
            
            enriched.append(enriched_teacher)
        
        return enriched
    
    def search_courses(self, course_code: Optional[str] = None, 
                      instructor: Optional[str] = None,
                      limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search courses by course code, title, or instructor name.
        
        Args:
            course_code: Course code or title to search for (e.g., "C S 142" or "Introduction")
            instructor: Instructor name to filter by
            limit: Maximum number of results to return
        
        Returns:
            List of course dictionaries matching the search criteria
        """
        filtered = self.courses_data
        
        # Filter by course code or title
        if course_code:
            search = course_code.lower()
            filtered = [
                course for course in filtered
                if (search in course.get('course_name', '').lower() or
                    search in course.get('full_title', '').lower())
            ]
        
        # Filter by instructor
        if instructor:
            search = instructor.lower()
            filtered = [
                {
                    **course,
                    'sections': [
                        section for section in course.get('sections', [])
                        if search in section.get('instructor_name', '').lower()
                    ]
                }
                for course in filtered
            ]
            # Remove courses with no matching sections
            filtered = [course for course in filtered if course['sections']]
        
        return filtered[:limit]
    
    def get_course_by_code(self, course_code: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific course by its exact course code.
        
        Args:
            course_code: Exact course code (e.g., "C S 142")
        
        Returns:
            Course dictionary or None if not found
        """
        for course in self.courses_data:
            if course.get('course_name', '').upper() == course_code.upper():
                return course
        return None
    
    def get_courses_by_instructor(self, instructor_name: str) -> List[Dict[str, Any]]:
        """
        Get all courses taught by a specific instructor.
        
        Args:
            instructor_name: Name of the instructor
        
        Returns:
            List of courses taught by the instructor
        """
        results = []
        search = instructor_name.lower()
        
        for course in self.courses_data:
            matching_sections = [
                section for section in course.get('sections', [])
                if search in section.get('instructor_name', '').lower()
            ]
            
            if matching_sections:
                course_copy = course.copy()
                course_copy['sections'] = matching_sections
                results.append(course_copy)
        
        return results


def main():
    """Example usage of the query tool."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Query BYU professor ratings, reviews, and courses')
    parser.add_argument('--data-dir', type=str, help='Directory containing data files')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Teacher ratings command
    ratings_parser = subparsers.add_parser('ratings', help='Query teacher ratings')
    ratings_parser.add_argument('--teacher-name', type=str, help='Teacher name to search for')
    ratings_parser.add_argument('--with-reviews', action='store_true', 
                               help='Include reviews in results')
    
    # Course search command
    courses_parser = subparsers.add_parser('courses', help='Search courses')
    courses_parser.add_argument('--course-code', type=str, help='Course code or title to search')
    courses_parser.add_argument('--instructor', type=str, help='Instructor name to filter by')
    courses_parser.add_argument('--limit', type=int, default=50, help='Maximum results')
    
    args = parser.parse_args()
    
    # Initialize tool
    tool = BYUQueryTool(data_dir=args.data_dir)
    
    # Execute command
    if args.command == 'ratings':
        if args.with_reviews:
            results = tool.get_teacher_ratings_with_reviews(args.teacher_name)
        else:
            results = tool.get_teacher_ratings(args.teacher_name)
        
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    elif args.command == 'courses':
        results = tool.search_courses(
            course_code=args.course_code,
            instructor=args.instructor,
            limit=args.limit
        )
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

