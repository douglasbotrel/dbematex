#!/usr/bin/env python3
"""
DBEMATEX — Gerador de Catálogo de Camadas
==========================================
Escaneia a pasta data/ e gera automaticamente o data/catalog.json.

Formatos suportados:
  .zip      → shapefile compactado (.shp + .dbf + .shx + .prj)
  .geojson  → GeoJSON padrão
  .json     → GeoJSON alternativo
  .shp      → shapefile (será ignorado se existir .zip homônimo)

Uso:
  python gerar_catalog.py
"""

import os
import json

# ─── Configuração ────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR     = os.path.join(SCRIPT_DIR, 'data')
CATALOG_FILE = os.path.join(DATA_DIR, 'catalog.json')
TITLE        = 'DBEMATEX - WebGIS Ambiental'

SUPPORTED = {'.zip', '.geojson', '.json', '.shp'}

# ─── Estilos padrão por palavra-chave no nome do arquivo ─────────────────────
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
    'servidao':      {'color': '#bf360c', 'weight': 1.5, 'fillColor': '#FF7043', 'fillOpacity': 0.40, 'dashArray': '6,4'},
    'vegetacao':     {'color': '#33691e', 'weight': 1.0, 'fillColor': '#8BC34A', 'fillOpacity': 0.45},
    'edificacao':    {'color': '#37474f', 'weight': 1.0, 'fillColor': '#90A4AE', 'fillOpacity': 0.70},
    'construcao':    {'color': '#37474f', 'weight': 1.0, 'fillColor': '#90A4AE', 'fillOpacity': 0.70},
    'estrada':       {'color': '#795548', 'weight': 2.5, 'fillOpacity': 0,    'opacity': 1},
    'via':           {'color': '#795548', 'weight': 2.0, 'fillOpacity': 0,    'opacity': 1},
}

# ─── Nomes de exibição amigáveis ──────────────────────────────────────────────
DISPLAY_NAMES = {
    'limite_imovel': 'Limite do Imóvel',
    'limite':        'Limite do Imóvel',
    'reserva_legal': 'Reserva Legal',
    'reserva':       'Reserva Legal',
    'app':           'APP — Área de Preservação Permanente',
    'area_app':      'APP — Área de Preservação Permanente',
    'hidrografia':   'Hidrografia',
    'curso_dagua':   "Curso D'Água",
    'corpo_dagua':   "Corpo D'Água",
    'uso_solo':      'Uso do Solo',
    'uso':           'Uso do Solo',
    'servidao':      'Servidão Administrativa',
    'vegetacao':     'Vegetação Nativa',
    'edificacao':    'Edificações',
    'construcao':    'Construções',
    'estrada':       'Estradas / Vias',
    'via':           'Vias de Acesso',
}


def to_id(filename_no_ext: str) -> str:
    """Converte nome de arquivo em ID normalizado."""
    return (filename_no_ext.lower()
            .replace(' ', '_').replace('-', '_').replace('.', '_'))


def get_style(layer_id: str) -> dict | None:
    """Retorna estilo padrão com base em palavra-chave no ID."""
    for key, style in STYLE_DEFAULTS.items():
        if key in layer_id:
            return style
    return None  # O WebGIS usará o estilo padrão azul


def get_display_name(layer_id: str, filename_no_ext: str) -> str:
    """Retorna nome de exibição amigável."""
    for key, name in DISPLAY_NAMES.items():
        if key in layer_id:
            return name
    # Fallback: title case do nome do arquivo
    return filename_no_ext.replace('_', ' ').replace('-', ' ').title()


def load_existing_catalog() -> dict:
    """Carrega catálogo existente para preservar ajustes manuais."""
    if os.path.exists(CATALOG_FILE):
        try:
            with open(CATALOG_FILE, encoding='utf-8') as f:
                return {l['id']: l for l in json.load(f).get('layers', [])}
        except Exception:
            pass
    return {}


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    existing = load_existing_catalog()

    all_files = sorted(os.listdir(DATA_DIR))
    zip_bases = {os.path.splitext(f)[0].lower()
                 for f in all_files if f.lower().endswith('.zip')}

    layers = []
    for fname in all_files:
        if fname == 'catalog.json':
            continue
        base, ext = os.path.splitext(fname)
        ext = ext.lower()

        if ext not in SUPPORTED:
            continue

        # Pula .shp se existir .zip correspondente
        if ext == '.shp' and base.lower() in zip_bases:
            continue

        layer_id = to_id(base)

        # Preserva configuração manual existente
        if layer_id in existing:
            layers.append(existing[layer_id])
            continue

        layers.append({
            'id':      layer_id,
            'name':    get_display_name(layer_id, base),
            'file':    f'data/{fname}',
            'visible': True,
            'style':   get_style(layer_id),
        })

    catalog = {'title': TITLE, 'layers': layers}

    with open(CATALOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f'\n✓ Catálogo gerado: {CATALOG_FILE}')
    print(f'  {len(layers)} camada(s) encontrada(s):\n')
    for l in layers:
        status = '✓' if l.get('style') else '○'
        print(f'  {status}  {l["name"]:40s}  ({l["file"]})')

    if not layers:
        print('  ⚠  Nenhum arquivo encontrado em data/')
        print('     Adicione arquivos .zip (shapefile) ou .geojson e rode novamente.')
    print()


if __name__ == '__main__':
    main()
