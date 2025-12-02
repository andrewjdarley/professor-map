#!/usr/bin/env python3
import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(Path(".") / ".env")

def normalize(s: str) -> str:
    """Normalize strings for flexible comparison."""
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9]", "", s)
    return s

class CourseSearch:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL or SUPABASE_KEY missing from .env")
        self.client: Client = create_client(url, key)

    def fetch_all_courses(self) -> List[Dict[str, Any]]:
        all_courses = []
        page_size = 1000
        offset = 0
        
        while True:
            resp = self.client.table("courses").select("*").range(offset, offset + page_size - 1).execute()
            if not resp.data:
                break
            all_courses.extend(resp.data)
            if len(resp.data) < page_size:
                break
            offset += page_size
        
        return all_courses

    def fetch_sections_for_course(self, course_id: int) -> List[Dict[str, Any]]:
        """Fetch all sections for a specific course with professor details."""
        resp = self.client.table("sections").select(
            "*, professor:professor_id(professor_id, first_name, last_name, avg_rating, avg_difficulty, num_ratings, would_take_again_percent)"
        ).eq("course_id", course_id).execute()
        return resp.data or []

    def fetch_professor_ratings(self, professor_id: int) -> List[Dict[str, Any]]:
        """Fetch all ratings and tags for a professor."""
        resp = self.client.table("ratings").select(
            "*, tags:rating_id(tag_name)"
        ).eq("professor_id", professor_id).execute()
        return resp.data or []

    def search(self, query: str, debug: bool = False) -> List[Dict[str, Any]]:
        """
        Search courses and return structured results with sections and professor info.
        Avoids returning duplicate professor/rating data.
        """
        if not query or not query.strip():
            return []

        q_norm = normalize(query)
        all_courses = self.fetch_all_courses()
        matched_courses = []

        if debug:
            print(f"  Query: '{query}' → normalized: '{q_norm}'")
            print(f"  Total courses in DB: {len(all_courses)}")

        # Find matching courses
        for c in all_courses:
            dept = c.get("dept_name", "").strip()
            num = str(c.get("catalog_number", "")).strip()
            suf = (c.get("catalog_suffix") or "").strip()
            title = c.get("title", "").strip()
            full_title = c.get("full_title", "").strip()

            dept_norm = normalize(dept)
            num_norm = normalize(num)
            suf_norm = normalize(suf)
            course_code_norm = dept_norm + num_norm + suf_norm
            
            title_norm = normalize(title)
            full_title_norm = normalize(full_title)

            matched = False

            if q_norm == dept_norm:
                matched = True
            elif course_code_norm.startswith(q_norm) and q_norm != dept_norm:
                matched = True
            elif q_norm in title_norm or q_norm in full_title_norm:
                matched = True

            if matched:
                matched_courses.append(c)

        if debug:
            print(f"  Found {len(matched_courses)} matching courses\n")

        # Build results with sections and professor data
        results = []
        professor_cache = {}  # Cache to avoid fetching same professor multiple times

        for course in matched_courses:
            course_id = course.get("course_id")
            dept = course.get("dept_name", "").strip()
            num = str(course.get("catalog_number", "")).strip()
            suf = (course.get("catalog_suffix") or "").strip()
            course_code = f"{dept} {num}{suf}".strip()

            sections = self.fetch_sections_for_course(course_id)
            
            # Group sections by professor to avoid duplicating professor info
            professor_sections = {}  # professor_id -> list of sections
            
            for section in sections:
                prof_id = section.get("professor_id")
                if prof_id not in professor_sections:
                    professor_sections[prof_id] = []
                professor_sections[prof_id].append(section)

            # Build professor entries with their ratings and sections
            professors_data = []
            
            for prof_id, sections_for_prof in professor_sections.items():
                # Fetch professor details and ratings
                if prof_id and prof_id not in professor_cache:
                    ratings = self.fetch_professor_ratings(prof_id)
                    professor_cache[prof_id] = ratings
                else:
                    ratings = professor_cache.get(prof_id, [])

                # Use professor info from first section
                prof_info = sections_for_prof[0].get("professor") or {}
                
                prof_entry = {
                    "professor_id": prof_id,
                    "first_name": prof_info.get("first_name", ""),
                    "last_name": prof_info.get("last_name", ""),
                    "avg_rating": prof_info.get("avg_rating"),
                    "avg_difficulty": prof_info.get("avg_difficulty"),
                    "num_ratings": prof_info.get("num_ratings"),
                    "would_take_again_percent": prof_info.get("would_take_again_percent"),
                    "sections": [
                        {
                            "section_id": sec.get("section_id"),
                            "section_number": sec.get("section_number"),
                            "credit_hours": sec.get("credit_hours"),
                            "section_type": sec.get("section_type"),
                            "mode": sec.get("mode"),
                            "mode_desc": sec.get("mode_desc"),
                        }
                        for sec in sections_for_prof
                    ],
                    "ratings": [
                        {
                            "rating_id": r.get("rating_id"),
                            "date": r.get("date"),
                            "class_name": r.get("class_name"),
                            "clarity_rating": r.get("clarity_rating"),
                            "helpful_rating": r.get("helpful_rating"),
                            "difficulty_rating": r.get("difficulty_rating"),
                            "comment": r.get("comment"),
                            "grade": r.get("grade"),
                            "would_take_again": r.get("would_take_again"),
                            "tags": [tag.get("tag_name") for tag in r.get("tags", [])] if r.get("tags") else [],
                        }
                        for r in ratings
                    ]
                }
                
                professors_data.append(prof_entry)

            course_entry = {
                "course_id": course_id,
                "course_code": course_code,
                "title": course.get("title", ""),
                "full_title": course.get("full_title", ""),
                "dept_name": course.get("dept_name", ""),
                "catalog_number": course.get("catalog_number", ""),
                "professors": professors_data
            }
            
            results.append(course_entry)

        return results


if __name__ == "__main__":
    searcher = CourseSearch()
    
    print("=" * 60)
    print("ENHANCED COURSE SEARCH TEST")
    print("=" * 60)
    
    tests = [
        # ("MATH", False),
        ("MATH 320", False),
        ("Linear Algebra", False),
    ]
    
    for query, debug in tests:
        print(f"\n>>> Query: '{query}'")
        results = searcher.search(query, debug=debug)
        
        if results:
            for course in results[:3]:
                print(f"\n  Course: {course['course_code']} - {course['full_title']}")
                print(f"  Department: {course['dept_name']}")
                
                for prof in course['professors']:
                    prof_name = f"{prof['first_name']} {prof['last_name']}".strip() or "Unknown"
                    print(f"\n    Professor: {prof_name}")
                    if prof['avg_rating']:
                        print(f"      Avg Rating: {prof['avg_rating']:.2f}/5.0 ({prof['num_ratings']} ratings)")
                        print(f"      Avg Difficulty: {prof['avg_difficulty']:.2f}/5.0")
                        print(f"      Would Take Again: {prof['would_take_again_percent']:.1f}%")
                    
                    print(f"      Sections: {len(prof['sections'])}")
                    for sec in prof['sections']:
                        sec_info = f"{sec['section_number']} ({sec['section_type']}) - {sec['mode']}"
                        print(f"        - {sec_info}")
                    
                    if prof['ratings']:
                        print(f"      Recent Ratings: {len(prof['ratings'])}")
                        for rating in prof['ratings'][:2]:
                            clarity = f"Clarity: {rating['clarity_rating']}" if rating['clarity_rating'] else "No clarity"
                            helpful = f"Helpful: {rating['helpful_rating']}" if rating['helpful_rating'] else "No helpful"
                            print(f"        - {clarity} | {helpful}")
                            if rating['comment']:
                                comment_preview = rating['comment'][:60] + "..." if len(rating['comment']) > 60 else rating['comment']
                                print(f"          \"{comment_preview}\"")
                    else:
                        print(f"      No ratings yet")
        else:
            print(f"  (no results)")