const PlayerPosition = Object.freeze({
    // Goalkeeper
    GOALKEEPER: "goalkeeper",

    // Defenders
    CENTRE_BACK: "centre_back", // Used
    SWEEPER: "sweeper",
    LEFT_BACK: "left_back", // Used
    RIGHT_BACK: "right_back", // Used
    LEFT_WING_BACK: "left_wing_back",
    RIGHT_WING_BACK: "right_wing_back",

    // Midfielders
    DEFENSIVE_MIDFIELDER: "defensive_midfielder", // Used
    CENTRAL_MIDFIELDER: "central_midfielder", // Used
    ATTACKING_MIDFIELDER: "attacking_midfielder", // Used
    LEFT_MIDFIELDER: "left_midfielder",
    RIGHT_MIDFIELDER: "right_midfielder",
    LEFT_WINGER: "left_winger", // Used
    RIGHT_WINGER: "right_winger",

    // Forwards
    STRIKER: "striker", // Used
    CENTRE_FORWARD: "centre_forward", // Used
    SECOND_STRIKER: "second_striker",
    FALSE_NINE: "false_nine",
    LEFT_FORWARD: "left_forward",
    RIGHT_FORWARD: "right_forward",

    // Specialized Roles
    PLAYMAKER: "playmaker",
    TARGET_MAN: "target_man",
    BOX_TO_BOX_MIDFIELDER: "box_to_box_midfielder",
    INVERTED_WINGER: "inverted_winger",
    LIBERO: "libero",
});



class MatchDetails {
    constructor() {
        this.matchId = this.getMatchIdFromUrl();
        this.socket = io("http://127.0.0.1:8000", {
            path: "/socket.io", // Ensure this matches the path in your FastAPI backend
        });


        // Handle connection events
        this.socket.on("connect", () => {
            console.log("Connected to the server!");
        });

        this.socket.on("disconnect", () => {
            console.log("Disconnected from the server.");
        });
        this.setupSocketListeners();
        this.initialize();
    }

    setupSocketListeners() {
        // Handle connection
        this.socket.on('connect', () => {
            console.log('Connected to Socket.IO server');
            this.subscribeToMatch();
        });

        // Handle disconnection
        this.socket.on('disconnect', () => {
            console.log('Disconnected from Socket.IO server');
        });

        // Handle match updates
        this.socket.on('match_update', (update) => {
            console.log('Received match update:', update);
            this.handleMatchUpdate(update);
        });

        // Handle subscription confirmation
        this.socket.on('subscribed', (data) => {
            console.log('Subscription confirmed:', data.message);
        });

        // Handle errors
        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this.showError(error.message);
        });
    }

    subscribeToMatch() {
        this.socket.emit('subscribe', { match_id: this.matchId });
    }

    unsubscribeFromMatch() {
        this.socket.emit('unsubscribe', { match_id: this.matchId });
    }

    handleMatchUpdate(update) {
        // Update match data
        this.matchData = { ...this.matchData, ...update };

        // Update scores
        if (update.score_team1 !== undefined) {
            document.getElementById('home-score').textContent = update.score_team1;
        }
        if (update.score_team2 !== undefined) {
            document.getElementById('away-score').textContent = update.score_team2;
        }

        // Update match status
        if (update.status) {
            this.updateMatchTime();
        }

        // Update stats if provided
        if (update.stats) {
            this.updateMatchStats();
        }

        // Update team information if provided
        if (update.team1) {
            this.homeTeam = update.team1;
            document.querySelectorAll('.team-name')[0].textContent = update.team1.name;
            this.renderLineups();
        }
        if (update.team2) {
            this.awayTeam = update.team2;
            document.querySelectorAll('.team-name')[1].textContent = update.team2.name;
            this.renderLineups();
        }

        // Add match event to timeline if provided
        if (update.event) {
            this.addMatchEvent(update.event);
        }
    }

    addMatchEvent(event) {
        const eventsContainer = document.querySelector('.card-body');
        const eventElement = document.createElement('div');
        eventElement.className = 'match-event';

        // Determine icon based on event type
        let icon = '';
        switch (event.type) {
            case 'goal':
                icon = 'fa-futbol text-success';
                break;
            case 'yellow_card':
                icon = 'fa-square text-warning';
                break;
            case 'red_card':
                icon = 'fa-square text-danger';
                break;
            case 'substitution':
                icon = 'fa-exchange-alt text-info';
                break;
            default:
                icon = 'fa-circle text-primary';
        }

        eventElement.innerHTML = `
            <strong>${event.time}'</strong> 
            <i class="fas ${icon}"></i> 
            ${event.description}
        `;

        // Insert at the top of the events list
        eventsContainer.insertBefore(eventElement, eventsContainer.firstChild);
    }

    // Clean up when leaving the page
    destroy() {
        this.unsubscribeFromMatch();
        this.socket.disconnect();
    }

    getMatchIdFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        const matchId = urlParams.get('matchId');
        if (!matchId) {
            this.showError('Match ID is required');
            throw new Error('Match ID is required');
        }
        return matchId;
    }

    async initialize() {
        try {
            await this.fetchMatchData();
            this.updateMatchTime();
            this.renderLineups();
            this.renderField();

            setInterval(() => this.updateMatchTime(), 1000);
        } catch (error) {
            this.showError(error.message);
        }
    }

    showError(message) {
        // Create error alert if it doesn't exist
        let errorAlert = document.getElementById('error-alert');
        if (!errorAlert) {
            errorAlert = document.createElement('div');
            errorAlert.id = 'error-alert';
            errorAlert.className = 'alert alert-danger alert-dismissible fade show m-3';
            errorAlert.innerHTML = `
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                <strong>Error!</strong> <span id="error-message"></span>
            `;
            document.querySelector('.container').prepend(errorAlert);
        }
        document.getElementById('error-message').textContent = message;
    }

    async fetchMatchData() {
        try {
            const response = await fetch(`http://localhost:8000/api/matches/${this.matchId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch match data');
            }
            const matchData = await response.json();

            this.matchData = matchData;
            this.homeTeam = matchData.team1;
            this.awayTeam = matchData.team2;

            // Update scores and team names
            document.getElementById('home-score').textContent = matchData.score_team1;
            document.getElementById('away-score').textContent = matchData.score_team2;

            const teamElements = document.querySelectorAll('.team-name');
            teamElements[0].textContent = matchData.team1.name;
            teamElements[1].textContent = matchData.team2.name;

            // Update location and date
            document.querySelector('.text-muted').innerHTML = `
                <i class="fas fa-calendar"></i> 15 April 2024, 20:00
                <br>
                <i class="fas fa-map-marker-alt"></i> ${matchData.team1.city}
            `;

            // Update match stats
            this.updateMatchStats();

        } catch (error) {
            console.error('Error fetching match data:', error);
            throw new Error('Failed to load match data');
        }
    }

    calculateMatchTime(matchData) {
        const now = new Date();
        
        // Second half time calculation
        if (matchData.second_start) {
            const secondHalfStart = new Date(matchData.second_start);
            const minutesPlayed = Math.floor((now - secondHalfStart) / (1000 * 60)) + 45;
            
            if (minutesPlayed > 90) {
                const extraMinutes = minutesPlayed - 90;
                return `90+${extraMinutes}'`;
            }
            return `${minutesPlayed}'`;
        }
        
        // First half time calculation
        if (matchData.start_time) {
            const startTime = new Date(matchData.start_time);
            const minutesPlayed = Math.floor((now - startTime) / (1000 * 60));
            
            if (minutesPlayed > 45) {
                const extraMinutes = minutesPlayed - 45;
                return `45+${extraMinutes}'`;
            }
            return `${minutesPlayed}'`;
        }
        
        return null;
    }

    updateMatchTime() {
        const matchStatusElement = document.getElementById('match-status');

        if (!this.matchData) {
            matchStatusElement.textContent = 'Loading...';
            return;
        }

        // Convert status to display format
        switch (this.matchData.status) {
            case MatchStatus.NOT_STARTED:
                matchStatusElement.textContent = 'Not Started';
                break;
            case MatchStatus.RUNNING:
                const matchTime = this.calculateMatchTime(this.matchData);
                matchStatusElement.textContent = matchTime || 'Running';
                break;
            case MatchStatus.HALF_TIME:
                matchStatusElement.textContent = 'HT';
                break;
            case MatchStatus.FULL_TIME:
                matchStatusElement.textContent = 'FT';
                break;
            default:
                matchStatusElement.textContent = this.matchData.status;
        }
    }

    renderLineups() {
        // Use actual players from the API
        const homeLineup = this.homeTeam?.players || [];
        const awayLineup = this.awayTeam?.players || [];

        // Dummy substitutes data since not provided by API
        const dummySubstitutes = [
            { id: 'SUB1', name: 'Substitute Player 1', position: 'Forward' },
            { id: 'SUB2', name: 'Substitute Player 2', position: 'Midfielder' },
            { id: 'SUB3', name: 'Substitute Player 3', position: 'Defender' },
        ];

        this.renderTeamLineup('home-lineup', homeLineup);
        this.renderTeamLineup('home-substitutes', dummySubstitutes);
        this.renderTeamLineup('away-lineup', awayLineup);
        this.renderTeamLineup('away-substitutes', dummySubstitutes);
    }

    renderTeamLineup(containerId, players) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '';

        players.forEach(player => {
            const playerCard = document.createElement('div');
            playerCard.className = 'col-6 player-card';
            playerCard.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title mb-0">
                            <span class="badge bg-secondary me-2">${player.id}</span>
                            ${player.name}
                        </h6>
                        <small class="text-muted">
                            ${player.position}
                            ${player.appearances ? `
                                <br>
                                <span class="stats">
                                    Apps: ${player.appearances} | 
                                    Goals: ${player.goals} | 
                                    Assists: ${player.assists}
                                </span>
                            ` : ''}
                        </small>
                    </div>
                </div>
            `;
            container.appendChild(playerCard);
        });
    }

    renderField() {
        const field = document.querySelector('.football-field');
        if (!field) return;

        // Clear existing players
        field.querySelectorAll('.player-position').forEach(el => el.remove());

        const formation = [
            {
                rowPosition: 10,
                players: 1,
                positions: [PlayerPosition.GOALKEEPER]
            },
            {
                rowPosition: 30,
                players: 3,
                positions: [
                    PlayerPosition.CENTRE_BACK,
                    PlayerPosition.SWEEPER,
                    PlayerPosition.LEFT_BACK,
                    PlayerPosition.RIGHT_BACK,
                    PlayerPosition.LEFT_WING_BACK,
                    PlayerPosition.RIGHT_WING_BACK
                ]
            },
            {
                rowPosition: 50,
                players: 4,
                positions: [
                    PlayerPosition.DEFENSIVE_MIDFIELDER,
                    PlayerPosition.CENTRAL_MIDFIELDER,
                    PlayerPosition.ATTACKING_MIDFIELDER,
                    PlayerPosition.LEFT_MIDFIELDER,
                    PlayerPosition.RIGHT_MIDFIELDER,
                    PlayerPosition.LEFT_WINGER,
                    PlayerPosition.RIGHT_WINGER
                ]
            },
            {
                rowPosition: 70,
                players: 3,
                positions: [
                    PlayerPosition.STRIKER,
                    PlayerPosition.CENTRE_FORWARD,
                    PlayerPosition.SECOND_STRIKER,
                    PlayerPosition.FALSE_NINE,
                    PlayerPosition.LEFT_FORWARD,
                    PlayerPosition.RIGHT_FORWARD
                ]
            }
        ];

        // Helper function to get player positions for a team
        const getTeamPositions = (lineup, isHome) => {
            const positions = [];

            formation.forEach(({ rowPosition, players, positions: allowedPositions }) => {
                const startingPlayers = lineup
                    .filter(player => allowedPositions.includes(player.position))
                    .slice(0, players);

                if (startingPlayers.length === 0) return;

                const advancedColBy = 90 / startingPlayers.length;
                let advanceCol = (90 - (startingPlayers.length === 1 ? 0 : advancedColBy)) /
                    (startingPlayers.length === 1 ? 2 : startingPlayers.length);

                startingPlayers.forEach(player => {
                    positions.push({
                        [isHome ? 'top' : 'bottom']: `${rowPosition}%`,
                        left: `${advanceCol}%`,
                        number: player.number || '-',
                        name: player.name
                    });
                    advanceCol += advancedColBy;
                });
            });

            return positions;
        };

        // Helper function to render a player on the field
        const renderPlayer = (position, isHome) => {
            const player = document.createElement('div');
            player.className = `player-position ${isHome ? 'home' : 'away'}`;

            // Set position styles
            Object.entries(position).forEach(([key, value]) => {
                if (!['number', 'name'].includes(key)) {
                    player.style[key] = value;
                }
            });

            // Set tooltip attributes
            player.setAttribute('data-bs-toggle', 'tooltip');
            player.setAttribute('data-bs-placement', isHome ? 'top' : 'bottom');
            player.setAttribute('title', position.name);
            player.textContent = position.number;

            return player;
        };

        // Render both teams
        const homeLineup = this.homeTeam?.players || [];
        const awayLineup = this.awayTeam?.players || [];

        // Render home team
        getTeamPositions(homeLineup, true)
            .forEach(pos => field.appendChild(renderPlayer(pos, true)));

        // Render away team
        getTeamPositions(awayLineup, false)
            .forEach(pos => field.appendChild(renderPlayer(pos, false)));

        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }

    updateMatchStats() {
        if (!this.matchData?.stats) return;

        const stats = this.matchData.stats;

        // Helper function to calculate percentages and update bars
        const updateStat = (statName, team1Value, team2Value) => {
            // Update values
            document.getElementById(`${statName}-team1`).textContent =
                statName === 'possession' ? `${team1Value}%` : team1Value;
            document.getElementById(`${statName}-team2`).textContent =
                statName === 'possession' ? `${team2Value}%` : team2Value;

            // Calculate percentages for progress bars
            const total = team1Value + team2Value;
            const team1Percent = total === 0 ? 50 : (team1Value / total) * 100;
            const team2Percent = total === 0 ? 50 : (team2Value / total) * 100;

            // Update progress bars
            document.getElementById(`${statName}-bar-team1`).style.width = `${team1Percent}%`;
            document.getElementById(`${statName}-bar-team2`).style.width = `${team2Percent}%`;
        };

        // Update each stat
        updateStat('possession', stats.possession_team1, stats.possession_team2);
        updateStat('shots', stats.shots_team1, stats.shots_team2);
        updateStat('shots-on-target', stats.shots_on_target_team1, stats.shots_on_target_team2);
        updateStat('corners', stats.corners_team1, stats.corners_team2);
        updateStat('yellow-cards', stats.yellow_cards_team1, stats.yellow_cards_team2);
    }
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.matchDetails = new MatchDetails();
    } catch (error) {
        console.error('Failed to initialize match details:', error);
    }
});

// Clean up when leaving the page
window.addEventListener('beforeunload', () => {
    if (window.matchDetails) {
        window.matchDetails.destroy();
    }
});