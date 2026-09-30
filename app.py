import hmac, os, re
from datetime import datetime
import pandas as pd
import streamlit as st
from sqlalchemy import text
from db import make_engine, meta

st.set_page_config(page_title="Vendor Directory", page_icon="📒", layout="centered")


def secret(name, default=""):
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, default)


@st.cache_resource
def engine():
    e = make_engine(secret("DATABASE_URL", "sqlite:///vendors.db"))
    meta.create_all(e)
    return e


def run(sql, args=None, write=False):
    with engine().begin() as con:
        res = con.execute(text(sql), args or {})
        return None if write else [dict(r._mapping) for r in res]


def admin_pw():
    return secret("ADMIN_PASSWORD")


def is_admin():
    return st.session_state.get("admin", False)


def need_admin():
    if not is_admin():
        st.stop()


def save(v, vid=None):
    need_admin()
    if vid is None:
        run("INSERT INTO vendors(created_at,category,name,location,phone,notes) "
            "VALUES(:created,:category,:name,:location,:phone,:notes)",
            dict(v, created=datetime.now().isoformat(timespec="seconds")), True)
    else:
        run("UPDATE vendors SET category=:category,name=:name,location=:location,phone=:phone,notes=:notes WHERE id=:id",
            dict(v, id=vid), True)


def remove(vid):
    need_admin()
    run("DELETE FROM vendors WHERE id=:id", {"id": vid}, True)


rows = run("SELECT * FROM vendors ORDER BY category, name")
cats = sorted({r["category"] for r in rows})
digits = lambda s: re.sub(r"\D", "", s or "")

st.title("📒 Vendor Directory")
t_search, t_stats, t_admin = st.tabs(["🔍 Search", "📊 By type", "🔐 Admin"])

with t_search:
    term = st.text_input("Search", placeholder="Name, business type or phone", label_visibility="collapsed")
    mode = st.radio("Search in", ["All", "Name", "Business type", "Phone"], horizontal=True)
    cat = st.selectbox("Business type", ["All types"] + cats)

    def hit(r):
        if cat != "All types" and r["category"] != cat:
            return False
        t = term.strip().lower()
        if not t:
            return True
        f = {"Name": t in r["name"].lower(), "Business type": t in r["category"].lower(),
             "Phone": bool(digits(t)) and digits(t) in digits(r["phone"])}
        return any(f.values()) if mode == "All" else f[mode]

    found = [r for r in rows if hit(r)]
    st.caption(f"{len(found)} of {len(rows)} vendors")
    for r in found:
        with st.container(border=True):
            st.markdown(f"**{r['name']}**  \n:gray[{r['category']}]")
            if r["phone"]:
                tel = re.sub(r"[^\d+]", "", r["phone"])
                st.markdown(f"📞 [{r['phone']}](tel:{tel})")
            loc = r["location"] or ""
            if loc:
                st.markdown(f"📍 [Open in Maps]({loc})" if loc.startswith("http") else f"📍 {loc}")
            if r["notes"]:
                st.caption(r["notes"])

with t_stats:
    if rows:
        counts = pd.Series([r["category"] for r in rows]).value_counts()
        a, b = st.columns(2)
        a.metric("Vendors", len(rows))
        b.metric("Business types", len(counts))
        st.bar_chart(counts, horizontal=True, height=max(300, 24 * len(counts)))
    else:
        st.info("No vendors yet.")


def form(v, key, label):
    v = v or {}
    with st.form(key):
        opts = cats + ["➕ New type…"]
        sel = st.selectbox("Business type", opts, index=cats.index(v["category"]) if v.get("category") in cats else 0)
        new = st.text_input("New business type (only if '➕ New type…' is selected)")
        name = st.text_input("Name & address of vendor", v.get("name", ""))
        loc = st.text_input("Location (map link or description)", v.get("location", ""))
        phone = st.text_input("Contact number", v.get("phone", ""))
        notes = st.text_area("Additional information", v.get("notes", ""))
        ok = st.form_submit_button(label, type="primary")
    if ok:
        c = " ".join((new if sel.startswith("➕") else sel).split())
        if not c or not name.strip():
            st.error("Business type and name are required.")
            return None
        return dict(category=c, name=name.strip(), location=loc.strip(), phone=phone.strip(), notes=notes.strip())


with t_admin:
    if not is_admin():
        if not admin_pw():
            st.warning("Admin is disabled: set an ADMIN_PASSWORD secret.")
        else:
            pw = st.text_input("Admin password", type="password")
            if st.button("Log in"):
                if hmac.compare_digest(pw, admin_pw()):
                    st.session_state.admin = True
                    st.rerun()
                else:
                    st.error("Wrong password.")
    else:
        if st.button("Log out"):
            st.session_state.admin = False
            st.rerun()
        act = st.radio("Action", ["Add vendor", "Edit / delete vendor"], horizontal=True)
        if act == "Add vendor":
            v = form(None, "add", "Add vendor")
            if v:
                save(v)
                st.success("Vendor added.")
                st.rerun()
        elif rows:
            pick = st.selectbox("Vendor", rows, format_func=lambda r: f"{r['name']} — {r['category']}")
            v = form(pick, f"edit{pick['id']}", "Save changes")
            if v:
                save(v, pick["id"])
                st.success("Saved.")
                st.rerun()
            st.divider()
            if st.checkbox("I want to delete this vendor", key=f"cd{pick['id']}") and st.button("🗑 Delete", type="secondary"):
                remove(pick["id"])
                st.rerun()
