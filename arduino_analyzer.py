#!/usr/bin/env python3
"""
Arduino Project Analyzer
Analizează și inventariază proiectele Arduino C++
"""

import os
import re
import json
import argparse
import datetime
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Set, Optional
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Pentru a evita probleme cu GUI

@dataclass
class FileStats:
    """Statistici pentru un fișier"""
    path: str
    extension: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    size_bytes: int
    functions: List[str]
    includes: List[str]
    defines: List[str]
    todos: List[str]
    last_modified: str

@dataclass
class ProjectStats:
    """Statistici pentru întregul proiect"""
    total_files: int
    total_lines: int
    total_code_lines: int
    total_comment_lines: int
    total_blank_lines: int
    total_size_bytes: int
    file_types: Dict[str, int]
    functions_count: int
    includes_count: int
    defines_count: int
    todos_count: int

class ArduinoProjectAnalyzer:
    def __init__(self, project_path: str, config_file: str = None):
        self.project_path = Path(project_path)
        self.config = self._load_config(config_file)
        self.file_stats: List[FileStats] = []
        self.project_stats: Optional[ProjectStats] = None
        
    def _load_config(self, config_file: str) -> dict:
        """Încarcă configurația din fișier sau folosește valorile implicite"""
        default_config = {
            "extensions": [".cpp", ".c", ".h", ".hpp", ".ino"],
            "exclude_dirs": [".git", ".vscode", "build", "libraries", "__pycache__", 
                           ".pio", "node_modules", "dist", "obj", "bin"],
            "exclude_files": ["*.tmp", "*.bak", "*.log"],
            "project_types": {
                "arduino": [".ino"],
                "platformio": ["platformio.ini"],
                "cmake": ["CMakeLists.txt"]
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Eroare la încărcarea configurației: {e}")
        
        return default_config
    
    def _should_exclude(self, path: Path) -> bool:
        """Verifică dacă un fișier/folder trebuie exclus"""
        # Verifică directoarele excluse
        for part in path.parts:
            if part in self.config["exclude_dirs"]:
                return True
        
        # Verifică fișierele excluse
        for pattern in self.config["exclude_files"]:
            if path.match(pattern):
                return True
        
        return False
    
    def _analyze_file_content(self, file_path: Path) -> FileStats:
        """Analizează conținutul unui fișier"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"Eroare la citirea fișierului {file_path}: {e}")
            return None
        
        # Contorizare linii
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = self._count_comment_lines(lines, file_path.suffix)
        code_lines = total_lines - blank_lines - comment_lines
        
        # Extragere funcții
        functions = self._extract_functions(content, file_path.suffix)
        
        # Extragere include-uri
        includes = self._extract_includes(content)
        
        # Extragere define-uri
        defines = self._extract_defines(content)
        
        # Extragere TODO/FIXME
        todos = self._extract_todos(lines)
        
        # Informații fișier
        stat = file_path.stat()
        size_bytes = stat.st_size
        last_modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        return FileStats(
            path=str(file_path.relative_to(self.project_path)),
            extension=file_path.suffix,
            total_lines=total_lines,
            code_lines=max(0, code_lines),
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            size_bytes=size_bytes,
            functions=functions,
            includes=includes,
            defines=defines,
            todos=todos,
            last_modified=last_modified
        )
    
    def _count_comment_lines(self, lines: List[str], extension: str) -> int:
        """Numără liniile de comentarii"""
        comment_count = 0
        in_multiline_comment = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if extension in ['.cpp', '.c', '.h', '.hpp', '.ino']:
                # Comentarii multiline /* */
                if '/*' in line and '*/' in line and not in_multiline_comment:
                    comment_count += 1
                elif '/*' in line:
                    in_multiline_comment = True
                    comment_count += 1
                elif '*/' in line and in_multiline_comment:
                    in_multiline_comment = False
                    comment_count += 1
                elif in_multiline_comment:
                    comment_count += 1
                # Comentarii single line //
                elif line.startswith('//'):
                    comment_count += 1
        
        return comment_count
    
    def _extract_functions(self, content: str, extension: str) -> List[str]:
        """Extrage numele funcțiilor din cod"""
        functions = []
        if extension in ['.cpp', '.c', '.ino']:
            # Pattern pentru funcții C/C++
            pattern = r'\b(?:void|int|float|double|bool|char|String|byte|word|long|short|unsigned)\s+(\w+)\s*\([^)]*\)\s*\{'
            matches = re.findall(pattern, content, re.MULTILINE)
            functions.extend(matches)
            
            # Pattern pentru funcții fără tip de return explicit (constructors, etc.)
            pattern2 = r'\b(\w+)\s*\([^)]*\)\s*\{'
            matches2 = re.findall(pattern2, content, re.MULTILINE)
            for match in matches2:
                if match not in ['if', 'for', 'while', 'switch'] and match not in functions:
                    functions.append(match)
        
        return list(set(functions))  # Remove duplicates
    
    def _extract_includes(self, content: str) -> List[str]:
        """Extrage include-urile din cod"""
        pattern = r'#include\s*[<"]([^>"]+)[>"]'
        return re.findall(pattern, content)
    
    def _extract_defines(self, content: str) -> List[str]:
        """Extrage define-urile din cod"""
        pattern = r'#define\s+(\w+)'
        return re.findall(pattern, content)
    
    def _extract_todos(self, lines: List[str]) -> List[str]:
        """Extrage comentariile TODO/FIXME/HACK"""
        todos = []
        patterns = [r'TODO:?\s*(.*)', r'FIXME:?\s*(.*)', r'HACK:?\s*(.*)', r'BUG:?\s*(.*)']
        
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    todos.append(f"Linia {i}: {match.group(0).strip()}")
        
        return todos
    
    def scan_project(self):
        """Scanează întregul proiect"""
        print(f"Scanarea proiectului: {self.project_path}")
        
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file() and not self._should_exclude(file_path):
                if file_path.suffix in self.config["extensions"]:
                    file_stats = self._analyze_file_content(file_path)
                    if file_stats:
                        self.file_stats.append(file_stats)
        
        self._calculate_project_stats()
        print(f"Analizate {len(self.file_stats)} fișiere")
    
    def _calculate_project_stats(self):
        """Calculează statisticile proiectului"""
        if not self.file_stats:
            return
        
        total_files = len(self.file_stats)
        total_lines = sum(f.total_lines for f in self.file_stats)
        total_code_lines = sum(f.code_lines for f in self.file_stats)
        total_comment_lines = sum(f.comment_lines for f in self.file_stats)
        total_blank_lines = sum(f.blank_lines for f in self.file_stats)
        total_size_bytes = sum(f.size_bytes for f in self.file_stats)
        
        file_types = Counter(f.extension for f in self.file_stats)
        functions_count = sum(len(f.functions) for f in self.file_stats)
        includes_count = sum(len(f.includes) for f in self.file_stats)
        defines_count = sum(len(f.defines) for f in self.file_stats)
        todos_count = sum(len(f.todos) for f in self.file_stats)
        
        self.project_stats = ProjectStats(
            total_files=total_files,
            total_lines=total_lines,
            total_code_lines=total_code_lines,
            total_comment_lines=total_comment_lines,
            total_blank_lines=total_blank_lines,
            total_size_bytes=total_size_bytes,
            file_types=dict(file_types),
            functions_count=functions_count,
            includes_count=includes_count,
            defines_count=defines_count,
            todos_count=todos_count
        )
    
    def detect_project_type(self) -> str:
        """Detectează tipul de proiect"""
        for project_type, indicators in self.config["project_types"].items():
            for indicator in indicators:
                if indicator.startswith('.'):
                    # Este o extensie de fișier
                    if any(f.extension == indicator for f in self.file_stats):
                        return project_type
                else:
                    # Este un nume de fișier
                    if (self.project_path / indicator).exists():
                        return project_type
        return "generic"
    
    def generate_tree_structure(self) -> str:
        """Generează structura în format arbore"""
        if not self.file_stats:
            return "Nu au fost găsite fișiere"
        
        # Organizează fișierele pe directoare
        dirs = defaultdict(list)
        for file_stat in self.file_stats:
            dir_path = str(Path(file_stat.path).parent)
            dirs[dir_path].append(file_stat)
        
        tree = []
        tree.append(f"📁 {self.project_path.name}/")
        
        for dir_path in sorted(dirs.keys()):
            if dir_path != '.':
                level = len(Path(dir_path).parts)
                indent = "  " * level
                tree.append(f"{indent}📁 {Path(dir_path).name}/")
            
            for file_stat in sorted(dirs[dir_path], key=lambda x: x.path):
                if dir_path == '.':
                    indent = "  "
                else:
                    level = len(Path(dir_path).parts) + 1
                    indent = "  " * level
                
                icon = "🔧" if file_stat.extension == ".ino" else "📄"
                tree.append(f"{indent}{icon} {Path(file_stat.path).name} "
                          f"({file_stat.total_lines} linii, {file_stat.code_lines} cod)")
        
        return "\n".join(tree)
    
    def create_visualizations(self, output_dir: Path):
        """Creează graficele pentru raport"""
        if not self.file_stats:
            return []
        
        output_dir.mkdir(exist_ok=True)
        charts = []
        
        # Grafic 1: Distribuția liniilor per fișier
        plt.figure(figsize=(12, 6))
        files = [Path(f.path).name for f in self.file_stats[:10]]  # Top 10
        lines = [f.total_lines for f in self.file_stats[:10]]
        
        plt.bar(files, lines, color='skyblue')
        plt.title('Top 10 Fișiere după Numărul de Linii')
        plt.xlabel('Fișiere')
        plt.ylabel('Numărul de Linii')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        chart1_path = output_dir / 'lines_distribution.png'
        plt.savefig(chart1_path, dpi=150, bbox_inches='tight')
        plt.close()
        charts.append(str(chart1_path.relative_to(output_dir)))
        
        # Grafic 2: Tipuri de fișiere
        if self.project_stats and len(self.project_stats.file_types) > 1:
            plt.figure(figsize=(8, 6))
            extensions = list(self.project_stats.file_types.keys())
            counts = list(self.project_stats.file_types.values())
            
            plt.pie(counts, labels=extensions, autopct='%1.1f%%', startangle=90)
            plt.title('Distribuția Tipurilor de Fișiere')
            plt.axis('equal')
            
            chart2_path = output_dir / 'file_types.png'
            plt.savefig(chart2_path, dpi=150, bbox_inches='tight')
            plt.close()
            charts.append(str(chart2_path.relative_to(output_dir)))
        
        # Grafic 3: Cod vs Comentarii vs Linii goale
        if self.project_stats:
            plt.figure(figsize=(8, 6))
            categories = ['Cod', 'Comentarii', 'Linii goale']
            values = [
                self.project_stats.total_code_lines,
                self.project_stats.total_comment_lines,
                self.project_stats.total_blank_lines
            ]
            colors = ['lightgreen', 'lightcoral', 'lightgray']
            
            plt.bar(categories, values, color=colors)
            plt.title('Distribuția Tipurilor de Linii')
            plt.ylabel('Numărul de Linii')
            
            chart3_path = output_dir / 'line_types.png'
            plt.savefig(chart3_path, dpi=150, bbox_inches='tight')
            plt.close()
            charts.append(str(chart3_path.relative_to(output_dir)))
        
        return charts


    def generate_html_report(self, output_file: str = "project_report.html"):
        """Generează raportul HTML interactiv"""
        if not self.file_stats or not self.project_stats:
            print("Nu există date pentru a generate raportul")
            return
        
        output_path = Path(output_file)
        project_type = self.detect_project_type()
        
        # Pregătește datele pentru JavaScript
        files_data = []
        for f in self.file_stats:
            files_data.append({
                'path': f.path,
                'name': Path(f.path).name,
                'extension': f.extension,
                'total_lines': f.total_lines,
                'code_lines': f.code_lines,
                'comment_lines': f.comment_lines,
                'blank_lines': f.blank_lines,
                'size_bytes': f.size_bytes,
                'functions': f.functions,
                'includes': f.includes,
                'defines': f.defines,
                'todos': f.todos,
                'last_modified': f.last_modified
            })
        
        # Colectează toate TODO-urile
        all_todos = []
        for file_stat in self.file_stats:
            for todo in file_stat.todos:
                all_todos.append({
                    'file': file_stat.path,
                    'todo': todo
                })
        
        html_content = f"""<!DOCTYPE html>
    <html lang="ro">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Raport Proiect Arduino - {self.project_path.name}</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            
            .header {{
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                padding: 20px 0;
                margin-bottom: 20px;
                border-bottom: 1px solid rgba(255,255,255,0.2);
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 0 20px;
            }}
            
            .header h1 {{
                color: white;
                text-align: center;
                font-size: 2.5em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            
            .nav-tabs {{
                display: flex;
                justify-content: center;
                margin: 20px 0;
                background: rgba(255,255,255,0.1);
                border-radius: 50px;
                padding: 5px;
                backdrop-filter: blur(10px);
            }}
            
            .nav-tab {{
                padding: 12px 24px;
                background: transparent;
                border: none;
                color: white;
                cursor: pointer;
                border-radius: 25px;
                margin: 0 5px;
                transition: all 0.3s ease;
                font-weight: 500;
            }}
            
            .nav-tab.active {{
                background: rgba(255,255,255,0.2);
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }}
            
            .nav-tab:hover {{
                background: rgba(255,255,255,0.15);
            }}
            
            .tab-content {{
                display: none;
                background: rgba(255,255,255,0.95);
                border-radius: 20px;
                padding: 30px;
                margin: 20px 0;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                backdrop-filter: blur(10px);
            }}
            
            .tab-content.active {{
                display: block;
                animation: fadeIn 0.5s ease-in-out;
            }}
            
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            
            .stat-card {{
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                padding: 25px;
                border-radius: 15px;
                text-align: center;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                transition: transform 0.3s ease;
                cursor: pointer;
            }}
            
            .stat-card:hover {{
                transform: translateY(-5px);
            }}
            
            .stat-number {{
                font-size: 2.5em;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            
            .stat-label {{
                opacity: 0.9;
                font-size: 1.1em;
            }}
            
            .chart-container {{
                background: white;
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                position: relative;
                height: 400px;
            }}
            
            .files-table-container {{
                background: white;
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                overflow-x: auto;
            }}
            
            .search-box {{
                width: 100%;
                padding: 12px 20px;
                border: 2px solid #ddd;
                border-radius: 25px;
                font-size: 16px;
                margin-bottom: 20px;
                transition: border-color 0.3s ease;
            }}
            
            .search-box:focus {{
                outline: none;
                border-color: #667eea;
            }}
            
            .files-table {{
                width: 100%;
                border-collapse: collapse;
            }}
            
            .files-table th {{
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                padding: 15px 10px;
                text-align: left;
                font-weight: 600;
                cursor: pointer;
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            
            .files-table td {{
                padding: 12px 10px;
                border-bottom: 1px solid #eee;
            }}
            
            .files-table tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            
            .files-table tr:hover {{
                background-color: #e3f2fd;
            }}
            
            .tree-structure {{
                background: #2c3e50;
                color: #ecf0f1;
                padding: 25px;
                border-radius: 15px;
                font-family: 'Courier New', monospace;
                white-space: pre-line;
                overflow-x: auto;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }}
            
            .todos-container {{
                background: white;
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                max-height: 500px;
                overflow-y: auto;
            }}
            
            .todo-item {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 12px;
                margin: 10px 0;
                transition: all 0.3s ease;
            }}
            
            .todo-item:hover {{
                background: #fff1b8;
                transform: translateX(5px);
            }}
            
            .project-info {{
                background: linear-gradient(135deg, #00b894, #00cec9);
                color: white;
                padding: 25px;
                border-radius: 15px;
                margin: 20px 0;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }}
            
            .sort-indicator {{
                margin-left: 5px;
                opacity: 0.6;
            }}
            
            .filter-controls {{
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin-bottom: 20px;
                align-items: center;
            }}
            
            .filter-select {{
                padding: 8px 15px;
                border: 2px solid #ddd;
                border-radius: 20px;
                background: white;
                font-size: 14px;
            }}
            
            .progress-bar {{
                width: 100%;
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
                overflow: hidden;
                margin: 5px 0;
            }}
            
            .progress-fill {{
                height: 100%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                transition: width 0.3s ease;
            }}
            
            @media (max-width: 768px) {{
                .nav-tabs {{
                    flex-wrap: wrap;
                }}
                
                .stats-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .filter-controls {{
                    flex-direction: column;
                    align-items: stretch;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>📊 Raport Proiect Arduino</h1>
            </div>
        </div>
        
        <div class="container">
            <div class="nav-tabs">
                <button class="nav-tab active" onclick="showTab('overview')">📊 Prezentare</button>
                <button class="nav-tab" onclick="showTab('charts')">📈 Grafice</button>
                <button class="nav-tab" onclick="showTab('files')">📁 Fișiere</button>
                <button class="nav-tab" onclick="showTab('structure')">🌳 Structură</button>
                <button class="nav-tab" onclick="showTab('todos')">⚠️ TODO</button>
            </div>
            
            <!-- Overview Tab -->
            <div id="overview" class="tab-content active">
                <div class="project-info">
                    <h3>📋 Informații Proiect</h3>
                    <p><strong>Nume:</strong> {self.project_path.name}</p>
                    <p><strong>Locație:</strong> {self.project_path.absolute()}</p>
                    <p><strong>Tip:</strong> {project_type.title()}</p>
                    <p><strong>Data analizei:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card" onclick="showTab('files')">
                        <div class="stat-number">{self.project_stats.total_files}</div>
                        <div class="stat-label">📁 Fișiere Total</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{self.project_stats.total_lines:,}</div>
                        <div class="stat-label">📄 Linii Total</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{self.project_stats.total_code_lines:,}</div>
                        <div class="stat-label">💻 Linii de Cod</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{self.project_stats.functions_count}</div>
                        <div class="stat-label">🔧 Funcții</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{self.project_stats.total_size_bytes/1024:.1f} KB</div>
                        <div class="stat-label">💾 Mărime Total</div>
                    </div>
                    <div class="stat-card" onclick="showTab('todos')">
                        <div class="stat-number">{self.project_stats.todos_count}</div>
                        <div class="stat-label">⚠️ TODO/FIXME</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <canvas id="overviewChart"></canvas>
                </div>
            </div>
            
            <!-- Charts Tab -->
            <div id="charts" class="tab-content">
                <h2>📈 Analiză Vizuală</h2>
                <div class="chart-container">
                    <h3>Distribuția Liniilor per Fișier</h3>
                    <canvas id="linesChart"></canvas>
                </div>
                <div class="chart-container">
                    <h3>Tipuri de Fișiere</h3>
                    <canvas id="fileTypesChart"></canvas>
                </div>
                <div class="chart-container">
                    <h3>Cod vs Comentarii vs Linii Goale</h3>
                    <canvas id="lineTypesChart"></canvas>
                </div>
            </div>
            
            <!-- Files Tab -->
            <div id="files" class="tab-content">
                <div class="files-table-container">
                    <h2>📁 Detalii Fișiere</h2>
                    <div class="filter-controls">
                        <input type="text" class="search-box" id="fileSearch" placeholder="🔍 Caută fișiere..." onkeyup="filterFiles()">
                        <select class="filter-select" id="extensionFilter" onchange="filterFiles()">
                            <option value="">Toate extensiile</option>"""
        
        # Adaugă opțiunile pentru filtrul de extensii
        for ext in sorted(self.project_stats.file_types.keys()):
            html_content += f'<option value="{ext}">{ext}</option>'
        
        html_content += f"""
                        </select>
                        <button class="nav-tab" onclick="sortTable()">🔄 Sortează</button>
                    </div>
                    
                    <table class="files-table" id="filesTable">
                        <thead>
                            <tr>
                                <th onclick="sortTableByColumn(0)">Fișier <span class="sort-indicator">↕️</span></th>
                                <th onclick="sortTableByColumn(1)">Extensie <span class="sort-indicator">↕️</span></th>
                                <th onclick="sortTableByColumn(2)">Total Linii <span class="sort-indicator">↕️</span></th>
                                <th onclick="sortTableByColumn(3)">Cod <span class="sort-indicator">↕️</span></th>
                                <th onclick="sortTableByColumn(4)">Comentarii <span class="sort-indicator">↕️</span></th>
                                <th onclick="sortTableByColumn(5)">Funcții <span class="sort-indicator">↕️</span></th>
                                <th onclick="sortTableByColumn(6)">Include-uri <span class="sort-indicator">↕️</span></th>
                                <th onclick="sortTableByColumn(7)">Mărime <span class="sort-indicator">↕️</span></th>
                            </tr>
                        </thead>
                        <tbody id="filesTableBody">
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Structure Tab -->
            <div id="structure" class="tab-content">
                <h2>🌳 Structura Proiectului</h2>
                <div class="tree-structure">{self.generate_tree_structure()}</div>
            </div>
            
            <!-- TODOs Tab -->
            <div id="todos" class="tab-content">
                <h2>⚠️ TODO/FIXME Items</h2>
                <div class="todos-container" id="todosContainer">
                </div>
            </div>
        </div>
        
        <script>
            // Date pentru JavaScript
            const filesData = {json.dumps(files_data, ensure_ascii=False)};
            const todosData = {json.dumps(all_todos, ensure_ascii=False)};
            const projectStats = {json.dumps(asdict(self.project_stats), ensure_ascii=False)};
            
            let currentSortColumn = -1;
            let currentSortDirection = 'asc';
            
            // Funcții pentru navigare prin tab-uri
            function showTab(tabName) {{
                // Ascunde toate tab-urile
                document.querySelectorAll('.tab-content').forEach(tab => {{
                    tab.classList.remove('active');
                }});
                
                // Ascunde toate butoanele active
                document.querySelectorAll('.nav-tab').forEach(btn => {{
                    btn.classList.remove('active');
                }});
                
                // Arată tab-ul selectat
                document.getElementById(tabName).classList.add('active');
                
                // Activează butonul corespunzător
                event.target.classList.add('active');
                
                // Inițializează graficele când tab-ul este afișat
                if (tabName === 'charts') {{
                    setTimeout(initCharts, 100);
                }}
                if (tabName === 'files') {{
                    populateFilesTable();
                }}
                if (tabName === 'todos') {{
                    populateTodos();
                }}
                if (tabName === 'overview') {{
                    setTimeout(initOverviewChart, 100);
                }}
            }}
            
            // Inițializare grafice
            function initCharts() {{
                // Grafic linii per fișier
                const topFiles = filesData.slice(0, 10).sort((a, b) => b.total_lines - a.total_lines);
                
                new Chart(document.getElementById('linesChart'), {{
                    type: 'bar',
                    data: {{
                        labels: topFiles.map(f => f.name),
                        datasets: [{{
                            label: 'Linii de cod',
                            data: topFiles.map(f => f.code_lines),
                            backgroundColor: 'rgba(102, 126, 234, 0.8)',
                            borderColor: 'rgba(102, 126, 234, 1)',
                            borderWidth: 2
                        }}, {{
                            label: 'Comentarii',
                            data: topFiles.map(f => f.comment_lines),
                            backgroundColor: 'rgba(118, 75, 162, 0.8)',
                            borderColor: 'rgba(118, 75, 162, 1)',
                            borderWidth: 2
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'top',
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});
                
                // Grafic tipuri de fișiere
                const extensions = Object.keys(projectStats.file_types);
                const counts = Object.values(projectStats.file_types);
                
                new Chart(document.getElementById('fileTypesChart'), {{
                    type: 'doughnut',
                    data: {{
                        labels: extensions,
                        datasets: [{{
                            data: counts,
                            backgroundColor: [
                                '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                                '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
                            ],
                            borderWidth: 3,
                            borderColor: '#fff'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'right',
                            }}
                        }}
                    }}
                }});
                
                // Grafic tipuri de linii
                new Chart(document.getElementById('lineTypesChart'), {{
                    type: 'bar',
                    data: {{
                        labels: ['Cod', 'Comentarii', 'Linii goale'],
                        datasets: [{{
                            label: 'Numărul de linii',
                            data: [
                                projectStats.total_code_lines,
                                projectStats.total_comment_lines,
                                projectStats.total_blank_lines
                            ],
                            backgroundColor: ['#2ECC71', '#E74C3C', '#95A5A6'],
                            borderColor: ['#27AE60', '#C0392B', '#7F8C8D'],
                            borderWidth: 2
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                display: false
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});
            }}
            
            // Grafic pentru overview
            function initOverviewChart() {{
                new Chart(document.getElementById('overviewChart'), {{
                    type: 'line',
                    data: {{
                        labels: filesData.slice(0, 20).map(f => f.name),
                        datasets: [{{
                            label: 'Complexitate (linii de cod)',
                            data: filesData.slice(0, 20).map(f => f.code_lines),
                            borderColor: 'rgba(102, 126, 234, 1)',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.4,
                            fill: true
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'top',
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});
            }}
            
            // Populare tabel fișiere
            function populateFilesTable() {{
                const tbody = document.getElementById('filesTableBody');
                tbody.innerHTML = '';
                
                filesData.forEach(file => {{
                    const row = tbody.insertRow();
                    row.innerHTML = `
                        <td>${{file.path}}</td>
                        <td><span style="padding: 4px 8px; background: #e3f2fd; border-radius: 12px; font-size: 0.9em;">${{file.extension}}</span></td>
                        <td>${{file.total_lines}}</td>
                        <td>${{file.code_lines}}</td>
                        <td>${{file.comment_lines}}</td>
                        <td>${{file.functions.length}}</td>
                        <td>${{file.includes.length}}</td>
                        <td>${{(file.size_bytes / 1024).toFixed(1)}} KB</td>
                    `;
                    
                    // Adaugă bara de progres pentru liniile de cod
                    const codeCell = row.cells[3];
                    const maxLines = Math.max(...filesData.map(f => f.code_lines));
                    const percentage = (file.code_lines / maxLines) * 100;
                    codeCell.innerHTML += `<div class="progress-bar"><div class="progress-fill" style="width: ${{percentage}}%"></div></div>`;
                }});
            }}
            
            // Filtrare fișiere
            function filterFiles() {{
                const searchTerm = document.getElementById('fileSearch').value.toLowerCase();
                const extensionFilter = document.getElementById('extensionFilter').value;
                const rows = document.querySelectorAll('#filesTableBody tr');
                
                rows.forEach(row => {{
                    const fileName = row.cells[0].textContent.toLowerCase();
                    const extension = row.cells[1].textContent.trim();
                    
                    const matchesSearch = fileName.includes(searchTerm);
                    const matchesExtension = !extensionFilter || extension.includes(extensionFilter);
                    
                    row.style.display = (matchesSearch && matchesExtension) ? '' : 'none';
                }});
            }}
            
            // Sortare tabel
            function sortTableByColumn(columnIndex) {{
                const table = document.getElementById('filesTable');
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                
                const isNumericColumn = [2, 3, 4, 5, 6, 7].includes(columnIndex);
                
                if (currentSortColumn === columnIndex) {{
                    currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
                }} else {{
                    currentSortDirection = 'asc';
                    currentSortColumn = columnIndex;
                }}
                
                rows.sort((a, b) => {{
                    let aVal = a.cells[columnIndex].textContent.trim();
                    let bVal = b.cells[columnIndex].textContent.trim();
                    
                    if (isNumericColumn) {{
                        aVal = parseFloat(aVal.replace(/[^0-9.-]/g, '')) || 0;
                        bVal = parseFloat(bVal.replace(/[^0-9.-]/g, '')) || 0;
                        return currentSortDirection === 'asc' ? aVal - bVal : bVal - aVal;
                    }} else {{
                        return currentSortDirection === 'asc' ? 
                            aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                    }}
                }});
                
                tbody.innerHTML = '';
                rows.forEach(row => tbody.appendChild(row));
                
                // Actualizează indicatorii de sortare
                document.querySelectorAll('.sort-indicator').forEach(indicator => {{
                    indicator.textContent = '↕️';
                }});
                
                const currentIndicator = table.querySelectorAll('th')[columnIndex].querySelector('.sort-indicator');
                currentIndicator.textContent = currentSortDirection === 'asc' ? '↑' : '↓';
            }}
            
            // Populare TODO-uri
            function populateTodos() {{
                const container = document.getElementById('todosContainer');
                
                if (todosData.length === 0) {{
                    container.innerHTML = '<p style="text-align: center; color: #666; font-size: 1.2em;">🎉 Nu există TODO-uri în acest proiect!</p>';
                    return;
                }}
                
                container.innerHTML = '';
                todosData.forEach(todo => {{
                    const div = document.createElement('div');
                    div.className = 'todo-item';
                    div.innerHTML = `
                        <strong>📁 ${{todo.file}}</strong><br>
                        <span style="margin-left: 20px;">${{todo.todo}}</span>
                    `;
                    container.appendChild(div);
                }});
            }}
            
            // Inițializare la încărcarea paginii
            document.addEventListener('DOMContentLoaded', function() {{
                initOverviewChart();
                populateFilesTable();
            }});
        </script>
    </body>
    </html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Raportul HTML interactiv a fost generat: {output_path.absolute()}")
        return str(output_path.absolute())




    def print_summary(self):
        """Afișează un rezumat în consolă"""
        if not self.project_stats:
            print("Nu există statistici de afișat")
            return
        
        print("\n" + "="*60)
        print(f"📊 REZUMAT PROIECT: {self.project_path.name}")
        print("="*60)
        print(f"📁 Fișiere analizate: {self.project_stats.total_files}")
        print(f"📄 Total linii: {self.project_stats.total_lines:,}")
        print(f"💻 Linii de cod: {self.project_stats.total_code_lines:,}")
        print(f"💬 Linii comentarii: {self.project_stats.total_comment_lines:,}")
        print(f"🔧 Funcții găsite: {self.project_stats.functions_count}")
        print(f"📦 Include-uri: {self.project_stats.includes_count}")
        print(f"⚠️  TODO/FIXME: {self.project_stats.todos_count}")
        print(f"💾 Mărime totală: {self.project_stats.total_size_bytes/1024:.1f} KB")
        
        print(f"\n🗂️  Tipuri de fișiere:")
        for ext, count in self.project_stats.file_types.items():
            print(f"   {ext}: {count} fișiere")
        
        print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(description="Arduino Project Analyzer")
    parser.add_argument("project_path", help="Calea către proiectul Arduino")
    parser.add_argument("--config", help="Fișier de configurație JSON")
    parser.add_argument("--output", default="project_report.html", help="Fișier de ieșire HTML")
    parser.add_argument("--no-html", action="store_true", help="Nu genera raportul HTML")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.project_path):
        print(f"Eroare: Proiectul {args.project_path} nu există!")
        return
    
    analyzer = ArduinoProjectAnalyzer(args.project_path, args.config)
    analyzer.scan_project()
    analyzer.print_summary()
    
    if not args.no_html:
        analyzer.generate_html_report(args.output)

if __name__ == "__main__":
    main()