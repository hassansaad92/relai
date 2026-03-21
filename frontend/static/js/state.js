// Theme definitions
const themes = {
    'star': {
        '--accent': '#06aeee',
        '--accent-text': '#333333',
        '--accent-hover-light': 'rgba(6, 174, 238, 0.1)',
        '--accent-active-light': 'rgba(6, 174, 238, 0.2)',
        '--page-bg': '#F4F5F7',
        '--surface-border': '#E0E2E6',
        '--mid-blue': '#2b69ac',
    },
    'otis': {
        '--accent': '#f65275',
        '--accent-text': '#f65275',
        '--accent-hover-light': 'rgba(246, 82, 117, 0.1)',
        '--accent-active-light': 'rgba(246, 82, 117, 0.2)',
        '--page-bg': '#ffffff',
        '--surface-border': '#f0f0f0',
        '--mid-blue': '#2b69ac',
    }
};

// Status options (single source of truth)
const AWARD_STATUSES = [
    { value: 'awarded', label: 'Awarded' },
    { value: 'prospect', label: 'Prospect' },
];
const SCHEDULE_STATUSES = [
    { value: 'scheduled', label: 'Scheduled' },
    { value: 'not_scheduled', label: 'Not Scheduled' },
    { value: 'active', label: 'Active' },
];

// Data store
let allPersonnel = [];
let allProjects = [];
let allSkills = [];
let allAssignments = [];
let currentView = 'home';

// Scenario state
let allScenarios = [];
let currentScenarioId = null;

// Gantt/Table toggle
let ganttMode = 'timeline';

// Edit state
let editingPersonnelId = null;
let editingProjectId = null;

// Chat
let chatHistory = [];

// Schedule state
let selectedScheduleProjectId = null;
let assignFormPersonnelId = null;

// Project form state
let lastEndDateSource = null;

// Current date
const currentDate = new Date();

// View loaders registry — populated by each module
const viewLoaders = {};
