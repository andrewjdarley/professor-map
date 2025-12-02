import json
import requests
import time

def fetch_professor_data(professor_id, after_cursor=None, first=100):
    url = "https://www.ratemyprofessors.com/graphql"
    
    # Paste your entire query here
    query = """query TeacherRatingsPageQuery(
  $id: ID!
  $first: Int!
  $after: String
) {
  node(id: $id) {
    __typename
    ... on Teacher {
      id
      legacyId
      firstName
      lastName
      department
      school {
        legacyId
        name
        city
        state
        country
        id
      }
      lockStatus
      ...StickyHeaderContent_teacher
      ...MiniStickyHeader_teacher
      ...TeacherBookmark_teacher
      ...RatingDistributionWrapper_teacher
      ...TeacherInfo_teacher
      ...SimilarProfessors_teacher
      ...TeacherRatingTabs_teacher
    }
    id
  }
}

fragment CompareProfessorLink_teacher on Teacher {
  legacyId
}

fragment CourseMeta_rating on Rating {
  attendanceMandatory
  wouldTakeAgain
  grade
  textbookUse
  isForOnlineClass
  isForCredit
}

fragment HeaderDescription_teacher on Teacher {
  id
  legacyId
  firstName
  lastName
  department
  school {
    legacyId
    name
    city
    state
    id
  }
  ...TeacherTitles_teacher
  ...TeacherBookmark_teacher
  ...RateTeacherLink_teacher
  ...CompareProfessorLink_teacher
}

fragment HeaderRateButton_teacher on Teacher {
  ...RateTeacherLink_teacher
  ...CompareProfessorLink_teacher
}

fragment MiniStickyHeader_teacher on Teacher {
  id
  legacyId
  firstName
  lastName
  department
  departmentId
  school {
    legacyId
    name
    city
    state
    id
  }
  ...TeacherBookmark_teacher
  ...RateTeacherLink_teacher
  ...CompareProfessorLink_teacher
}

fragment NameLink_teacher on Teacher {
  isProfCurrentUser
  id
  legacyId
  firstName
  lastName
  school {
    name
    id
  }
}

fragment NameTitle_teacher on Teacher {
  id
  firstName
  lastName
  department
  school {
    legacyId
    name
    id
  }
  ...TeacherDepartment_teacher
  ...TeacherBookmark_teacher
}

fragment NoRatingsArea_teacher on Teacher {
  lastName
  ...RateTeacherLink_teacher
}

fragment NumRatingsLink_teacher on Teacher {
  numRatings
  ...RateTeacherLink_teacher
}

fragment ProfessorNoteEditor_rating on Rating {
  id
  legacyId
  class
  teacherNote {
    id
    teacherId
    comment
  }
}

fragment ProfessorNoteEditor_teacher on Teacher {
  id
}

fragment ProfessorNoteFooter_note on TeacherNotes {
  legacyId
  flagStatus
}

fragment ProfessorNoteFooter_teacher on Teacher {
  legacyId
  isProfCurrentUser
}

fragment ProfessorNoteHeader_note on TeacherNotes {
  createdAt
  updatedAt
}

fragment ProfessorNoteHeader_teacher on Teacher {
  lastName
}

fragment ProfessorNoteSection_rating on Rating {
  teacherNote {
    ...ProfessorNote_note
    id
  }
  ...ProfessorNoteEditor_rating
}

fragment ProfessorNoteSection_teacher on Teacher {
  ...ProfessorNote_teacher
  ...ProfessorNoteEditor_teacher
}

fragment ProfessorNote_note on TeacherNotes {
  comment
  ...ProfessorNoteHeader_note
  ...ProfessorNoteFooter_note
}

fragment ProfessorNote_teacher on Teacher {
  ...ProfessorNoteHeader_teacher
  ...ProfessorNoteFooter_teacher
}

fragment RateTeacherLink_teacher on Teacher {
  legacyId
  numRatings
  lockStatus
}

fragment RatingDistributionChart_ratingsDistribution on ratingsDistribution {
  r1
  r2
  r3
  r4
  r5
}

fragment RatingDistributionWrapper_teacher on Teacher {
  ...NoRatingsArea_teacher
  ratingsDistribution {
    total
    ...RatingDistributionChart_ratingsDistribution
  }
}

fragment RatingFooter_rating on Rating {
  id
  comment
  adminReviewedAt
  flagStatus
  legacyId
  thumbsUpTotal
  thumbsDownTotal
  thumbs {
    thumbsUp
    thumbsDown
    computerId
    id
  }
  teacherNote {
    id
  }
  ...Thumbs_rating
}

fragment RatingFooter_teacher on Teacher {
  id
  legacyId
  lockStatus
  isProfCurrentUser
  ...Thumbs_teacher
}

fragment RatingHeader_rating on Rating {
  legacyId
  date
  class
  helpfulRating
  clarityRating
  isForOnlineClass
}

fragment RatingSuperHeader_rating on Rating {
  legacyId
}

fragment RatingSuperHeader_teacher on Teacher {
  firstName
  lastName
  legacyId
  school {
    name
    id
  }
}

fragment RatingTags_rating on Rating {
  ratingTags
}

fragment RatingValue_teacher on Teacher {
  avgRating
  numRatings
  ...NumRatingsLink_teacher
}

fragment RatingValues_rating on Rating {
  helpfulRating
  clarityRating
  difficultyRating
}

fragment Rating_rating on Rating {
  comment
  flagStatus
  createdByUser
  teacherNote {
    id
  }
  ...RatingHeader_rating
  ...RatingSuperHeader_rating
  ...RatingValues_rating
  ...CourseMeta_rating
  ...RatingTags_rating
  ...RatingFooter_rating
  ...ProfessorNoteSection_rating
}

fragment Rating_teacher on Teacher {
  ...RatingFooter_teacher
  ...RatingSuperHeader_teacher
  ...ProfessorNoteSection_teacher
}

fragment RatingsFilter_teacher on Teacher {
  courseCodes {
    courseCount
    courseName
  }
}

fragment RatingsList_teacher on Teacher {
  id
  legacyId
  lastName
  numRatings
  school {
    id
    legacyId
    name
    city
    state
    avgRating
    numRatings
  }
  ...Rating_teacher
  ...NoRatingsArea_teacher
  ratings(first: $first, after: $after) {
    edges {
      cursor
      node {
        ...Rating_rating
        id
        __typename
      }
    }
    pageInfo {
      hasNextPage
      endCursor
      startCursor
      hasPreviousPage
    }
  }
}

fragment SimilarProfessorListItem_teacher on RelatedTeacher {
  legacyId
  firstName
  lastName
  avgRating
}

fragment SimilarProfessors_teacher on Teacher {
  department
  relatedTeachers {
    legacyId
    ...SimilarProfessorListItem_teacher
    id
  }
}

fragment StickyHeaderContent_teacher on Teacher {
  ...HeaderDescription_teacher
  ...HeaderRateButton_teacher
  ...MiniStickyHeader_teacher
}

fragment TeacherBookmark_teacher on Teacher {
  id
  isSaved
}

fragment TeacherDepartment_teacher on Teacher {
  department
  departmentId
  school {
    legacyId
    name
    isVisible
    id
  }
}

fragment TeacherFeedback_teacher on Teacher {
  numRatings
  avgDifficulty
  wouldTakeAgainPercent
}

fragment TeacherInfo_teacher on Teacher {
  id
  lastName
  numRatings
  ...RatingValue_teacher
  ...NameTitle_teacher
  ...TeacherTags_teacher
  ...NameLink_teacher
  ...TeacherFeedback_teacher
  ...RateTeacherLink_teacher
  ...CompareProfessorLink_teacher
}

fragment TeacherRatingTabs_teacher on Teacher {
  numRatings
  courseCodes {
    courseName
    courseCount
  }
  ...RatingsList_teacher
  ...RatingsFilter_teacher
}

fragment TeacherTags_teacher on Teacher {
  lastName
  teacherRatingTags {
    legacyId
    tagCount
    tagName
    id
  }
}

fragment TeacherTitles_teacher on Teacher {
  department
  school {
    legacyId
    name
    id
  }
}

fragment Thumbs_rating on Rating {
  id
  comment
  adminReviewedAt
  flagStatus
  legacyId
  thumbsUpTotal
  thumbsDownTotal
  thumbs {
    computerId
    thumbsUp
    thumbsDown
    id
  }
  teacherNote {
    id
  }
}

fragment Thumbs_teacher on Teacher {
  id
  legacyId
  lockStatus
  isProfCurrentUser
}
"""
    
    variables = {
        "id": professor_id,
        "first": first
    }
    
    if after_cursor:
        variables["after"] = after_cursor
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def fetch_all_professor_reviews(professor_id):
    """Fetch all reviews for a professor using pagination"""
    all_edges = []  # Store full edges (cursor + node) to preserve original cursors
    after_cursor = None
    first_response = None
    
    while True:
        response = fetch_professor_data(professor_id, after_cursor=after_cursor, first=100)
        
        # Save first response for the teacher metadata
        if first_response is None:
            first_response = response
            teacher_data = response.get('data', {}).get('node', {})
            if not teacher_data or teacher_data.get('__typename') != 'Teacher':
                return response  # Return error response if not a teacher
        
        # Extract ratings from this page
        teacher = response.get('data', {}).get('node', {})
        if not teacher or teacher.get('__typename') != 'Teacher':
            break
            
        ratings_data = teacher.get('ratings', {})
        edges = ratings_data.get('edges', [])
        page_info = ratings_data.get('pageInfo', {})
        
        # Add full edges (preserving original cursors) from this page
        all_edges.extend(edges)
        
        # Check if there are more pages
        has_next = page_info.get('hasNextPage', False)
        if not has_next:
            break
        
        # Get cursor for next page
        after_cursor = page_info.get('endCursor')
        if not after_cursor:
            break
        
        # Be nice to the API
        time.sleep(0.12)
    
    # Reconstruct the response with all ratings
    if first_response:
        teacher_data = first_response.get('data', {}).get('node', {})
        
        if teacher_data and teacher_data.get('__typename') == 'Teacher':
            # Replace the ratings with all collected edges (preserving original cursors)
            first_cursor = all_edges[0].get('cursor') if all_edges else None
            last_cursor = all_edges[-1].get('cursor') if all_edges else None
            
            teacher_data['ratings'] = {
                'edges': all_edges,
                'pageInfo': {
                    'hasNextPage': False,
                    'endCursor': last_cursor,
                    'startCursor': first_cursor,
                    'hasPreviousPage': False
                }
            }
            
            return {
                'data': {
                    'node': teacher_data
                }
            }
    
    return first_response if first_response else response

def main():
    with open('byu_professors.json', 'r') as f:
        professors = json.load(f)
    
    first_10 = professors # [:10]
    all_responses = []
    
    # Try to load existing data if file exists
    output_file = 'ratings.json'
    try:
        with open(output_file, 'r') as f:
            all_responses = json.load(f)
            print(f"Loaded {len(all_responses)} existing responses. Resuming...")
    except FileNotFoundError:
        print("Starting fresh...")
    
    print(f"Fetching {len(first_10)} professors...\n")
    
    for i, prof in enumerate(first_10, 1):
        print(f"{i}. {prof.get('firstName')} {prof.get('lastName')}...")
        response = fetch_all_professor_reviews(prof['id'])
        
        # Count reviews fetched
        teacher = response.get('data', {}).get('node', {})
        if teacher and teacher.get('__typename') == 'Teacher':
            ratings_count = len(teacher.get('ratings', {}).get('edges', []))
            num_ratings = teacher.get('numRatings', 0)
            print(f"    → Fetched {ratings_count} reviews (total available: {num_ratings})")
        
        all_responses.append(response)
        time.sleep(.12)  # Be nice to the API
        
        # Save every 100 professors
        if i % 100 == 0:
            with open(output_file, 'w') as f:
                json.dump(all_responses, f, indent=2)
            print(f"  → Progress saved ({i}/{len(first_10)})")
    
    # Final save
    with open(output_file, 'w') as f:
        json.dump(all_responses, f, indent=2)
    
    print(f"\n✓ Done! Saved to '{output_file}'")

if __name__ == "__main__":
    main()