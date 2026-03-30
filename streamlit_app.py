import streamlit as st
from datetime import datetime, timedelta

# إعدادات واجهة منصة Relax
st.set_page_config(page_title="Relax Smart", page_icon="🟢", layout="centered")

# --- نظام البيانات المؤقتة ---
if 'balance_profit' not in st.session_state:
    st.session_state.balance_profit = 18.50  # أرباح قابلة للسحب
if 'initial_deposit' not in st.session_state:
    st.session_state.initial_deposit = 1000.00  # الإيداع الأساسي
if 'deposit_date' not in st.session_state:
    st.session_state.deposit_date = datetime.now() - timedelta(days=5) # مثال: أودع منذ 5 أيام

# حساب الـ 90 يوم
days_passed = (datetime.now() - st.session_state.deposit_date).days
days_remaining = max(0, 90 - days_passed)

st.markdown("<h2 style='text-align: center; color: #28a745;'>📊 منصة Relax الذكية</h2>", unsafe_allow_html=True)

# عرض الحالة المالية للمستثمر
col1, col2 = st.columns(2)
with col1:
    st.metric("أرباحك (قابلة للسحب)", f"{st.session_state.balance_profit} USDT")
with col2:
    st.metric("رأس المال المستثمر", f"{st.session_state.initial_deposit} USDT")
    st.caption(f"🔒 قفل السيولة: {days_remaining} يوم متبقي")

st.divider()

# القائمة الرئيسية للعمليات
option = st.selectbox("اختر ما تريد القيام به:", ["نظرة عامة", "تعبئة رصيد (إيداع)", "سحب الأرباح", "سحب رأس المال"])

if option == "تعبئة رصيد (إيداع)":
    st.info("🔄 حول USDT (شبكة BEP20) إلى العنوان أدناه:")
    st.code("0x05aec19d3d5e5cb9400caff56ab69c3799019942")
    st.file_uploader("ارفع صورة إثبات التحويل")
    if st.button("تأكيد الإيداع"):
        st.success("تم الإرسال! سيتم تفعيل باقة الـ 90 يوم فور التأكيد.")

elif option == "سحب الأرباح":
    st.write(f"المبلغ المتاح للسحب الفوري: **{st.session_state.balance_profit} USDT**")
    st.number_input("المبلغ المراد سحبه", min_value=5.0)
    st.text_input("عنوان محفظتك (BEP20)")
    if st.button("طلب سحب الأرباح"):
        st.success("تم طلب السحب! سيصلك خلال 24 ساعة.")

elif option == "سحب رأس المال":
    if days_remaining > 0:
        st.error(f"🚫 غير مسموح بسحب رأس المال حالياً. يجب مرور 90 يوماً. متبقي {days_remaining} يوم.")
        st.info("ملاحظة: يمكنك سحب أرباحك اليومية بشكل طبيعي من قسم 'سحب الأرباح'.")
    else:
        st.success("✅ انتهت فترة القفل. يمكنك سحب رأس مالك الآن.")
        st.button("سحب رأس المال")

# تسجيل الخروج
if st.sidebar.button("تسجيل الخروج"):
    st.rerun()
