import streamlit as st

st.set_page_config(page_title="Relax", page_icon="💰", layout="centered")

if 'user_db' not in st.session_state:
    st.session_state.user_db = {"عمر": "1234"}
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 منصة Relax الذكية</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["تسجيل الدخول", "إنشاء حساب جديد"])
    with tab1:
        u = st.text_input("الاسم")
        p = st.text_input("السر", type="password")
        if st.button("دخول"):
            if u in st.session_state.user_db and st.session_state.user_db[u] == p:
                st.session_state.logged_in = True
                st.rerun()
    with tab2:
        nu = st.text_input("اسم جديد")
        np = st.text_input("سر جديد", type="password")
        if st.button("تسجيل"):
            st.session_state.user_db[nu] = np
            st.success("تم! سجل دخولك الآن.")
else:
    st.title("💰 محفظة Relax")
    st.metric("إجمالي الأصول (USDT)", "10192.03", "12%")
    if st.button("💰 تعبئة رصيد"):
        st.info("🔄 حول USDT (شبكة BEP20) إلى:")
        st.code("0x05aec19d3d5e5cb9400caff56ab69c3799019942")
    if st.sidebar.button("خروج"):
        st.session_state.logged_in = False
        st.rerun()
