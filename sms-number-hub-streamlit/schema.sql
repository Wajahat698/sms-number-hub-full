PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    email TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    e164 TEXT NOT NULL UNIQUE,
    provider TEXT,
    country TEXT,
    capabilities TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS store_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    store_name TEXT,
    store_id TEXT,
    login_email TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(platform, store_id, login_email)
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    number_id INTEGER NOT NULL,
    store_account_id INTEGER NOT NULL,
    purpose TEXT NOT NULL DEFAULT '2fa',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY(person_id) REFERENCES people(id),
    FOREIGN KEY(number_id) REFERENCES numbers(id),
    FOREIGN KEY(store_account_id) REFERENCES store_accounts(id),
    UNIQUE(number_id, store_account_id)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS user_phone_numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    number_id INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(number_id) REFERENCES numbers(id) ON DELETE CASCADE,
    UNIQUE(user_id, number_id)
);

CREATE TABLE IF NOT EXISTS phone_number_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number_id INTEGER NOT NULL,
    store_tag TEXT,
    purpose_tag TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(number_id) REFERENCES numbers(id) ON DELETE CASCADE,
    UNIQUE(number_id)
);

CREATE TABLE IF NOT EXISTS sms_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    provider_message_sid TEXT,
    to_number TEXT NOT NULL,
    from_number TEXT,
    body TEXT,
    received_at TEXT NOT NULL,
    number_id INTEGER,
    is_read INTEGER NOT NULL DEFAULT 0,
    otp_code TEXT,
    raw_payload TEXT,
    FOREIGN KEY(number_id) REFERENCES numbers(id) ON DELETE SET NULL,
    UNIQUE(provider, provider_message_sid)
);

CREATE TABLE IF NOT EXISTS app_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    context_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sms_received_at ON sms_messages(received_at);
CREATE INDEX IF NOT EXISTS idx_sms_to_number ON sms_messages(to_number);
CREATE INDEX IF NOT EXISTS idx_sms_number_id ON sms_messages(number_id);
CREATE INDEX IF NOT EXISTS idx_user_numbers_user_id ON user_phone_numbers(user_id);
CREATE INDEX IF NOT EXISTS idx_user_numbers_number_id ON user_phone_numbers(number_id);
