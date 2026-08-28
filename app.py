import streamlit as st
import pandas as pd

st.set_page_config(page_title="نظام تدفق المرضى", layout="wide")

# دعم الاتجاه من اليمين إلى اليسار (RTL)
st.markdown('''
    <style>
        body, div, h1, h2, h3, h4, p, span, label {
            direction: RTL !important;
            text-align: right !important;
        }
        .stSelectbox label, .stButton button {
            direction: RTL !important;
            float: right !important;
        }
        .stMetric {
            text-align: right !important;
        }
    </style>
''', unsafe_allow_html=True)

if "clinics" not in st.session_state:
    st.session_state.clinics = {
        "192.168.1.101": {"name": "عيادة العظام 1", "specialty": "عظام", "status": "🟢 أخضر", "queue": 2, "avg_time": 10},
        "192.168.1.102": {"name": "عيادة العظام 2", "specialty": "عظام", "status": "🟡 أصفر", "queue": 5, "avg_time": 10},
        "192.168.1.103": {"name": "عيادة الباطنية 1", "specialty": "باطنية", "status": "🟢 أخضر", "queue": 1, "avg_time": 8},
        "192.168.1.104": {"name": "عيادة الباطنية 2", "specialty": "باطنية", "status": "🔴 أحمر", "queue": 8, "avg_time": 8},
    }

st.title("🚑 نظام التوجيه الذكي وتدفق المرضى")
st.write("---")

# أزرار التنقل العلوي للجوال
nav1, nav2, nav3 = st.columns(3)
if "current_page" not in st.session_state:
    st.session_state.current_page = "الرئيسية"

if nav1.button("🚑 الطوارئ والتوجيه", use_container_width=True):
    st.session_state.current_page = "الرئيسية"
    st.rerun()

if nav2.button("👨‍⚕️ مكتب الطبيب", use_container_width=True):
    st.session_state.current_page = "الطبيب"
    st.rerun()

if nav3.button("🚪 شاشة الباب", use_container_width=True):
    st.session_state.current_page = "الباب"
    st.rerun()

st.write("---")
mode = st.session_state.current_page

if mode == "الباب":
    selected_ip = st.selectbox("اختر العيادة:", list(st.session_state.clinics.keys()))
    clinic = st.session_state.clinics[selected_ip]
    st.markdown(f"<h1 style='text-align: center;'>🏥 {clinic['name']}</h1>", unsafe_allow_html=True)
    status = clinic["status"]
    if "أخضر" in status:
        st.success("## 🟢 العيادة متاحة - تفضل بالدخول")
    elif "أصفر" in status:
        st.warning("## 🟡 ضغط مرتفع - يرجى الانتظار")
    else:
        st.error("## 🔴 العيادة متوقفة مؤقتاً")
    st.metric(label="عدد الحالات المنتظرة", value=f"{clinic['queue']} مرضى")

elif mode == "الطبيب":
    selected_ip = st.selectbox("اختر IP الجهاز الخاص بك:", list(st.session_state.clinics.keys()))
    clinic = st.session_state.clinics[selected_ip]
    st.subheader(f"👨‍⚕️ لوحة تحكم: {clinic['name']} ({selected_ip})")
    
    col1, col2, col3 = st.columns(3)
    if col1.button("🟢 متاح", use_container_width=True):
        st.session_state.clinics[selected_ip]["status"] = "🟢 أخضر"
        st.rerun()
    if col2.button("🟡 ضغط مرتفع", use_container_width=True):
        st.session_state.clinics[selected_ip]["status"] = "🟡 أصفر"
        st.rerun()
    if col3.button("🔴 توقف", use_container_width=True):
        st.session_state.clinics[selected_ip]["status"] = "🔴 أحمر"
        st.rerun()
        
    st.write("### إدارة الطابور:")
    c1, c2 = st.columns(2)
    if c1.button("➕ دخول مريض جديد", use_container_width=True):
        st.session_state.clinics[selected_ip]["queue"] += 1
        st.rerun()
    if c2.button("➖ إنهاء حالة ومعاينة", use_container_width=True) and clinic["queue"] > 0:
        st.session_state.clinics[selected_ip]["queue"] -= 1
        st.rerun()

else:
    def get_best_clinic(specialty):
        best_ip, min_wait = None, float('inf')
        for ip, data in st.session_state.clinics.items():
            if data["specialty"] == specialty and data["status"] != "🔴 أحمر":
                penalty = 15 if data["status"] == "🟡 أصفر" else 0
                wait = (data["queue"] * data["avg_time"]) + penalty
                if wait < min_wait:
                    min_wait, best_ip = wait, ip
        return best_ip, min_wait

    spec = st.selectbox("اختر التخصص المطلوب للمريض:", ["عظام", "باطنية"])
    best_ip, wait_time = get_best_clinic(spec)
    if best_ip:
        st.success(f"💡 **التوصية الذكية:** تحويل المريض إلى **{st.session_state.clinics[best_ip]['name']}** | ⏱️ الانتظار المتوقع: **{wait_time} دقيقة**")
    else:
        st.error("⚠️ جميع عيادات هذا التخصص متوقفة حالياً!")
        
    st.write("### حالة العيادات اللحظية:")
    df = pd.DataFrame([{"IP": ip, "العيادة": d["name"], "التخصص": d["specialty"], "الحالة": d["status"], "المنتظرون": d["queue"]} for ip, d in st.session_state.clinics.items()])
    st.dataframe(df, use_container_width=True)
