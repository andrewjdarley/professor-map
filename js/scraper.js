// scraper.js
// Standalone version for Node.js or other environments

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.38.5/+esm';

const SUPABASE_URL = 'https://dltiuafpersxnnwxfwve.supabase.co';
const SUPABASE_ANON_KEY = 'sb_secret_ao2BKnbQI9FxJqlrDmJ_Fg_FieCdlLs';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

class ProfessorScraper {
  constructor(html) {
    this.html = html;
    this.professors = [];
    this.courseCode = null;
  }

  extractProfessors() {
    if (!this.html) throw new Error('No HTML provided.');

    const parser = new DOMParser();
    const doc = parser.parseFromString(this.html, 'text/html');

    const headerH1 = doc.querySelector('.chooseASectionMainHeader h1');
    if (headerH1) {
      const match = headerH1.textContent.match(/([A-Z]+\s+\d+[A-Z]?)/);
      this.courseCode = match ? match[0].trim() : null;
    }

    const sectionElements = doc.querySelectorAll('.sectionDetailsRoot');
    console.log(`Found ${sectionElements.length} sections`);

    sectionElements.forEach((section) => {
      try {
        const h4 = section.querySelector('.sectionDetailsFlex > .sectionDetailsCol:first-child h4');
        if (!h4) return;

        const professorName = h4.textContent.trim();
        if (!professorName) return;

        const sectionDiv = h4.nextElementSibling;
        const sectionMatch = sectionDiv?.textContent.match(/Section (\d+)/);
        const sectionNumber = sectionMatch ? sectionMatch[1] : null;

        const timeGroup = section.querySelector('.sectionDetailsTimeGroup');
        let days = '', startTime = '', endTime = '', building = '', room = '';

        if (timeGroup) {
          const daysEl = timeGroup.querySelector('.sectionDetailsDays');
          days = daysEl?.textContent.trim() || '';

          const timeRoom = timeGroup.querySelector('.sectionDetailsTimeRoom');
          if (timeRoom) {
            const timeEl = timeRoom.querySelector('.sectionDetailsTime');
            if (timeEl) {
              const timeText = timeEl.textContent.trim();
              const [start, end] = timeText.split('-').map(t => t.trim());
              startTime = start;
              endTime = end;
            }

            const roomEl = timeRoom.querySelector('.sectionDetailsRoom');
            if (roomEl) {
              const roomText = roomEl.textContent.trim();
              const [build, rm] = roomText.split(/\s+/);
              building = build;
              room = rm;
            }
          }
        }

        const seatPool = section.querySelector('.sectionDetailsSeatPool');
        const seatMatch = seatPool?.textContent.match(/(\d+)\/(\d+)\s+seats\s+left/);
        const seatsLeft = seatMatch ? parseInt(seatMatch[1]) : null;
        const totalSeats = seatMatch ? parseInt(seatMatch[2]) : null;

        this.professors.push({
          name: professorName,
          sectionNumber,
          days,
          startTime,
          endTime,
          building,
          room,
          seatsLeft,
          totalSeats
        });

      } catch (error) {
        console.error('Error extracting professor:', error);
      }
    });

    console.log(`✓ Extracted ${this.professors.length} professors`);
    return this.professors;
  }

  async querySupabase(professorName) {
    const [firstName, ...lastNameParts] = professorName.split(/\s+/);
    const lastName = lastNameParts.join(' ');

    try {
      const { data, error } = await supabase
        .from('professors')
        .select('professor_id,first_name,last_name,avg_rating,avg_difficulty,would_take_again_percent,num_ratings')
        .ilike('first_name', `%${firstName}%`)
        .ilike('last_name', `%${lastName}%`)
        .single();

      if (error && error.code !== 'PGRST116') {
        throw new Error(error.message);
      }

      return data || null;

    } catch (error) {
      console.error(`Error querying Supabase for ${professorName}:`, error.message);
      return null;
    }
  }

  async enrichProfessors() {
    console.log('\nQuerying Supabase for professor ratings...');

    for (let prof of this.professors) {
      const rating = await this.querySupabase(prof.name);
      prof.rating = rating || {
        avg_rating: null,
        avg_difficulty: null,
        would_take_again_percent: null,
        num_ratings: 0
      };

      if (rating) {
        console.log(`✓ ${prof.name}: ${rating.avg_rating?.toFixed(2)}/5 (${rating.num_ratings} ratings)`);
      } else {
        console.log(`✗ ${prof.name}: No ratings found`);
      }
    }

    return this.professors;
  }

  displayResults() {
    console.log('\n' + '='.repeat(80));
    console.log(`COURSE: ${this.courseCode}`);
    console.log('='.repeat(80));

    this.professors.forEach(prof => {
      console.log(`\n${prof.name} (Section ${prof.sectionNumber})`);
      console.log(`  Time: ${prof.days} ${prof.startTime}–${prof.endTime}`);
      console.log(`  Location: ${prof.building} ${prof.room}`);
      console.log(`  Seats: ${prof.seatsLeft}/${prof.totalSeats} available`);

      if (prof.rating && prof.rating.avg_rating) {
        console.log(`  Rating: ${prof.rating.avg_rating.toFixed(2)}/5.0 (${prof.rating.num_ratings} ratings)`);
        console.log(`  Difficulty: ${prof.rating.avg_difficulty?.toFixed(2)}/5.0`);
        console.log(`  Would Retake: ${prof.rating.would_take_again_percent?.toFixed(0)}%`);
      } else {
        console.log(`  Rating: No data`);
      }
    });

    console.log('\n' + '='.repeat(80));
  }

  async run() {
    try {
      this.extractProfessors();
      await this.enrichProfessors();
      this.displayResults();
      return this.professors;
    } catch (error) {
      console.error('Fatal error:', error);
      throw error;
    }
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ProfessorScraper;
}

// Global access
if (typeof window !== 'undefined') {
  window.ProfessorScraper = ProfessorScraper;
}

export default ProfessorScraper;