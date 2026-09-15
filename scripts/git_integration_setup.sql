-- =============================================================
-- Git Integration Setup Scripts
-- =============================================================

-- Step 1: Create a dedicated database and schema for Git secrets
CREATE DATABASE IF NOT EXISTS GIT_INTEGRATION_DB;
CREATE SCHEMA IF NOT EXISTS GIT_INTEGRATION_DB.SECRETS;

-- Step 2: Create a secret with your personal access token
USE SCHEMA GIT_INTEGRATION_DB.SECRETS;

CREATE OR REPLACE SECRET GIT_PAT
  TYPE = PASSWORD
  USERNAME = 'your-git-username'
  PASSWORD = 'your-personal-access-token';

-- Step 3: Create the API integration (references the secret)
CREATE OR REPLACE API INTEGRATION GIT_API_INTEGRATION
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/your-org/')
  ALLOWED_AUTHENTICATION_SECRETS = (GIT_INTEGRATION_DB.SECRETS.GIT_PAT)
  ENABLED = TRUE;
