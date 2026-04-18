import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old_str, new_str in replacements.items():
        content = content.replace(old_str, new_str)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

replacements = {
    # Reverse Backgrounds
    "bg-slate-50": "bg-slate-900",
    "bg-white": "bg-slate-950",
    "bg-slate-100": "bg-slate-800",
    
    # Reverse Borders
    "border-slate-200": "border-slate-800",
    "border-slate-300": "border-slate-700",
    
    # Reverse Texts - Note, need to be careful with text-slate-900 which was mapped from both text-slate-50 and text-slate-100 and text-white. 
    # I mapped "text-slate-50": "text-slate-900", "text-slate-100": "text-slate-900", "text-white": "text-slate-900",
    # so we map "text-slate-900" back to "text-white"
    "text-slate-9000": "text-slate-500", # Need to fix my previous error with 900 vs 9000, wait, did I make text-slate-9000? Let's check Dashboard.jsx
    
    "text-slate-900": "text-white",
    "text-slate-800": "text-slate-200",
    "text-slate-600": "text-slate-300",
    "text-slate-500": "text-slate-400",
    "text-slate-400": "text-slate-500",
    
    # Reverse SVGs and FlowChart colors
    "stroke=\"#94a3b8\"": "stroke=\"#475569\"",
    "fill: '#475569'": "fill: '#64748b'",
    "stroke=\"#e2e8f0\"": "stroke=\"#1e293b\"",
    
    # Reverse Map
    "light_all": "dark_all",
}

def process_index_css(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace("background-color: #f8fafc;", "background-color: #0f172a;")
    content = content.replace("color: #0f172a;", "color: #f8fafc;")
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

print("Dark mode restore complete!")
