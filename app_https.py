#!/usr/bin/env python3
import os
import ssl

from dotenv import load_dotenv

print("🔧 Carregando variáveis do arquivo .env...")
load_dotenv()

# Importa o app Flask com todos os logs
from app import app

if __name__ == '__main__':
    print("🔐 Iniciando aplicação Flask com HTTPS...")
    
    # Verifica se os certificados existem
    cert_file = 'server.pem'  # Certificados na raiz do projeto
    key_file = 'server.key'   # Certificados na raiz do projeto
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("✅ Certificados SSL encontrados!")
        print(f"📜 Certificado: {cert_file}")
        print(f"🔑 Chave: {key_file}")
        
        # Configuração SSL
        print("🔒 Configurando contexto SSL...")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)
        
        host = os.environ.get('BACKEND_HOST', '0.0.0.0')
        port = int(os.environ.get('BACKEND_PORT', 5000))
        
        print(f"🌐 Configuração do servidor HTTPS:")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Debug: True")
        print(f"   URL completa: https://{host}:{port}")
        print("⚠️  Aceite o certificado se solicitado pelo navegador")
        
        try:
            print("🚀 Iniciando servidor HTTPS...")
            app.run(debug=True, host=host, port=port, ssl_context=context)
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor HTTPS: {e}")
            print(f"   Tipo do erro: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
    else:
        print("❌ Certificados SSL não encontrados!")
        print(f"   Esperado: {cert_file}")
        print(f"   Esperado: {key_file}")
        print("🔄 Execute o servidor HTTPS do frontend primeiro para gerar os certificados.")
        print("📁 Ou verifique se os certificados estão na pasta 'frontend/'")
        
        print("\n🔄 Rodando sem HTTPS como fallback...")
        host = os.environ.get('BACKEND_HOST', '0.0.0.0')
        port = int(os.environ.get('BACKEND_PORT', 5000))
        
        print(f"🌐 Configuração do servidor HTTP (fallback):")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   URL completa: http://{host}:{port}")
        
        try:
            app.run(debug=True, host=host, port=port)
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor HTTP: {e}")
            print(f"   Tipo do erro: {type(e).__name__}")
            import traceback
            traceback.print_exc()
