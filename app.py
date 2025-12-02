#!/usr/bin/env python3
import streamlit as st
from course_search import CourseSearch
from supabase import create_client, Client
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(".") / ".env")

# Page configuration
st.set_page_config(page_title="Course Search", layout="wide")
st.title("🔍 Course Search")

# Initialize session state
if "searcher" not in st.session_state:
    st.session_state.searcher = CourseSearch()

if "supabase" not in st.session_state:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    st.session_state.supabase = create_client(url, key)

searcher = st.session_state.searcher
supabase = st.session_state.supabase

def fetch_section_times(section_id: int):
    """Fetch all times for a section."""
    try:
        resp = supabase.table("section_times").select("*").eq("section_id", section_id).execute()
        return resp.data or []
    except Exception as e:
        st.error(f"Error fetching section times: {e}")
        return []

def get_day_order(days_str: str) -> int:
    """Get the order of the first day in a days string (M=0, T=1, W=2, etc.)"""
    day_map = {"M": 0, "T": 1, "W": 2, "R": 3, "F": 4, "S": 5, "U": 6}
    if not days_str:
        return 7
    first_day = days_str.split()[0]
    return day_map.get(first_day, 7)

def format_time_slot(time_data: dict) -> str:
    """Format a single time slot."""
    days = time_data.get("days", "")
    start = time_data.get("start_time", "")
    end = time_data.get("end_time", "")
    building = time_data.get("building", "")
    room = time_data.get("room", "")
    
    location = f"{building} {room}".strip()
    time_str = f"{start} - {end}".strip()
    
    return f"{days} {time_str} @ {location}"

# Search input
query = st.text_input(
    "Search for a course",
    placeholder="e.g., 'MATH 320', 'Linear Algebra', 'CS'",
    label_visibility="collapsed"
)

# Execute search
if query:
    with st.spinner("Searching..."):
        try:
            results = searcher.search(query)
        except Exception as e:
            st.error(f"Search error: {str(e)}")
            st.info("This error typically occurs due to Supabase connection issues. Try again in a moment.")
            results = []
    
    if not results:
        st.info("No courses found matching your query.")
    else:
        st.success(f"Found {len(results)} course(s)")
        
        # Display each course as an expander
        for course in results:
            course_header = f"{course['course_code']} — {course['full_title']}"
            
            with st.expander(course_header, expanded=False):
                st.markdown(f"**Department:** {course['dept_name']}")
                
                # Fetch all section times for this course
                section_times_map = {}
                for prof in course['professors']:
                    for sec in prof['sections']:
                        sec_id = sec['section_id']
                        if sec_id not in section_times_map:
                            times = fetch_section_times(sec_id)
                            # Sort by day of week first, then by start time
                            times = sorted(times, key=lambda t: (get_day_order(t.get("days", "")), t.get("start_time", "")))
                            section_times_map[sec_id] = times
                
                # Build a map of section_id -> professor info
                section_prof_map = {}
                for prof in course['professors']:
                    for sec in prof['sections']:
                        section_prof_map[sec['section_id']] = prof
                
                # Collect all unique sections with their times
                all_sections = []
                for prof in course['professors']:
                    for sec in prof['sections']:
                        times = section_times_map.get(sec['section_id'], [])
                        all_sections.append({
                            'section': sec,
                            'professor': prof,
                            'times': times
                        })
                
                # Sort sections by first time
                def get_section_sort_key(item):
                    times = item['times']
                    if times:
                        return (get_day_order(times[0].get("days", "")), times[0].get("start_time", ""))
                    return (7, "99:99 PM")
                
                all_sections = sorted(all_sections, key=get_section_sort_key)
                
                # Display sections organized by time
                for item in all_sections:
                    sec = item['section']
                    prof = item['professor']
                    times = item['times']
                    
                    prof_name = f"{prof['first_name']} {prof['last_name']}".strip() or "Unknown"
                    
                    # Build section header with time info
                    if times:
                        time_display = " | ".join([format_time_slot(t) for t in times])
                        sec_header = f"Section {sec['section_number']} — {time_display}"
                    else:
                        sec_header = f"Section {sec['section_number']} (no times)"
                    
                    with st.expander(sec_header, expanded=False):
                        # Professor summary (always visible)
                        st.markdown(f"**Professor:** {prof_name}")
                        
                        prof_cols = st.columns(3)
                        
                        if prof['avg_rating'] is not None:
                            with prof_cols[0]:
                                st.metric("Rating", f"{prof['avg_rating']:.2f}/5.0")
                            with prof_cols[1]:
                                st.metric("Difficulty", f"{prof['avg_difficulty']:.2f}/5.0")
                            with prof_cols[2]:
                                st.metric("Would Retake", f"{prof['would_take_again_percent']:.0f}%")
                        else:
                            st.info("No ratings yet")
                        
                        st.markdown("---")
                        
                        # Section details
                        st.markdown("**Section Details:**")
                        st.write(f"**Credit Hours:** {sec['credit_hours']}")
                        st.write(f"**Type:** {sec['section_type']}")
                        st.write(f"**Mode:** {sec['mode_desc']}")
                        
                        # Professor reviews dropdown
                        if prof['ratings']:
                            st.markdown("---")
                            with st.expander("📋 Professor Reviews", expanded=False):
                                for rating in prof['ratings'][:5]:
                                    with st.container(border=True):
                                        # Rating metadata
                                        meta_cols = st.columns([1, 1, 1, 1])
                                        
                                        if rating['clarity_rating']:
                                            with meta_cols[0]:
                                                st.write(f"🎯 Clarity: **{rating['clarity_rating']}/5**")
                                        
                                        if rating['helpful_rating']:
                                            with meta_cols[1]:
                                                st.write(f"💡 Helpful: **{rating['helpful_rating']}/5**")
                                        
                                        if rating['difficulty_rating']:
                                            with meta_cols[2]:
                                                st.write(f"📊 Difficulty: **{rating['difficulty_rating']}/5**")
                                        
                                        if rating['would_take_again']:
                                            with meta_cols[3]:
                                                st.write(f"✅ Would Retake")
                                        
                                        # Comment
                                        if rating['comment']:
                                            st.write(f"_{rating['comment']}_")
                                        
                                        # Tags
                                        if rating['tags']:
                                            st.caption(" • ".join(rating['tags']))
                        
else:
    st.write("Enter a course name, code, or department to get started!")