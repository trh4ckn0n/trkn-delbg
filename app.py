import os
import cv2
import numpy as np
from flask import Flask, render_template, request, send_from_directory, flash, redirect, url_for
from rembg import new_session, remove
from werkzeug.utils import secure_filename
import tempfile
import subprocess

app = Flask(__name__)
app.secret_key = "trhacknon_secret_key"

UPLOAD_FOLDER = 'static/output'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}

MODELS = {
    "u2net": "Standard, bon pour tout usage",
    "u2netp": "Plus léger, moins précis",
    "u2net_human_seg": "Optimisé pour personnes (meilleure précision humain)",
    "u2net_cloth_seg": "Optimisé pour vêtements",
}

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

def preprocess_frame(frame):
    # Convertir en RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # CLAHE pour améliorer contraste local
    lab = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl,a,b))
    frame_enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
    return frame_enhanced

def postprocess_alpha(alpha_channel):
    alpha = alpha_channel.astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel)
    alpha = cv2.GaussianBlur(alpha, (7,7), 0)
    alpha = alpha.astype(np.float32) / 255.0
    return alpha

def process_video(input_video, background_img, output_path, model_name):
    rembg_session = new_session(model_name)

    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        raise Exception("Impossible d'ouvrir la vidéo.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps > 120:
        fps = 25

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

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

        frame_enhanced = preprocess_frame(frame)
        rgba = remove(frame_enhanced, session=rembg_session)

        alpha = postprocess_alpha(rgba[:, :, 3])
        fg = rgba[:, :, :3]

        composite = (fg * alpha[..., None] + background * (1 - alpha[..., None])).astype(np.uint8)
        out.write(composite)

    cap.release()
    out.release()

    # Extraction audio
    tmp_audio_fd, tmp_audio_path = tempfile.mkstemp(suffix=".aac")
    os.close(tmp_audio_fd)
    subprocess.run([
        "ffmpeg", "-y", "-i", input_video,
        "-vn", "-acodec", "copy", tmp_audio_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # Fusion vidéo + audio
    subprocess.run([
        "ffmpeg", "-y",
        "-i", tmp_video_path,
        "-i", tmp_audio_path,
        "-c:v", "copy",
        "-c:a", "copy",
        output_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    os.remove(tmp_video_path)
    os.remove(tmp_audio_path)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_file = request.files.get("video")
        background_file = request.files.get("background")
        model_name = request.form.get("model")

        if not video_file or not background_file:
            flash("Merci de fournir une vidéo ET une image de fond.")
            return redirect(request.url)

        if model_name not in MODELS.keys():
            flash("Modèle sélectionné invalide.")
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
            process_video(video_path, bg_path, output_path, model_name)
            flash("Traitement terminé avec succès !")
            return render_template("index.html", download_url=url_for('download_file', filename=output_filename), models=MODELS, selected_model=model_name)
        except Exception as e:
            flash(f"Erreur durant le traitement : {e}")
            return redirect(request.url)

    return render_template("index.html", download_url=None, models=MODELS, selected_model="u2net")

@app.route('/static/output/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
