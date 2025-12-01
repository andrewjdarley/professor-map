#!/usr/bin/env python3
import json

def parse_classes(filename='classes_full.json'):
    """Parse classes JSON and organize by class code"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Data is already organized by class code (curriculum_id-title_code)
    # Just return it
    return data

def save_parsed(data, filename='parsed_classes.json'):
    """Save parsed data"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} courses to {filename}")

if __name__ == "__main__":
    data = parse_classes('classes_full.json')
    save_parsed(data)
    print(f"Total courses: {len(data)}")