import streamlit as st
import pandas as pd
import time
import qrcode
from io import BytesIO

# 1. تهيئة الصفحة والديكور
st.set_page_config(page_title="نظام التوجيه الذكي وتدفق المرضى", layout="wide", page_icon="🚑")

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
        .critical-box {
            background-color: #ffe6e6;
            border-right: 5px solid #ff4d4d;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
    </style>
''', unsafe_allow_html=True)

# 2. تهيئة قواعد البيانات المؤقتة في الـ Session State
if "clinics" not in st.session_state:
    st.session_state.clinics = {
        "192.168.1.101": {"name": "عيادة العظام 1", "specialty": "عظام", "status": "🟢 أخضر", "queue": 2, "avg_time": 10, "critical_count": 0},
        "192.168.1.102": {"name": "عيادة العظام 2", "specialty": "عظام", "status": "🟡 أصفر", "queue": 5, "avg_time": 10, "critical_count": 1},
        "192.168.1.103": {"name": "عيادة الباطنية 1", "specialty": "باطنية", "status": "🟢 أخضر", "queue": 1, "avg_time": 8, "critical_count": 0},
        "192.168.1.104": {"name": "عيادة الباطنية 2", "specialty": "باطنية", "status": "🔴 أحمر", "queue": 8, "avg_time": 8, "critical_count": 2},
    }

if "patients_history" not in st.session_state:
    st.session_state.patients_history = [
        {"id": "P-101", "triage": "🟢 عادي", "clinic": "عيادة العظام 1", "wait": 10},
        {"id": "P-102", "triage": "🔴 حرج جداً", "clinic": "عيادة الباطنية 1", "wait": 0},
        {"id": "P-103", "triage": "🟡 متوسط", "clinic": "عيادة العظام 2", "wait": 20},
    ]

# 3. شريط الهيدر والتنقل
st.title("🚑 نظام التوجيه الذكي وتدفق المرضى (Smart Patient Routing System)")
st.caption("نظام الفرز الطبي التلقائي والمزامنة اللحظية للطوارئ والعيادات")
st.write("---")

nav1, nav2, nav3, nav4 = st.columns(4)
if "current_page" not in st.session_state:
    st.session_state.current_page = "الرئيسية"

if nav1.button("🚑 الاستقبال والفرز (Triage)", use_container_width=True):
    st.session_state.current_page = "الرئيسية"
    st.rerun()

if nav2.button("👨‍⚕️ مكتب الطبيب", use_container_width=True):
    st.session_state.current_page = "الطبيب"
    st.rerun()

if nav3.button("🚪 شاشة الانتظار", use_container_width=True):
    st.session_state.current_page = "الباب"
    st.rerun()

if nav4.button("📊 لوحة التحليلات", use_container_width=True):
    st.session_state.current_page = "التحليلات"
    st.rerun()

st.write("---")
mode = st.session_state.current_page

# 4. الشاشة الأولى: الفرز والاستقبال (Triage & Reception)
if mode == "الرئيسية":
    st.subheader("📋 تسجيل مريض جديد وفرز الحالات (Triage & Routing)")
    
    col_input1, col_input2, col_input3 = st.columns(3)
    patient_name = col_input1.text_input("اسم المريض / الرقم:", value="مريض جديد")
    spec = col_input2.selectbox("التخصص المطلوب:", ["عظام", "باطنية"])
    triage_level = col_input3.selectbox("مستوى الفرز الطبي (Triage):", [
        "🟢 عادي (Stable)",
        "🟡 متوسط (Urgent)",
        "🔴 حرج جداً (Critical / Emergency)"
    ])
    
    # خوارزمية التوجيه الذكي المعدلة ببروتوكول Triage
    def get_best_clinic(specialty, triage):
        best_ip, min_wait = None, float('inf')
        for ip, data in st.session_state.clinics.items():
            if data["specialty"] == specialty and data["status"] != "🔴 أحمر":
                # إذا كانت الحالة حرجة، يتم إنقاص وزن الانتظار للتوجيه للعيادة الأسرع فوراً
                penalty = 15 if data["status"] == "🟡 أصفر" else 0
                if "🔴" in triage:
                    wait = (data["queue"] * 2) # أولوية قصوى للم الحالات الحرجة
                else:
                    wait = (data["queue"] * data["avg_time"]) + penalty
                
                if wait < min_wait:
                    min_wait, best_ip = wait, ip
        return best_ip, min_wait

    if st.button("🚀 توجيه واستخراج تذكرة المريض", type="primary", use_container_width=True):
        best_ip, wait_time = get_best_clinic(spec, triage_level)
        if best_ip:
            st.session_state.clinics[best_ip]["queue"] += 1
            if "🔴" in triage_level:
                st.session_state.clinics[best_ip]["critical_count"] += 1
                st.error(f"🚨 **توجيه طوارئ عاجل:** تم تحويل الحالة الحرجة إلى **{st.session_state.clinics[best_ip]['name']}** وتنبيه الطبيب فوراً!")
            else:
                st.success(f"💡 **التوصية الذكية:** تحويل المريض إلى **{st.session_state.clinics[best_ip]['name']}** | ⏱️ الانتظار المتوقع: **{wait_time} دقيقة**")
            
            # إضافة المريض لسجل التحليلات
            st.session_state.patients_history.append({
                "id": patient_name, "triage": triage_level, "clinic": st.session_state.clinics[best_ip]['name'], "wait": wait_time
            })
            
            # إنشاء QR Code للتذكرة الرقمية
            qr = qrcode.make(f"Patient: {patient_name} | Clinic: {st.session_state.clinics[best_ip]['name']} | Status: {triage_level}")
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            st.image(buffer.getvalue(), caption="امسح الرمز لتتبع التذكرة من الجوال 📱", width=150)
        else:
            st.error("⚠️ جميع عيادات هذا التخصص متوقفة حالياً! يرجى تحويل الحالة لقسم الطوارئ المركزي.")

    st.write("### 🏥 حالة العيادات والضغط اللحظي:")
    df = pd.DataFrame([
        {
            "IP": ip, 
            "العيادة": d["name"], 
            "التخصص": d["specialty"], 
            "الحالة": d["status"], 
            "المرضى المنتظرون": d["queue"],
            "الحالات الحرجة": d["critical_count"]
        } for ip, d in st.session_state.clinics.items()
    ])
    st.dataframe(df, use_container_width=True)

# 5. الشاشة الثانية: مكتب الطبيب (Doctor Portal)
elif mode == "الطبيب":
    selected_ip = st.selectbox("اختر العيادة / IP الجهاز الخاص بك:", list(st.session_state.clinics.keys()))
    clinic = st.session_state.clinics[selected_ip]
    
    st.subheader(f"👨‍⚕️ لوحة تحكم: {clinic['name']} ({selected_ip})")
    
    if clinic["critical_count"] > 0:
        st.markdown(f'''
            <div class="critical-box">
                <h4>🚨 تنبيه طوارئ: يوجد {clinic['critical_count']} حالة حرجة بالانتظار تتطلب التدخل الفوري!</h4>
            </div>
        ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    if col1.button("🟢 متاح (جاهز لاستقبال)", use_container_width=True):
        st.session_state.clinics[selected_ip]["status"] = "🟢 أخضر"
        st.rerun()
    if col2.button("🟡 ضغط مرتفع", use_container_width=True):
        st.session_state.clinics[selected_ip]["status"] = "🟡 أصفر"
        st.rerun()
    if col3.button("🔴 توقف مؤقت / طوارئ", use_container_width=True):
        st.session_state.clinics[selected_ip]["status"] = "🔴 أحمر"
        st.rerun()
        
    st.write("---")
    st.write("### 👥 إدارة طابور العيادة:")
    c1, c2 = st.columns(2)
    if c1.button("➕ دخول مريض جديد", use_container_width=True):
        st.session_state.clinics[selected_ip]["queue"] += 1
        st.rerun()
    if c2.button("✅ إنهاء المعاينة ودخول التالي", use_container_width=True) and clinic["queue"] > 0:
        st.session_state.clinics[selected_ip]["queue"] -= 1
        if clinic["critical_count"] > 0:
            st.session_state.clinics[selected_ip]["critical_count"] -= 1
        st.rerun()

# 6. الشاشة الثالثة: شاشة الانتظار والباب (Door & Waiting Display)
elif mode == "الباب":
    selected_ip = st.selectbox("اختر العيادة للمعاينة:", list(st.session_state.clinics.keys()))
    clinic = st.session_state.clinics[selected_ip]
    
    st.markdown(f"<h1 style='text-align: center; color: #1E88E5;'>🏥 {clinic['name']}</h1>", unsafe_allow_html=True)
    status = clinic["status"]
    
    if "أخضر" in status:
        st.success("## 🟢 العيادة متاحة - تفضل بالدخول عند استدعاء رقمك")
    elif "أصفر" in status:
        st.warning("## 🟡 ضغط مرتفع - يرجى الانتظار")
    else:
        st.error("## 🔴 العيادة متوقفة مؤقتاً لعلاج حالة حادّة")
        
    m1, m2 = st.columns(2)
    m1.metric(label="عدد الحالات المنتظرة", value=f"{clinic['queue']} مرضى")
    m2.metric(label="زمن الانتظار المتوقع", value=f"{clinic['queue'] * clinic['avg_time']} دقيقة")

# 7. الشاشة الرابعة: التحليلات والإحصائيات (Analytics & Insights)
elif mode == "التحليلات":
    st.subheader("📊 لوحة التحليلات الذكية وكفاءة المستشفى")
    st.write("بيانات وتحليلات لحظية لدعم اتخاذ القرار وتوزيع الكوادر الطبية:")
    
    chart_data = pd.DataFrame([
        {"العيادة": d["name"], "المرضى": d["queue"], "الحالات الحرجة": d["critical_count"]}
        for d in st.session_state.clinics.values()
    ]).set_index("العيادة")
    
    st.bar_chart(chart_data)
    
    st.write("### 📜 السجل اللحظي لتوجيه المرضى اليوم:")
    st.table(pd.DataFrame(st.session_state.patients_history))

# 8. التحديث التلقائي لمحاكاة المزامنة الحية (Auto Refresh)
time.sleep(5)
st.rerun()
