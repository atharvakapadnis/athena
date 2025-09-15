export const APP_TITLE = 'Athena Smart Description System';

export const ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  BATCHES: '/batches',
  RULES: '/rules',
  AI_ANALYSIS: '/ai-analysis',
  SYSTEM: '/system',
} as const;

export const BATCH_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const;

export const RULE_TYPES = {
  CONFIDENCE: 'confidence',
  CONTENT: 'content',
  FORMAT: 'format',
} as const;

export const FEEDBACK_TYPES = {
  QUALITY: 'quality',
  ACCURACY: 'accuracy',
  PREFERENCE: 'preference',
} as const;

export const QUERY_KEYS = {
  DASHBOARD_SUMMARY: ['dashboard', 'summary'] as const,
  BATCH_QUEUE: ['batches', 'queue'] as const,
  BATCH_HISTORY: ['batches', 'history'] as const,
  BATCH_DETAILS: (id: string) => ['batches', 'details', id] as const,
  BATCH_RESULTS: (id: string) => ['batches', 'results', id] as const,
  RULES_ACTIVE: ['rules', 'active'] as const,
  RULES_ALL: ['rules', 'all'] as const,
  AI_PATTERNS: ['ai', 'patterns'] as const,
  AI_CONFIDENCE: ['ai', 'confidence'] as const,
  SYSTEM_HEALTH: ['system', 'health'] as const,
  SYSTEM_STATS: ['system', 'stats'] as const,
  SYSTEM_LOGS: ['system', 'logs'] as const,
  CURRENT_USER: ['auth', 'me'] as const,
} as const;