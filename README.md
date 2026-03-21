# YALex Generator — CC3071 Diseño de Lenguajes de Programación
## Universidad del Valle de Guatemala

Generador de Analizadores Léxicos basado en la especificación YALex.

---

## Estructura del Proyecto

```
src/
  main.py          → Punto de entrada del generador
  yalex_parser.py  → Parser de archivos .yal
  regex_parser.py  → Parser de Expresiones Regulares → AST
  regex_ast.py     → Nodos del Árbol de Expresión
  automata.py      → NFA (Thompson) + DFA (Subconjuntos) + Minimización (Hopcroft)
  visualizer.py    → Visualización con Graphviz
  code_gen.py      → Generación de código Python

examples/
  ejemplo.yal      → Especificación YALex de ejemplo
  input_prueba.txt → Archivo de entrada para probar el lexer

output/
  ejemplo_lexer.py                  → Analizador Léxico generado
  ejemplo_lexer_expression_tree.png → Árbol de Expresión
  ejemplo_lexer_dfa.png             → Diagrama DFA minimizado
  ejemplo_lexer_nfa.png             → Diagrama NFA (Thompson)
```

---

## Requisitos

- Python 3.10+
- Graphviz (para visualizaciones): `sudo apt-get install graphviz`

---

## Uso del Generador

```bash
# Uso básico
python src/main.py mi_lexer.yal

# Con nombre de salida personalizado
python src/main.py mi_lexer.yal -o output/mi_lexer

# Modo detallado + diagrama NFA
python src/main.py mi_lexer.yal -o output/mi_lexer --verbose --show-nfa

# Sin minimización DFA
python src/main.py mi_lexer.yal --no-minimize
```

### Parámetros

| Parámetro       | Descripción                          |
|-----------------|--------------------------------------|
| `input`         | Archivo `.yal` de entrada            |
| `-o / --output` | Nombre base de archivos de salida    |
| `--verbose`     | Mostrar detalles del proceso         |
| `--show-nfa`    | Generar visualización del NFA        |
| `--no-minimize` | No minimizar el DFA                  |

---

## Uso del Analizador Léxico Generado

```bash
python output/mi_lexer.py archivo_entrada.txt
```

### Como módulo Python

```python
from mi_lexer import gettoken   # o el entrypoint definido en el .yal

tokens = gettoken("x = 10 + 20")
for tok in tokens:
    print(tok)
```

---

## Estructura de Archivo `.yal`

```
(* comentario *)
{ header_code }

let ident = regexp
...

rule entrypoint =
    regexp { acción }
  | regexp { acción }
  ...

{ trailer_code }
```

### Operadores de Expresiones Regulares

| Operador        | Descripción                        |
|-----------------|------------------------------------|
| `'c'`           | Carácter literal                   |
| `"str"`         | Cadena de caracteres               |
| `[abc]`         | Conjunto de caracteres             |
| `['a'-'z']`     | Rango de caracteres                |
| `[^abc]`        | Complemento del conjunto           |
| `r1 # r2`       | Diferencia de conjuntos            |
| `r*`            | Cerradura de Kleene                |
| `r+`            | Cerradura positiva                 |
| `r?`            | Opcional                           |
| `r1 r2`         | Concatenación                      |
| `r1 \| r2`      | Alternación (unión)                |
| `(r)`           | Agrupación                         |
| `_`             | Cualquier carácter                 |
| `eof`           | Fin de archivo                     |
| `ident`         | Referencia a definición `let`      |

### Precedencia (mayor a menor)

1. `#`
2. `*`, `+`, `?`
3. Concatenación
4. `|`

---

## Algoritmos Implementados

1. **Construcción de Thompson** — Convierte el AST de la regex en un NFA
2. **Construcción de Subconjuntos** — Convierte el NFA en un DFA
3. **Minimización de Hopcroft** — Minimiza el DFA
4. **Longest Match** — El lexer generado usa concordancia más larga

---

## Salidas del Generador

| Archivo                            | Contenido                         |
|------------------------------------|-----------------------------------|
| `<nombre>.py`                      | Analizador Léxico en Python       |
| `<nombre>_expression_tree.png`     | Árbol de Expresión combinado      |
| `<nombre>_dfa.png`                 | Diagrama del DFA minimizado       |
| `<nombre>_nfa.png` (opcional)      | Diagrama del NFA de Thompson      |
| `<nombre>_*.dot`                   | Fuente Graphviz de cada diagrama  |
