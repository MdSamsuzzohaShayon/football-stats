// Public Matches Manager class
class PublicMatchesManager extends BaseManager {
    async getAllMatches() {
        try {
            const matches = await this.apiService.get(ApiConfig.ENDPOINTS.MATCHES);
            this.renderMatches(matches);
        } catch (error) {
            this.handleError(error, 'fetch matches');
        }
    }

    async viewMatch(matchId) {
        try {
            window.location.href = `single-match.html?matchId=${matchId}`;
        } catch (error) {
            this.handleError(error, 'view match');
        }
    }

    formatDate(dateString) {
        const options = { day: 'numeric', month: 'short', year: 'numeric' };
        return new Date(dateString).toLocaleDateString('en-US', options);
    }

    renderMatches(matches) {
        const matchesContainer = document.querySelector('.row');
        if (!matchesContainer) return;

        matchesContainer.innerHTML = matches
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .map(match => `
                <div class="col-12 col-md-6 col-lg-4">
                    <div class="card match-card" onclick="app.publicMatchesManager.viewMatch(${match.id})">
                        <div class="card-body">
                            <span class="badge bg-primary date-badge">
                                ${this.formatDate(match.created_at)}
                            </span>
                            <h5 class="card-title">
                                ${match.team1?.name || 'TBA'} vs ${match.team2?.name || 'TBA'}
                            </h5>
                            <p class="score text-center my-3">
                                ${match.score_team1} - ${match.score_team2}
                            </p>
                            <div class="d-flex justify-content-between text-muted">
                                <small>${match.tournament || 'League Match'}</small>
                                <small>${match.status}</small>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
    }
}

// Application initialization
class App {
    constructor() {
        this.publicMatchesManager = new PublicMatchesManager();
    }

    initialize() {
        this.publicMatchesManager.getAllMatches();
    }
}

// Initialize the application
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new App();
    app.initialize();
});
