import json
import requests
import time

def fetch_professor_ratings_page(professor_id, after_cursor=None, first=5):
    """Fetch a page of professor ratings with optional pagination"""
    url = "https://www.ratemyprofessors.com/graphql"
    
    # Simplified query focusing on ratings pagination
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
      numRatings
      ratings(first: $first, after: $after) {
        edges {
          cursor
          node {
            id
            legacyId
            comment
            date
            class
            helpfulRating
            clarityRating
            difficultyRating
            grade
            wouldTakeAgain
            attendanceMandatory
            textbookUse
            isForOnlineClass
            isForCredit
            ratingTags
            thumbsUpTotal
            thumbsDownTotal
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
  }
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

def test_pagination():
    # Use a professor with many reviews for testing
    # David Hollan has 1707 ratings
    test_professor_id = "VGVhY2hlci0yMzMwNzY0"
    
    print("=" * 80)
    print("TEST 1: Fetch first page with first=5")
    print("=" * 80)
    result1 = fetch_professor_ratings_page(test_professor_id, first=5)
    print(json.dumps(result1, indent=2))
    print("\n")
    time.sleep(1)
    
    # Extract pageInfo from first request
    if result1.get('data') and result1['data'].get('node'):
        teacher = result1['data']['node']
        if teacher.get('ratings'):
            page_info = teacher['ratings']['pageInfo']
            end_cursor = page_info.get('endCursor')
            has_next = page_info.get('hasNextPage')
            
            print("=" * 80)
            print(f"TEST 2: Fetch second page using endCursor: {end_cursor}")
            print(f"hasNextPage: {has_next}")
            print("=" * 80)
            
            if has_next and end_cursor:
                result2 = fetch_professor_ratings_page(test_professor_id, after_cursor=end_cursor, first=5)
                print(json.dumps(result2, indent=2))
                print("\n")
                time.sleep(1)
                
                # Try fetching more pages
                if result2.get('data') and result2['data'].get('node'):
                    teacher2 = result2['data']['node']
                    if teacher2.get('ratings'):
                        page_info2 = teacher2['ratings']['pageInfo']
                        end_cursor2 = page_info2.get('endCursor')
                        has_next2 = page_info2.get('hasNextPage')
                        
                        print("=" * 80)
                        print(f"TEST 3: Fetch third page using endCursor: {end_cursor2}")
                        print(f"hasNextPage: {has_next2}")
                        print("=" * 80)
                        
                        if has_next2 and end_cursor2:
                            result3 = fetch_professor_ratings_page(test_professor_id, after_cursor=end_cursor2, first=5)
                            print(json.dumps(result3, indent=2))
                            print("\n")
                            time.sleep(1)
    
    print("=" * 80)
    print("TEST 4: Try fetching with larger first value (first=20)")
    print("=" * 80)
    result4 = fetch_professor_ratings_page(test_professor_id, first=20)
    print(json.dumps(result4, indent=2))
    print("\n")
    time.sleep(1)
    
    print("=" * 80)
    print("TEST 5: Try fetching with first=100")
    print("=" * 80)
    result5 = fetch_professor_ratings_page(test_professor_id, first=100)
    print(json.dumps(result5, indent=2))
    print("\n")

if __name__ == "__main__":
    test_pagination()




