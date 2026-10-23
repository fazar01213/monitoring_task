import streamlit as st
import pandas as pd
import datetime
import os
import json
from datetime import date

st.set_page_config(page_title="Monitoring Task Tim", page_icon="📋", layout="wide")

DB_FILE = "data_task.csv"
MEMBERS_FILE = "anggota_tim.json"

DEFAULT_MEMBERS = ["Lando", "Rahma", "Anggota 3", "Anggota 4"]

def load_members():
    if os.path.exists(MEMBERS_FILE):
        with open(MEMBERS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_MEMBERS

def save_members(members):
    with open(MEMBERS_FILE, "w") as f:
        json.dump(members, f, indent=2)

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        if "id" in df.columns:
            df["id"] = df["id"].astype(str)
        return df
    return pd.DataFrame(columns=[
        "id", "jenis", "nama_task", "pic", "prioritas", 
        "tgl_mulai", "deadline", "status", "progress", 
        "catatan", "link_bukti", "tgl_selesai", "tindak_lanjut"
    ])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def main():
    st.sidebar.title("📌 Navigation")
    
    # Viewer terbuka untuk siapa saja; mode edit dilindungi password server-side.
    st.sidebar.caption("Akses umum: hanya melihat")
    admin_password = st.secrets.get("ADMIN_PASSWORD", os.environ.get("ADMIN_PASSWORD", ""))
    is_admin = False
    if admin_password:
        entered_password = st.sidebar.text_input("Password Admin", type="password")
        if entered_password:
            if entered_password == admin_password:
                is_admin = True
                st.sidebar.success("🔑 Mode Admin aktif")
            else:
                st.sidebar.error("Password admin salah")
    else:
        st.sidebar.warning("Password admin belum dikonfigurasi")
    
    members = load_members()
    df = load_data()

    if is_admin:
        st.sidebar.success("🔑 Mode Admin / Editor Aktif")
    else:
        st.sidebar.info("👁️ Mode Viewer (Read-Only)")

    menu = st.sidebar.selectbox("Pilih Halaman", [
        "📊 Dashboard Monitoring", 
        "➕ Tambah / Edit Task", 
        "📂 Daftar & Filter Task",
        "📅 Rekap Task",
        "⚙️ Pengaturan Tim"
    ])

    if menu == "📊 Dashboard Monitoring":
        render_dashboard(df, members)
    elif menu == "➕ Tambah / Edit Task":
        render_task_form(df, members, is_admin)
    elif menu == "📂 Daftar & Filter Task":
        render_task_list(df, members, is_admin)
    elif menu == "📅 Rekap Task":
        render_recap(df)
    elif menu == "⚙️ Pengaturan Tim":
        render_settings(members, is_admin)

def render_dashboard(df, members):
    st.title("📊 Dashboard Monitoring Task Tim")
    st.markdown("---")

    if df.empty:
        st.info("Belum ada data task. Silakan tambahkan task pada menu **Tambah / Edit Task**.")
        return

    today = date.today().strftime("%Y-%m-%d")
    
    total_task = len(df)
    selesai = len(df[df["status"] == "Selesai"])
    on_progress = len(df[df["status"] == "On Progress"])
    belum_mulai = len(df[df["status"] == "Belum Mulai"])
    hold = len(df[df["status"] == "Hold"])
    
    # Terlambat: deadline < today & status != Selesai
    terlambat = len(df[(df["deadline"] < today) & (df["status"] != "Selesai")])

    m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
    m1.metric("Total Task", total_task)
    m2.metric("Selesai", selesai)
    m3.metric("On Progress", on_progress)
    m4.metric("Belum Mulai", belum_mulai)
    m5.metric("Hold", hold)
    m6.metric("Terlambat", terlambat, delta_color="inverse")
    pct = (selesai / total_task * 100) if total_task > 0 else 0
    m7.metric("% Selesai", f"{pct:.1f}%")

    st.markdown("### 👥 Rekap per Anggota Tim")
    
    member_stats = []
    for m in members:
        m_df = df[df["pic"] == m]
        m_total = len(m_df)
        m_done = len(m_df[m_df["status"] == "Selesai"])
        m_prog = len(m_df[m_df["status"] == "On Progress"])
        m_start = len(m_df[m_df["status"] == "Belum Mulai"])
        m_hold = len(m_df[m_df["status"] == "Hold"])
        m_late = len(m_df[(m_df["deadline"] < today) & (m_df["status"] != "Selesai")])
        m_pct = f"{(m_done / m_total * 100):.1f}%" if m_total > 0 else "0%"
        
        member_stats.append({
            "Anggota Tim": m,
            "Total Task": m_total,
            "Selesai": m_done,
            "On Progress": m_prog,
            "Belum Mulai": m_start,
            "Hold": m_hold,
            "Terlambat": m_late,
            "% Selesai": m_pct
        })
    
    st.dataframe(pd.DataFrame(member_stats), use_container_width=True)

    st.markdown("### 📅 Rekap Berdasarkan Jenis Task")
    cat_stats = []
    for cat in ["Daily", "Weekly", "Monthly"]:
        c_df = df[df["jenis"] == cat]
        c_total = len(c_df)
        c_done = len(c_df[c_df["status"] == "Selesai"])
        c_prog = len(c_df[c_df["status"] == "On Progress"])
        c_start = len(c_df[c_df["status"] == "Belum Mulai"])
        c_hold = len(c_df[c_df["status"] == "Hold"])
        c_late = len(c_df[(c_df["deadline"] < today) & (c_df["status"] != "Selesai")])
        
        cat_stats.append({
            "Jenis Task": cat,
            "Total Task": c_total,
            "Selesai": c_done,
            "On Progress": c_prog,
            "Belum Mulai": c_start,
            "Hold": c_hold,
            "Terlambat": c_late
        })
    
    st.dataframe(pd.DataFrame(cat_stats), use_container_width=True)

def render_task_form(df, members, is_admin):
    st.title("➕ Tambah / Edit Task")
    
    if not is_admin:
        st.warning("🔒 Mode Viewer: Anda hanya dapat melihat data. Untuk menambah atau mengubah task, ubah mode ke Admin / Editor pada sidebar.")
        return

    st.markdown("Isi form di bawah untuk menambahkan task baru.")

    with st.form("task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            jenis = st.selectbox("Jenis Task", ["Daily", "Weekly", "Monthly"])
            nama_task = st.text_input("Nama Task *")
            pic = st.selectbox("PIC (Anggota Tim)", members)
            prioritas = st.selectbox("Prioritas", ["Tinggi", "Sedang", "Rendah"])
            catatan = st.text_area("Catatan / Kendala")

        with col2:
            tgl_mulai = st.date_input("Tanggal Mulai", date.today())
            deadline = st.date_input("Deadline", date.today())
            status = st.selectbox("Status", ["Belum Mulai", "On Progress", "Selesai", "Hold"])
            progress = st.slider("Progress (%)", 0, 100, 0, step=5)
            link_bukti = st.text_input("Link Bukti Google Drive (opsional)")
            tindak_lanjut = st.text_input("Tindak Lanjut")

        submitted = st.form_submit_button("Simpan Task")

        if submitted:
            if not nama_task.strip():
                st.error("Nama Task wajib diisi.")
                return

            new_id = str(len(df) + 1)
            tgl_selesai = str(date.today()) if status == "Selesai" else ""

            new_row = {
                "id": new_id,
                "jenis": jenis,
                "nama_task": nama_task,
                "pic": pic,
                "prioritas": prioritas,
                "tgl_mulai": str(tgl_mulai),
                "deadline": str(deadline),
                "status": status,
                "progress": progress,
                "catatan": catatan,
                "link_bukti": link_bukti,
                "tgl_selesai": tgl_selesai,
                "tindak_lanjut": tindak_lanjut
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success(f"Task '{nama_task}' berhasil disimpan!")

def render_task_list(df, members, is_admin):
    st.title("📂 Daftar & Filter Task")
    
    if df.empty:
        st.info("Belum ada data task.")
        return

    c1, c2, c3 = st.columns(3)
    filter_pic = c1.multiselect("Filter PIC", members, default=[])
    filter_jenis = c2.multiselect("Filter Jenis", ["Daily", "Weekly", "Monthly"], default=[])
    filter_status = c3.multiselect("Filter Status", ["Belum Mulai", "On Progress", "Selesai", "Hold"], default=[])

    filtered_df = df.copy()
    if filter_pic:
        filtered_df = filtered_df[filtered_df["pic"].isin(filter_pic)]
    if filter_jenis:
        filtered_df = filtered_df[filtered_df["jenis"].isin(filter_jenis)]
    if filter_status:
        filtered_df = filtered_df[filtered_df["status"].isin(filter_status)]

    st.markdown(f"**Menampilkan {len(filtered_df)} dari {len(df)} task**")

    # Display clean table
    display_cols = ["id", "jenis", "nama_task", "pic", "prioritas", "deadline", "status", "progress", "link_bukti"]
    st.dataframe(filtered_df[display_cols], use_container_width=True)

    if is_admin and not filtered_df.empty:
        st.markdown("### ✏️ Update Status Task")
        selected_id = st.selectbox("Pilih ID Task yang ingin di-update", filtered_df["id"].tolist())
        
        row_idx = df[df["id"] == selected_id].index[0]
        curr_row = df.loc[row_idx]

        with st.form("update_form"):
            st.write(f"Editing: **{curr_row['nama_task']}** (PIC: {curr_row['pic']})")
            
            u_status = st.selectbox("Status Baru", ["Belum Mulai", "On Progress", "Selesai", "Hold"], index=["Belum Mulai", "On Progress", "Selesai", "Hold"].index(curr_row["status"]))
            u_prog = st.slider("Progress %", 0, 100, int(curr_row["progress"]))
            u_link = st.text_input("Link Bukti Google Drive", value=str(curr_row["link_bukti"]))
            u_cat = st.text_area("Catatan / Kendala", value=str(curr_row["catatan"]))
            
            if st.form_submit_button("Update Task"):
                df.at[row_idx, "status"] = u_status
                df.at[row_idx, "progress"] = u_prog
                df.at[row_idx, "link_bukti"] = u_link
                df.at[row_idx, "catatan"] = u_cat
                if u_status == "Selesai" and not curr_row["tgl_selesai"]:
                    df.at[row_idx, "tgl_selesai"] = str(date.today())
                
                save_data(df)
                st.success("Task berhasil diperbarui!")
                st.rerun()

def render_recap(df):
    st.title("📅 Rekap Task per Periode")

    if df.empty:
        st.info("Belum ada data task.")
        return

    tab1, tab2, tab3 = st.tabs(["Daily", "Weekly", "Monthly"])

    with tab1:
        st.subheader("Task Daily")
        daily_df = df[df["jenis"] == "Daily"]
        st.dataframe(daily_df, use_container_width=True)

    with tab2:
        st.subheader("Task Weekly")
        weekly_df = df[df["jenis"] == "Weekly"]
        st.dataframe(weekly_df, use_container_width=True)

    with tab3:
        st.subheader("Task Monthly")
        monthly_df = df[df["jenis"] == "Monthly"]
        st.dataframe(monthly_df, use_container_width=True)

def render_settings(members, is_admin):
    st.title("⚙️ Pengaturan Tim")

    st.markdown("### Daftar Anggota Tim Aktif")
    for idx, m in enumerate(members, 1):
        st.write(f"{idx}. {m}")

    if not is_admin:
        st.warning("🔒 Mengubah daftar anggota tim membutuhkan Mode Admin / Editor.")
        return

    st.markdown("---")
    st.markdown("### Kelola Anggota Tim")

    new_member = st.text_input("Tambah Anggota Baru")
    if st.button("Tambah Anggota"):
        if new_member.strip() and new_member not in members:
            members.append(new_member.strip())
            save_members(members)
            st.success(f"Anggota '{new_member}' berhasil ditambahkan!")
            st.rerun()

if __name__ == "__main__":
    main()
