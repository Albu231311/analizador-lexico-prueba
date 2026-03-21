"""
yalex_parser.py - Parser para archivos escritos en lenguaje YALex
Universidad del Valle de Guatemala - CC3071

Estructura de un archivo .yal:
  { header }
  let ident = regexp
  ...
  rule entrypoint =
      regexp { action }
      | regexp { action }
      ...
  { trailer }
"""

import re


# ──────────────────────── Utilidades ────────────────────────

def strip_comments(text):
    """Elimina comentarios (* ... *) del texto (no anidados)."""
    result = []
    i = 0
    n = len(text)
    while i < n:
        if i + 1 < n and text[i] == '(' and text[i+1] == '*':
            end = text.find('*)', i + 2)
            if end == -1:
                raise SyntaxError(f"Comentario no cerrado en posición {i}")
            i = end + 2
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


def skip_ws(text, pos):
    """Salta espacios en blanco."""
    n = len(text)
    while pos < n and text[pos] in ' \t\n\r':
        pos += 1
    return pos


def is_keyword(text, pos, kw):
    """Verifica si la palabra clave kw aparece en pos como palabra completa."""
    end = pos + len(kw)
    if text[pos:end] != kw:
        return False
    if end < len(text) and (text[end].isalnum() or text[end] == '_'):
        return False
    return True


def read_ident(text, pos):
    """Lee un identificador. Retorna (ident, nueva_pos)."""
    n = len(text)
    start = pos
    while pos < n and (text[pos].isalnum() or text[pos] == '_'):
        pos += 1
    if pos == start:
        raise SyntaxError(
            f"Se esperaba un identificador en posición {pos}, "
            f"encontré: {text[pos:pos+5]!r}"
        )
    return text[start:pos], pos


def read_braced(text, pos):
    """
    Lee contenido entre { } manejando anidación.
    Retorna (contenido_sin_llaves, nueva_pos).
    """
    if pos >= len(text) or text[pos] != '{':
        raise SyntaxError(f"Se esperaba '{{' en posición {pos}")
    pos += 1
    depth = 1
    start = pos
    n = len(text)
    while pos < n and depth > 0:
        if text[pos] == '{':
            depth += 1
        elif text[pos] == '}':
            depth -= 1
        pos += 1
    if depth != 0:
        raise SyntaxError("Bloque { } no cerrado")
    return text[start:pos - 1], pos


# ──────────────────────── Parser Principal ────────────────────────

def _find_action_brace(text, pos):
    """
    Busca la posición del próximo '{' que sea inicio de bloque de acción,
    saltando sobre literales de carácter ('x') y de cadena ("abc")
    para no confundirlos con llaves de acción.
    """
    n = len(text)
    i = pos
    while i < n:
        c = text[i]
        if c == '{':
            return i
        elif c == "'":
            # saltar literal de carácter: 'x' o '\n'
            i += 1
            if i < n and text[i] == '\\':
                i += 2   # escape + carácter
            elif i < n:
                i += 1   # carácter normal
            if i < n and text[i] == "'":
                i += 1   # cerrar comilla
        elif c == '"':
            # saltar literal de cadena
            i += 1
            while i < n and text[i] != '"':
                if text[i] == '\\':
                    i += 1  # saltar escape
                i += 1
            if i < n:
                i += 1  # cerrar comilla
        else:
            i += 1
    return -1

def parse_yalex_file(filename):
    """Parsea un archivo .yal y retorna su especificación como diccionario."""
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    return parse_yalex_text(text)


def parse_yalex_text(text):
    """
    Parsea el texto de un archivo YALex.

    Retorna:
      {
        'header':     str | None,
        'lets':       dict[str, str],   # nombre -> regexp_string
        'let_order':  list[str],         # orden de definición
        'entrypoint': str,
        'rules':      list[(regexp_str, action_str)],
        'trailer':    str | None,
      }
    """
    text = strip_comments(text)
    n = len(text)
    pos = 0

    header = None
    lets = {}
    let_order = []
    rules = []
    entrypoint = None
    trailer = None

    pos = skip_ws(text, pos)

    # ── Sección header opcional { ... } ──
    if pos < n and text[pos] == '{':
        header, pos = read_braced(text, pos)
        header = header.strip()
        pos = skip_ws(text, pos)

    # ── Definiciones let ──
    while pos < n and is_keyword(text, pos, 'let'):
        pos += 3  # saltar 'let'
        pos = skip_ws(text, pos)

        ident, pos = read_ident(text, pos)
        pos = skip_ws(text, pos)

        if pos >= n or text[pos] != '=':
            raise SyntaxError(f"Se esperaba '=' después de 'let {ident}'")
        pos += 1
        pos = skip_ws(text, pos)

        # La regexp termina cuando aparece la siguiente 'let' o 'rule'
        start = pos
        while pos < n:
            if is_keyword(text, pos, 'let') or is_keyword(text, pos, 'rule'):
                break
            pos += 1

        regexp_str = text[start:pos].strip()
        if not regexp_str:
            raise SyntaxError(f"Expresión regular vacía para 'let {ident}'")

        lets[ident] = regexp_str
        let_order.append(ident)
        pos = skip_ws(text, pos)

    # ── Definición rule ──
    if pos < n and is_keyword(text, pos, 'rule'):
        pos += 4
        pos = skip_ws(text, pos)

        entrypoint, pos = read_ident(text, pos)
        pos = skip_ws(text, pos)

        # Saltar argumentos opcionales hasta '='
        while pos < n and text[pos] != '=':
            pos += 1
        if pos >= n:
            raise SyntaxError("Se esperaba '=' en la definición de rule")
        pos += 1  # saltar '='
        pos = skip_ws(text, pos)

        # ── Parsear alternativas: regexp { action } | regexp { action } ... ──
        #
        # Estrategia: leer hasta el próximo '{' para obtener el regexp,
        # luego leer el bloque { action }.  Separador '|' entre alternativas
        # aparece antes del regexp siguiente (no dentro de él).
        #
        first = True
        while pos < n:
            pos = skip_ws(text, pos)
            if pos >= n:
                break

            # Buscar siguiente '{' que sea inicio de bloque de acción,
            # ignorando '{' dentro de literales de carácter o cadena
            brace_pos = _find_action_brace(text, pos)
            if brace_pos == -1:
                break  # sin más reglas

            regexp_raw = text[pos:brace_pos].strip()

            # Quitar separador '|' inicial (salvo primera alternativa)
            if not first and regexp_raw.startswith('|'):
                regexp_raw = regexp_raw[1:].strip()

            if not regexp_raw:
                # Bloque vacío = posible trailer
                break

            pos = brace_pos
            action, pos = read_braced(text, pos)
            rules.append((regexp_raw.strip(), action.strip()))
            first = False

            pos = skip_ws(text, pos)
            if pos >= n:
                break

            # ¿Hay más alternativas? El siguiente '|' indica más reglas.
            # Si el siguiente carácter visible es '{', es el trailer.
            if text[pos] == '{':
                break
            # Si es '|', continuar (se eliminará en la próxima iteración)
            # Si no hay nada, también salir
            if text[pos] not in ('|', '\n', '\r', ' ', '\t'):
                break

    # ── Sección trailer opcional { ... } ──
    pos = skip_ws(text, pos)
    if pos < n and text[pos] == '{':
        trailer, pos = read_braced(text, pos)
        trailer = trailer.strip()

    if not rules:
        raise SyntaxError("No se encontraron reglas en el archivo .yal")

    return {
        'header':     header,
        'lets':       lets,
        'let_order':  let_order,
        'entrypoint': entrypoint or 'gettoken',
        'rules':      rules,
        'trailer':    trailer,
    }
