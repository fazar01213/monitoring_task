import os
from datetime import date
import pandas as pd
import streamlit as st
from storage import load_data, save_data, load_members, save_members, upload_evidence, is_admin_password_valid, task_is_late
st.set_page_config(page_title='Monitoring Task Tim',page_icon='📋',layout='wide')
@st.cache_data(ttl=30)
def cached_data(): return load_data()
@st.cache_data(ttl=60)
def cached_members(): return load_members()
def admin_login():
    configured=st.secrets.get('ADMIN_PASSWORD',os.environ.get('ADMIN_PASSWORD',''))
    if not configured: st.sidebar.warning('Password admin belum dikonfigurasi — mode lihat saja'); return False
    if st.session_state.get('admin_authenticated',False): return True
    with st.sidebar.form('login'):
        password=st.text_input('Password Admin',type='password'); submit=st.form_submit_button('Masuk sebagai Admin')
    if submit:
        if is_admin_password_valid(password,configured): st.session_state.admin_authenticated=True; st.rerun()
        st.sidebar.error('Password salah')
    return False
def main():
    st.sidebar.title('📌 Monitoring Task'); admin=admin_login()
    if admin:
        st.sidebar.success('🔑 Admin aktif')
        if st.sidebar.button('Keluar dari Admin'): st.session_state.admin_authenticated=False; st.rerun()
    else: st.sidebar.info('👁️ Mode Viewer — read-only')
    try: df,members=cached_data(),cached_members()
    except Exception as e:
        st.title('📋 Monitoring Task Tim'); st.error(f'Backend belum siap: {e}'); st.info('Isi TASK_SPREADSHEET_ID dan DRIVE_FOLDER_ID di Streamlit Secrets.'); return
    menus=['Dashboard','Daftar Task','Rekap Daily/Weekly/Monthly']+(['Tambah Task','Pengaturan'] if admin else [])
    menu=st.sidebar.radio('Halaman',menus)
    if menu=='Dashboard': dashboard(df,members)
    elif menu=='Daftar Task': task_list(df)
    elif menu=='Rekap Daily/Weekly/Monthly': recap(df)
    elif menu=='Tambah Task': task_form(df,members)
    else: settings(members)
def dashboard(df,members):
    st.title('📊 Dashboard Monitoring Task Tim'); today=date.today().isoformat(); n=len(df); done=int((df.status=='Selesai').sum()) if n else 0
    metrics=[('Total Task',n),('Selesai',done),('On Progress',int((df.status=='On Progress').sum())),('Belum Mulai',int((df.status=='Belum Mulai').sum())),('Hold',int((df.status=='Hold').sum())),('Terlambat',sum(task_is_late(r.deadline,r.status,today) for _,r in df.iterrows())),('% Selesai',f'{done/n*100:.1f}%' if n else '0%')]
    for col,(label,value) in zip(st.columns(7),metrics): col.metric(label,value)
    rows=[]
    for p in members:
        x=df[df.pic==p]; total=len(x); d=int((x.status=='Selesai').sum())
        rows.append({'Anggota':p,'Total':total,'Selesai':d,'On Progress':int((x.status=='On Progress').sum()),'Belum Mulai':int((x.status=='Belum Mulai').sum()),'Hold':int((x.status=='Hold').sum()),'Terlambat':sum(task_is_late(r.deadline,r.status,today) for _,r in x.iterrows()),'% Selesai':f'{d/total*100:.1f}%' if total else '0%'})
    st.subheader('👥 Rekap per Anggota'); st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    kinds=[]
    for k in ['Daily','Weekly','Monthly']:
        x=df[df.jenis==k]; kinds.append({'Jenis':k,'Total':len(x),'Selesai':int((x.status=='Selesai').sum()),'On Progress':int((x.status=='On Progress').sum()),'Belum Mulai':int((x.status=='Belum Mulai').sum()),'Hold':int((x.status=='Hold').sum())})
    st.subheader('📅 Rekap Jenis Task'); st.dataframe(pd.DataFrame(kinds),use_container_width=True,hide_index=True)
def task_list(df):
    st.title('📂 Daftar Task')
    if df.empty: st.info('Belum ada task.'); return
    a,b,c=st.columns(3); pics=a.multiselect('PIC',sorted(df.pic.unique())); kinds=b.multiselect('Jenis',['Daily','Weekly','Monthly']); states=c.multiselect('Status',['Belum Mulai','On Progress','Selesai','Hold']); x=df.copy()
    if pics:x=x[x.pic.isin(pics)]
    if kinds:x=x[x.jenis.isin(kinds)]
    if states:x=x[x.status.isin(states)]
    st.dataframe(x,use_container_width=True,hide_index=True,column_config={'link_bukti':st.column_config.LinkColumn('Bukti')})
def task_form(df,members):
    st.title('➕ Tambah Task')
    with st.form('new_task'):
        a,b=st.columns(2); kind=a.selectbox('Jenis',['Daily','Weekly','Monthly']); name=a.text_input('Nama Task *'); pic=a.selectbox('PIC',members); priority=a.selectbox('Prioritas',['Tinggi','Sedang','Rendah']); start=b.date_input('Tanggal Mulai',date.today()); deadline=b.date_input('Deadline',date.today()); status=b.selectbox('Status',['Belum Mulai','On Progress','Selesai','Hold']); progress=st.slider('Progress',0,100,0,5); note=st.text_area('Catatan / Kendala'); follow=st.text_input('Tindak Lanjut'); file=st.file_uploader('Upload Bukti ke Google Drive')
        if st.form_submit_button('Simpan Task'):
            if not name.strip(): st.error('Nama task wajib diisi.'); return
            with st.spinner('Mengunggah bukti dan menyimpan task...'):
                link=upload_evidence(file,name) if file else ''
                row={'id':str(len(df)+1),'jenis':kind,'nama_task':name,'pic':pic,'prioritas':priority,'tgl_mulai':str(start),'deadline':str(deadline),'status':status,'progress':progress,'catatan':note,'link_bukti':link,'tgl_selesai':str(date.today()) if status=='Selesai' else '','tindak_lanjut':follow}
                save_data(pd.concat([df,pd.DataFrame([row])],ignore_index=True)); cached_data.clear()
            st.success('Task berhasil disimpan.'); st.rerun()
def recap(df):
    st.title('📅 Rekap Task')
    for k in ['Daily','Weekly','Monthly']:
        with st.expander(k,expanded=True): st.dataframe(df[df.jenis==k],use_container_width=True,hide_index=True,column_config={'link_bukti':st.column_config.LinkColumn('Bukti')})
def settings(members):
    st.title('⚙️ Pengaturan Tim'); st.write(members); name=st.text_input('Tambah anggota')
    if st.button('Simpan Anggota') and name.strip() and name not in members: save_members(members+[name.strip()]); cached_members.clear(); st.success('Anggota ditambahkan.'); st.rerun()
if __name__=='__main__': main()
