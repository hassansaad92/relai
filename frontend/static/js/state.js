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
