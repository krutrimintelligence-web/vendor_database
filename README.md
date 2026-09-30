# Vendor Directory
## One-time setup
1. Create a free Postgres database (Supabase or Neon). For Supabase use the *Session pooler* connection string (works on Streamlit Cloud).
2. Load the data from your PC:
   `pip install xlrd pandas sqlalchemy psycopg2-binary`
   `DATABASE_URL="postgresql://..." python seed_db.py Vendor_List.xls`
3. Push this folder to a GitHub repo (do not commit real secrets), then on share.streamlit.io: New app -> pick repo -> `app.py`.
4. App settings -> Secrets: paste `ADMIN_PASSWORD` and `DATABASE_URL` (see `.streamlit/secrets.toml.example`).
## Install on phones
Open the app URL: Android Chrome -> menu -> Add to Home screen; iPhone Safari -> Share -> Add to Home Screen.
## Local run
`pip install -r requirements.txt && ADMIN_PASSWORD=x streamlit run app.py` (uses local vendors.db when DATABASE_URL is unset)
