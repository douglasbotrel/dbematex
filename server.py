#!/usr/bin/env python3
"""
Servidor HTTP local para o WebGIS DBEMATEX
Uso: python server.py
"""
import http.server
import socketserver
import os
import webbrowser
import threading

PORT = 8080
DIR  = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        # CORS — necessário para carregar arquivos locais via fetch()
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def log_message(self, fmt, *args):
        # Exibe apenas erros (status >= 400)
        code = args[1] if len(args) > 1 else '---'
        try:
            if int(code) >= 400:
                print(f'  [WARN] {args[0]} → {code}')
        except ValueError:
            pass

    def handle_error(self, request, client_address):
        # Suprime erros de conexão abortada pelo navegador (WinError 10053 / BrokenPipe)
        import sys
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)):
            return  # silencia — é normal o browser fechar a conexão cedo
        super().handle_error(request, client_address)


def open_browser():
    import time
    time.sleep(0.8)
    webbrowser.open(f'http://localhost:{PORT}')


if __name__ == '__main__':
    print()
    print('╔═══════════════════════════════════════════╗')
    print('║        DBEMATEX WebGIS — Servidor         ║')
    print(f'║   Acesse: http://localhost:{PORT}           ║')
    print('║   Encerre: Ctrl + C                       ║')
    print('╚═══════════════════════════════════════════╝')
    print()

    threading.Thread(target=open_browser, daemon=True).start()

    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n  Servidor encerrado. Até logo!')
