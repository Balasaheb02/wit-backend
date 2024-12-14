from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from moviepy.editor import *
from rembg import remove
from PIL import Image, ImageColor
import firebase_admin
from firebase_admin import credentials, initialize_app, storage
import os

# import io

app = Flask(__name__)
CORS(app)
# Initialize Firebase
cred = credentials.Certificate("./hoknow-prod-firebase-adminsdk-gq6wx-70918305c8.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'hoknow-prod.appspot.com'})

# Set allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_image():
    # Get the uploaded image file
    image = request.files.get('image')
    color = request.form.get('color', '255 255 255')  # Default color is white if not specified
    duration = int(request.form.get('duration', 3))  # Default duration to 3 seconds if not specified

    if not image:
        return jsonify({'error': 'No file uploaded'}), 400

    # Save the uploaded image
    image_path = 'uploaded_image.png'
    image.save(image_path)

    # Remove background from the uploaded image
    no_bg_image_path = 'no_bg_image.png'
    remove_background(image_path, no_bg_image_path)

    # Generate the animated GIF based on parameters
    output_path = 'output.gif'
    create_gif(no_bg_image_path, color, duration, output_path)
    bucket = storage.bucket()
    blob = bucket.blob(request.form.get('id'))
    blob.upload_from_filename('./output.gif')

    # Make the blob publicly accessible
    blob.make_public()

    image_url = blob.public_url

    return jsonify({'message': 'Image uploaded successfully', 'url': image_url}), 200



def remove_background(input_path, output_path):
    """Removes the background from an image."""
    with open(input_path, 'rb') as inp_file:
        input_data = inp_file.read()
        output_data = remove(input_data)
    with open(output_path, 'wb') as out_file:
        out_file.write(output_data)


def create_gif(image_path, bg_color, duration, output_path):

    image_clip = ImageClip(image_path)
    total_duration = duration
    if bg_color.startswith('#'):
        bg_color = ImageColor.getrgb(bg_color)
    background_clip = ColorClip(size=image_clip.size, color=bg_color, duration=total_duration)
    image_width, image_height = (700, 700)

    def slide_in(t):
        return -image_width + (image_width + 100) * (t / 2), 'center'

    def slide_out(t):
        return (image_width + 100) * ((t - 2) / 3), 'center'

    image_clip_slide_in = image_clip.set_duration(2).set_position(slide_in)
    image_clip_slide_out = image_clip.set_start(2).set_duration(3).set_position(slide_out)
    composite_clip = CompositeVideoClip([background_clip, image_clip_slide_in, image_clip_slide_out])
    composite_clip.write_gif(output_path, fps=10)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8080)), debug=True)
