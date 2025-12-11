console.log('[MyMAP] Content script loaded');

class ProfessorEnhancer {
    constructor() {
        this.cache = {};
        this.reviewsCache = {};
        this.isEnhancing = false;
        this.injectStyles();
    }

    injectStyles() {
        if (document.getElementById('mymap-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'mymap-styles';
        styles.textContent = `
            .mymap-rating-container {
                position: relative;
                display: flex;
                flex-direction: row;
                align-items: stretch;
                gap: 6px;
            }
            
            .mymap-rating-badge {
                display: flex;
                flex-direction: row;
                align-items: stretch;
                gap: 6px;
                padding: 8px 10px;
                background: white;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            
            .mymap-rating-box {
                color: white;
                padding: 8px 10px;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
                min-width: 60px;
            }
            
            .mymap-reviews-trigger {
                display: flex;
                align-items: center;
                padding: 8px 12px;
                background: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-size: 12px;
                color: #666;
                cursor: pointer;
                transition: all 0.2s;
                white-space: nowrap;
            }
            
            .mymap-reviews-trigger:hover {
                background: #e8e8e8;
                color: #333;
            }
            
            .mymap-reviews-panel {
                position: absolute;
                top: 0;
                left: 100%;
                margin-left: 8px;
                width: 320px;
                max-height: 400px;
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                opacity: 0;
                visibility: hidden;
                transition: opacity 0.2s, visibility 0.2s;
                z-index: 9999;
                overflow: hidden;
            }
            
            .mymap-rating-container:hover .mymap-reviews-panel,
            .mymap-reviews-panel:hover {
                opacity: 1;
                visibility: visible;
            }
            
            .mymap-reviews-header {
                padding: 12px 16px;
                background: #f8f8f8;
                border-bottom: 1px solid #e0e0e0;
                font-weight: 600;
                font-size: 14px;
                color: #333;
            }
            
            .mymap-reviews-scroll {
                max-height: 340px;
                overflow-y: auto;
                padding: 8px;
            }
            
            .mymap-review-card {
                padding: 12px;
                margin-bottom: 8px;
                background: #fafafa;
                border-radius: 6px;
                border: 1px solid #eee;
            }
            
            .mymap-review-card:last-child {
                margin-bottom: 0;
            }
            
            .mymap-review-class {
                font-size: 12px;
                font-weight: 600;
                color: #085DDC;
                margin-bottom: 6px;
            }
            
            .mymap-review-meta {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-bottom: 8px;
                font-size: 11px;
                color: #666;
            }
            
            .mymap-review-meta span {
                display: flex;
                align-items: center;
                gap: 3px;
            }
            
            .mymap-review-comment {
                font-size: 13px;
                color: #333;
                line-height: 1.4;
                margin-bottom: 8px;
            }
            
            .mymap-review-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
            }
            
            .mymap-review-tag {
                padding: 2px 8px;
                background: #e8f4f8;
                border-radius: 12px;
                font-size: 10px;
                color: #0077aa;
            }
            
            .mymap-no-data {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 12px 16px;
                background: white;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                color: #999;
                font-size: 12px;
                font-style: italic;
            }
            
            .mymap-no-reviews {
                padding: 20px;
                text-align: center;
                color: #999;
                font-size: 13px;
            }
        `;
        document.head.appendChild(styles);
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

    async queryReviews(professorId) {
        if (this.reviewsCache[professorId]) {
            return this.reviewsCache[professorId];
        }

        try {
            const result = await chrome.runtime.sendMessage({
                action: 'queryReviews',
                professorId: professorId
            });

            console.log(`[MyMAP] Reviews for professor ${professorId}:`, result);
            this.reviewsCache[professorId] = result || [];
            return result || [];
        } catch (error) {
            console.error(`[MyMAP] Error querying reviews:`, error);
            return [];
        }
    }

    getRatingColor(rating) {
        if (rating >= 4.2) return '#085DDC';
        if (rating >= 3.4) return '#34c759';
        if (rating >= 2.6) return '#ffcc00';
        if (rating >= 1.8) return '#ff9500';
        return '#ff3b30';
    }

    getDifficultyColor(difficulty) {
        if (difficulty <= 2.0) return '#085DDC';
        if (difficulty <= 2.8) return '#34c759';
        if (difficulty <= 3.4) return '#ffcc00';
        if (difficulty <= 4.2) return '#ff9500';
        return '#ff3b30';
    }

    hasValidRatings(rating) {
        if (!rating) return false;
        // Check if professor has actual ratings (not 0 or null)
        const hasRating = rating.avg_rating && rating.avg_rating > 0;
        const hasNumRatings = rating.num_ratings && rating.num_ratings > 0;
        return hasRating || hasNumRatings;
    }

    createReviewCard(review) {
        const card = document.createElement('div');
        card.className = 'mymap-review-card';

        let classHtml = '';
        if (review.class_name) {
            classHtml = `<div class="mymap-review-class">${review.class_name}</div>`;
        }

        let metaHtml = '<div class="mymap-review-meta">';
        if (review.quality_rating) metaHtml += `<span>⭐ ${review.quality_rating}/5</span>`;
        if (review.difficulty_rating) metaHtml += `<span>📊 ${review.difficulty_rating}/5</span>`;
        if (review.would_take_again !== null) {
            metaHtml += `<span>${review.would_take_again ? '✅ Would retake' : '❌ No retake'}</span>`;
        }
        if (review.grade) metaHtml += `<span>📝 ${review.grade}</span>`;
        metaHtml += '</div>';

        let commentHtml = '';
        if (review.comment) {
            commentHtml = `<div class="mymap-review-comment">${review.comment}</div>`;
        }

        let tagsHtml = '';
        if (review.tags && review.tags.length > 0) {
            tagsHtml = '<div class="mymap-review-tags">';
            review.tags.forEach(tag => {
                tagsHtml += `<span class="mymap-review-tag">${tag}</span>`;
            });
            tagsHtml += '</div>';
        }

        card.innerHTML = classHtml + metaHtml + commentHtml + tagsHtml;
        return card;
    }

    createRatingElement(rating) {
        const container = document.createElement('div');
        container.className = 'mymap-rating-container';

        // Check if we have valid rating data
        if (!this.hasValidRatings(rating)) {
            container.innerHTML = '<div class="mymap-no-data">No data found</div>';
            return container;
        }

        const qualityColor = this.getRatingColor(rating.avg_rating);
        const difficultyColor = this.getDifficultyColor(rating.avg_difficulty);

        const badge = document.createElement('div');
        badge.className = 'mymap-rating-badge';

        const qualityBox = document.createElement('div');
        qualityBox.className = 'mymap-rating-box';
        qualityBox.style.background = qualityColor;
        qualityBox.innerHTML = `
            <div style="font-size: 16px;">${rating.avg_rating.toFixed(1)}</div>
            <div style="font-size: 9px; opacity: 0.9;">QUALITY</div>
        `;

        const difficultyBox = document.createElement('div');
        difficultyBox.className = 'mymap-rating-box';
        difficultyBox.style.background = difficultyColor;
        difficultyBox.innerHTML = `
            <div style="font-size: 16px;">${rating.avg_difficulty.toFixed(1)}</div>
            <div style="font-size: 9px; opacity: 0.9;">DIFFICULTY</div>
        `;

        badge.appendChild(qualityBox);
        badge.appendChild(difficultyBox);

        // Reviews trigger button
        const reviewsTrigger = document.createElement('div');
        reviewsTrigger.className = 'mymap-reviews-trigger';
        reviewsTrigger.innerHTML = '📋 Reviews';

        // Reviews panel (hidden by default, shown on hover)
        const reviewsPanel = document.createElement('div');
        reviewsPanel.className = 'mymap-reviews-panel';
        reviewsPanel.innerHTML = `
            <div class="mymap-reviews-header">Student Reviews</div>
            <div class="mymap-reviews-scroll">
                <div class="mymap-no-reviews">Loading reviews...</div>
            </div>
        `;

        // Load reviews on first hover
        let reviewsLoaded = false;
        container.addEventListener('mouseenter', async () => {
            if (reviewsLoaded) return;
            reviewsLoaded = true;

            const reviews = await this.queryReviews(rating.professor_id);
            const scrollContainer = reviewsPanel.querySelector('.mymap-reviews-scroll');
            scrollContainer.innerHTML = '';

            if (reviews && reviews.length > 0) {
                reviews.forEach(review => {
                    scrollContainer.appendChild(this.createReviewCard(review));
                });
            } else {
                scrollContainer.innerHTML = '<div class="mymap-no-reviews">No reviews available</div>';
            }
        });

        container.appendChild(badge);
        container.appendChild(reviewsTrigger);
        container.appendChild(reviewsPanel);

        return container;
    }

    async enhanceProfessors() {
        if (this.isEnhancing) return;
        this.isEnhancing = true;

        try {
            const sections = document.querySelectorAll('.sectionDetailsRoot');
            console.log(`[MyMAP] Found ${sections.length} sections to enhance`);

            for (const section of sections) {
                if (section.querySelector('.mymap-rating-container')) {
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