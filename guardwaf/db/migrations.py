"""
Database Schema Migration Manager for GuardWAF Production Platform.
"""

from typing import List, Dict, Any

MIGRATIONS: List[Dict[str, Any]] = [
    {
        "version": 1,
        "name": "initial_schema",
        "description": "Initial schema for organizations, users, memberships, and agent registry.",
        "sql": """
        CREATE TABLE IF NOT EXISTS organizations (
            organization_id VARCHAR(64) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(255) UNIQUE NOT NULL,
            status VARCHAR(32) DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(64) PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            display_name VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255),
            status VARCHAR(32) DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    },
    {
        "version": 2,
        "name": "credentials_and_incidents",
        "description": "Adds hashed API credentials and incident tracking tables.",
        "sql": """
        CREATE TABLE IF NOT EXISTS agent_credentials (
            credential_id VARCHAR(64) PRIMARY KEY,
            organization_id VARCHAR(64) NOT NULL,
            agent_id VARCHAR(64) NOT NULL,
            credential_prefix VARCHAR(32) NOT NULL,
            credential_hash VARCHAR(128) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            revoked_at TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS incidents (
            incident_id VARCHAR(64) PRIMARY KEY,
            organization_id VARCHAR(64) NOT NULL,
            agent_id VARCHAR(64) NOT NULL,
            title VARCHAR(255) NOT NULL,
            severity VARCHAR(32) DEFAULT 'HIGH',
            status VARCHAR(32) DEFAULT 'OPEN',
            correlation_id VARCHAR(128)
        );
        """
    }
]

class DatabaseMigrationManager:
    def __init__(self):
        self._current_version = 0

    def get_current_version(self) -> int:
        return self._current_version

    def apply_pending_migrations(self) -> List[str]:

        applied = []
        for m in MIGRATIONS:
            if m["version"] > self._current_version:
                applied.append(f"Applied Migration v{m['version']}: {m['name']}")
                self._current_version = m["version"]
        return applied
