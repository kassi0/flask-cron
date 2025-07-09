
from flask import Flask, render_template, request, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import uuid
import json
import os
from datetime import datetime

app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'dados')
JOBS_DIR = os.path.join(DATA_DIR, 'jobs')
TASK_FILE = os.path.join(DATA_DIR, 'tasks.json')

os.makedirs(JOBS_DIR, exist_ok=True)

def load_tasks():
    if os.path.exists(TASK_FILE):
        with open(TASK_FILE, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    return []

def save_tasks(tasks):
    with open(TASK_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

def run_task(script_path):
    full_path = os.path.join(JOBS_DIR, script_path)
    command = f"python {full_path}"
    print(f"Executando: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    output = out.decode('utf-8', errors='replace') + err.decode('utf-8', errors='replace')

    tasks = load_tasks()
    for task in tasks:
        if task['command'] == script_path:
            task['last_run'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            task['last_output'] = output.strip()
            break
    save_tasks(tasks)

def schedule_job(task):
    scheduler.add_job(
        func=run_task,
        trigger='cron',
        args=[task['command']],
        id=task['id'],
        **task['cron']
    )

@app.route('/')
def index():
    tasks = load_tasks()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    data = request.form
    file = request.files.get('script_file')
    command_input = data.get('command', '').strip()
    task_name = data['name'].strip()
    task_folder = os.path.join(JOBS_DIR, task_name)
    os.makedirs(task_folder, exist_ok=True)

    script_name = None
    if file and file.filename.endswith('.py'):
        script_name = file.filename
        file.save(os.path.join(task_folder, script_name))
    elif command_input:
        source_path = os.path.join(JOBS_DIR, command_input)
        dest_path = os.path.join(task_folder, command_input)
        if os.path.exists(source_path):
            import shutil
            shutil.copy2(source_path, dest_path)
            script_name = command_input
        else:
            return f"Script '{command_input}' não encontrado.", 400
    else:
        return "Você deve fornecer um script .py via upload ou nome existente.", 400

    task_id = str(uuid.uuid4())
    task = {
        'id': task_id,
        'name': task_name,
        'command': f"{task_name}/{script_name}",
        'enabled': True,
        'last_run': None,
        'last_output': '',
        'cron': {
            'minute': data['minute'],
            'hour': data['hour'],
            'day': data['day'],
            'month': data['month'],
            'day_of_week': data['dow']
        }
    }

    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)
    schedule_job(task)
    return redirect(url_for('index'))

@app.route('/toggle/<task_id>')
def toggle_task(task_id):
    tasks = load_tasks()
    for task in tasks:
        if task['id'] == task_id:
            task['enabled'] = not task['enabled']
            if task['enabled']:
                schedule_job(task)
            else:
                scheduler.remove_job(task_id)
            break
    save_tasks(tasks)
    return redirect(url_for('index'))

@app.route('/delete/<task_id>')
def delete_task(task_id):
    tasks = load_tasks()
    tasks = [task for task in tasks if task['id'] != task_id]
    try:
        scheduler.remove_job(task_id)
    except:
        pass
    save_tasks(tasks)
    return redirect(url_for('index'))

if __name__ == '__main__':
    for task in load_tasks():
        if task['enabled']:
            try:
                schedule_job(task)
            except:
                pass
    app.run(debug=True)
