-- BYU Courses Database Schema (Supabase/PostgreSQL)
-- Generated: 2025-12-01T22:01:49.153683

-- Drop tables
DROP TABLE IF EXISTS professor_name_variants CASCADE;
DROP TABLE IF EXISTS rating_tags CASCADE;
DROP TABLE IF EXISTS ratings CASCADE;
DROP TABLE IF EXISTS section_times CASCADE;
DROP TABLE IF EXISTS sections CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS professors CASCADE;

-- Create tables
CREATE TABLE professors (
            professor_id SERIAL PRIMARY KEY,
            rmp_id TEXT UNIQUE,
            rmp_legacy_id INTEGER,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            department TEXT,
            school TEXT,
            avg_rating DOUBLE PRECISION,
            avg_difficulty DOUBLE PRECISION,
            num_ratings INTEGER,
            would_take_again_percent DOUBLE PRECISION,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE courses (
            course_id SERIAL PRIMARY KEY,
            course_key TEXT UNIQUE NOT NULL,
            year_term TEXT,
            curriculum_id TEXT,
            title_code TEXT,
            dept_name TEXT,
            catalog_number TEXT,
            catalog_suffix TEXT,
            title TEXT,
            full_title TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

CREATE TABLE sections (
            section_id SERIAL PRIMARY KEY,
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
        );

CREATE TABLE section_times (
            time_id SERIAL PRIMARY KEY,
            section_id INTEGER NOT NULL,
            days TEXT,
            start_time TEXT,
            end_time TEXT,
            building TEXT,
            room TEXT,
            FOREIGN KEY (section_id) REFERENCES sections(section_id)
        );

CREATE TABLE ratings (
            rating_id SERIAL PRIMARY KEY,
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
        );

CREATE TABLE rating_tags (
            tag_id SERIAL PRIMARY KEY,
            rating_id INTEGER NOT NULL,
            tag_name TEXT NOT NULL,
            FOREIGN KEY (rating_id) REFERENCES ratings(rating_id)
        );

CREATE TABLE professor_name_variants (
            variant_id SERIAL PRIMARY KEY,
            professor_id INTEGER NOT NULL,
            variant_name TEXT NOT NULL,
            source TEXT,
            match_confidence DOUBLE PRECISION,
            FOREIGN KEY (professor_id) REFERENCES professors(professor_id)
        );

