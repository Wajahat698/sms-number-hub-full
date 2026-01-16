# SMS Number Hub (Streamlit)

## Run

Create a virtualenv, install dependencies, then run:

streamlit run app.py

## Authentication

This app uses username/password authentication with roles:

- admin: manage users, view logs, assign numbers
- user: view inbox for assigned numbers

Bootstrap the initial admin by setting environment variables before first run:

- ADMIN_USERNAME (default: admin)
- ADMIN_PASSWORD (required to bootstrap)
- ADMIN_EMAIL (optional)

## Data

SQLite DB is stored at data/app.db

## Notes

Inbound SMS viewing requires connecting a provider (e.g., Twilio) and configuring credentials.

## Twilio webhook service

Inbound messages are ingested via a separate FastAPI service:

uvicorn webhook:app --host 0.0.0.0 --port 8000

Configure the Twilio phone number's Messaging webhook URL to:

http(s)://YOUR_PUBLIC_DOMAIN/twilio/sms

Environment variables:

- TWILIO_AUTH_TOKEN (required for signature verification)
- ENFORCE_TWILIO_SIGNATURE (default: true)

If you're running locally, use a tunneling tool (ngrok/Cloudflare Tunnel) to expose port 8000.

## Deployment notes

- Streamlit app and webhook can be deployed as two services (recommended).
- Ensure the DB path is persisted (SQLite) or swap to Postgres for production.
- Never commit credentials. Use environment variables in Render/Railway/AWS.
