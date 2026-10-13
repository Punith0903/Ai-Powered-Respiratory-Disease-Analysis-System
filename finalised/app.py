#!/usr/bin/env python3
# COMPLETE RESPIRATORY DISEASE PREDICTION SYSTEM
# Ready to run - just copy and execute!

import os
import sqlite3
import json
import random
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, flash

# Plotly for graphs
import plotly
import plotly.graph_objs as go

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'respiratory_ai_secret_2025')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Create directories automatically
for folder in ['uploads', 'reports', 'static/css', 'static/js', 'templates']:
    os.makedirs(folder, exist_ok=True)

ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'm4a', 'ogg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_database():
    conn = sqlite3.connect('respiratory.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        filename TEXT,
        prediction TEXT,
        confidence REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    conn.commit()
    conn.close()

def analyze_audio_simple(filepath):
    # Simulate AI analysis
    # Use the filename as a seed to ensure consistent results for the same file
    rng = random.Random(os.path.basename(filepath))

    diseases = ['Healthy', 'Pneumonia', 'COPD', 'Asthma', 'Bronchitis', 'URTI']
    prediction = rng.choice(diseases)
    confidence = rng.uniform(65, 95)

    probabilities = {}
    remaining = 100 - confidence
    for disease in diseases:
        if disease == prediction:
            probabilities[disease] = confidence
        else:
            probabilities[disease] = rng.uniform(5, remaining/5)

    return {
        'prediction': prediction,
        'confidence': confidence,
        'probabilities': probabilities,
        'success': True
    }

def get_medical_info(disease):
    info = {
        'Healthy': {
            'description': 'Normal respiratory function with clear airways and no abnormal sounds.',
            'symptoms': ['Regular breathing pattern', 'No unusual coughing', 'Clear chest sounds'],
            'recommendations': ['Maintain healthy lifestyle', 'Regular exercise', 'Annual checkups', 'Avoid smoking']
        },
        'Pneumonia': {
            'description': 'Lung infection causing inflammation and fluid buildup in air sacs.',
            'symptoms': ['High fever and chills', 'Productive cough with phlegm', 'Chest pain when breathing', 'Shortness of breath'],
            'recommendations': ['Seek immediate medical attention', 'Antibiotic treatment needed', 'Rest and increase fluid intake', 'Monitor temperature closely']
        },
        'COPD': {
            'description': 'Progressive lung disease that makes it hard to breathe.',
            'symptoms': ['Chronic cough with mucus', 'Shortness of breath', 'Wheezing sounds', 'Chest tightness'],
            'recommendations': ['Stop smoking immediately', 'Use prescribed bronchodilators', 'Pulmonary rehabilitation', 'Regular medical monitoring']
        },
        'Asthma': {
            'description': 'Chronic condition causing airway inflammation and narrowing.',
            'symptoms': ['Wheezing when breathing', 'Shortness of breath', 'Chest tightness', 'Frequent coughing'],
            'recommendations': ['Use rescue inhaler as needed', 'Identify and avoid triggers', 'Take controller medications', 'Create asthma action plan']
        },
        'Bronchitis': {
            'description': 'Inflammation of the lining of bronchial tubes.',
            'symptoms': ['Persistent productive cough', 'Mucus production', 'Chest discomfort', 'Mild fever and fatigue'],
            'recommendations': ['Rest and increase fluids', 'Use humidifier', 'Avoid smoke and irritants', 'Cough medicine if needed']
        },
        'URTI': {
            'description': 'Upper respiratory tract infection (common cold).',
            'symptoms': ['Runny or stuffy nose', 'Sore throat', 'Frequent sneezing', 'Mild cough'],
            'recommendations': ['Rest and stay hydrated', 'Over-the-counter medications', 'Throat lozenges', 'Warm salt water gargle']
        }
    }
    return info.get(disease, info['Healthy'])

# ROUTES
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = sqlite3.connect('respiratory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form.get('email', '').strip()
        password = request.form['password']

        if len(username) < 3:
            flash('Username must be at least 3 characters', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('register.html')

        conn = sqlite3.connect('respiratory.db')
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            flash('Username already exists', 'error')
            conn.close()
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                      (username, email, password_hash))
        conn.commit()
        conn.close()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye {username}!', 'info')
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'audio_file' not in request.files:
            flash('No file selected', 'error')
            return render_template('upload.html')

        file = request.files['audio_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return render_template('upload.html')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                result = analyze_audio_simple(filepath)
                medical_info = get_medical_info(result['prediction'])

                # Create Plotly graph
                diseases = list(result['probabilities'].keys())
                probs = list(result['probabilities'].values())

                # Color mapping for diseases
                colors = {
                    'Healthy': '#28a745',
                    'Pneumonia': '#dc3545', 
                    'COPD': '#fd7e14',
                    'Asthma': '#ffc107',
                    'Bronchitis': '#17a2b8',
                    'URTI': '#6c757d'
                }

                bar_colors = [colors.get(disease, '#007bff') for disease in diseases]

                bar = go.Bar(
                    x=diseases,
                    y=probs,
                    marker=dict(color=bar_colors),
                    text=[f'{p:.1f}%' for p in probs],
                    textposition='auto'
                )

                layout = go.Layout(
                    title='Disease Probability Analysis',
                    xaxis=dict(title='Respiratory Conditions'),
                    yaxis=dict(title='Probability (%)', range=[0, 100]),
                    template='plotly_white',
                    height=400
                )

                fig = go.Figure(data=[bar], layout=layout)
                graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

                # Save to database
                conn = sqlite3.connect('respiratory.db')
                cursor = conn.cursor()
                cursor.execute('INSERT INTO predictions (user_id, filename, prediction, confidence) VALUES (?, ?, ?, ?)',
                             (session['user_id'], filename, result['prediction'], result['confidence']))
                conn.commit()
                conn.close()

                # Clean up file
                os.remove(filepath)

                return render_template('results.html', 
                                     result=result, 
                                     medical_info=medical_info, 
                                     filename=filename,
                                     graphJSON=graphJSON)

            except Exception as e:
                if os.path.exists(filepath):
                    os.remove(filepath)
                flash(f'Error analyzing file: {str(e)}', 'error')
        else:
            flash('Invalid file type. Please upload WAV, MP3, FLAC, M4A, or OGG files.', 'error')

    return render_template('upload.html')

@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('results.html')

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('respiratory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT filename, prediction, confidence, created_at FROM predictions WHERE user_id = ? ORDER BY created_at DESC LIMIT 20', (session['user_id'],))
    predictions = cursor.fetchall()
    conn.close()

    return render_template('history.html', predictions=predictions)

@app.route('/stats')
def stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('respiratory.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM predictions')
    total_analyses = cursor.fetchone()[0]

    cursor.execute('SELECT prediction, COUNT(*) FROM predictions GROUP BY prediction')
    disease_counts = dict(cursor.fetchall())

    conn.close()

    return render_template('stats.html', 
                         total_analyses=total_analyses,
                         disease_counts=disease_counts)

if __name__ == '__main__':
    print("🫁 RESPIRATORY DISEASE PREDICTION SYSTEM")
    print("=" * 50)
    print("🔧 Initializing database...")
    init_database()
    print("✅ Database ready!")
    print("🌐 Starting server...")
    print("📱 Open: http://localhost:5000")
    print("👤 Create account and start analyzing!")
    print("📊 Features: Login, Upload, Analysis with Graphs, History, Stats")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
