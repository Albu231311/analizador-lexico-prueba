"""
Nicolás Concuá - 23197
Esteban Cárcamo - 23016
Kevin Villagrán - 23584
Carlos Alburez - 231311
Universidad del Valle de Guatemala - CC3071
Fases de Compilación: Generador de Analizadores Léxicos

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
    """Lee contenido entre { } manejando anidación y retorna (contenido_sin_llaves, nueva_pos)."""
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
            i += 1
            if i < n and text[i] == '\\':
                i += 2
            elif i < n:
                i += 1
            if i < n and text[i] == "'":
                i += 1
        elif c == '"':
            i += 1
            while i < n and text[i] != '"':
                if text[i] == '\\':
                    i += 1
                i += 1
            if i < n:
                i += 1
        else:
            i += 1
    return -1

def parse_yalex_file(filename):
    """Parsea un archivo .yal y retorna su especificación como diccionario."""
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    return parse_yalex_text(text)


def parse_yalex_text(text):
    """Parsea el texto de un archivo YALex."""
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

    if pos < n and text[pos] == '{':
        header, pos = read_braced(text, pos)
        header = header.strip()
        pos = skip_ws(text, pos)

    while pos < n and is_keyword(text, pos, 'let'):
        pos += 3
        pos = skip_ws(text, pos)

        ident, pos = read_ident(text, pos)
        pos = skip_ws(text, pos)

        if pos >= n or text[pos] != '=':
            raise SyntaxError(f"Se esperaba '=' después de 'let {ident}'")
        pos += 1
        pos = skip_ws(text, pos)

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

    if pos < n and is_keyword(text, pos, 'rule'):
        pos += 4
        pos = skip_ws(text, pos)

        entrypoint, pos = read_ident(text, pos)
        pos = skip_ws(text, pos)

        while pos < n and text[pos] != '=':
            pos += 1
        if pos >= n:
            raise SyntaxError("Se esperaba '=' en la definición de rule")
        pos += 1
        pos = skip_ws(text, pos)

        first = True
        while pos < n:
            pos = skip_ws(text, pos)
            if pos >= n:
                break

            brace_pos = _find_action_brace(text, pos)
            if brace_pos == -1:
                break

            regexp_raw = text[pos:brace_pos].strip()

            if not first and regexp_raw.startswith('|'):
                regexp_raw = regexp_raw[1:].strip()

            if not regexp_raw:
                break

            pos = brace_pos
            action, pos = read_braced(text, pos)
            rules.append((regexp_raw.strip(), action.strip()))
            first = False

            pos = skip_ws(text, pos)
            if pos >= n:
                break

            if text[pos] == '{':
                break
            if text[pos] not in ('|', '\n', '\r', ' ', '\t'):
                break

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
