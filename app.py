import os
import cv2
import numpy as np
from flask import Flask, render_template, request, send_from_directory, flash, redirect, url_for
from rembg import new_session, remove
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "trhacknon_secret_key"  # Pour flash messages

UPLOAD_FOLDER = 'static/output'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Session rembg optimisée
rembg_session = new_session("u2net")

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_file = request.files.get("video")
        background_file = request.files.get("background")

        if not video_file or not background_file:
            flash("Merci de fournir une vidéo ET une image de fond.")
            return redirect(request.url)

        if not (allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS) and
                allowed_file(background_file.filename, ALLOWED_IMAGE_EXTENSIONS)):
            flash("Format vidéo ou image non supporté.")
            return redirect(request.url)

        video_filename = secure_filename(video_file.filename)
        bg_filename = secure_filename(background_file.filename)

        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        bg_path = os.path.join(app.config['UPLOAD_FOLDER'], bg_filename)

        video_file.save(video_path)
        background_file.save(bg_path)

        output_filename = f"output_{os.path.splitext(video_filename)[0]}.mp4"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        try:
            process_video(video_path, bg_path, output_path)
            flash("Traitement terminé avec succès !")
            return render_template("index.html", download_url=url_for('download_file', filename=output_filename))
        except Exception as e:
            flash(f"Erreur durant le traitement : {e}")
            return redirect(request.url)

    return render_template("index.html", download_url=None)


import subprocess
import tempfile

def process_video(input_video, background_img, output_path):
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        raise Exception("Impossible d'ouvrir la vidéo.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps > 120:
        fps = 25  # fallback fps

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # fichier temporaire pour vidéo sans audio
    tmp_video_fd, tmp_video_path = tempfile.mkstemp(suffix=".mp4")
    os.close(tmp_video_fd)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(tmp_video_path, fourcc, fps, (width, height))

    background = cv2.imread(background_img)
    if background is None:
        raise Exception("Impossible de lire l'image de fond.")
    background = cv2.resize(background, (width, height))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        print(f"[INFO] Traitement frame {frame_idx}")

        rgba = remove(frame, session=rembg_session)
        alpha = rgba[:, :, 3] / 255.0
        fg = rgba[:, :, :3]

        composite = (fg * alpha[..., None] + background * (1 - alpha[..., None])).astype(np.uint8)
        out.write(composite)

    cap.release()
    out.release()

    # Extraction audio de la vidéo originale
    tmp_audio_fd, tmp_audio_path = tempfile.mkstemp(suffix=".aac")
    os.close(tmp_audio_fd)
    extract_audio_cmd = [
        "ffmpeg", "-y", "-i", input_video,
        "-vn", "-acodec", "copy", tmp_audio_path
    ]
    subprocess.run(extract_audio_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # Fusion de la vidéo traitée + audio original
    merge_cmd = [
        "ffmpeg", "-y",
        "-i", tmp_video_path,
        "-i", tmp_audio_path,
        "-c:v", "copy",
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(merge_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # Suppression fichiers temporaires
    os.remove(tmp_video_path)
    os.remove(tmp_audio_path)

@app.route('/static/output/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
