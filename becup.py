import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import cv2
from ultralytics import YOLO
import threading

video_finished = threading.Event()


def play_video(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    delay = int(700 / fps)

    cv2.namedWindow("Rezultats", cv2.WINDOW_NORMAL)

    while not video_finished.is_set():
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        window_width = cv2.getWindowImageRect("Rezultats")[2]
        window_height = cv2.getWindowImageRect("Rezultats")[3]
        resized_frame = cv2.resize(frame, (window_width, window_height))
        cv2.imshow("Rezultats", resized_frame)
        if cv2.waitKey(delay) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


root = tk.Tk()
root.withdraw()

initial_dir = "C:\\Users\\dyomk\\PycharmProjects\\YoloV8_BakD\\Video"
video_path = filedialog.askopenfilename(title="Izvēlieties video failu", initialdir=initial_dir)

if not video_path:
    messagebox.showerror("Kļūda", "Video fails nav izvēlēts.")
    root.destroy()
    exit()

video_confirmation = messagebox.askyesno("Apstiprināšana", f"Vai vēlaties apstrādāt šo video: {video_path}?")

if not video_confirmation:
    root.destroy()
    exit()

# Получение FPS из выбранного видео файла
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    messagebox.showerror("Kļūda", "Nevar atvērt video failu.")
    root.destroy()
    exit()

feim_per_sek = cap.get(cv2.CAP_PROP_FPS)  # получение FPS
ret, frame = cap.read()
H, W, _ = frame.shape
cap.release()

base_name = os.path.basename(video_path)
file_name, file_extension = os.path.splitext(base_name)
detected_video_directory = "C:\\Users\\dyomk\\PycharmProjects\\YoloV8_BakD\\detectedVideo"
new_file_name = f"{file_name}_detected{file_extension}"
video_path_out = os.path.join(detected_video_directory, new_file_name)

if not os.path.exists(detected_video_directory):
    os.makedirs(detected_video_directory)

out = cv2.VideoWriter(video_path_out, cv2.VideoWriter_fourcc(*'MP4V'), int(feim_per_sek), (W, H))
model_path = os.path.join('.', 'runs', 'detect', 'train', 'weights', 'best.pt')
model = YOLO(model_path)

threshold = 0.6
frame_counter = total_lines = total_poles = 0
object_last_seen = {0: 0, 1: 0}
gap_frames = 3

cap = cv2.VideoCapture(video_path)
while ret:
    frame_counter += 1
    print(f"Processing frame {frame_counter}...")

    results = model(frame)[0]

    for result in results.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = result
        if score > threshold:
            if frame_counter - object_last_seen[int(class_id)] > gap_frames or object_last_seen[int(class_id)] == 0:
                if class_id == 0:
                    total_lines += 1
                elif class_id == 1:
                    total_poles += 1
            object_last_seen[int(class_id)] = frame_counter

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.putText(frame, f"{results.names[int(class_id)]}: {score:.2f}", (int(x1), int(y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    out.write(frame)
    ret, frame = cap.read()

cap.release()
out.release()

line = messagebox.askyesno("Objektu izvēle", "Vai vēlaties aprēķināt ātrumu, izmantojot līnijas?")
stab = messagebox.askyesno("Objektu izvēle", "Vai vēlaties aprēķināt ātrumu, izmantojot stabus?")

if line:
    line_len = simpledialog.askfloat("Ievade", "Ievediet līnijas garumu:")
    line_interval = simpledialog.askfloat("Ievade", "Ievadiet attālumu starp līnijām:")
else:
    line_len = line_interval = 0

time = frame_counter / feim_per_sek if feim_per_sek > 0 else 0
if line and stab:
    line_dist = total_lines * (line_len + line_interval) if total_lines > 0 else 0
else:
    line_dist = (total_lines * (line_len + line_interval) - line_interval) if total_lines > 0 else 0
stab_dist = (total_poles - 1) * 100 if total_poles > 0 else 0

line_sp = line_dist / time if line_dist > 0 else 0
stab_sp = stab_dist / time if stab_dist > 0 else 0
line_sp_km = line_sp * 3.6
stab_sp_km = stab_sp * 3.6
if line and stab:
    average_sp = (line_sp_km + stab_sp_km) / 2
elif line:
    average_sp = line_sp_km
else:
    average_sp = stab_sp_km

if line and stab:
    sp_error = (abs(line_sp_km - stab_sp_km) / 2)
else:
    sp_error = 0

average_sp_er = average_sp - sp_error

result_text = (f"Freimu skaits: {frame_counter}"
               f"\nLaiks sekundēs: {time}\n"
               f"Kadri sekunde: {feim_per_sek}\n")
if line:
    result_text += (f"Detektēto līniju skaits: {total_lines}"
                    f"\nAttālums pa līnijām (m): {line_dist}"
                    f"\nĀtrums pa līnijām (km/h): {round(line_sp_km, 3)}\n")
if stab:
    result_text += (f"Detektēto stabu skaits: {total_poles}"
                    f"\nAttālums pa stabiem (m): {stab_dist}"
                    f"\nĀtrums pa stabiem (km/h): {round(stab_sp_km, 3)}\n")
if line and stab:
    result_text += f"Ātruma noteikšanas iespējamā neprecizitāte (km/h): {round(sp_error, 3)}\n"
else:
    result_text += "Ātruma noteikšanas neprecizitāti nevar noteikt izmantojot tikai vienu parametru.\n"

result_text += f"Vidējais ātrums neiekļāujot neprecizitāti (km/h): {round(average_sp, 3)}\n"

if line and stab:
    result_text += f"Vidējais ātrums iekļāujot neprecizitāti (km/h): {round(average_sp_er, 3)}\n"

# Запуск видео в паралельном потоке
video_thread = threading.Thread(target=play_video, args=(video_path_out,))
video_thread.start()

messagebox.showinfo("Rezultāti", result_text)

# Установка флага для завершения видео
video_finished.set()

# Ожидание пока видео завершится
video_thread.join()

# Запись результатов в txt
results_directory = os.path.join(detected_video_directory, "detected_INFO")
if not os.path.exists(results_directory):
    os.makedirs(results_directory)

results_file_path = os.path.join(results_directory, f"{file_name}_results.txt")

with open(results_file_path, "w", encoding='utf-8') as file:
    file.write(result_text)
messagebox.showinfo("Information", f"Rezultāti ir saglabāti: {results_file_path}")
