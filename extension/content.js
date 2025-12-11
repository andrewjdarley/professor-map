console.log('[MyMAP] Content script loaded');

class ProfessorEnhancer {
    constructor() {
        this.cache = {};
        this.isEnhancing = false;
    }

    async querySupabase(professorName) {
        if (this.cache[professorName]) {
            console.log(`[MyMAP] Cache hit for ${professorName}`);
            return this.cache[professorName];
        }

        const normalizedName = professorName.replace(/\./g, '').replace(/\s+/g, ' ').trim();
        const [firstName, ...lastNameParts] = normalizedName.split(/\s+/);
        const lastName = lastNameParts.join(' ');

        console.log(`[MyMAP] Querying: firstName="${firstName}" lastName="${lastName}"`);

        try {
            // Send message to background worker to make the fetch
            const result = await chrome.runtime.sendMessage({
                action: 'queryProfessor',
                firstName: firstName,
                lastName: lastName
            });

            console.log(`[MyMAP] API response for ${professorName}:`, result);
            this.cache[professorName] = result;
            return result;
        } catch (error) {
            console.error(`[MyMAP] Error querying ${professorName}:`, error);
            return null;
        }
    }

    getRatingColor(rating) {
        if (rating >= 4.2) return '#085DDC';
        if (rating >= 3.4) return '#34c759';
        if (rating >= 2.6) return '#ffcc00';
        if (rating >= 1.8) return '#ff9500';
        return '#ff3b30';
    }

    createRatingElement(rating) {
        const container = document.createElement('div');
        container.className = 'professor-rating-badge';
        container.style.cssText = `
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            padding: 8px 12px;
            background: white;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            min-width: 70px;
        `;

        if (rating) {
            const ratingColor = this.getRatingColor(rating.avg_rating);
            
            const ratingBox = document.createElement('div');
            ratingBox.style.cssText = `
                background: ${ratingColor};
                color: white;
                padding: 6px 10px;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
                min-width: 50px;
            `;
            ratingBox.innerHTML = `
                <div style="font-size: 16px;">${rating.avg_rating.toFixed(1)}</div>
                <div style="font-size: 10px; opacity: 0.9;">/ 5.0</div>
            `;

            const stats = document.createElement('div');
            stats.style.cssText = `
                font-size: 11px;
                color: #666;
                text-align: center;
                line-height: 1.3;
            `;
            stats.innerHTML = `
                <div><strong>Difficulty:</strong> ${rating.avg_difficulty.toFixed(1)}</div>
                <div><strong>Retake:</strong> ${rating.would_take_again_percent.toFixed(0)}%</div>
                <div style="color: #999; margin-top: 2px;">${rating.num_ratings} ratings</div>
            `;

            container.appendChild(ratingBox);
            container.appendChild(stats);
        } else {
            container.style.cssText += `
                justify-content: center;
                color: #999;
                font-size: 12px;
                font-style: italic;
                min-height: 60px;
            `;
            container.textContent = 'No data';
        }

        return container;
    }

    async enhanceProfessors() {
        if (this.isEnhancing) return;
        this.isEnhancing = true;

        try {
            const sections = document.querySelectorAll('.sectionDetailsRoot');
            console.log(`[MyMAP] Found ${sections.length} sections to enhance`);

            for (const section of sections) {
                if (section.querySelector('.professor-rating-badge')) {
                    continue;
                }

                const h4 = section.querySelector('.sectionDetailsFlex > .sectionDetailsCol:first-child h4');
                if (!h4) continue;

                const professorName = h4.textContent.trim();
                if (!professorName) continue;

                console.log(`[MyMAP] Processing professor: ${professorName}`);

                const rating = await this.querySupabase(professorName);

                const flex = section.querySelector('.sectionDetailsFlex');
                if (!flex) continue;

                const ratingElement = this.createRatingElement(rating);
                flex.appendChild(ratingElement);

                await new Promise(resolve => setTimeout(resolve, 150));
            }

            console.log('[MyMAP] Enhancement complete');
        } catch (error) {
            console.error('[MyMAP] Error enhancing professors:', error);
        } finally {
            this.isEnhancing = false;
        }
    }

    observeDOM() {
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                if (mutation.addedNodes.length) {
                    const hasSections = Array.from(mutation.addedNodes).some(node => 
                        node.nodeType === 1 && (
                            node.classList?.contains('sectionDetailsRoot') ||
                            node.querySelector?.('.sectionDetailsRoot')
                        )
                    );
                    
                    if (hasSections) {
                        clearTimeout(this.debounceTimer);
                        this.debounceTimer = setTimeout(() => {
                            console.log('[MyMAP] New sections detected, enhancing...');
                            this.enhanceProfessors();
                        }, 300);
                    }
                }
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        console.log('[MyMAP] DOM observer started');
    }
}

const enhancer = new ProfessorEnhancer();

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'activate') {
        console.log('[MyMAP] Manual activation triggered from popup');
        enhancer.enhanceProfessors();
        enhancer.observeDOM();
        sendResponse({ success: true });
    }
});

function autoActivate() {
    const courseHeader = document.querySelector('.chooseASectionMainHeader');
    if (courseHeader) {
        console.log('[MyMAP] Course page detected, auto-activating');
        enhancer.enhanceProfessors();
        enhancer.observeDOM();
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoActivate);
} else {
    autoActivate();
}

setTimeout(autoActivate, 1500);