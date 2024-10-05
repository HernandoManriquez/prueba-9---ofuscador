import os
import re
import random
import string
import base64
import shutil
import json
import argparse

obfuscation_map = {}
preserved_names = set()

# Lista de clases de Bootstrap a preservar
bootstrap_classes = {
    # Aquí puedes añadir las clases de Bootstrap que necesitas preservar
    'container', 'row', 'col', 'btn', 'navbar', 
    'alert', 'card', 'dropdown', 'form-control',
    # Añade más según sea necesario
}

def generate_random_string(length):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

def encrypt_string(s):
    return base64.b64encode(s.encode()).decode()

def decrypt_string(s):
    return f"atob('{s}')"

def rename_preserving_resources(name):
    if name in preserved_names or name in bootstrap_classes:
        return name
    new_name = generate_random_string(5)
    obfuscation_map[new_name] = name
    return new_name

def obfuscate_html(html, level):
    global preserved_names
    # Extraer nombres de recursos y clases antes de la ofuscación
    resource_names = re.findall(r'(src|href)=["\']([^"\']+)["\']', html)
    class_names = re.findall(r'class=["\']([^"\']+)["\']', html)
    preserved_names.update(name for _, name in resource_names)
    preserved_names.update(name.strip() for classes in class_names for name in classes.split())

    # Añadir clases de Bootstrap a los nombres preservados
    preserved_names.update(bootstrap_classes)
    
    # Eliminar comentarios HTML
    html = re.sub(r'<!--[\s\S]*?-->', '', html)
    
    if level >= 2:
        # Ofuscar atributos
        def obfuscate_attr(match):
            attr, value = match.groups()
            if attr not in ['ng-', 'data-', 'aria-', 'src', 'href', 'class']:
                encrypted = encrypt_string(value)
                obfuscation_map[encrypted] = value
                return f'{attr}="{encrypted}"'
            return match.group(0)
        
        html = re.sub(r'(\w+)="([^"]*)"', obfuscate_attr, html)
    
    if level >= 3:
        # Eliminar espacios en blanco innecesarios
        html = re.sub(r'\s+', ' ', html)
    
    return html.strip()

def obfuscate_js(js, level):
    global preserved_names
    # Extraer nombres de recursos y posibles referencias a clases antes de la ofuscación
    resource_names = re.findall(r'(import|from)\s+["\']([^"\']+)["\']', js)
    class_names = re.findall(r'(className|classList.add)\s*\(\s*["\']([^"\']+)["\']', js)
    preserved_names.update(name for _, name in resource_names)
    preserved_names.update(name.strip() for _, classes in class_names for name in classes.split())

    # Añadir clases de Bootstrap a los nombres preservados
    preserved_names.update(bootstrap_classes)
    
    # Eliminar comentarios de una línea y multilínea
    js = re.sub(r'//.*|/\*[\s\S]*?\*/', '', js)
    
    if level >= 2:
        # Renombrar variables y funciones
        identifiers = set(re.findall(r'\b(?:var|let|const|function)\s+(\w+)', js))
        for ident in identifiers:
            if not ident.startswith('$'):
                new_name = rename_preserving_resources(ident)
                js = re.sub(r'\b' + ident + r'\b', new_name, js)
    
    if level >= 3:
        # Encriptar strings
        def encrypt_match(match):
            return decrypt_string(encrypt_string(match.group(1)))
        
        js = re.sub(r'"([^"]*)"', encrypt_match, js)
        js = re.sub(r"'([^']*)'", encrypt_match, js)
        
        # Añadir código muerto
        dead_code = f"if(false){{console.log('{generate_random_string(10)}');}}"
        js = dead_code + js
        
        # Envolver en una función auto-ejecutable
        js = f"(function(){{ {js} }})();"
    
    if level >= 4:
        # Eliminar espacios en blanco innecesarios
        js = re.sub(r'\s+', ' ', js)
    
    return js.strip()

def obfuscate_css(css, level):
    # Eliminar comentarios CSS
    css = re.sub(r'/\*[\s\S]*?\*/', '', css)
    
    if level >= 2:
        # Renombrar clases y IDs, preservando todas las clases y IDs
        def rename_selector(match):
            selector = match.group(1)
            if selector.startswith('.') or selector.startswith('#'):
                preserved_names.add(selector[1:])
            return selector
        
        css = re.sub(r'([.#][\w-]+)', rename_selector, css)
    
    if level >= 3:
        # Minimizar valores de colores
        css = re.sub(r'#([0-9a-fA-F])\1([0-9a-fA-F])\2([0-9a-fA-F])\3', r'#\1\2\3', css)
    
    if level >= 4:
        # Eliminar espacios en blanco innecesarios
        css = re.sub(r'\s+', ' ', css)
    
    return css.strip()

def deobfuscate_html(html):
    for obfuscated, original in obfuscation_map.items():
        html = html.replace(obfuscated, original)
    return html

def deobfuscate_js(js):
    # Revertir la función auto-ejecutable
    js = re.sub(r'^\(function\(\)\{([\s\S]*)\}\)\(\);$', r'\1', js)
    
    # Eliminar código muerto
    js = re.sub(r'if\(false\)\{[^}]*\};', '', js)
    
    # Desencriptar strings
    def decrypt_match(match):
        return f'"{base64.b64decode(match.group(1)).decode()}"'
    js = re.sub(r'atob\(\'([^\']+)\'\)', decrypt_match, js)
    
    # Revertir nombres de variables y funciones
    for obfuscated, original in obfuscation_map.items():
        js = re.sub(r'\b' + obfuscated + r'\b', original, js)
    
    return js

def deobfuscate_css(css):
    for obfuscated, original in obfuscation_map.items():
        css = css.replace(f'.{obfuscated}', f'.{original}')
        css = css.replace(f'#{obfuscated}', f'#{original}')
    return css

def obfuscate_file(input_file, output_file, level):
    _, ext = os.path.splitext(input_file)
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if ext.lower() == '.html':
        obfuscated_content = obfuscate_html(content, level)
    elif ext.lower() == '.js':
        obfuscated_content = obfuscate_js(content, level)
    elif ext.lower() == '.css':
        obfuscated_content = obfuscate_css(content, level)
    else:
        obfuscated_content = content  # No ofuscar otros tipos de archivos
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(obfuscated_content)
    
    # Guardar el mapa de ofuscación
    map_file = f"{output_file}.map"
    with open(map_file, 'w') as f:
        json.dump(obfuscation_map, f)

def deobfuscate_file(input_file, output_file, map_file):
    with open(map_file, 'r') as f:
        global obfuscation_map
        obfuscation_map = json.load(f)
    
    _, ext = os.path.splitext(input_file)
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if ext.lower() == '.html':
        deobfuscated_content = deobfuscate_html(content)
    elif ext.lower() == '.js':
        deobfuscated_content = deobfuscate_js(content)
    elif ext.lower() == '.css':
        deobfuscated_content = deobfuscate_css(content)
    else:
        deobfuscated_content = content  # No desofuscar otros tipos de archivos
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(deobfuscated_content)

def process_directory(input_dir, output_dir, mode='obfuscate', level=1):
    global preserved_names, obfuscation_map
    preserved_names.clear()
    obfuscation_map.clear()
    
    # Primera pasada: recopilar nombres de recursos y clases
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.html', '.js', '.css')):
                input_path = os.path.join(root, file)
                with open(input_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if file.lower().endswith('.html'):
                        resource_names = re.findall(r'(src|href)=["\']([^"\']+)["\']', content)
                        class_names = re.findall(r'class=["\']([^"\']+)["\']', content)
                        preserved_names.update(name for _, name in resource_names)
                        preserved_names.update(name.strip() for classes in class_names for name in classes.split())
                    elif file.lower().endswith('.js'):
                        resource_names = re.findall(r'(import|from)\s+["\']([^"\']+)["\']', content)
                        class_names = re.findall(r'(className|classList.add)\s*\(\s*["\']([^"\']+)["\']', content)
                        preserved_names.update(name for _, name in resource_names)
                        preserved_names.update(name.strip() for _, classes in class_names for name in classes.split())
                    elif file.lower().endswith('.css'):
                        class_names = re.findall(r'([.#][\w-]+)', content)
                        preserved_names.update(name[1:] for name in class_names)
    
    # Añadir clases de Bootstrap a los nombres preservados
    preserved_names.update(bootstrap_classes)
    
    # Segunda pasada: procesar archivos
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            input_path = os.path.join(root, file)
            relative_path = os.path.relpath(input_path, input_dir)
            output_path = os.path.join(output_dir, relative_path)
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            _, ext = os.path.splitext(file)
            if ext.lower() in ['.html', '.js', '.css']:
                if mode == 'obfuscate':
                    obfuscate_file(input_path, output_path, level)
                    print(f"Archivo ofuscado (nivel {level}): {output_path}")
                else:
                    map_file = f"{input_path}.map"
                    if os.path.exists(map_file):
                        deobfuscate_file(input_path, output_path, map_file)
                        print(f"Archivo desofuscado: {output_path}")
                    else:
                        print(f"No se encontró mapa de ofuscación para: {input_path}")
                        shutil.copy2(input_path, output_path)
            else:
                shutil.copy2(input_path, output_path)
                print(f"Archivo copiado sin modificar: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ofuscador y desofuscador de código para proyectos web.")
    parser.add_argument("input_dir", help="Directorio de entrada")
    parser.add_argument("output_dir", help="Directorio de salida")
    parser.add_argument("--mode", choices=["obfuscate", "deobfuscate"], default="obfuscate", help="Modo de operación")
    parser.add_argument("--level", type=int, choices=[1, 2, 3, 4], default=1, help="Nivel de ofuscación (1-4)")

    args = parser.parse_args()

    process_directory(args.input_dir, args.output_dir, args.mode, args.level)
    print(f"Proceso de {'ofuscación' if args.mode == 'obfuscate' else 'desofuscación'} completado.")
    print(f"Archivos {'ofuscados' if args.mode == 'obfuscate' else 'desofuscados'} guardados en {args.output_dir}")