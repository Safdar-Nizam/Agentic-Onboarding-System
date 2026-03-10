-- ============================================================
-- AI Onboarding Agent — PostgreSQL Schema
-- ============================================================
-- Run this file once against your database to create tables
-- and seed initial laptop inventory data.
--
--   psql -U postgres -d onboarding_db -f db/schema.sql
-- ============================================================

-- ── Employees ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employees (
    employee_id     TEXT PRIMARY KEY,
    name            TEXT        NOT NULL,
    email           TEXT        NOT NULL UNIQUE,
    role            TEXT        NOT NULL,
    department      TEXT        NOT NULL,
    start_date      DATE        NOT NULL,
    manager         TEXT        NOT NULL,
    location        TEXT        DEFAULT 'Remote',
    employment_type TEXT        DEFAULT 'Full-time',
    status          TEXT        DEFAULT 'Pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Onboarding Tasks ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS onboarding_tasks (
    task_id         SERIAL      PRIMARY KEY,
    employee_id     TEXT        NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    task_name       TEXT        NOT NULL,
    task_status     TEXT        DEFAULT 'Pending',
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_employee ON onboarding_tasks(employee_id);

-- ── Laptop Inventory ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS laptop_inventory (
    laptop_id       TEXT PRIMARY KEY,
    model           TEXT        NOT NULL DEFAULT 'MacBook Pro 16"',
    status          TEXT        NOT NULL DEFAULT 'Available',
    assigned_to     TEXT        REFERENCES employees(employee_id),
    assigned_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Seed Data — 10 laptops ready for assignment ──────────────
INSERT INTO laptop_inventory (laptop_id, model, status) VALUES
    ('LPT-001', 'MacBook Pro 16" M3',     'Available'),
    ('LPT-002', 'MacBook Pro 14" M3',     'Available'),
    ('LPT-003', 'Dell XPS 15',            'Available'),
    ('LPT-004', 'Dell XPS 13',            'Available'),
    ('LPT-005', 'ThinkPad X1 Carbon',     'Available'),
    ('LPT-006', 'ThinkPad T14s',          'Available'),
    ('LPT-007', 'MacBook Air 15" M3',     'Available'),
    ('LPT-008', 'HP EliteBook 840',       'Available'),
    ('LPT-009', 'MacBook Pro 16" M3',     'Available'),
    ('LPT-010', 'Dell Latitude 7440',     'Available')
ON CONFLICT (laptop_id) DO NOTHING;
