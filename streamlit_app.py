import streamlit as st

# إعدادات الواجهة لتشبه الصورة التي أرسلتها
st.set_page_config(page_title="منصة Relax الذكية", layout="wide")

# نظام الدخول (لحماية بياناتك)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 مرحباً بك في Relax")
    user = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")
    if st.button("دخول", use_container_width=True):
        if user == "عمر" and password == "1234":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("بيانات الدخول خاطئة")
else:
    # القائمة الجانبية (الأيقونات السفلية في صورتك)
    page = st.sidebar.radio("القائمة الرئيسية", ["بيت", "تحديد الكمية", "أنا"])
    
    if page == "بيت":
        st.title("🏠 الصفحة الرئيسية")
        # الأزرار الثمانية كما في الصورة (1000083604.jpg)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("💰 تعبئة رصيد"):
                st.info("عنوان المحفظة (USDT - TRC20):")
                st.code("5D25D6BA994F8AC011F9017F96931C78F611D95CB93A3EF9")
                st.warning("سيتم خصم 12% عمولة إدارية.")
        with col2: st.button("📤 ينسحب")
        with col3: st.button("🤝 يساعد")
        with col4: st.button("👥 فريق")
        
        # عرض الأصول
        st.divider()
        c_a, c_b = st.columns(2)
        c_a.metric("إجمالي الأصول (USDT)", "10192.03", "12%")
        c_b.metric("الحساب الكمي (USDT)", "110.00", "نشط")
        
        st.divider()
        st.subheader("سجل الانسحاب")
        st.table({"المستخدم": ["+72****74", "b****@e..."], "المبلغ": ["+19359.91", "+17053.48"]})

    elif page == "تحديد الكمية":
        st.title("📊 نظام التحديد الكمي")
        amount = st.number_input("أدخل المبلغ لبدء العملية", min_value=10)
        if st.button("تشغيل الذكاء الاصطناعي ⚡"):
            st.balloons()
            st.success(f"تمت العملية! الربح المحتسب: {amount * 0.12} USDT")
