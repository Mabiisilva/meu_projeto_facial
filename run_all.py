
import os
import platform
import re
import socket
import subprocess
import sys

# Caminhos
BACKEND = 'app.py'
FRONTEND = os.path.join('frontend', 'https_server.py')

# Detecta o comando python correto
PYTHON_CMD = 'python'
if platform.system() != 'Windows':
    PYTHON_CMD = 'python3'

# Função para abrir terminal separado (cross-platform)
def run_in_terminal(cmd, title):
    if platform.system() == 'Windows':
        # Abre novo terminal no Windows
        return subprocess.Popen(['start', 'cmd', '/k', cmd], shell=True)
    else:
        # Abre novo terminal no Linux/macOS
        terminal = os.environ.get('TERM_PROGRAM')
        if terminal == 'Apple_Terminal':
            return subprocess.Popen(['osascript', '-e', f'tell app "Terminal" to do script "{cmd}"'])
        # Tenta gnome-terminal, xterm, konsole, etc
        for term in ['gnome-terminal', 'x-terminal-emulator', 'konsole', 'xfce4-terminal', 'xterm']:
            if subprocess.call(['which', term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                return subprocess.Popen([term, '-e', cmd])
        # Fallback: roda no mesmo terminal
        return subprocess.Popen(cmd, shell=True)

if __name__ == '__main__':


    # Descobre o IP local
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()

    # Atualiza o .env com o IP detectado
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            env_lines = f.readlines()
        new_lines = []
        for line in env_lines:
            if line.startswith('FRONTEND_IP='):
                new_lines.append(f'FRONTEND_IP={ip}\n')
            elif line.startswith('BACKEND_HOST='):
                new_lines.append('BACKEND_HOST=0.0.0.0\n')
            else:
                new_lines.append(line)
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f'.env atualizado: FRONTEND_IP={ip}')
    else:
        print('.env não encontrado, pulando atualização de IP.')

    # Atualiza o valor do API_URL no frontend/index.html
    index_path = os.path.join('frontend', 'index.html')
    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()
    html_new = re.sub(r"const API_URL = '[^']*';", f"const API_URL = 'http://{ip}:5000';", html)
    if html != html_new:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html_new)
        print(f'API_URL atualizado para http://{ip}:5000 em frontend/index.html')
    else:
        print('API_URL já está correto.')

    print('Iniciando backend (Flask)...')
    backend_cmd = f'{PYTHON_CMD} {BACKEND}'
    run_in_terminal(backend_cmd, 'Backend')

    print('Iniciando frontend (HTTPS)...')
    frontend_cmd = f'{PYTHON_CMD} {FRONTEND}'
    run_in_terminal(frontend_cmd, 'Frontend')

    print('\nAmbos os servidores foram iniciados!')
    print('Acesse o frontend em: https://<seu-ip-local>:8443/index.html')
    print('Acesse o backend em: http://<seu-ip-local>:5000/')
    print('\nPressione Ctrl+C para sair deste script (os terminais abertos continuarão rodando)')
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print('\nScript finalizado. Feche os terminais abertos para encerrar os servidores.')
