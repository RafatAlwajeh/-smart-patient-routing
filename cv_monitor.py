import cv2
import json
import os
import time
from ultralytics import YOLO

DATA_FILE = "clinics_data.json"
TARGET_CLINIC_IP = "192.168.1.101" # العيادة المستهدفة للكاميرا

# تحميل نموذج YOLOv8
model = YOLO('yolov8n.pt')

def update_camera_data(clinic_ip, count):
    if not os.path.exists(DATA_FILE):
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if clinic_ip in data:
            data[clinic_ip]["camera_count"] = count
            
            # تحديث الحالة تلقائياً بناءً على قراءة الكاميرا
            if count >= 8:
                data[clinic_ip]["status"] = "🔴 أحمر"
            elif count >= 4:
                data[clinic_ip]["status"] = "🟡 أصفر"
            else:
                data[clinic_ip]["status"] = "🟢 أخضر"

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
    except Exception as e:
        print(f"خطأ أثناء تحديث الملف: {e}")

cap = cv2.VideoCapture(0)
print("🎥 تم تشغيل نظام الرؤية الحاسوبية لمعاينة الازدحام...")

last_update = time.time()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # الكشف عن الأشخاص فقط (Class 0 = Person)
    results = model(frame, classes=[0], verbose=False)
    people_count = len(results[0].boxes)

    # تحديث كل ثانية
    if time.time() - last_update > 1.0:
        update_camera_data(TARGET_CLINIC_IP, people_count)
        last_update = time.time()

    annotated_frame = results[0].plot()
    cv2.putText(annotated_frame, f"People Count: {people_count}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Smart Patient Routing - Live CV Density Detection", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
