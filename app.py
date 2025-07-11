import os
import shutil
import uuid
import subprocess
from flask import Flask, render_template, request, redirect, session, url_for, jsonify, flash
from functools import wraps
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "dados")
JOBS_DIR = os.path.join(DADOS_DIR, "jobs")
DB_PATH = os.path.join(DADOS_DIR, "tasks.db")
os.makedirs(JOBS_DIR, exist_ok=True)

APP_VERSION = "2.2"

app = Flask(__name__)
app.secret_key = "supersecretkey"
scheduler = BackgroundScheduler(timezone=timezone("America/Sao_Paulo"))
scheduler.start()
app.jinja_env.globals.update(now=datetime.now)

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        tarefa TEXT,
        task_name TEXT,
        script TEXT,
        enabled INTEGER,
        last_run TEXT,
        last_output TEXT,
        cron_minute TEXT,
        cron_hour TEXT,
        cron_day TEXT,
        cron_month TEXT,
        cron_day_of_week TEXT
    )
    ''')
    conn.commit()
    conn.close()
init_db()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["logged_in"] = True
            return redirect("/")
        flash("Usuário ou senha incorretos.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

def load_tasks():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks")
    rows = cur.fetchall()
    conn.close()
    tasks = []
    for row in rows:
        tasks.append({
            'id': row['id'],
            'tarefa': row['tarefa'],
            'task_name': row['task_name'],
            'script': row['script'],
            'enabled': bool(row['enabled']),
            'last_run': row['last_run'],
            'last_output': row['last_output'],
            'cron': {
                'minute': row['cron_minute'],
                'hour': row['cron_hour'],
                'day': row['cron_day'],
                'month': row['cron_month'],
                'day_of_week': row['cron_day_of_week']
            }
        })
    return tasks

def save_task(task):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''REPLACE INTO tasks (
        id, tarefa, task_name, script, enabled, last_run, last_output,
        cron_minute, cron_hour, cron_day, cron_month, cron_day_of_week
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
        task['id'], task['tarefa'], task['task_name'], task['script'],
        int(task['enabled']), task['last_run'], task['last_output'],
        task['cron']['minute'], task['cron']['hour'], task['cron']['day'],
        task['cron']['month'], task['cron']['day_of_week']
    ))
    conn.commit()
    conn.close()

def delete_task_by_id(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def delete_tasks_by_tarefa(tarefa):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE tarefa = ?", (tarefa,))
    conn.commit()
    conn.close()

def run_task(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return
    script_path = os.path.join(JOBS_DIR, row['tarefa'], row['script'])
    command = ["python", script_path]
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(timeout=180)
        output = out.decode(errors="replace") + err.decode(errors="replace")
    except Exception as e:
        output = f"Erro ao executar: {e}"
    last_run = datetime.now(timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
    cur.execute('''
        UPDATE tasks
        SET last_run = ?, last_output = ?
        WHERE id = ?
    ''', (last_run, output.strip(), task_id))
    conn.commit()
    conn.close()

def schedule_job(task):
    if task.get('enabled'):
        scheduler.add_job(
            func=run_task,
            trigger='cron',
            args=[task['id']],
            id=task['id'],
            misfire_grace_time=60,
            coalesce=False,
            replace_existing=True,
            **task['cron']
        )

@app.route("/")
@login_required
def index():
    tasks = load_tasks()
    tarefas = {}
    for t in tasks:
        tarefas.setdefault(t['tarefa'], []).append(t)
    tarefa_nomes = sorted(list(set(t['tarefa'] for t in tasks)))
    from datetime import datetime
    return render_template(
        "index.html",
        tarefas=tarefas,
        tarefa_nomes=tarefa_nomes,
        versao=APP_VERSION,
        ano=datetime.now().year
    )

@app.route("/add", methods=["POST"])
@login_required
def add_task():
    data = request.form
    file = request.files.get('script_file')
    tarefa = data['tarefa'].strip() if data.get('tarefa') else ""
    tarefa_nova = data.get('tarefa_nova', "").strip()
    task_name = data['task_name'].strip() if data.get('task_name') else ""
    if tarefa_nova:
        tarefa = tarefa_nova
    if not tarefa:
        flash("Informe a tarefa.", "danger")
        return redirect("/")
    pasta_tarefa = os.path.join(JOBS_DIR, tarefa)
    os.makedirs(pasta_tarefa, exist_ok=True)

    script_name = None
    if file and file.filename.endswith('.py'):
        script_name = file.filename
        file.save(os.path.join(pasta_tarefa, script_name))
    elif data.get('script_existente'):
        script_name = data['script_existente']
    else:
        flash("Informe ou faça upload de um script .py.", "danger")
        return redirect("/")

    task_id = str(uuid.uuid4())
    task = {
        'id': task_id,
        'tarefa': tarefa,
        'task_name': task_name,
        'script': script_name,
        'enabled': True,
        'last_run': None,
        'last_output': "",
        'cron': {
            'minute': data['minute'],
            'hour': data['hour'],
            'day': data['day'],
            'month': data['month'],
            'day_of_week': data['day_of_week']
        }
    }
    save_task(task)
    schedule_job(task)
    flash(f"Task '{task_name}' criada com sucesso.", "success")
    return redirect("/")

@app.route("/toggle/<task_id>")
@login_required
def toggle_task(task_id):
    tasks = load_tasks()
    for task in tasks:
        if task['id'] == task_id:
            task['enabled'] = not task['enabled']
            save_task(task)
            if task['enabled']:
                schedule_job(task)
            else:
                try:
                    scheduler.remove_job(task_id)
                except:
                    pass
    return redirect("/")

@app.route("/delete/<task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    try:
        scheduler.remove_job(task_id)
    except:
        pass
    delete_task_by_id(task_id)
    flash("Task excluída.", "success")
    return redirect("/")

@app.route("/delete_tarefa/<tarefa>", methods=["POST"])
@login_required
def delete_tarefa(tarefa):
    tasks = load_tasks()
    for task in tasks:
        if task['tarefa'] == tarefa:
            try:
                scheduler.remove_job(task['id'])
            except:
                pass
    delete_tasks_by_tarefa(tarefa)
    # Remove a pasta do disco, se existir
    pasta = os.path.join(JOBS_DIR, tarefa)
    if os.path.exists(pasta):
        try:
            shutil.rmtree(pasta)
            flash(f"Tarefa '{tarefa}' e arquivos excluídos com sucesso.", "success")
        except Exception as e:
            flash(f"Erro ao excluir a pasta da tarefa: {e}", "danger")
    else:
        flash(f"Pasta da tarefa '{tarefa}' não encontrada.", "warning")
    return redirect("/")

@app.route("/edit/<task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    if not row:
        flash("Task não encontrada.", "danger")
        return redirect("/")
    
    if request.method == "POST":
        data = request.form
        file = request.files.get('script_file')
        # Atualiza campos editáveis:
        task_name = data.get('task_name', row['task_name'])
        cron_minute = data.get('minute', row['cron_minute'])
        cron_hour = data.get('hour', row['cron_hour'])
        cron_day = data.get('day', row['cron_day'])
        cron_month = data.get('month', row['cron_month'])
        cron_day_of_week = data.get('day_of_week', row['cron_day_of_week'])
        
        # Script: pode trocar por upload ou seleção
        script_name = row['script']
        pasta_tarefa = os.path.join(JOBS_DIR, row['tarefa'])
        if file and file.filename.endswith('.py'):
            script_name = file.filename
            file.save(os.path.join(pasta_tarefa, script_name))
        elif data.get('script_existente'):
            script_name = data['script_existente']

        # Atualiza o banco
        cur.execute('''
            UPDATE tasks SET 
                task_name=?, script=?, 
                cron_minute=?, cron_hour=?, cron_day=?, cron_month=?, cron_day_of_week=?
            WHERE id=?
        ''', (
            task_name, script_name,
            cron_minute, cron_hour, cron_day, cron_month, cron_day_of_week,
            task_id
        ))
        conn.commit()
        conn.close()
        # Reagendar
        try:
            scheduler.remove_job(task_id)
        except:
            pass
        # Recupera task atualizada
        cur = get_db().cursor()
        cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        t = cur.fetchone()
        if t and t['enabled']:
            task = {
                'id': t['id'],
                'tarefa': t['tarefa'],
                'task_name': t['task_name'],
                'script': t['script'],
                'enabled': bool(t['enabled']),
                'last_run': t['last_run'],
                'last_output': t['last_output'],
                'cron': {
                    'minute': t['cron_minute'],
                    'hour': t['cron_hour'],
                    'day': t['cron_day'],
                    'month': t['cron_month'],
                    'day_of_week': t['cron_day_of_week']
                }
            }
            schedule_job(task)
        flash("Task editada com sucesso!", "success")
        return redirect("/")
    else:
        # Renderiza a tela de edição
        pasta_tarefa = os.path.join(JOBS_DIR, row['tarefa'])
        scripts_existentes = []
        if os.path.exists(pasta_tarefa):
            scripts_existentes = [f for f in os.listdir(pasta_tarefa) if f.endswith('.py')]
        return render_template(
            "edit_task.html", 
            task=row, 
            scripts_existentes=scripts_existentes
        )


@app.route("/scripts/<tarefa>")
@login_required
def scripts_por_tarefa(tarefa):
    pasta = os.path.join(JOBS_DIR, tarefa)
    if not os.path.isdir(pasta):
        return jsonify(scripts=[])
    lista = [f for f in os.listdir(pasta) if f.endswith('.py')]
    return jsonify(scripts=lista)

if __name__ == "__main__":
    for task in load_tasks():
        if task['enabled']:
            try:
                schedule_job(task)
            except Exception as e:
                print(f"Erro ao agendar: {e}")
    app.run(debug=True, host="0.0.0.0",port=5000)
