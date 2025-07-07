import cv2
import os
import pickle
import mediapipe as mp
import sqlite3
import requests
import time

# === Rutas ===
rostros_dir = os.path.join(os.getcwd(), "rostros")
pickle_path = "known_faces.pkl"
db_path = "facelock.db"
EDGE_API_URL = "http://localhost:5000/api/notify-access"

os.makedirs(rostros_dir, exist_ok=True)

known_face_bboxes = []
known_face_names = []
known_face_data = {}
last_mod_time = 0

# Para evitar notificaciones excesivas por usuario reconocido
last_notification_time = {}
COOLDOWN_SECONDS = 30

def load_known_faces():
    global known_face_bboxes, known_face_names, known_face_data, last_mod_time

    if os.path.exists(pickle_path):
        mod_time = os.path.getmtime(pickle_path)
        if mod_time != last_mod_time:
            try:
                with open(pickle_path, "rb") as f:
                    known_face_bboxes, known_face_names, known_face_data = pickle.load(f)
                last_mod_time = mod_time
                print(" Rostros recargados desde pickle.")
            except:
                print(" Error al cargar pickle. Se limpia.")
                known_face_bboxes.clear()
                known_face_names.clear()
                known_face_data.clear()
    else:
        known_face_bboxes.clear()
        known_face_names.clear()
        known_face_data.clear()
        last_mod_time = 0
        print("Pickle no existe. No hay rostros.")

    # Verificar si las imágenes asociadas aún existen
    nombres_a_remover = []
    for name in known_face_names:
        image_path = os.path.join(rostros_dir, f"{name}.jpg")
        if not os.path.exists(image_path):
            print(f"Imagen de {name} fue eliminada. Se remueve del sistema.")
            nombres_a_remover.append(name)

    for name in nombres_a_remover:
        index = known_face_names.index(name)
        known_face_names.pop(index)
        known_face_bboxes.pop(index)
        known_face_data.pop(name, None)

    if nombres_a_remover:
        with open(pickle_path, "wb") as f:
            pickle.dump((known_face_bboxes, known_face_names, known_face_data), f)
        last_mod_time = os.path.getmtime(pickle_path)

def register_face(image, name, age, pin):
    global known_face_bboxes, known_face_names, known_face_data

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    with mp.solutions.face_detection.FaceDetection(min_detection_confidence=0.5) as face_detection:
        results = face_detection.process(rgb_image)

    if not results.detections:
        print("No se detectó rostro en la imagen capturada.")
        return

    detection = results.detections[0]
    bbox = detection.location_data.relative_bounding_box
    known_face_bboxes.append((bbox.xmin, bbox.ymin, bbox.width, bbox.height))
    known_face_names.append(name)
    known_face_data[name] = {"age": age, "pin": pin}

    # Guardar en pickle
    with open(pickle_path, "wb") as f:
        pickle.dump((known_face_bboxes, known_face_names, known_face_data), f)

    # Guardar en SQLite 
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (name, age, pin, is_active)
        VALUES (?, ?, ?, 1)
    ''', (name, age, pin))
    conn.commit()
    conn.close()

    print(f"{name} registrado y guardado.")

def notify_access(user_name, method, success=True, confidence=1.0):
    try:
        data = {
            "user_name": user_name,
            "method": method,
            "success": success,
            "confidence": confidence
        }
        response = requests.post(EDGE_API_URL, json=data, timeout=2)
        if response.status_code == 200:
            print(f"📡 Notificación enviada: {user_name} - {method}")
        else:
            print(f"⚠ Error notificando acceso: {response.status_code}")
    except Exception as e:
        print(f"⚠ Excepción notificando acceso: {e}")

def validate_pin(pin_input):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM users WHERE pin = ? AND is_active = 1', (pin_input,))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def activate_pin_mode():
    print("\n" + "="*50)
    print(" MODO PIN ACTIVADO")
    print("Ingrese su PIN para acceder (o presione ENTER para cancelar):")
    print("="*50)

    max_pin_attempts = 3
    pin_attempts = 0

    while pin_attempts < max_pin_attempts:
        pin_input = input("PIN (4-6 dígitos): ").strip()
        if not pin_input:
            print(" Cancelado. Regresando...")
            return False
        user_name = validate_pin(pin_input)
        if user_name:
            print(f" PIN correcto. Acceso autorizado para {user_name}")
            notify_access(user_name, "pin_access", True, 1.0)
            return True
        else:
            pin_attempts += 1
            print(f" PIN incorrecto ({pin_attempts}/{max_pin_attempts})")

    print(" Máximo de intentos alcanzado o cancelado. Acceso denegado.")
    notify_access("UNKNOWN", "pin_failed_attempts", False, 0.0)
    return False

# === Iniciar cámara ===
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print(" Cámara no disponible.")
    exit()

mp_face_detection = mp.solutions.face_detection

print("\nPresiona:\n 1 - Nuevo registro\n 2 - Ingresar PIN\n ESC - Salir\n")

with mp_face_detection.FaceDetection(min_detection_confidence=0.5) as face_detection:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        clean_frame = frame.copy()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        load_known_faces()  # Refrescar rostros

        results = face_detection.process(rgb_frame)
        face_locations = []
        face_names = []

        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                ih, iw, _ = frame.shape
                x1 = int(bbox.xmin * iw)
                y1 = int(bbox.ymin * ih)
                x2 = int((bbox.xmin + bbox.width) * iw)
                y2 = int((bbox.ymin + bbox.height) * ih)
                face_locations.append((x1, y1, x2, y2))

                name = "Desconocido"
                for (kx, ky, kw, kh), known_name in zip(known_face_bboxes, known_face_names):
                    if abs(kx - bbox.xmin) < 0.05 and abs(ky - bbox.ymin) < 0.05:
                        name = known_name
                        break
                face_names.append(name)

        # Visualización y lógica de acceso
        for (x1, y1, x2, y2), name in zip(face_locations, face_names):
            color = (0, 255, 0) if name != "Desconocido" else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.rectangle(frame, (x1, y2), (x2, y2 + 30), color, cv2.FILLED)
            cv2.putText(frame, name, (x1 + 6, y2 + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            if name in known_face_data:
                age = known_face_data[name].get("age", "N/A")
                cv2.putText(frame, f"Edad: {age}", (x1 + 6, y2 + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # Notificación automática al reconocer rostro conocido, con cooldown
            if name != "Desconocido":
                current_time = time.time()
                if (
                    name not in last_notification_time or
                    (current_time - last_notification_time[name]) > COOLDOWN_SECONDS
                ):
                    notify_access(name, "facial_recognition", True, 0.99)
                    last_notification_time[name] = current_time

        # Si hay rostro pero no reconocido, mostrar "Desconocido"
        if face_locations and all(n == "Desconocido" for n in face_names):
            cv2.putText(frame, "Usuario desconocido", (40, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        # Instrucciones siempre visibles
        instru = "Presiona 1: Nuevo registro  |  2: Ingresar PIN  |  ESC: Salir"
        cv2.putText(frame, instru, (20, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("Reconocimiento Facial", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            break
        elif key == ord('1'):
            print("\n--- Nuevo registro ---")
            name = input("Nombre: ")
            age = input("Edad: ")
            pin = input("PIN (4-6 dígitos): ")
            filename = os.path.join(rostros_dir, f"{name}.jpg")
            cv2.imwrite(filename, clean_frame)
            print(f"📸 Imagen guardada sin marcadores en: {filename}")
            register_face(clean_frame, name, age, pin)
        elif key == ord('2'):
            activate_pin_mode()

cap.release()
cv2.destroyAllWindows()