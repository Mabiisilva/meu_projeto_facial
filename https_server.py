#!/usr/bin/env python3
import http.server
import os
import socketserver
import ssl
import subprocess

from dotenv import load_dotenv


def create_self_signed_cert():
    """Cria um certificado SSL self-signed usando openssl"""
    if not (os.path.exists('server.pem') and os.path.exists('server.key')):
        print("Criando certificado SSL...")
        cmd = [
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', 'server.key', '-out', 'server.pem',
            '-days', '30', '-nodes', '-subj', '/CN=192.168.1.103'
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print("✅ Certificado SSL criado com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao criar certificado: {e}")
            return False
    return True


def start_https_server():
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    
    PORT = int(os.environ.get('FRONTEND_PORT', 8443))
    IP = os.environ.get('FRONTEND_IP', '192.168.1.103')
    
    # Cria certificado se não existir
    if not create_self_signed_cert():
        print("❌ Não foi possível criar o certificado SSL")
        return
    
    # Configura o servidor HTTPS
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(('', PORT), Handler) as httpd:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain('server.pem', 'server.key')
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            
            print("✅ Servidor HTTPS rodando em:")
            print(f"🔗 https://{IP}:{PORT}/frontend/")
            print("⚠️  Você verá um aviso de certificado no navegador")
            print("   - No Chrome: clique em 'Avançado' > 'Prosseguir'")
            print("   - No Firefox: clique em 'Avançado' > 'Aceitar risco'")
            print("🎯 No celular: acesse a URL acima e aceite o certificado")
            print("🛑 Para parar: Ctrl+C")
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")


if __name__ == "__main__":
    start_https_server()
