import cv2


def get_fps(video_path):
    # Открываем видеофайл
    video = cv2.VideoCapture(video_path)

    # Проверяем, открылось ли видео
    if not video.isOpened():
        print("Error: Could not open video.")
        return None

    # Получаем FPS видео
    fps = video.get(cv2.CAP_PROP_FPS)
    video.release()  # Освобождаем ресурсы
    return fps


# Пример использования функции
video_file_path = 'C:\\Users\\dyomk\\PycharmProjects\\YoloV8_BakD\\Video\\sp70_7omai_200m.mp4'
print(f"The FPS of the video is: {get_fps(video_file_path)}")