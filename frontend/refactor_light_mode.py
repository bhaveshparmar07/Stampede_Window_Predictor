import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old_str, new_str in replacements.items():
        content = content.replace(old_str, new_str)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

replacements = {
    # Backgrounds
    "bg-slate-900": "bg-slate-50",
    "bg-slate-950": "bg-white",
    "bg-slate-800": "bg-slate-100",
    
    # Borders
    "border-slate-800": "border-slate-200",
    "border-slate-700": "border-slate-300",
    
    # Texts
    "text-slate-50": "text-slate-900",
    "text-slate-100": "text-slate-900",
    "text-slate-200": "text-slate-800",
    "text-slate-300": "text-slate-600",
    "text-slate-400": "text-slate-500",
    "text-slate-500": "text-slate-400",
    "text-white": "text-slate-900",
    
    # SVGs and FlowChart colors
    "stroke=\"#475569\"": "stroke=\"#94a3b8\"",
    "fill: '#64748b'": "fill: '#475569'",
    "stroke=\"#1e293b\"": "stroke=\"#e2e8f0\"",
    
    # Map
    "dark_all": "light_all",
    "#0f172a": "#f8fafc",
    "#f8fafc": "#0f172a",  # Note: #0f172a to #f8fafc mapping in index.css will be handled specially
}

# Special mapping for index.css to swap correctly without overriding issues
# since we have #0f172a and #f8fafc both existing.
def process_index_css(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace("background-color: #0f172a;", "background-color: #f8fafc;")
    content = content.replace("color: #f8fafc;", "color: #0f172a;")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

src_dir = r"R:\ai\Stampede Window Predictor\frontend\src"

for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith('.jsx') or file.endswith('.js'):
            filepath = os.path.join(root, file)
            replace_in_file(filepath, replacements)
        elif file == 'index.css':
            filepath = os.path.join(root, file)
            process_index_css(filepath)

print("Light mode refactor complete!")
