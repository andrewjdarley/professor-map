const SUPABASE_URL = 'https://dltiuafpersxnnwxfwve.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRsdGl1YWZwZXJzeG5ud3hmd3ZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2ODMxODUsImV4cCI6MjA4MDI1OTE4NX0.zuThXcIZVh0eyWLGBJZrrgBMFQQbUm302GOSHRlpc-E';
const cache = {};

chrome.runtime.onInstalled.addListener(() => {
    console.log('[MyMAP] Extension installed');
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'queryProfessor') {
        const { firstName, lastName } = request;
        const cacheKey = `${firstName}|${lastName}`;
        
        console.log(`[MyMAP BG] Querying for ${firstName} ${lastName}`);
        
        if (cache[cacheKey]) {
            console.log(`[MyMAP BG] Cache hit`);
            sendResponse(cache[cacheKey]);
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
            cache[cacheKey] = result;
            console.log(`[MyMAP BG] Result:`, result);
            sendResponse(result);
        })
        .catch(error => {
            console.error('[MyMAP BG] Error:', error);
            sendResponse(null);
        });
        
        return true;
    }
});