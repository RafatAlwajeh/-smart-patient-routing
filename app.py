import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# 1. تهيئة الصفحة
st.set_page_config(page_title="نظام التوجيه الذكي وتدفق المرضى", layout="wide", page_icon="🚑")

# دعم RTL وتنسيق البطاقة للوضع الداكن والديناميكي
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
            color: #900C3F !important;
        }
        .patient-card {
            border: 2px solid #1E88E5;
            border-radius: 12px;
            padding: 25px;
            background-color: #1e2640;
            color: #ffffff !important;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }
        .patient-card h3 {
            color: #64B5F6 !important;
            margin-bottom: 15px;
            text-align: center !important;
        }
        .patient-card p {
            color: #e0e0e0 !important;
            font-size: 1.1rem;
            text-align: center !important;
            margin: 8px 0;
        }
    </style>
''', unsafe_allow_html=True)

# 2. البيانات اللحظية في session_state
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

if "authenticated_doctor" not in st.session_state:
    st.session_state.authenticated_doctor = False

# دالة توليد صورة بطاقة المريض للتحميل
def generate_ticket_image(name, clinic, triage, wait):
    img = Image.new('RGB', (600, 350), color='#1e2640')
    d = ImageDraw.Draw(img)
    
    # إطار خارجي
    d.rectangle([10, 10, 590, 340], outline='#1E88E5', width=3)
    
    # كتابة النصوص داخل الصورة
    d.text((300, 40), "بطاقة تذكرة المريض الرقمية", fill='#64B5F6', anchor="mm")
    d.text((300, 110), f"اسم المريض: {name}", fill='#ffffff', anchor="mm")
    d.text((300, 170), f"العيادة الموجه إليها: {clinic}", fill='#ffffff', anchor="mm")
    d.text((300, 230), f"مستوى الفرز الطبي: {triage}", fill='#ffffff', anchor="mm")
    d.text((300, 290), f"زمن الانتظار المتبقي: {wait} دقيقة", fill='#4CAF50', anchor="mm")
    
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# قراءة معاملات الرابط عند مسح QR Code من الجوال
query_params = st.query_params

if "ticket_patient" in query_params:
    p_name = query_params["ticket_patient"]
    p_clinic_name = query_params.get("clinic", "غير محدد")
    p_triage = query_params.get("triage", "عادي")
    
    # حساب الانتظار اللحظي المتبقي
    current_wait = 0
    for ip, d in st.session_state.clinics.items():
        if d["name"] == p_clinic_name:
            current_wait = d["queue"] * d["avg_time"]
            break

    st.markdown("<h2 style='text-align: center;'>🎫 بطاقة تذكرة المريض الرقمية</h2>", unsafe_allow_html=True)
    
    # عرض بطاقة المريض
    st.markdown(f'''
        <div class="patient-card">
            <h3>👤 اسم المريض: {p_name}</h3>
            <p><strong>🏥 العيادة الموجه إليها:</strong> {p_clinic_name}</p>
            <p><strong>🚨 مستوى الفرز الطبي:</strong> {p_triage}</p>
            <p><strong>⏱️ زمن الانتظار المتبقي الآن:</strong> {current_wait} دقيقة</p>
        </div>
    ''', unsafe_allow_html=True)
    
    # زر تنزيل صورة البطاقة من صفحة المريض
    card_img_bytes = generate_ticket_image(p_name, p_clinic_name, p_triage, current_wait)
    
    c_down, _ = st.columns([1, 1])
    with c_down:
        st.download_button(
            label="📥 تنزيل بطاقة التذكرة (صورة PNG)",
            data=card_img_bytes,
            file_name=f"Patient_Ticket_{p_name}.png",
            mime="image/png",
            use_container_width=True
        )
    
    st.info("💡 قم بتحديث الصفحة لتتبع انخفاض زمن انتظارك عند دخول الحالات.")
    st.stop()

# 3. الهيدر والتنقل
st.title("🚑 نظام التوجيه الذكي وتدفق المرضى (Smart Patient Routing)")
st.caption("نظام الفرز الطبي التلقائي، التنبؤ بالازدحام، والمزامنة اللحظية")
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

if nav4.button("📊 التحليلات والتنبؤ", use_container_width=True):
    st.session_state.current_page = "التحليلات"
    st.rerun()

st.write("---")
mode = st.session_state.current_page

# 4. الشاشة الأولى: الفرز والاستقبال
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
    
    def get_best_clinic(specialty, triage):
        best_ip, min_wait = None, float('inf')
        for ip, data in st.session_state.clinics.items():
            if data["specialty"] == specialty and data["status"] != "🔴 أحمر":
                penalty = 15 if data["status"] == "🟡 أصفر" else 0
                wait = (data["queue"] * 2) if "🔴" in triage else (data["queue"] * data["avg_time"]) + penalty
                if wait < min_wait:
                    min_wait, best_ip = wait, ip
        return best_ip, min_wait

    if st.button("🚀 توجيه واستخراج تذكرة المريض", type="primary", use_container_width=True):
        best_ip, wait_time = get_best_clinic(spec, triage_level)
        if best_ip:
            clinic_name = st.session_state.clinics[best_ip]['name']
            st.session_state.clinics[best_ip]["queue"] += 1
            if "🔴" in triage_level:
                st.session_state.clinics[best_ip]["critical_count"] += 1
                st.error(f"🚨 **توجيه طوارئ عاجل:** تم تحويل الحالة الحرجة إلى **{clinic_name}** وتنبيه الطبيب فوراً!")
            else:
                st.success(f"💡 **التوصية الذكية:** تحويل المريض إلى **{clinic_name}** | ⏱️ الانتظار المتوقع: **{wait_time} دقيقة**")
            
            st.session_state.patients_history.append({
                "id": patient_name, "triage": triage_level, "clinic": clinic_name, "wait": wait_time
            })
            
            # رابط التذكرة الذي يفتحه الـ QR
            base_url = "https://smart-patient-routing.streamlit.app/"
            ticket_url = f"{base_url}?ticket_patient={patient_name}&clinic={clinic_name}&triage={triage_level}"
            
            # إنتاج الـ QR Code
            qr = qrcode.make(ticket_url)
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()
            
            col_qr, col_info = st.columns([1, 2])
            with col_qr:
                st.image(img_bytes, caption="امسح الرمز للتذكرة الرقمية 📱", width=180)
                st.download_button(
                    label="📥 تنزيل رمز QR",
                    data=img_bytes,
                    file_name=f"QR_{patient_name}.png",
                    mime="image/png",
                    use_container_width=True
                )
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

# 5. الشاشة الثانية: مكتب الطبيب
elif mode == "الطبيب":
    if not st.session_state.authenticated_doctor:
        st.subheader("🔒 دخول الكادر الطبي")
        pwd = st.text_input("أدخل كلمة مرور الطبيب للوصول للوحة التحكم:", type="password")
        if st.button("تسجيل الدخول"):
            if pwd == "1234" or pwd == "admin":
                st.session_state.authenticated_doctor = True
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة!")
    else:
        if st.button("🚪 تسجيل الخروج من لوحة الطبيب"):
            st.session_state.authenticated_doctor = False
            st.rerun()
            
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

# 6. الشاشة الثالثة: شاشة الانتظار
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

# 7. الشاشة الرابعة: التحليلات والتنبؤ الذكي
elif mode == "التحليلات":
    st.subheader("📊 لوحة التحليلات والتنبؤ الذكي باقتظاط العيادات")
    
    total_waiting = sum(d["queue"] for d in st.session_state.clinics.values())
    if total_waiting > 10:
        st.warning(f"⚠️ **تنبؤ الذكاء الاصطناعي:** يُتوقع ذروة ازدحام خلال 45 دقيقة القادمة ({total_waiting} حالة منتظرة). يُوصى بفتح عيادات إضافية.")
    else:
        st.info("ℹ️ **حالة التدفق:** معدل الانتظار ضمن النطاق الطبيعي والأداء استباقي.")

    chart_data = pd.DataFrame([
        {"العيادة": d["name"], "المرضى": d["queue"], "الحالات الحرجة": d["critical_count"]}
        for d in st.session_state.clinics.values()
    ]).set_index("العيادة")
    
    st.bar_chart(chart_data)
    
    st.write("### 📜 السجل اللحظي لتوجيه المرضى اليوم:")
    st.table(pd.DataFrame(st.session_state.patients_history))
