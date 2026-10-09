/**
 * VisionFit AI - Dashboard
 * Interactive dashboard with charts and AI companion
 */

class DashboardManager {
    constructor() {
        this.charts = {};
        this.chatHistory = [];
        this.isLoading = false;

        this.init();
    }

    // Bluetooth Manager Removed
    initBluetooth() {
        // Bluetooth functionality removed in favor of Google Fit
    }

    async init() {
        try {
            await this.loadDashboardData();
            this.initializeCharts();
            this.setupChatInterface();
            this.setupEventListeners();
            this.startLiveUpdates();

            this.startLiveUpdates();
            this.initBluetooth();

            console.log('Dashboard initialized successfully');
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            VisionFit.utils.showToast('Failed to load dashboard data', 'danger');
        }
    }

    async loadDashboardData() {
        try {
            const response = await VisionFit.api.get('/dashboard-stats');

            if (response.success) {
                this.dashboardData = response.data;
                this.updateStatCards();
            } else {
                throw new Error(response.error || 'Failed to load dashboard data');
            }

            // Also load Google Fit data if available
            this.loadGoogleFitData();

            // Auto-refresh Google Fit data every 60 seconds
            if (!this.fitInterval) {
                this.fitInterval = setInterval(() => {
                    this.loadGoogleFitData();
                }, 60000);
            }

        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            // Use mock data for demonstration
            this.dashboardData = this.generateMockData();
            this.updateStatCards();
        }
    }

    async loadGoogleFitData() {
        try {
            const response = await VisionFit.api.get('/google-fit-data');
            if (response.success && response.data) {
                this.updateGoogleFitUI(response.data);
            }
        } catch (error) {
            console.log('Google Fit data not available or not connected');
        }
    }

    updateGoogleFitUI(data) {
        // Update the Health Sync sidebar widgets

        // Show metrics section if hidden
        const metricsSection = document.getElementById('googleFitMetrics');
        const connectSection = document.getElementById('googleFitConnect');
        const statusBadge = document.getElementById('googleFitStatus');

        if (metricsSection) metricsSection.classList.remove('d-none');
        if (connectSection) connectSection.classList.add('d-none');
        if (statusBadge) statusBadge.innerHTML = '<span class="text-success">● On</span>';

        // Animate numbers
        const animateValue = (id, start, end, duration) => {
            const obj = document.getElementById(id);
            if (!obj) return;
            start = start || 0;
            end = end || 0;
            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                obj.innerHTML = Math.floor(progress * (end - start) + start);
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                }
            };
            window.requestAnimationFrame(step);
        };

        // Steps
        if (data.steps !== undefined) {
            animateValue('fitSteps', 0, data.steps, 1000);
        }

        // Calories
        if (data.calories !== undefined) {
            animateValue('fitCalories', 0, data.calories, 1000);
        }

        // Heart Rate
        const hrEl = document.getElementById('fitHeartRate');
        if (hrEl && data.heart_rate) {
            hrEl.textContent = data.heart_rate;
            if (data.heart_rate !== '--') {
                // Add pulse effect
                const icon = hrEl.closest('.d-flex').querySelector('.fa-heartbeat');
                if (icon) icon.classList.add('heart-pulse');
            }
        }

        // Update timestamp
        const timeEl = document.getElementById('fitLastUpdate');
        if (timeEl) {
            const now = new Date();
            timeEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
    }


    generateMockData() {
        const dates = [];
        const calories = [];
        const formScores = [];
        const workouts = [];

        // Generate data for past 14 days
        for (let i = 13; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            dates.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));

            if (Math.random() > 0.45) {
                calories.push(Math.floor(Math.random() * 200) + 120);
                formScores.push(Math.floor(Math.random() * 12) + 84);
                workouts.push(1);
            } else {
                calories.push(0);
                formScores.push(0);
                workouts.push(0);
            }
        }

        return {
            workout_dates: dates,
            calories_burned: calories,
            form_scores: formScores,
            exercise_distribution: {
                pushup: 5,
                squat: 8,
                jumping_jack: 4,
                yoga: 2,
                other: 0
            },
            total_workouts: workouts.reduce((sum, w) => sum + w, 0),
            total_reps: 185,
            avg_form_score: 87.5,
            avg_calories: Math.round(calories.reduce((sum, c) => sum + c, 0) / (workouts.filter(w => w > 0).length || 1))
        };
    }

    updateStatCards() {
        const totalWorkoutsCard = document.getElementById('totalWorkoutsCard');
        const totalCaloriesCard = document.getElementById('totalCaloriesCard');
        const totalRepsCard = document.getElementById('totalRepsCard');
        const avgFormScoreCard = document.getElementById('avgFormScoreCard');

        if (this.dashboardData) {
            if (totalWorkoutsCard && this.dashboardData.total_workouts !== undefined) {
                totalWorkoutsCard.textContent = this.dashboardData.total_workouts;
            }
            if (totalCaloriesCard && this.dashboardData.avg_calories !== undefined) {
                const sumCals = (this.dashboardData.calories_burned || []).reduce((a, b) => a + b, 0);
                totalCaloriesCard.textContent = sumCals || totalCaloriesCard.textContent;
            }
            if (totalRepsCard && this.dashboardData.total_reps !== undefined) {
                totalRepsCard.textContent = this.dashboardData.total_reps;
            }
            if (avgFormScoreCard && this.dashboardData.avg_form_score !== undefined) {
                avgFormScoreCard.textContent = `${this.dashboardData.avg_form_score}%`;
            }
        }
    }

    initializeCharts() {
        this.createWorkoutProgressChart();
        this.createExerciseDistributionChart();
        this.createFormScoreChart();
    }

    createWorkoutProgressChart() {
        const ctx = document.getElementById('workoutChart');
        if (!ctx) return;

        const dates = (this.dashboardData.workout_dates && this.dashboardData.workout_dates.length) 
            ? this.dashboardData.workout_dates 
            : ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5'];
        const calories = (this.dashboardData.calories_burned && this.dashboardData.calories_burned.length) 
            ? this.dashboardData.calories_burned 
            : [0, 0, 0, 0, 0];

        this.charts.workoutProgress = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Calories Burned',
                    data: calories,
                    borderColor: '#0072FF',
                    backgroundColor: 'rgba(0, 114, 255, 0.15)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#0dcaf0',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#0dcaf0',
                        borderColor: '#0072FF',
                        borderWidth: 1,
                        padding: 10,
                        callbacks: {
                            label: function (context) { return context.parsed.y + ' kcal'; }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.04)' },
                        ticks: { color: '#94a3b8', font: { size: 11 } }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: {
                            color: '#94a3b8',
                            callback: function (value) { return value + ' cal'; }
                        }
                    }
                }
            }
        });
    }

    createExerciseDistributionChart() {
        const ctx = document.getElementById('exerciseChart');
        if (!ctx) return;

        const dist = this.dashboardData.exercise_distribution || {};
        const pushups = dist.pushup || 0;
        const squats = dist.squat || 0;
        const jacks = dist.jumping_jack || 0;
        const yoga = dist.yoga || 0;
        const other = dist.other || 0;

        const total = pushups + squats + jacks + yoga + other;
        const displayData = total > 0 
            ? [pushups, squats, jacks, yoga] 
            : [1, 1, 1, 1];

        this.charts.exerciseDistribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Pushups', 'Squats', 'Jumping Jacks', 'Yoga'],
                datasets: [{
                    data: displayData,
                    backgroundColor: [
                        '#0dcaf0',
                        '#7000FF',
                        '#FF6B35',
                        '#20c997'
                    ],
                    borderWidth: 2,
                    borderColor: '#0f172a',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 16,
                            color: '#94a3b8',
                            font: { size: 11 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        bodyColor: '#ffffff',
                        borderColor: '#7000FF',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                cutout: '65%'
            }
        });
    }

    createFormScoreChart() {
        const ctx = document.getElementById('formScoreChart');
        if (!ctx) return;

        const dates = (this.dashboardData.workout_dates && this.dashboardData.workout_dates.length) 
            ? this.dashboardData.workout_dates 
            : ['Session 1', 'Session 2', 'Session 3', 'Session 4', 'Session 5'];
        const scores = (this.dashboardData.form_scores && this.dashboardData.form_scores.length) 
            ? this.dashboardData.form_scores 
            : [85, 88, 90, 87, 92];

        this.charts.formScoreProgression = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Posture Form Score (%)',
                    data: scores,
                    borderColor: '#20c997',
                    backgroundColor: 'rgba(32, 201, 151, 0.12)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#20c997',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#20c997',
                        borderColor: '#20c997',
                        borderWidth: 1,
                        padding: 10,
                        callbacks: {
                            label: function (context) { return 'Form Score: ' + context.parsed.y + '%'; }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.04)' },
                        ticks: { color: '#94a3b8', font: { size: 11 } }
                    },
                    y: {
                        min: 40,
                        max: 100,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: {
                            color: '#94a3b8',
                            callback: function (value) { return value + '%'; }
                        }
                    }
                }
            }
        });
    setupChatInterface() {
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendChat');

        if (chatInput && sendBtn) {
            // Send message on button click
            sendBtn.addEventListener('click', () => this.sendChatMessage());

            // Send message on Enter key
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendChatMessage();
                }
            });
        }
    }

    async sendChatMessage() {
        const chatInput = document.getElementById('chatInput');
        const message = chatInput.value.trim();

        if (!message || this.isLoading) return;

        // Clear input and show loading
        chatInput.value = '';
        this.isLoading = true;

        // Add user message to chat
        this.addChatMessage(message, 'user');

        try {
            // Show typing indicator
            this.showTypingIndicator();

            // Send to AI
            const response = await VisionFit.api.post('/fitness-chat', { question: message });

            // Remove typing indicator
            this.hideTypingIndicator();

            if (response.success) {
                this.addChatMessage(response.response, 'ai');
            } else {
                throw new Error(response.error || 'Failed to get response');
            }

        } catch (error) {
            console.error('Chat error:', error);
            this.hideTypingIndicator();
            this.addChatMessage('Sorry, I encountered an error. Please try again.', 'ai');
        } finally {
            this.isLoading = false;
        }
    }

    addChatMessage(message, sender) {
        const chatContainer = document.getElementById('chatMessages');
        if (!chatContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${sender} mb-2`;

        if (sender === 'user') {
            messageElement.innerHTML = `
                <div class="chat-bubble user ms-auto">
                    ${this.escapeHtml(message)}
                </div>
            `;
        } else {
            messageElement.innerHTML = `
                <div class="chat-bubble ai">
                    <strong>VisionFit AI:</strong><br>
                    ${this.escapeHtml(message)}
                </div>
            `;
        }

        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Add fade-in animation
        messageElement.style.opacity = '0';
        messageElement.style.transform = 'translateY(20px)';

        requestAnimationFrame(() => {
            messageElement.style.transition = 'all 0.3s ease';
            messageElement.style.opacity = '1';
            messageElement.style.transform = 'translateY(0)';
        });

        // Store in history
        this.chatHistory.push({ message, sender, timestamp: new Date() });
    }

    showTypingIndicator() {
        const chatContainer = document.getElementById('chatMessages');
        if (!chatContainer) return;

        const typingElement = document.createElement('div');
        typingElement.className = 'chat-message ai mb-2 typing-indicator';
        typingElement.innerHTML = `
            <div class="chat-bubble ai">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        chatContainer.appendChild(typingElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Add CSS for typing animation
        const style = document.createElement('style');
        style.textContent = `
            .typing-dots {
                display: flex;
                gap: 4px;
                align-items: center;
            }
            .typing-dots span {
                width: 6px;
                height: 6px;
                background: #6c757d;
                border-radius: 50%;
                animation: typing 1.4s infinite ease-in-out;
            }
            .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
            .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
            @keyframes typing {
                0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
                40% { transform: scale(1); opacity: 1; }
            }
        `;
        if (!document.querySelector('style[data-typing]')) {
            style.setAttribute('data-typing', 'true');
            document.head.appendChild(style);
        }
    }

    hideTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    setupEventListeners() {
        // Refresh data button (if exists)
        const refreshBtn = document.querySelector('[data-action="refresh"]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshDashboard());
        }

        // Export data button (if exists)
        const exportBtn = document.querySelector('[data-action="export"]');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportData());
        }

        // Listen for window resize to update charts
        window.addEventListener('visionfit:resize', () => {
            Object.values(this.charts).forEach(chart => {
                if (chart && typeof chart.resize === 'function') {
                    chart.resize();
                }
            });
        });
    }

    startLiveUpdates() {
        // Update every 30 seconds
        this.updateInterval = setInterval(() => {
            this.updateLiveData();
        }, 30000);
    }

    async updateLiveData() {
        try {
            // Update workout duration if timer is running
            const workoutTimer = VisionFit.components.timer.getElapsed('workout');
            if (workoutTimer > 0) {
                const duration = VisionFit.components.timer.formatTime(workoutTimer);
                document.getElementById('workoutDuration').textContent = duration;
            }

            // Refresh dashboard data periodically
            if (Math.random() > 0.8) { // 20% chance every 30 seconds
                await this.loadDashboardData();
                this.updateCharts();
            }

        } catch (error) {
            console.error('Live update error:', error);
        }
    }

    updateCharts() {
        if (!this.dashboardData) return;

        // 1. Update workout progress chart (Calories)
        if (this.charts.workoutProgress && this.dashboardData.workout_dates) {
            this.charts.workoutProgress.data.labels = this.dashboardData.workout_dates;
            this.charts.workoutProgress.data.datasets[0].data = this.dashboardData.calories_burned || [];
            this.charts.workoutProgress.update();
        }

        // 2. Update exercise distribution doughnut chart
        if (this.charts.exerciseDistribution && this.dashboardData.exercise_distribution) {
            const dist = this.dashboardData.exercise_distribution;
            const pushups = dist.pushup || 0;
            const squats = dist.squat || 0;
            const jacks = dist.jumping_jack || 0;
            const yoga = dist.yoga || 0;
            const total = pushups + squats + jacks + yoga;
            this.charts.exerciseDistribution.data.datasets[0].data = total > 0 ? [pushups, squats, jacks, yoga] : [1, 1, 1, 1];
            this.charts.exerciseDistribution.update();
        }

        // 3. Update form score progression chart
        if (this.charts.formScoreProgression && this.dashboardData.workout_dates) {
            this.charts.formScoreProgression.data.labels = this.dashboardData.workout_dates;
            this.charts.formScoreProgression.data.datasets[0].data = this.dashboardData.form_scores || [];
            this.charts.formScoreProgression.update();
        }
    }

    async refreshDashboard() {
        const refreshBtn = document.querySelector('[data-action="refresh"]');
        if (refreshBtn) {
            const originalText = refreshBtn.innerHTML;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            refreshBtn.disabled = true;
        }

        try {
            await this.loadDashboardData();
            this.updateCharts();
            VisionFit.utils.showToast('Dashboard refreshed', 'success');
        } catch (error) {
            VisionFit.utils.showToast('Failed to refresh dashboard', 'danger');
        } finally {
            if (refreshBtn) {
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
                refreshBtn.disabled = false;
            }
        }
    }

    exportData() {
        try {
            const exportData = {
                stats: this.dashboardData,
                chatHistory: this.chatHistory,
                exportDate: new Date().toISOString()
            };

            const dataStr = JSON.stringify(exportData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });

            const link = document.createElement('a');
            link.href = URL.createObjectURL(dataBlob);
            link.download = `visionfit-data-${new Date().toISOString().split('T')[0]}.json`;
            link.click();

            VisionFit.utils.showToast('Data exported successfully', 'success');
        } catch (error) {
            console.error('Export error:', error);
            VisionFit.utils.showToast('Failed to export data', 'danger');
        }
    }

    destroy() {
        // Clean up intervals and event listeners
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
    }
}




// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    // Check if we're on the dashboard page
    if (document.getElementById('workoutChart')) {
        window.dashboardManager = new DashboardManager();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function () {
    if (window.dashboardManager) {
        window.dashboardManager.destroy();
    }
});
