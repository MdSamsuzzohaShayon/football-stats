// Teams Manager class
class TeamsManager extends BaseManager {
    constructor() {
        super();
        this.endpoint = ApiConfig.ENDPOINTS.TEAMS;
    }

    async getAllTeams() {
        return this.getAll(this.endpoint, (teams) => {
            this.renderTeams(teams);
            this.populateTeamDropdowns();
        });
    }

    async createTeam(teamData) {
        await this.create(this.endpoint, teamData, 'Team created successfully');
    }

    async updateTeam(teamId, teamData) {
        await this.update(this.endpoint, teamId, teamData, 'Team updated successfully');
    }

    async deleteTeam(teamId) {
        await this.delete(this.endpoint, teamId, 'Team deleted successfully');
    }

    refreshData() {
        return this.getAllTeams();
    }

    populateTeamDropdowns() {
        const teamSelects = document.querySelectorAll('select[name="team_id"]');
        const options = this.data.map(team => 
            `<option value="${team.id}">${team.name}</option>`
        ).join('');

        teamSelects.forEach(select => {
            select.innerHTML = `<option value="">Select Team</option>${options}`;
        });
    }

    renderTeams(teams) {
        const tbody = document.querySelector('#teams table tbody');
        tbody.innerHTML = teams.map(team => `
            <tr>
                <td>${team.name}</td>
                <td>${team.playerCount || 0}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="app.teamsManager.editTeam(${team.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="app.teamsManager.deleteTeam(${team.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
}

// Matches Manager class
class MatchesManager extends BaseManager {
    constructor() {
        super();
        this.endpoint = ApiConfig.ENDPOINTS.MATCHES;
    }

    async getAllMatches() {
        return this.getAll(this.endpoint, (matches) => {
            this.renderMatches(matches);
        });
    }

    async getMatch(matchId) {
        try {
            return await this.apiService.get(`${ApiConfig.ENDPOINTS.MATCHES}/${matchId}`);
        } catch (error) {
            this.handleError(error, 'fetch match');
        }
    }

    async createMatch(matchData) {
        try {
            await this.apiService.post(ApiConfig.ENDPOINTS.MATCHES, matchData);
            NotificationService.show('success', 'Match created successfully');
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addMatchModal'));
            modal.hide();
            
            await this.getAllMatches();
        } catch (error) {
            this.handleError(error, 'create match');
        }
    }

    async updateMatch(matchId, matchData) {
        try {
            await this.apiService.put(`${ApiConfig.ENDPOINTS.MATCHES}/${matchId}`, matchData);
            NotificationService.show('success', 'Match updated successfully');
            await this.getAllMatches();
        } catch (error) {
            this.handleError(error, 'update match');
        }
    }

    async viewMatch(matchId) {
        try {
            window.location.href = `single-match.html?matchId=${matchId}`;
        } catch (error) {
            this.handleError(error, 'view match');
        }
    }

    renderMatches(matches) {
        const tbody = document.querySelector('#matches table tbody');
        tbody.innerHTML = matches.map(match => `
            <tr>

                <td>${match.team1.name}</td>
                <td>${match.team2.name}</td>
                <td>${match.score_team1}</td>
                <td>${match.score_team2}</td>
                <td>${new Date(match.created_at).toLocaleDateString()}</td>
                <td>${match.status}</td>
                <td>
                    <a class="btn btn-sm btn-primary" href="update-match.html?matchId=${match.id}">
                        <i class="fas fa-edit"></i>
                    </a>
                    <a class="btn btn-sm btn-info" href="single-match.html?matchId=${match.id}">
                        <i class="fas fa-eye"></i>
                    </a>
                </td>
            </tr>
        `).join('');
    }
}

// Players Manager class
class PlayersManager extends BaseManager {
    constructor() {
        super();
        this.endpoint = ApiConfig.ENDPOINTS.PLAYERS;
    }

    async getAllPlayers() {
        return this.getAll(this.endpoint, (players) => {
            this.renderPlayers(players);
        });
    }

    async createPlayer(playerData) {
        try {
            await this.apiService.post(ApiConfig.ENDPOINTS.PLAYERS, playerData);
            NotificationService.show('success', 'Player created successfully');
            await this.getAllPlayers();

            this.closeModal('addPlayerModal');
        } catch (error) {
            this.handleError(error, 'create player');
        }
    }

    async updatePlayer(playerId, playerData) {
        try {
            await this.apiService.put(`${ApiConfig.ENDPOINTS.PLAYERS}/${playerId}`, playerData);
            NotificationService.show('success', 'Player updated successfully');
            await this.getAllPlayers();

            this.closeModal('editPlayerModal');
        } catch (error) {
            this.handleError(error, 'update player');
        }
    }

    async deletePlayer(playerId) {
        try {
            await this.apiService.delete(`${ApiConfig.ENDPOINTS.PLAYERS}/${playerId}`);
            NotificationService.show('success', 'Player deleted successfully');
            await this.getAllPlayers();
        } catch (error) {
            this.handleError(error, 'delete player');
        }
    }

    calculateYearsAndDays(isoDate) {
        const inputDate = new Date(isoDate);
        const currentDate = new Date();
        
        // Calculate the difference in milliseconds
        const differenceInMillis = currentDate - inputDate;
        
        // Convert milliseconds to days
        const differenceInDays = Math.floor(differenceInMillis / (1000 * 60 * 60 * 24));
        
        // Calculate the years and remaining days
        const years = Math.floor(differenceInDays / 365.25); // Account for leap years
        const days = Math.floor(differenceInDays % 365.25);
        
        return `${years} years, ${days} days`;
    }


    renderPlayers(players) {
        const tbody = document.querySelector('#players table tbody');
        tbody.innerHTML = players.map(player => `
            <tr class="align-middle">
                <td>${player.name}</td>
                <td>${this.calculateYearsAndDays(player.birth)}</td>
                <td>${player.position}</td>
                <td>${player.team?.name || 'Unassigned'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" 
                            type="button" 
                            data-bs-toggle="collapse" 
                            data-bs-target="#stats${player.id}" 
                            aria-expanded="false">
                        View Stats <i class="fas fa-chevron-down ms-1"></i>
                    </button>
                </td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-primary" onclick="app.playersManager.editPlayer(${player.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="app.playersManager.deletePlayer(${player.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
            <tr class="collapse" id="stats${player.id}">
                <td colspan="6" class="p-0">
                    <div class="container-fluid bg-light py-3">
                        <div class="row text-center">
                            <div class="col-md-4">
                                <div class="card border-0 bg-transparent">
                                    <div class="card-body">
                                        <h6 class="card-title text-muted mb-1">Appearances</h6>
                                        <h4 class="card-text text-primary">${player.appearances}</h4>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card border-0 bg-transparent">
                                    <div class="card-body">
                                        <h6 class="card-title text-muted mb-1">Goals</h6>
                                        <h4 class="card-text text-success">${player.goals}</h4>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card border-0 bg-transparent">
                                    <div class="card-body">
                                        <h6 class="card-title text-muted mb-1">Assists</h6>
                                        <h4 class="card-text text-info">${player.assists}</h4>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-12">
                                <div class="d-flex justify-content-between align-items-center px-3">
                                    <small class="text-muted">Last Updated: ${new Date(player.updated_at).toLocaleDateString()}</small>
                                    <small class="text-muted">Created: ${new Date(player.created_at).toLocaleDateString()}</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        `).join('');
    }
}

// Application initialization
class App {
    constructor() {
        this.teamsManager = new TeamsManager();
        this.matchesManager = new MatchesManager();
        this.playersManager = new PlayersManager();

        this.teams = [];
        this.matches = [];
        this.players = [];
    }

    async initialize() {
        this.teams = await this.teamsManager.getAllTeams();
        this.matches = await this.matchesManager.getAllMatches();
        this.players = await this.playersManager.getAllPlayers();

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Add form submission handlers here
        const addTeamForm = document.getElementById('addTeamForm');
        if (addTeamForm) {
            addTeamForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                this.teamsManager.createTeam(Object.fromEntries(formData));
            });
        }

        const addMatchForm = document.getElementById('addMatchForm');
        if (addMatchForm) {
            this.populateTeamDropdowns(addMatchForm, this.teams);
            
            addMatchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                this.matchesManager.createMatch(Object.fromEntries(formData));
            });
        }


        const addPlayerForm = document.getElementById('addPlayerForm');
        if (addPlayerForm) {
            this.populateTeamDropdowns(addPlayerForm, this.teams);
            
            addPlayerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                this.playersManager.createPlayer(Object.fromEntries(formData));
            });
        }
    }

    populateTeamDropdowns(form, teams) {
        const team1Select = form.querySelector('[name="team1_id"]');
        const team2Select = form.querySelector('[name="team2_id"]');

        if (!team1Select || !team2Select || !teams.length) {
            return;
        }

        const createTeamOption = (team) => {
            const option = document.createElement('option');
            option.value = team.id;
            option.textContent = team.name;
            return option;
        };

        // Clear existing options
        team1Select.innerHTML = '<option value="">Select Team 1</option>';
        team2Select.innerHTML = '<option value="">Select Team 2</option>';

        // Populate dropdowns
        teams.forEach(team => {
            team1Select.appendChild(createTeamOption(team));
            team2Select.appendChild(createTeamOption(team));
        });
    }
}

// Initialize the application
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new App();
    app.initialize();
});
