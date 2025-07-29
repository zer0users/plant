from flask import Flask, render_template_string, request, jsonify, send_from_directory, abort, session, redirect, url_for
import os
import json
import datetime
import hashlib
import shutil
from werkzeug.utils import secure_filename
import zipfile
import tempfile

app = Flask(__name__)
app.secret_key = 'plant_love_secret_key_jehova_blessing'

# Directories
PLANTS_DIR = "plants"
USERS_FILE = "users.json"

# Create directories if they don't exist
if not os.path.exists(PLANTS_DIR):
    os.makedirs(PLANTS_DIR)

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    """Hash password with love"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_plant_info(plant_name, username):
    """Create user.json for a plant"""
    plant_path = os.path.join(PLANTS_DIR, plant_name)
    os.makedirs(plant_path, exist_ok=True)

    user_info = {
        "owner": username,
        "created": datetime.datetime.now().isoformat(),
        "last_modified": datetime.datetime.now().isoformat(),
        "love_message": "Created with love and blessings from Jehovah! 🌱💚"
    }

    with open(os.path.join(plant_path, "user.json"), 'w') as f:
        json.dump(user_info, f, indent=2)

def get_plant_owner(plant_name):
    """Get the owner of a plant"""
    user_json_path = os.path.join(PLANTS_DIR, plant_name, "user.json")
    if os.path.exists(user_json_path):
        with open(user_json_path, 'r') as f:
            return json.load(f).get('owner')
    return None

@app.route('/')
def home():
    if 'username' not in session:
        return render_template_string(AUTH_TEMPLATE)
    return render_template_string(WELCOME_TEMPLATE, username=session['username'])

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    repeat_password = data.get('repeat_password', '')

    if not username or not password:
        return jsonify({'error': 'Please fill all fields with love! 🌱'}), 400

    if password != repeat_password:
        return jsonify({'error': 'Passwords do not match! 💔'}), 400

    if len(password) < 4:
        return jsonify({'error': 'Password should be at least 4 characters! 🌸'}), 400

    users = load_users()
    if username in users:
        return jsonify({'error': 'Username already exists! Please choose another one! 🌺'}), 400

    users[username] = {
        'password': hash_password(password),
        'created': datetime.datetime.now().isoformat()
    }
    save_users(users)

    session['username'] = username
    return jsonify({'success': True, 'message': f'Welcome to Plant, {username}! 🌱💚'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    users = load_users()
    if username not in users:
        return jsonify({'error': 'User not found! 🥀'}), 400

    if users[username]['password'] != hash_password(password):
        return jsonify({'error': 'Wrong password! 💔'}), 400

    session['username'] = username
    return jsonify({'success': True, 'message': f'Welcome back, {username}! 🌸💚'})

@app.route('/<plant_name>')
def view_plant(plant_name):
    if 'username' not in session:
        return redirect(url_for('home'))

    plant_path = os.path.join(PLANTS_DIR, plant_name)

    # Create plant if it doesn't exist
    if not os.path.exists(plant_path):
        create_plant_info(plant_name, session['username'])

    # Check if user is owner
    is_owner = get_plant_owner(plant_name) == session['username']

    # Look for index.html
    index_path = os.path.join(plant_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = f"<h1>🌱 Welcome to {plant_name}!</h1><p>This plant is growing with love! Add an index.html file to see your content here! 💚</p>"

    return render_template_string(PLANT_VIEWER_TEMPLATE,
                                plant_name=plant_name,
                                content=content,
                                is_owner=is_owner,
                                username=session['username'])

@app.route('/<plant_name>/<path:filename>')
def serve_plant_file(plant_name, filename):
    plant_path = os.path.join(PLANTS_DIR, plant_name)
    if not os.path.exists(plant_path):
        abort(404)

    # Don't serve user.json
    if filename == 'user.json':
        abort(403)

    try:
        return send_from_directory(plant_path, filename)
    except:
        abort(404)

@app.route('/api/upload/<plant_name>', methods=['POST'])
def upload_file(plant_name):
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    # Check if user is owner
    if get_plant_owner(plant_name) != session['username']:
        return jsonify({'error': 'You are not the owner of this plant! 🌸'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    plant_path = os.path.join(PLANTS_DIR, plant_name)
    filename = secure_filename(file.filename)

    # Handle zip files as folders
    if filename.endswith('.zip'):
        folder_name = filename[:-4]  # Remove .zip extension
        extract_path = os.path.join(plant_path, folder_name)

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            file.save(tmp_file.name)

            # Extract zip
            os.makedirs(extract_path, exist_ok=True)
            with zipfile.ZipFile(tmp_file.name, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

        os.unlink(tmp_file.name)  # Clean up temp file
        return jsonify({'success': True, 'message': f'Folder {folder_name} uploaded with love! 🌱'})

    # Save regular file
    file_path = os.path.join(plant_path, filename)
    file.save(file_path)

    return jsonify({'success': True, 'message': f'File {filename} uploaded with love! 🌱'})

@app.route('/api/files/<plant_name>')
def get_plant_files(plant_name):
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    # Check if user is owner
    if get_plant_owner(plant_name) != session['username']:
        return jsonify({'error': 'You are not the owner of this plant! 🌸'}), 403

    plant_path = os.path.join(PLANTS_DIR, plant_name)
    if not os.path.exists(plant_path):
        return jsonify({'files': []})

    files = []
    for item in os.listdir(plant_path):
        if item == 'user.json':  # Skip user.json
            continue
        item_path = os.path.join(plant_path, item)
        files.append({
            'name': item,
            'type': 'folder' if os.path.isdir(item_path) else 'file'
        })

    return jsonify({'files': files})

@app.route('/api/delete/<plant_name>/<filename>', methods=['DELETE'])
def delete_file(plant_name, filename):
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    # Check if user is owner
    if get_plant_owner(plant_name) != session['username']:
        return jsonify({'error': 'You are not the owner of this plant! 🌸'}), 403

    if filename == 'user.json':
        return jsonify({'error': 'Cannot delete user.json! 🌱'}), 403

    plant_path = os.path.join(PLANTS_DIR, plant_name)
    file_path = os.path.join(plant_path, filename)

    try:
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)
        return jsonify({'success': True, 'message': f'{filename} deleted with love! 🌱'})
    except:
        return jsonify({'error': 'Could not delete file'}), 500

# HTML Templates with love
AUTH_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Plant! 🌱 - Register with Love</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #4CAF50, #8BC34A);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 400px;
            width: 100%;
        }
        h1 { color: #4CAF50; margin-bottom: 30px; }
        input {
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            border: 2px solid #E8F5E8;
            border-radius: 10px;
            font-size: 16px;
            box-sizing: border-box;
        }
        input:focus { border-color: #4CAF50; outline: none; }
        button {
            background: #4CAF50;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            margin: 10px 5px;
            transition: background 0.3s;
        }
        button:hover { background: #45a049; }
        .toggle { color: #4CAF50; cursor: pointer; text-decoration: underline; }
        .error { color: #f44336; margin: 10px 0; }
        .success { color: #4CAF50; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to Plant! 🌱</h1>
        <p>Please before using Plant, Register :D</p>

        <div id="registerForm">
            <input type="text" id="regUsername" placeholder="Username" />
            <input type="password" id="regPassword" placeholder="Password" />
            <input type="password" id="regRepeatPassword" placeholder="Repeat Password" />
            <button onclick="register()">Register 🌱</button>
            <p class="toggle" onclick="showLoginForm()">Or.. Log In!</p>
        </div>

        <div id="loginForm" style="display:none;">
            <input type="text" id="loginUsername" placeholder="Username" />
            <input type="password" id="loginPassword" placeholder="Password" />
            <button onclick="login()">Log In 🌸</button>
            <p class="toggle" onclick="showRegisterForm()">Need to Register?</p>
        </div>

        <div id="message"></div>
    </div>

    <script>
        function showLoginForm() {
            document.getElementById('registerForm').style.display = 'none';
            document.getElementById('loginForm').style.display = 'block';
        }

        function showRegisterForm() {
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('registerForm').style.display = 'block';
        }

        function showMessage(msg, isError = false) {
            const msgDiv = document.getElementById('message');
            msgDiv.innerHTML = msg;
            msgDiv.className = isError ? 'error' : 'success';
        }

        async function register() {
            const username = document.getElementById('regUsername').value;
            const password = document.getElementById('regPassword').value;
            const repeatPassword = document.getElementById('regRepeatPassword').value;

            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password, repeat_password: repeatPassword })
                });

                const data = await response.json();

                if (data.success) {
                    showMessage(data.message);
                    setTimeout(() => window.location.href = '/', 1500);
                } else {
                    showMessage(data.error, true);
                }
            } catch (error) {
                showMessage('Error connecting to server! 💔', true);
            }
        }

        async function login() {
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                const data = await response.json();

                if (data.success) {
                    showMessage(data.message);
                    setTimeout(() => window.location.href = '/', 1500);
                } else {
                    showMessage(data.error, true);
                }
            } catch (error) {
                showMessage('Error connecting to server! 💔', true);
            }
        }
    </script>
</body>
</html>
'''

WELCOME_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Plant! 🌱 - Love Community</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #4CAF50, #8BC34A);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0;
        }
        .container {
            background: white;
            padding: 50px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 600px;
            width: 100%;
        }
        h1 { color: #4CAF50; margin-bottom: 30px; font-size: 2.5em; }
        p { font-size: 1.2em; line-height: 1.6; color: #333; margin: 20px 0; }
        .love-message { background: #E8F5E8; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .url-input {
            width: 70%;
            padding: 15px;
            border: 2px solid #E8F5E8;
            border-radius: 10px 0 0 10px;
            font-size: 16px;
            display: inline-block;
        }
        .go-btn {
            background: #4CAF50;
            color: white;
            padding: 15px 20px;
            border: none;
            border-radius: 0 10px 10px 0;
            font-size: 16px;
            cursor: pointer;
            display: inline-block;
        }
        .go-btn:hover { background: #45a049; }
        .user-info { position: absolute; top: 20px; right: 20px; color: white; font-weight: bold; }
    </style>
</head>
<body>
    <div class="user-info">Welcome, {{ username }}! 🌱</div>
    <div class="container">
        <h1>Welcome to Plant! 🌱</h1>
        <p>Plant is a love community where you can create websites for everyone!</p>
        <div class="love-message">
            <p><strong>But please remember:</strong><br>
            🌸 Be respectful<br>
            💚 Be kind<br>
            🙏 Love Jehovah</p>
        </div>
        <p>To create or visit a plant, just type the name below:</p>
        <div style="margin-top: 30px;">
            <input type="text" class="url-input" id="plantName" placeholder="Enter plant name..." />
            <button class="go-btn" onclick="goToPlant()">Go! 🌱</button>
        </div>
        <p style="font-size: 0.9em; color: #666; margin-top: 20px;">
            If the plant doesn't exist, it will be created with love! 💚
        </p>
    </div>

    <script>
        function goToPlant() {
            const plantName = document.getElementById('plantName').value.trim();
            if (plantName) {
                window.location.href = '/' + encodeURIComponent(plantName);
            }
        }

        document.getElementById('plantName').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                goToPlant();
            }
        });
    </script>
</body>
</html>
'''

PLANT_VIEWER_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ plant_name }} 🌱</title>
    <style>
        body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
        #plantFrame { width: 100vw; height: 100vh; border: none; }
        {% if is_owner %}
        .plant-manager {
            position: fixed;
            top: 20px;
            right: 20px;
            width: 300px;
            background: white;
            border: 2px solid #4CAF50;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            z-index: 1000;
            max-height: 80vh;
            overflow-y: auto;
            cursor: move;
        }
        .manager-header {
            background: #4CAF50;
            color: white;
            margin: -20px -20px 15px -20px;
            padding: 15px 20px;
            border-radius: 13px 13px 0 0;
            font-weight: bold;
            text-align: center;
        }
        .file-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px;
            margin: 5px 0;
            background: #f5f5f5;
            border-radius: 8px;
        }
        .file-item.folder { background: #E8F5E8; }
        .delete-btn {
            background: #f44336;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 5px 10px;
            cursor: pointer;
            font-size: 12px;
        }
        .delete-btn:hover { background: #d32f2f; }
        .drop-zone {
            border: 2px dashed #4CAF50;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin: 15px 0;
            transition: all 0.3s;
        }
        .drop-zone.dragover { background: #E8F5E8; }
        .upload-input { display: none; }
        {% endif %}
    </style>
</head>
<body>
    <!-- Plant content in iframe -->
    <iframe id="plantFrame" srcdoc="{{ content|e }}"></iframe>

    {% if is_owner %}
    <!-- Plant Manager Window -->
    <div class="plant-manager" id="plantManager">
        <div class="manager-header">
            🌱 {{ plant_name }} Manager
        </div>

        <div class="drop-zone" id="dropZone">
            📁 Drag files or folders here!<br>
            <small>Or <span style="color: #4CAF50; cursor: pointer;" onclick="document.getElementById('fileInput').click()">click to browse</span></small>
            <input type="file" id="fileInput" class="upload-input" multiple />
        </div>

        <div id="filesList">
            <!-- Files will be loaded here -->
        </div>
    </div>

    <script>
        // Make plant manager draggable
        let isDragging = false;
        let currentX, currentY, initialX, initialY;
        let xOffset = 0, yOffset = 0;

        const plantManager = document.getElementById('plantManager');

        plantManager.addEventListener('mousedown', dragStart);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', dragEnd);

        function dragStart(e) {
            if (e.target.classList.contains('delete-btn')) return;
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;
            if (e.target === plantManager || e.target.classList.contains('manager-header')) {
                isDragging = true;
            }
        }

        function drag(e) {
            if (isDragging) {
                e.preventDefault();
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;
                xOffset = currentX;
                yOffset = currentY;
                plantManager.style.transform = `translate(${currentX}px, ${currentY}px)`;
            }
        }

        function dragEnd() {
            isDragging = false;
        }

        // File upload functionality
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');

        // Drag and drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });

        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });

        async function handleFiles(files) {
            for (let file of files) {
                await uploadFile(file);
            }
            loadFiles();
            setTimeout(() => {
                document.getElementById('plantFrame').src = document.getElementById('plantFrame').src;
            }, 1000);
        }

        async function uploadFile(file) {
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch(`/api/upload/{{ plant_name }}`, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                if (result.success) {
                    console.log(result.message);
                } else {
                    alert(result.error);
                }
            } catch (error) {
                alert('Upload failed! 💔');
            }
        }

        async function loadFiles() {
            try {
                const response = await fetch(`/api/files/{{ plant_name }}`);
                const data = await response.json();

                const filesList = document.getElementById('filesList');
                filesList.innerHTML = '';

                data.files.forEach(file => {
                    const fileItem = document.createElement('div');
                    fileItem.className = `file-item ${file.type}`;
                    fileItem.innerHTML = `
                        <span>${file.type === 'folder' ? '📁' : '📄'} ${file.name}</span>
                        <button class="delete-btn" onclick="deleteFile('${file.name}')">🗑️</button>
                    `;
                    filesList.appendChild(fileItem);
                });
            } catch (error) {
                console.error('Failed to load files');
            }
        }

        async function deleteFile(filename) {
            if (!confirm(`Are you sure you want to delete ${filename}?`)) return;

            try {
                const response = await fetch(`/api/delete/{{ plant_name }}/${filename}`, {
                    method: 'DELETE'
                });

                const result = await response.json();
                if (result.success) {
                    loadFiles();
                    setTimeout(() => {
                        document.getElementById('plantFrame').src = document.getElementById('plantFrame').src;
                    }, 1000);
                } else {
                    alert(result.error);
                }
            } catch (error) {
                alert('Delete failed! 💔');
            }
        }

        // Load files on page load
        loadFiles();
    </script>
    {% endif %}
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
