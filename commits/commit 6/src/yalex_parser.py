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
