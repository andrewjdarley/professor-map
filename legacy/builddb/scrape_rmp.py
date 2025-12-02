import requests
import json
import time
from typing import List, Dict, Optional

class RateMyProfessorsScraper:
    def __init__(self):
        self.url = "https://www.ratemyprofessors.com/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic dGVzdDp0ZXN0",  # Common RMP auth header
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        self.query = """query TeacherSearchPaginationQuery(
          $count: Int!
          $cursor: String
          $query: TeacherSearchQuery!
        ) {
          search: newSearch {
            ...TeacherSearchPagination_search_1jWD3d
          }
        }

        fragment CardFeedback_teacher on Teacher {
          wouldTakeAgainPercent
          avgDifficulty
        }

        fragment CardName_teacher on Teacher {
          firstName
          lastName
        }

        fragment CardSchool_teacher on Teacher {
          department
          school {
            name
            id
          }
        }

        fragment TeacherBookmark_teacher on Teacher {
          id
          isSaved
        }

        fragment TeacherCard_teacher on Teacher {
          id
          legacyId
          avgRating
          numRatings
          ...CardFeedback_teacher
          ...CardSchool_teacher
          ...CardName_teacher
          ...TeacherBookmark_teacher
        }

        fragment TeacherSearchPagination_search_1jWD3d on newSearch {
          teachers(query: $query, first: $count, after: $cursor) {
            didFallback
            edges {
              cursor
              node {
                ...TeacherCard_teacher
                id
                __typename
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
            resultCount
            filters {
              field
              options {
                value
                id
              }
            }
          }
        }
        """
    
    def fetch_page(self, cursor: Optional[str] = None, count: int = 100) -> Dict:
        """Fetch a single page of results"""
        variables = {
            "count": count,
            "cursor": cursor,
            "query": {
                "text": "",
                "schoolID": "U2Nob29sLTEzNQ==",  # BYU school ID
                "fallback": True
            }
        }
        
        payload = {
            "query": self.query,
            "variables": variables
        }
        
        try:
            response = requests.post(self.url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
    
    def scrape_all_professors(self, batch_size: int = 100, delay: float = 1.0) -> List[Dict]:
        """Scrape all professors from BYU"""
        all_professors = []
        cursor = None
        page_num = 0
        
        print("Starting to scrape BYU professors from RateMyProfessors...")
        
        while True:
            page_num += 1
            print(f"\nFetching page {page_num}... (cursor: {cursor})")
            
            data = self.fetch_page(cursor=cursor, count=batch_size)
            
            if not data or 'data' not in data:
                print("Failed to fetch data or reached end")
                break
            
            teachers_data = data['data']['search']['teachers']
            edges = teachers_data.get('edges', [])
            page_info = teachers_data.get('pageInfo', {})
            result_count = teachers_data.get('resultCount', 0)
            
            # Extract professor information
            for edge in edges:
                node = edge['node']
                professor = {
                    'id': node.get('id'),
                    'legacyId': node.get('legacyId'),
                    'firstName': node.get('firstName'),
                    'lastName': node.get('lastName'),
                    'department': node.get('department'),
                    'school': node.get('school', {}).get('name'),
                    'avgRating': node.get('avgRating'),
                    'avgDifficulty': node.get('avgDifficulty'),
                    'numRatings': node.get('numRatings'),
                    'wouldTakeAgainPercent': node.get('wouldTakeAgainPercent')
                }
                all_professors.append(professor)
            
            print(f"  - Fetched {len(edges)} professors")
            print(f"  - Total so far: {len(all_professors)} / {result_count}")
            
            # Check if there are more pages
            has_next_page = page_info.get('hasNextPage', False)
            
            if not has_next_page:
                print("\nReached last page!")
                break
            
            # Update cursor for next page
            cursor = page_info.get('endCursor')
            
            if not cursor:
                print("No cursor found, stopping")
                break
            
            # Delay to be respectful to the server
            time.sleep(delay)
        
        print(f"\n{'='*60}")
        print(f"Scraping complete! Total professors collected: {len(all_professors)}")
        print(f"{'='*60}")
        
        return all_professors
    
    def save_to_json(self, professors: List[Dict], filename: str = "byu_professors.json"):
        """Save professors data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(professors, f, indent=2, ensure_ascii=False)
        print(f"\nData saved to {filename}")
    
    def save_to_csv(self, professors: List[Dict], filename: str = "byu_professors.csv"):
        """Save professors data to CSV file"""
        import csv
        
        if not professors:
            print("No data to save")
            return
        
        keys = professors[0].keys()
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(professors)
        
        print(f"Data saved to {filename}")


# Main execution
if __name__ == "__main__":
    scraper = RateMyProfessorsScraper()
    
    # Scrape all professors (100 per page with 1 second delay)
    professors = scraper.scrape_all_professors(batch_size=100, delay=1.0)
    
    # Save to both JSON and CSV
    scraper.save_to_json(professors, "byu_professors.json")
    scraper.save_to_csv(professors, "byu_professors.csv")
    
    # Print some statistics
    if professors:
        print(f"\n{'='*60}")
        print("STATISTICS")
        print(f"{'='*60}")
        
        # Top rated professors (with at least 10 ratings)
        top_rated = sorted(
            [p for p in professors if p.get('numRatings', 0) >= 10],
            key=lambda x: x.get('avgRating', 0),
            reverse=True
        )[:10]
        
        print("\nTop 10 Highest Rated Professors (min 10 ratings):")
        for i, prof in enumerate(top_rated, 1):
            print(f"{i}. {prof['firstName']} {prof['lastName']} ({prof['department']})")
            print(f"   Rating: {prof['avgRating']:.1f}/5.0 | Difficulty: {prof['avgDifficulty']:.1f} | {prof['numRatings']} ratings")