import cv2
import os
import pickle
import mediapipe as mp

# === Rutas ===
rostros_dir = r"C:\9 CICLO\Desarrollo de Soluciones IOT\Proyecto\pyyt\rostros"
pickle_path = "known_faces.pkl"

os.makedirs(rostros_dir, exist_ok=True)

known_face_bboxes = []
known_face_names = []
known_face_data = {}
last_mod_time = 0

def load_known_faces():
    global known_face_bboxes, known_face_names, known_face_data, last_mod_time

    if os.path.exists(pickle_path):
        mod_time = os.path.getmtime(pickle_path)
        if mod_time != last_mod_time:
            try:
                with open(pickle_path, "rb") as f:
                    known_face_bboxes, known_face_names, known_face_data = pickle.load(f)
                last_mod_time = mod_time
                print("🔄 Rostros recargados desde pickle.")
            except:
                print("⚠ Error al cargar pickle. Se limpia.")
                known_face_bboxes.clear()
                known_face_names.clear()
                known_face_data.clear()
    else:
        known_face_bboxes.clear()
        known_face_names.clear()
        known_face_data.clear()
        last_mod_time = 0
        print("⚠ Pickle no existe. No hay rostros.")

    # Verificar si las imágenes asociadas aún existen
    nombres_a_remover = []
    for name in known_face_names:
        image_path = os.path.join(rostros_dir, f"{name}.jpg")
        if not os.path.exists(image_path):
            print(f"❌ Imagen de {name} fue eliminada. Se remueve del sistema.")
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

def register_face(image, name, age):
    global known_face_bboxes, known_face_names, known_face_data

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    with mp.solutions.face_detection.FaceDetection(min_detection_confidence=0.5) as face_detection:
        results = face_detection.process(rgb_image)

    if not results.detections:
        print("❌ No se detectó rostro en la imagen capturada.")
        return

    detection = results.detections[0]
    bbox = detection.location_data.relative_bounding_box
    known_face_bboxes.append((bbox.xmin, bbox.ymin, bbox.width, bbox.height))
    known_face_names.append(name)
    known_face_data[name] = {"age": age}

    with open(pickle_path, "wb") as f:
        pickle.dump((known_face_bboxes, known_face_names, known_face_data), f)

    print(f"✅ {name} registrado y guardado.")

# === Iniciar cámara ===
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Cámara no disponible.")
    exit()

mp_face_detection = mp.solutions.face_detection

with mp_face_detection.FaceDetection(min_detection_confidence=0.5) as face_detection:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        clean_frame = frame.copy()  # <- Guardamos una versión sin dibujos
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

        for (x1, y1, x2, y2), name in zip(face_locations, face_names):
            color = (0, 255, 0) if name != "Desconocido" else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.rectangle(frame, (x1, y2), (x2, y2 + 30), color, cv2.FILLED)
            cv2.putText(frame, name, (x1 + 6, y2 + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            if name in known_face_data:
                age = known_face_data[name].get("age", "N/A")
                cv2.putText(frame, f"Edad: {age}", (x1 + 6, y2 + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("Reconocimiento Facial", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        elif key == ord('5'):
            print("👤 Registrando nueva persona:")
            name = input("Nombre: ")
            age = input("Edad: ")
            filename = os.path.join(rostros_dir, f"{name}.jpg")
            cv2.imwrite(filename, clean_frame)  # <- Guardamos imagen limpia
            print(f"📸 Imagen guardada sin marcadores en: {filename}")
            register_face(clean_frame, name, age)

cap.release()
cv2.destroyAllWindows()
