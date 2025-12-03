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

def deduplicate_times(times: list) -> list:
    """Remove duplicate time entries, keeping only unique combinations."""
    seen = set()
    unique = []
    for t in times:
        key = (t.get("days"), t.get("start_time"), t.get("end_time"), 
               t.get("building"), t.get("room"))
        if key not in seen:
            seen.add(key)
            unique.append(t)
    return unique

def display_time_boxes(times: list):
    """Display meeting times as Apple-style tags."""
    if not times:
        st.caption("No times scheduled")
        return
    
    # Deduplicate times
    unique_times = deduplicate_times(times)
    
    # Create tag HTML
    tags_html = '<div style="display: flex; flex-wrap: wrap; gap: 8px;">'
    
    for time_data in unique_times:
        days = time_data.get("days", "")
        start = time_data.get("start_time", "")
        end = time_data.get("end_time", "")
        building = time_data.get("building", "")
        room = time_data.get("room", "")
        
        location = f"{building} {room}".strip() if building or room else "TBA"
        time_str = f"{start} - {end}".strip() if start or end else "TBA"
        
        tag_content = f"{days} | {time_str} | {location}"
        
        tags_html += f"""
        <div style="display: inline-flex; align-items: center; background-color: #f0f0f0; border: 1px solid #d0d0d0; border-radius: 20px; padding: 6px 12px; font-size: 13px; color: #333; white-space: nowrap;">
            {tag_content}
        </div>
        """
    
    tags_html += '</div>'
    st.markdown(tags_html, unsafe_allow_html=True)

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
                
                # Sort sections by section number (as requested in edit prompt)
                def section_number_sort_key(item):
                    # Handle both string and int section_numbers
                    sec_num = item['section'].get('section_number', None)
                    # Try to convert to int for proper numeric ordering, fallback to string
                    try:
                        return int(sec_num)
                    except (ValueError, TypeError):
                        return str(sec_num).zfill(8) if sec_num is not None else ""
                
                all_sections = sorted(all_sections, key=section_number_sort_key)
                
                # Display sections organized by section number
                for item in all_sections:
                    sec = item['section']
                    prof = item['professor']
                    times = item['times']
                    
                    prof_name = f"{prof['first_name']} {prof['last_name']}".strip() or "Unknown"
                    
                    # Build section header with consolidated time info
                    unique_times = deduplicate_times(times)
                    
                    # Consolidate times that are the same and combine days
                    time_to_days = {}
                    for t in unique_times:
                        days = t.get('days', '')
                        time_str = f"{t.get('start_time', '')}-{t.get('end_time', '')}".strip("-")
                        if days and time_str:
                            if time_str not in time_to_days:
                                time_to_days[time_str] = []
                            time_to_days[time_str].append(days)
                    
                    # Create consolidated header string
                    time_parts = []
                    for time_str, days_list in time_to_days.items():
                        combined_days = " ".join(days_list)
                        time_parts.append(f"{combined_days} {time_str}")
                    
                    time_header = " ".join(time_parts) if time_parts else ""
                    sec_header = f"Section {sec['section_number']} — {prof_name} • {time_header}".rstrip(" •")
                    
                    with st.expander(sec_header, expanded=False):
                        # Display time tags inside expander
                        if unique_times:
                            # st.markdown("**Meeting Times:**")
                            prof_col, time_col = st.columns([2,1])
                            with prof_col:
                                st.markdown(f"### **Professor:** {prof_name}")
                            with time_col:
                                st.markdown('<div style="margin-top:8px"></div>', unsafe_allow_html=True)
                                display_time_boxes(unique_times)
                        
                        prof_cols = st.columns(3)
                        
                        if prof['avg_rating'] is not None:
                            def get_color(val):
                                """Given a value between 1 and 5, return a hex color based on the scale."""
                                if val < 1.8:
                                    return "#ff3b30"  # red
                                elif val < 2.6:
                                    return "#ff9500"  # orange
                                elif val < 3.4:
                                    return "#ffcc00"  # yellow
                                elif val < 4.2:
                                    return "#34c759"  # green
                                else:
                                    return "#007aff"  # blue

                            # Ensure values are in the 1-5 range for display and color
                            avg_rating_val = min(max(prof['avg_rating'], 1), 5) if prof['avg_rating'] is not None else 1
                            avg_diff_val = min(max(prof['avg_difficulty'], 1), 5) if prof['avg_difficulty'] is not None else 1
                            # Flip for difficulty color (easy=blue, hard=red)
                            avg_diff_val_flipped = 6 - avg_diff_val
                            would_retake_val = (prof['would_take_again_percent'] or 0) / 100.0

                            rating_color = get_color(avg_rating_val)
                            diff_color = get_color(avg_diff_val_flipped)
                            # For would retake, interpolate into 1-5
                            would_retake_score = 1 + 4 * would_retake_val
                            retake_color = get_color(would_retake_score)

                            with prof_cols[0]:
                                st.markdown(
                                    "<div style='margin-bottom: -10px;'><h4 style='margin-bottom:2px;margin-top:2px;'>Rating</h4></div>",
                                    unsafe_allow_html=True
                                )
                                st.markdown(
                                    f"<div style='font-size: 1.6em; font-weight: 600; color:{rating_color}; margin-top:-10px; margin-bottom:-18px'>{prof['avg_rating']:.2f}/5.0</div>",
                                    unsafe_allow_html=True
                                )
                            with prof_cols[1]:
                                st.markdown(
                                    "<div style='margin-bottom: -10px;'><h4 style='margin-bottom:2px;margin-top:2px;'>Difficulty</h4></div>",
                                    unsafe_allow_html=True
                                )
                                st.markdown(
                                    f"<div style='font-size: 1.6em; font-weight: 600; color:{diff_color}; margin-top:-10px; margin-bottom:-18px'>{prof['avg_difficulty']:.2f}/5.0</div>",
                                    unsafe_allow_html=True
                                )
                            with prof_cols[2]:
                                st.markdown(
                                    "<div style='margin-bottom: -10px;'><h4 style='margin-bottom:2px;margin-top:2px;'>Would Retake</h4></div>",
                                    unsafe_allow_html=True
                                )
                                st.markdown(
                                    f"<div style='font-size: 1.6em; font-weight: 600; color:{retake_color}; margin-top:-10px; margin-bottom:-18px'>{prof['would_take_again_percent']:.0f}%</div>",
                                    unsafe_allow_html=True
                                )
                        else:
                            st.info("No ratings yet")
                        
                        st.markdown("---")
                        
                        # Section details
                        # '''st.markdown("**Section Details:**")
                        # st.write(f"**Credit Hours:** {sec['credit_hours']}")
                        # st.write(f"**Type:** {sec['section_type']}")
                        # st.write(f"**Mode:** {sec['mode_desc']}")'''
                        
                        # Professor reviews dropdown
                        if prof['ratings']:
                            # st.markdown("---")    
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