#!/usr/bin/env python3
"""
Servidor HTTP local — DBEMATEX WebGIS
Uso: python server.py

- Gera o catalog.json DINAMICAMENTE a cada requisição do browser
  (basta dar F5 para ver novos arquivos da pasta data/)
- Não depende de catalog.json em disco
"""
import http.server
import socketserver
import os
import json
import webbrowser
import threading
import time

PORT     = 8080
DIR      = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(DIR, 'data')
TITLE    = 'DBEMATEX - WebGIS Ambiental'

SUPPORTED = {'.zip', '.geojson', '.json', '.shp'}

# ── Estilos padrão por palavra-chave ──────────────────────────
STYLE_DEFAULTS = {
    'limite_imovel': {'color': '#000000', 'weight': 2.5, 'fillOpacity': 0,    'opacity': 1},
    'limite':        {'color': '#000000', 'weight': 2.5, 'fillOpacity': 0,    'opacity': 1},
    'reserva_legal': {'color': '#1b5e20', 'weight': 1.5, 'fillColor': '#4CAF50', 'fillOpacity': 0.50},
    'reserva':       {'color': '#1b5e20', 'weight': 1.5, 'fillColor': '#4CAF50', 'fillOpacity': 0.50},
    'app':           {'color': '#0d47a1', 'weight': 1.5, 'fillColor': '#42A5F5', 'fillOpacity': 0.45},
    'area_app':      {'color': '#0d47a1', 'weight': 1.5, 'fillColor': '#42A5F5', 'fillOpacity': 0.45},
    'hidrografia':   {'color': '#01579b', 'weight': 1.5, 'fillColor': '#29b6f6', 'fillOpacity': 0.50},
    'curso_dagua':   {'color': '#0277bd', 'weight': 2.0, 'fillOpacity': 0,    'opacity': 1},
    'corpo_dagua':   {'color': '#01579b', 'weight': 1.5, 'fillColor': '#29b6f6', 'fillOpacity': 0.45},
    'uso_solo':      {'color': '#424242', 'weight': 1.0, 'fillColor': '#FFC107', 'fillOpacity': 0.40},
    'uso':           {'color': '#424242', 'weight': 1.0, 'fillColor': '#FFC107', 'fillOpacity': 0.40},
    'servidao':      {'color': '#bf360c', 'weight': 1.5, 'fillColor': '#FF7043', 'fillOpacity': 0.40},
    'vegetacao':     {'color': '#33691e', 'weight': 1.0, 'fillColor': '#8BC34A', 'fillOpacity': 0.45},
    'edificacao':    {'color': '#37474f', 'weight': 1.0, 'fillColor': '#90A4AE', 'fillOpacity': 0.70},
    'estrada':       {'color': '#795548', 'weight': 2.5, 'fillOpacity': 0,    'opacity': 1},
    'via':           {'color': '#795548', 'weight': 2.0, 'fillOpacity': 0,    'opacity': 1},
}
DISPLAY_NAMES = {
    'limite_imovel': 'Limite do Imóvel',
    'limite':        'Limite do Imóvel',
    'reserva_legal': 'Reserva Legal',
    'app':           'APP — Área de Preservação Permanente',
    'hidrografia':   'Hidrografia',
    'uso_solo':      'Uso do Solo',
    'servidao':      'Servidão Administrativa',
    'vegetacao':     'Vegetação Nativa',
    'edificacao':    'Edificações',
    'estrada':       'Estradas / Vias',
}


def to_id(name: str) -> str:
    return name.lower().replace(' ', '_').replace('-', '_').replace('.', '_')


def get_style(lid: str):
    for key, style in STYLE_DEFAULTS.items():
        if key in lid:
            return style
    return None


def get_display_name(lid: str, base: str) -> str:
    for key, name in DISPLAY_NAMES.items():
        if key in lid:
            return name
    return base.replace('_', ' ').replace('-', ' ').title()


def build_catalog() -> dict:
    """Escaneia data/ e retorna o catálogo como dict (sem gravar em disco)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    all_files  = sorted(os.listdir(DATA_DIR))
    zip_bases  = {os.path.splitext(f)[0].lower() for f in all_files if f.lower().endswith('.zip')}

    layers = []
    for fname in all_files:
        if fname == 'catalog.json':
            continue
        base, ext = os.path.splitext(fname)
        if ext.lower() not in SUPPORTED:
            continue
        if ext.lower() == '.shp' and base.lower() in zip_bases:
            continue  # prefere .zip

        lid = to_id(base)
        layers.append({
            'id':      lid,
            'name':    get_display_name(lid, base),
            'file':    f'data/{fname}',
            'visible': True,
            'style':   get_style(lid),
        })

    return {'title': TITLE, 'layers': layers}


# ── Handler HTTP ──────────────────────────────────────────────
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    # Intercepta requisições ao catalog.json → gera na hora
    def do_GET(self):
        path = self.path.split('?')[0]   # ignora query string
        if path in ('/data/catalog.json', 'data/catalog.json'):
            catalog = build_catalog()
            data    = json.dumps(catalog, ensure_ascii=False, indent=2).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type',  'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data)
            n = len(catalog['layers'])
            print(f'  📋 catalog.json → {n} camada(s)')
        else:
            super().do_GET()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def log_message(self, fmt, *args):
        code = args[1] if len(args) > 1 else '---'
        try:
            if int(code) >= 400:
                print(f'  [WARN] {args[0]} → {code}')
        except ValueError:
            pass

    def handle_error(self, request, client_address):
        import sys
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)


def open_browser():
    time.sleep(1.0)
    webbrowser.open(f'http://localhost:{PORT}')


if __name__ == '__main__':
    # Exibe preview do que será carregado
    catalog = build_catalog()
    n = len(catalog['layers'])

    print()
    print('╔════════════════════════════════════════════╗')
    print('║        DBEMATEX WebGIS — Servidor          ║')
    print(f'║   Acesse: http://localhost:{PORT}            ║')
    print('║   Encerre: Ctrl + C                        ║')
    print('╚════════════════════════════════════════════╝')
    print()
    if n == 0:
        print('  ⚠  Nenhum arquivo encontrado em data/')
        print('     Adicione ZIPs e dê F5 no navegador.')
    else:
        print(f'  ✓ {n} arquivo(s) encontrado(s) em data/:')
        for layer in catalog['layers']:
            print(f'     • {layer["name"]}  ({layer["file"]})')
    print()
    print('  Dica: adicione ZIPs em data/ e dê F5 no navegador — sem reiniciar!')
    print()

    threading.Thread(target=open_browser, daemon=True).start()

    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n  Servidor encerrado. Até logo!')
