# YALex Generator — CC3071 Diseño de Lenguajes de Programación
## Universidad del Valle de Guatemala

Generador de Analizadores Léxicos basado en la especificación YALex.

---

## Estructura del Proyecto

```
src/
  main.py          → Punto de entrada del generador (Orquestador Pipeline)
  yalex_parser.py  → Parser de archivos .yal y Generador de Tokens
  regex_parser.py  → Parser de Expresiones Regulares → AST y Combinación (Single Regex)
  regex_ast.py     → Nodos del Árbol de Expresión (Cálculo de Anulable, Firstpos, Lastpos)
  automata.py      → Construcción Directa de DFA evaluando 'followpos' del Árbol
  visualizer.py    → Visualización con Graphviz
  code_gen.py      → Generación de código Python (Orquesta Longest Match)

examples/
  ejemplo.yal      → Especificación YALex de ejemplo
  input_prueba.txt → Archivo de entrada para probar el lexer

output/
  ejemplo_lexer.py                  → Analizador Léxico generado en Python
  ejemplo_lexer_expression_tree.png → Imagen del Árbol de Expresión Combinado
  ejemplo_lexer_dfa.png             → Imagen del Diagrama DFA Directo
  ejemplo_lexer_*.dot               → Código fuente Graphviz
```

---

## Requisitos

- Python 3.10+
- Graphviz (para visualizaciones): `sudo apt-get install graphviz` o equivalente en Windows

---

## Uso del Generador

```bash
# Uso básico ("hello.pico" por defecto si existe, o especificar)
python src/main.py mi_lexer.yal

# Con nombre de salida personalizado
python src/main.py mi_lexer.yal -o output/mi_lexer
```

### Parámetros

| Parámetro       | Descripción                          |
|-----------------|--------------------------------------|
| `input`         | Archivo `.yal` de entrada            |
| `-o / --output` | Nombre base de archivos de salida    |

---

## Uso del Analizador Léxico Generado

```bash
python output/mi_lexer_lexer.py archivo_entrada.pico
```

El autogenerador priorizará las coincidencias a través del concepto de **Longest Match**. En caso de empates en el escaneo, su autómata utilizará el Token definido con **prioridad más alta** (El id menor / definido primero).

---

## Arquitectura y Algoritmos (Método del Árbol)

1. **Expansión de Macros y YALex Parse** — Se procesan las reglas y lets.
2. **Single Regex (La Gran Unión)** — Todos los tokens se unifican bajo la regla de Aho-Sethi-Ullman agregando `#` finalizadores.
3. **AST a DFA Directo** — El árbol computa de forma ascendente las tablas de anulabilidad, firstpos, lastpos y **followpos** para iterar dinámicamente y hallar los estados finitos deterministas sin transiciones épsilon intermedias.
4. **Generación** — Escritura final al disco.

---

## Operadores de Expresiones Regulares
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
