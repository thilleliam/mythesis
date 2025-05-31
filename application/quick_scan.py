import os

def quick_scan(path="./application"):
    """Scan rapide de la structure du projet"""
    
    print("🔍 STRUCTURE DU PROJET")
    print("=" * 50)
    
    for root, dirs, files in os.walk(path):
        # Ignorer __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('__pycache__')]
        
        level = root.replace(path, '').count(os.sep)
        indent = ' ' * 2 * level
        folder_name = os.path.basename(root)
        
        if level == 0:
            print(f"📁 {os.path.basename(path)}/")
        else:
            print(f"{indent}📁 {folder_name}/")
        
        # Lister les fichiers Python
        py_files = [f for f in files if f.endswith('.py')]
        for file in py_files:
            print(f"{indent}  📄 {file}")
            
            # Analyse rapide du contenu
            try:
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Compter les classes
                class_count = content.count('class ')
                function_count = content.count('def ')
                
                if class_count > 0 or function_count > 0:
                    print(f"{indent}     📊 {class_count} classes, {function_count} fonctions")
                    
                # Trouver les imports intéressants
                lines = content.split('\n')
                for line in lines[:20]:  # Regarder les 20 premières lignes
                    line = line.strip()
                    if line.startswith('from ') and ('sqlalchemy' in line or 'tkinter' in line or 'flask' in line):
                        print(f"{indent}     🔗 {line}")
                        
            except Exception as e:
                print(f"{indent}     ❌ Erreur lecture: {e}")
        
        print()

if __name__ == "__main__":
    quick_scan()