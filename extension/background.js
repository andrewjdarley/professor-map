const SUPABASE_URL = 'https://dltiuafpersxnnwxfwve.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRsdGl1YWZwZXJzeG5ud3hmd3ZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODMxODUsImV4cCI6MjA4MDI1OTE4NX0.zuThXcIZVh0eyWLGBJZrrgBMFQQbUm302GOSHRlpc-E';

const professorCache = {};
const reviewsCache = {};

chrome.runtime.onInstalled.addListener(() => {
    console.log('[MyMAP] Extension installed');
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'queryProfessor') {
        const { firstName, lastName } = request;
        const cacheKey = `${firstName}|${lastName}`;
        
        console.log(`[MyMAP BG] Querying for ${firstName} ${lastName}`);
        
        if (professorCache[cacheKey]) {
            console.log(`[MyMAP BG] Cache hit`);
            sendResponse(professorCache[cacheKey]);
            return true;
        }
        
        const url = `${SUPABASE_URL}/rest/v1/professors?select=professor_id,first_name,last_name,avg_rating,avg_difficulty,would_take_again_percent,num_ratings&first_name=ilike.%25${firstName}%25&last_name=ilike.%25${lastName}%25&limit=1`;
        
        fetch(url, {
            headers: {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            const result = Array.isArray(data) && data.length > 0 ? data[0] : null;
            professorCache[cacheKey] = result;
            console.log(`[MyMAP BG] Result:`, result);
            sendResponse(result);
        })
        .catch(error => {
            console.error('[MyMAP BG] Error:', error);
            sendResponse(null);
        });
        
        return true;
    }
    
    if (request.action === 'queryReviews') {
        const { professorId } = request;
        
        console.log(`[MyMAP BG] Querying reviews for professor ${professorId}`);
        
        if (reviewsCache[professorId]) {
            console.log(`[MyMAP BG] Reviews cache hit`);
            sendResponse(reviewsCache[professorId]);
            return true;
        }
        
        // First get ratings
        const ratingsUrl = `${SUPABASE_URL}/rest/v1/ratings?select=rating_id,date,class_name,clarity_rating,helpful_rating,difficulty_rating,comment,grade,would_take_again&professor_id=eq.${professorId}&order=date.desc&limit=20`;
        
        fetch(ratingsUrl, {
            headers: {
                'apikey': SUPABASE_ANON_KEY,
                'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(async (ratings) => {
            if (!Array.isArray(ratings)) {
                sendResponse([]);
                return;
            }
            
            // Fetch tags for each rating
            const reviewsWithTags = await Promise.all(ratings.map(async (rating) => {
                try {
                    const tagsUrl = `${SUPABASE_URL}/rest/v1/rating_tags?select=tag_name&rating_id=eq.${rating.rating_id}`;
                    const tagsResponse = await fetch(tagsUrl, {
                        headers: {
                            'apikey': SUPABASE_ANON_KEY,
                            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
                            'Content-Type': 'application/json'
                        }
                    });
                    const tags = await tagsResponse.json();
                    
                    return {
                        ...rating,
                        quality_rating: rating.clarity_rating || rating.helpful_rating,
                        tags: Array.isArray(tags) ? tags.map(t => t.tag_name) : []
                    };
                } catch (e) {
                    return { ...rating, tags: [] };
                }
            }));
            
            reviewsCache[professorId] = reviewsWithTags;
            console.log(`[MyMAP BG] Reviews result:`, reviewsWithTags);
            sendResponse(reviewsWithTags);
        })
        .catch(error => {
            console.error('[MyMAP BG] Reviews error:', error);
            sendResponse([]);
        });
        
        return true;
    }
});