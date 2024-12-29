class MatchesManager extends BaseManager {
    constructor() {
        super();
        this.endpoint = ApiConfig.ENDPOINTS.MATCHES;
    }

    async updateMatch(matchId, data) {
        try {
            return await this.apiService.put(`${this.endpoint}/${matchId}`, data);
        } catch (error) {
            this.handleError(error, 'fetch match');
        }
    }

    async getMatch(matchId) {
        try {
            return await this.apiService.get(`${this.endpoint}/${matchId}`);
        } catch (error) {
            this.handleError(error, 'fetch match');
        }
    }
}

// Match Update Manager
class MatchUpdateManager {
    constructor() {
        this.apiService = new ApiService();
        this.matchId = new URLSearchParams(window.location.search).get('matchId');
        this.form = document.getElementById('updateMatchForm');
        this.matchesManager = new MatchesManager();

        this.initialize();
    }

    async initialize() {
        if (!this.matchId) {
            NotificationService.show('error', 'Match ID is required');
            return;
        }

        await this.loadMatchData();
        this.setupEventListeners();
    }

    async loadMatchData() {
        try {
            const match = await this.matchesManager.getMatch(this.matchId);
            this.populateForm(match);
        } catch (error) {
            console.error('Failed to load match:', error);
            NotificationService.show('error', 'Failed to load match data');
        }
    }

    populateForm(match) {
        console.log({ match });

        // Populate basic match info
        document.getElementById('team1Name').textContent = match.team1.name;
        document.getElementById('team2Name').textContent = match.team2.name;
        document.getElementById('score_team1').value = match.score_team1;
        document.getElementById('score_team2').value = match.score_team2;
        document.getElementById('status').value = match.status;

        if (match.start_time) {
            document.getElementById('start_time').value = match.start_time.slice(0, 16);
        }
        if (match.half_time) {
            document.getElementById('half_time').value = match.half_time.slice(0, 16);
        }
        if (match.second_start) {
            document.getElementById('second_start').value = match.second_start.slice(0, 16);
        }
        if (match.end_time) {
            document.getElementById('end_time').value = match.end_time.slice(0, 16);
        }

        // Populate statistics if available
        if (match.stats) {
            const statsFields = [
                'possession_team1', 'possession_team2',
                'shots_team1', 'shots_team2',
                'shots_on_target_team1', 'shots_on_target_team2',
                'corners_team1', 'corners_team2',
                'yellow_cards_team1', 'yellow_cards_team2',
                'red_cards_team1', 'red_cards_team2',
                'fouls_team1', 'fouls_team2',
                'offsides_team1', 'offsides_team2'
            ];

            statsFields.forEach(field => {
                const element = document.getElementById(field);
                if (element && match.stats[field] !== undefined) {
                    element.value = match.stats[field];
                }
            });
        }
    }

    setupEventListeners() {
        this.form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleSubmit(e);
        });

        // Add real-time validation listeners
        this.form.querySelectorAll('input[type="number"]').forEach(input => {
            input.addEventListener('input', this.validateInput.bind(this));
        });
    }

    validateInput(event) {
        const input = event.target;
        const value = parseInt(input.value);

        if (input.hasAttribute('max') && value > parseInt(input.getAttribute('max'))) {
            input.value = input.getAttribute('max');
        }
        if (value < 0) {
            input.value = 0;
        }
    }

    async handleSubmit(event) {
        try {
            const formData = new FormData(event.target);
            const matchData = Object.fromEntries(formData);

            // Validate required fields
            if (!this.validateForm(matchData)) {
                return;
            }

            // Convert string values to numbers where appropriate
            const processedData = this.processFormData(matchData);

            await this.matchesManager.updateMatch(this.matchId, processedData);
            NotificationService.show('success', 'Match updated successfully');

            // Reload match data to show updated values
            await this.loadMatchData();
        } catch (error) {
            console.error('Failed to update match:', error);
            NotificationService.show('error', 'Failed to update match');
        }
    }

    validateForm(data) {
        // Timeline validation
        if (data.half_time && !data.start_time) {
            NotificationService.show('error', 'Cannot set Half Time without Start Time');
            return false;
        }

        if (data.second_start && !data.half_time) {
            NotificationService.show('error', 'Cannot set Second Half Start without Half Time');
            return false;
        }

        if (data.end_time && !data.second_start) {
            NotificationService.show('error', 'Cannot set End Time without Second Half Start');
            return false;
        }

        // Chronological order validation
        if (data.start_time && data.half_time && new Date(data.half_time) <= new Date(data.start_time)) {
            NotificationService.show('error', 'Half Time must be after Start Time');
            return false;
        }

        if (data.half_time && data.second_start && new Date(data.second_start) <= new Date(data.half_time)) {
            NotificationService.show('error', 'Second Half Start must be after Half Time');
            return false;
        }

        if (data.second_start && data.end_time && new Date(data.end_time) <= new Date(data.second_start)) {
            NotificationService.show('error', 'End Time must be after Second Half Start');
            return false;
        }

        return true;
    }

    processFormData(data) {
        // Separate match and stats data
        const matchUpdate = {
            score_team1: parseInt(data.score_team1) || 0,
            score_team2: parseInt(data.score_team2) || 0,
            status: data.status,
            start_time: data.start_time || null,
            half_time: data.half_time || null,
            second_start: data.second_start || null,
            end_time: data.end_time || null,
        };

        const statsUpdate = {
            possession_team1: parseInt(data.possession_team1) || 0,
            possession_team2: parseInt(data.possession_team2) || 0,
            shots_team1: parseInt(data.shots_team1) || 0,
            shots_team2: parseInt(data.shots_team2) || 0,
            shots_on_target_team1: parseInt(data.shots_on_target_team1) || 0,
            shots_on_target_team2: parseInt(data.shots_on_target_team2) || 0,
            corners_team1: parseInt(data.corners_team1) || 0,
            corners_team2: parseInt(data.corners_team2) || 0,
            yellow_cards_team1: parseInt(data.yellow_cards_team1) || 0,
            yellow_cards_team2: parseInt(data.yellow_cards_team2) || 0,
            red_cards_team1: parseInt(data.red_cards_team1) || 0,
            red_cards_team2: parseInt(data.red_cards_team2) || 0,
            fouls_team1: parseInt(data.fouls_team1) || 0,
            fouls_team2: parseInt(data.fouls_team2) || 0,
            offsides_team1: parseInt(data.offsides_team1) || 0,
            offsides_team2: parseInt(data.offsides_team2) || 0
        };

        return {
            match_update: matchUpdate,
            stats_update: statsUpdate
        };
    }
}

// Initialize the match update manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MatchUpdateManager();
});