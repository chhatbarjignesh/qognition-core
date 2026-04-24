import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/generated',
  testMatch: '**/*.spec.ts',
  timeout: 30000,
  outputDir: './test-results',
  reporter: [
    ['list'],
    ['json', { outputFile: 'tests/results/playwright_results.json' }],
    ['@reportportal/agent-js-playwright', {
      apiKey:      process.env.RP_API_KEY   || '',
      endpoint:    process.env.RP_ENDPOINT  || '',
      project:     process.env.RP_PROJECT   || 'qognition',
      launch:      'qognition-e2e',
      description: 'AI Generated E2E Tests',
      attributes:  [{ key: 'branch', value: process.env.BRANCH || 'feature' }],
    }],
  ],
  use: {
    baseURL:    'http://localhost:3000',
    headless:   true,
    screenshot: 'only-on-failure',
  },
});
