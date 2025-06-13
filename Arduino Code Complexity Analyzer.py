#!/usr/bin/env python3
"""
Arduino Code Complexity Analyzer
Analizează complexitatea codului C/C++ dintr-un proiect PlatformIO Arduino
"""

import os
import re
import argparse
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
import statistics

@dataclass
class FileMetrics:
    filename: str
    lines_of_code: int
    lines_of_comments: int
    blank_lines: int
    cyclomatic_complexity: int
    functions_count: int
    max_function_complexity: int
    average_function_complexity: float
    nested_depth: int
    
@dataclass
class ProjectMetrics:
    total_files: int
    total_loc: int
    total_comments: int
    total_blank_lines: int
    average_complexity: float
    max_complexity: int
    total_functions: int
    files_metrics: List[FileMetrics]

class CodeComplexityAnalyzer:
    def __init__(self):
        # Regex patterns pentru detectarea structurilor de control
        self.control_structures = [
            r'\bif\s*\(',
            r'\belse\s+if\s*\(',
            r'\bwhile\s*\(',
            r'\bfor\s*\(',
            r'\bdo\s*\{',
            r'\bswitch\s*\(',
            r'\bcase\s+',
            r'\bcatch\s*\(',
            r'\?\s*.*\s*:',  # ternary operator
        ]
        
        # Pattern pentru funcții
        self.function_pattern = r'^\s*(?:(?:inline|static|virtual|explicit|const)\s+)*(?:\w+(?:\s*\*|\s*&)?(?:\s*const)?\s+)+(\w+)\s*\([^;]*\)\s*(?:const\s*)?(?:override\s*)?(?:final\s*)?\s*\{'
        
        # Pattern pentru comentarii
        self.single_comment = r'//.*$'
        self.multi_comment_start = r'/\*'
        self.multi_comment_end = r'\*/'
        
    def remove_comments_and_strings(self, content: str) -> str:
        """Elimină comentariile și string-urile din cod pentru analiză mai precisă"""
        # Elimină string-urile
        content = re.sub(r'"(?:[^"\\]|\\.)*"', '""', content)
        content = re.sub(r"'(?:[^'\\]|\\.)*'", "''", content)
        
        # Elimină comentariile single-line
        content = re.sub(self.single_comment, '', content, flags=re.MULTILINE)
        
        # Elimină comentariile multi-line
        while True:
            match = re.search(self.multi_comment_start, content)
            if not match:
                break
            start = match.start()
            end_match = re.search(self.multi_comment_end, content[start:])
            if end_match:
                end = start + end_match.end()
                content = content[:start] + content[end:]
            else:
                content = content[:start]
                break
                
        return content
    
    def count_lines(self, filepath: str) -> Tuple[int, int, int]:
        """Contorizează liniile de cod, comentarii și linii goale"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Eroare la citirea fișierului {filepath}: {e}")
            return 0, 0, 0
            
        loc = 0
        comments = 0
        blank = 0
        in_multiline_comment = False
        
        for line in lines:
            line = line.strip()
            
            if not line:
                blank += 1
                continue
                
            # Verifică comentarii multi-line
            if '/*' in line and '*/' in line:
                # Comentariu pe o singură linie
                if not re.match(r'^\s*/\*.*\*/\s*$', line):
                    loc += 1
                else:
                    comments += 1
                continue
            elif '/*' in line:
                in_multiline_comment = True
                comments += 1
                continue
            elif '*/' in line:
                in_multiline_comment = False
                comments += 1
                continue
            elif in_multiline_comment:
                comments += 1
                continue
                
            # Verifică comentarii single-line
            if line.startswith('//'):
                comments += 1
            else:
                loc += 1
                
        return loc, comments, blank
    
    def calculate_cyclomatic_complexity(self, content: str) -> int:
        """Calculează complexitatea ciclomatică McCabe"""
        content = self.remove_comments_and_strings(content)
        complexity = 1  # Complexitatea de bază
        
        for pattern in self.control_structures:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            complexity += len(matches)
            
        return complexity
    
    def find_functions(self, content: str) -> List[Tuple[str, int, int]]:
        """Găsește funcțiile și calculează complexitatea fiecăreia"""
        content_clean = self.remove_comments_and_strings(content)
        functions = []
        
        lines = content_clean.split('\n')
        current_function = None
        brace_count = 0
        function_content = []
        
        for i, line in enumerate(lines):
            # Caută începutul unei funcții
            func_match = re.search(self.function_pattern, line)
            if func_match and current_function is None:
                current_function = func_match.group(1)
                function_content = [line]
                brace_count = line.count('{') - line.count('}')
                continue
                
            if current_function is not None:
                function_content.append(line)
                brace_count += line.count('{') - line.count('}')
                
                if brace_count <= 0:
                    # Sfârșitul funcției
                    func_code = '\n'.join(function_content)
                    complexity = self.calculate_cyclomatic_complexity(func_code)
                    functions.append((current_function, complexity, len(function_content)))
                    current_function = None
                    function_content = []
                    brace_count = 0
                    
        return functions
    
    def calculate_nesting_depth(self, content: str) -> int:
        """Calculează adâncimea maximă de imbricare"""
        content = self.remove_comments_and_strings(content)
        max_depth = 0
        current_depth = 0
        
        for char in content:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth = max(0, current_depth - 1)
                
        return max_depth
    
    def analyze_file(self, filepath: str) -> FileMetrics:
        """Analizează un singur fișier"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Eroare la citirea fișierului {filepath}: {e}")
            return FileMetrics(
                filename=os.path.basename(filepath),
                lines_of_code=0, lines_of_comments=0, blank_lines=0,
                cyclomatic_complexity=0, functions_count=0,
                max_function_complexity=0, average_function_complexity=0,
                nested_depth=0
            )
        
        # Calculează metricile
        loc, comments, blank = self.count_lines(filepath)
        file_complexity = self.calculate_cyclomatic_complexity(content)
        functions = self.find_functions(content)
        nesting_depth = self.calculate_nesting_depth(content)
        
        # Calculează statisticile funcțiilor
        if functions:
            function_complexities = [f[1] for f in functions]
            max_func_complexity = max(function_complexities)
            avg_func_complexity = statistics.mean(function_complexities)
        else:
            max_func_complexity = 0
            avg_func_complexity = 0
        
        return FileMetrics(
            filename=os.path.basename(filepath),
            lines_of_code=loc,
            lines_of_comments=comments,
            blank_lines=blank,
            cyclomatic_complexity=file_complexity,
            functions_count=len(functions),
            max_function_complexity=max_func_complexity,
            average_function_complexity=round(avg_func_complexity, 2),
            nested_depth=nesting_depth
        )
    
    def analyze_project(self, project_path: str) -> ProjectMetrics:
        """Analizează întreg proiectul PlatformIO"""
        project_path = Path(project_path)
        
        # Găsește fișierele C/C++ și header
        cpp_extensions = ['.cpp', '.c', '.cc', '.cxx', '.ino']
        header_extensions = ['.h', '.hpp', '.hxx']
        all_extensions = cpp_extensions + header_extensions
        
        files_to_analyze = []
        
        # Caută în directorul src/ și în rădăcina proiectului
        search_dirs = ['src', 'lib', 'include', '.']
        
        for search_dir in search_dirs:
            dir_path = project_path / search_dir
            if dir_path.exists():
                for ext in all_extensions:
                    files_to_analyze.extend(dir_path.rglob(f'*{ext}'))
        
        # Elimină duplicatele
        files_to_analyze = list(set(files_to_analyze))
        
        if not files_to_analyze:
            print(f"Nu s-au găsit fișiere C/C++ în {project_path}")
            return ProjectMetrics(0, 0, 0, 0, 0, 0, 0, [])
        
        print(f"Analizez {len(files_to_analyze)} fișiere...")
        
        # Analizează fiecare fișier
        files_metrics = []
        for filepath in files_to_analyze:
            print(f"Analizez: {filepath.name}")
            metrics = self.analyze_file(str(filepath))
            files_metrics.append(metrics)
        
        # Calculează metricile proiectului
        total_loc = sum(fm.lines_of_code for fm in files_metrics)
        total_comments = sum(fm.lines_of_comments for fm in files_metrics)
        total_blank = sum(fm.blank_lines for fm in files_metrics)
        total_functions = sum(fm.functions_count for fm in files_metrics)
        
        complexities = [fm.cyclomatic_complexity for fm in files_metrics if fm.cyclomatic_complexity > 0]
        avg_complexity = statistics.mean(complexities) if complexities else 0
        max_complexity = max(complexities) if complexities else 0
        
        return ProjectMetrics(
            total_files=len(files_metrics),
            total_loc=total_loc,
            total_comments=total_comments,
            total_blank_lines=total_blank,
            average_complexity=round(avg_complexity, 2),
            max_complexity=max_complexity,
            total_functions=total_functions,
            files_metrics=files_metrics
        )

def generate_html_report(metrics: ProjectMetrics, project_name: str = "Arduino Project") -> str:
    """Generează raportul HTML"""
    # Sortează fișierele după complexitate
    sorted_files = sorted(metrics.files_metrics, key=lambda x: x.cyclomatic_complexity, reverse=True)
    
    # Calculează distribuția complexității
    low_complexity = sum(1 for fm in metrics.files_metrics if fm.cyclomatic_complexity <= 10)
    medium_complexity = sum(1 for fm in metrics.files_metrics if 10 < fm.cyclomatic_complexity <= 20)
    high_complexity = sum(1 for fm in metrics.files_metrics if fm.cyclomatic_complexity > 20)
    
    # Clasifica complexitatea generală
    if metrics.max_complexity <= 10:
        overall_status = "success"
        overall_text = "SCĂZUTĂ"
    elif metrics.max_complexity <= 20:
        overall_status = "warning"
        overall_text = "MODERATĂ"
    else:
        overall_status = "danger"
        overall_text = "RIDICATĂ"
    
    # Generează rândurile tabelului pentru fișiere
    files_rows = ""
    for fm in sorted_files:
        if fm.cyclomatic_complexity > 0:
            if fm.cyclomatic_complexity > 20:
                row_class = "table-danger"
                badge_class = "bg-danger"
            elif fm.cyclomatic_complexity > 10:
                row_class = "table-warning"
                badge_class = "bg-warning"
            else:
                row_class = "table-success"
                badge_class = "bg-success"
            
            files_rows += f"""
            <tr class="{row_class}">
                <td><strong>{fm.filename}</strong></td>
                <td>{fm.lines_of_code}</td>
                <td>{fm.lines_of_comments}</td>
                <td><span class="badge {badge_class}">{fm.cyclomatic_complexity}</span></td>
                <td>{fm.functions_count}</td>
                <td>{fm.max_function_complexity}</td>
                <td>{fm.average_function_complexity}</td>
                <td>{fm.nested_depth}</td>
            </tr>
            """
    
    # Template HTML
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ro">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Raport Complexitate - {project_name}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            .complexity-card {{
                border-left: 4px solid;
                transition: transform 0.2s;
            }}
            .complexity-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            .success-border {{ border-left-color: #28a745; }}
            .warning-border {{ border-left-color: #ffc107; }}
            .danger-border {{ border-left-color: #dc3545; }}
            .metric-icon {{
                font-size: 2rem;
                opacity: 0.8;
            }}
            .chart-container {{
                position: relative;
                height: 300px;
                margin: 20px 0;
            }}
            body {{
                background-color: #f8f9fa;
            }}
            .main-card {{
                border: none;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <div class="container-fluid py-4">
            <div class="row">
                <div class="col-12">
                    <div class="card main-card">
                        <div class="card-header bg-primary text-white">
                            <h1 class="mb-0">
                                <i class="fas fa-code me-2"></i>
                                Raport Complexitate Cod Arduino
                            </h1>
                            <p class="mb-0 mt-2">Proiect: <strong>{project_name}</strong></p>
                            <small>Generat pe: {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</small>
                        </div>
                        <div class="card-body">
                            
                            <!-- Statistici Generale -->
                            <div class="row mb-4">
                                <div class="col-12">
                                    <h3><i class="fas fa-chart-bar me-2"></i>Statistici Generale</h3>
                                </div>
                                <div class="col-md-3 mb-3">
                                    <div class="card complexity-card success-border h-100">
                                        <div class="card-body text-center">
                                            <i class="fas fa-file-code metric-icon text-primary mb-2"></i>
                                            <h4 class="card-title">{metrics.total_files}</h4>
                                            <p class="card-text">Fișiere analizate</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3 mb-3">
                                    <div class="card complexity-card success-border h-100">
                                        <div class="card-body text-center">
                                            <i class="fas fa-lines-leaning metric-icon text-success mb-2"></i>
                                            <h4 class="card-title">{metrics.total_loc:,}</h4>
                                            <p class="card-text">Linii de cod</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3 mb-3">
                                    <div class="card complexity-card warning-border h-100">
                                        <div class="card-body text-center">
                                            <i class="fas fa-comment-dots metric-icon text-info mb-2"></i>
                                            <h4 class="card-title">{metrics.total_comments:,}</h4>
                                            <p class="card-text">Comentarii</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3 mb-3">
                                    <div class="card complexity-card success-border h-100">
                                        <div class="card-body text-center">
                                            <i class="fas fa-function metric-icon text-warning mb-2"></i>
                                            <h4 class="card-title">{metrics.total_functions}</h4>
                                            <p class="card-text">Funcții totale</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Analiza Complexității -->
                            <div class="row mb-4">
                                <div class="col-md-8">
                                    <h3><i class="fas fa-brain me-2"></i>Analiza Complexității</h3>
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <div class="card complexity-card {overall_status}-border h-100">
                                                <div class="card-body">
                                                    <h5>Complexitate Maximă</h5>
                                                    <h2 class="text-{overall_status}">{metrics.max_complexity}</h2>
                                                    <span class="badge bg-{overall_status}">{overall_text}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <div class="card complexity-card success-border h-100">
                                                <div class="card-body">
                                                    <h5>Complexitate Medie</h5>
                                                    <h2 class="text-primary">{metrics.average_complexity}</h2>
                                                    <small class="text-muted">Pe toate fișierele</small>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <h3>Distribuția Complexității</h3>
                                    <div class="chart-container">
                                        <canvas id="complexityChart"></canvas>
                                    </div>
                                </div>
                            </div>

                            <!-- Tabel Detaliat Fișiere -->
                            <div class="row">
                                <div class="col-12">
                                    <h3><i class="fas fa-table me-2"></i>Detalii Fișiere</h3>
                                    <div class="table-responsive">
                                        <table class="table table-hover">
                                            <thead class="table-dark">
                                                <tr>
                                                    <th>Fișier</th>
                                                    <th>LOC</th>
                                                    <th>Comentarii</th>
                                                    <th>Complexitate</th>
                                                    <th>Funcții</th>
                                                    <th>Max Func</th>
                                                    <th>Avg Func</th>
                                                    <th>Adâncime</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {files_rows}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>

                            <!-- Recomandări -->
                            <div class="row mt-4">
                                <div class="col-12">
                                    <h3><i class="fas fa-lightbulb me-2"></i>Recomandări</h3>
                                    <div class="card">
                                        <div class="card-body">
                                            <ul class="list-unstyled">
                                                <li class="mb-2">
                                                    <i class="fas fa-check-circle text-success me-2"></i>
                                                    <strong>Complexitate 1-10:</strong> Cod simplu, ușor de menținut
                                                </li>
                                                <li class="mb-2">
                                                    <i class="fas fa-exclamation-circle text-warning me-2"></i>
                                                    <strong>Complexitate 11-20:</strong> Cod moderat, necesită atenție pentru refactorizare
                                                </li>
                                                <li class="mb-2">
                                                    <i class="fas fa-times-circle text-danger me-2"></i>
                                                    <strong>Complexitate >20:</strong> Cod foarte complex, refactorizare urgentă recomandată
                                                </li>
                                            </ul>
                                            {f'<div class="alert alert-warning mt-3"><i class="fas fa-exclamation-triangle me-2"></i><strong>Atenție:</strong> {high_complexity} fișier(e) au complexitate ridicată și necesită refactorizare.</div>' if high_complexity > 0 else '<div class="alert alert-success mt-3"><i class="fas fa-check me-2"></i><strong>Excelent:</strong> Toate fișierele au complexitate acceptabilă!</div>'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Grafic distribuția complexității
            const ctx = document.getElementById('complexityChart').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: ['Scăzută (≤10)', 'Moderată (11-20)', 'Ridicată (>20)'],
                    datasets: [{{
                        data: [{low_complexity}, {medium_complexity}, {high_complexity}],
                        backgroundColor: ['#28a745', '#ffc107', '#dc3545'],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return html_template

def print_report(metrics: ProjectMetrics):
    """Afișează raportul de complexitate în consolă"""
    print("\n" + "="*60)
    print("RAPORT COMPLEXITATE PROIECT ARDUINO")
    print("="*60)
    
    print(f"\n📊 STATISTICI GENERALE:")
    print(f"   Fișiere analizate: {metrics.total_files}")
    print(f"   Linii de cod total: {metrics.total_loc}")
    print(f"   Linii de comentarii: {metrics.total_comments}")
    print(f"   Linii goale: {metrics.total_blank_lines}")
    print(f"   Funcții totale: {metrics.total_functions}")
    
    print(f"\n🔍 COMPLEXITATE:")
    print(f"   Complexitate medie: {metrics.average_complexity}")
    print(f"   Complexitate maximă: {metrics.max_complexity}")
    
    # Clasifica complexitatea
    if metrics.max_complexity <= 10:
        complexity_level = "🟢 SCĂZUTĂ"
    elif metrics.max_complexity <= 20:
        complexity_level = "🟡 MODERATĂ"
    else:
        complexity_level = "🔴 RIDICATĂ"
    
    print(f"   Nivel complexitate: {complexity_level}")
    
    print(f"\n📁 DETALII FIȘIERE:")
    print("-" * 60)
    
    # Sortează fișierele după complexitate
    sorted_files = sorted(metrics.files_metrics, key=lambda x: x.cyclomatic_complexity, reverse=True)
    
    for fm in sorted_files:
        if fm.cyclomatic_complexity > 0:
            complexity_indicator = "🔴" if fm.cyclomatic_complexity > 20 else "🟡" if fm.cyclomatic_complexity > 10 else "🟢"
            print(f"{complexity_indicator} {fm.filename}")
            print(f"   LOC: {fm.lines_of_code}, Complexitate: {fm.cyclomatic_complexity}, "
                  f"Funcții: {fm.functions_count}, Adâncime: {fm.nested_depth}")
            if fm.functions_count > 0:
                print(f"   Complexitate max/medie funcție: {fm.max_function_complexity}/{fm.average_function_complexity}")
            print()

def main():
    parser = argparse.ArgumentParser(description='Analizează complexitatea codului unui proiect Arduino PlatformIO')
    parser.add_argument('project_path', help='Calea către proiectul PlatformIO')
    parser.add_argument('--json', '-j', help='Salvează rezultatele în format JSON')
    parser.add_argument('--html', '-H', help='Generează raport HTML')
    parser.add_argument('--threshold', '-t', type=int, default=10, 
                       help='Pragul de complexitate pentru avertismente (default: 10)')
    parser.add_argument('--project-name', '-n', default="Arduino Project",
                       help='Numele proiectului pentru raportul HTML')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.project_path):
        print(f"Eroare: Directorul {args.project_path} nu există!")
        return
    
    analyzer = CodeComplexityAnalyzer()
    metrics = analyzer.analyze_project(args.project_path)
    
    if metrics.total_files == 0:
        print("Nu s-au găsit fișiere pentru analiză!")
        return
    
    # Afișează raportul în consolă
    print_report(metrics)
    
    # Avertismente
    print(f"\n⚠️  AVERTISMENTE (prag: {args.threshold}):")
    high_complexity_files = [fm for fm in metrics.files_metrics 
                           if fm.cyclomatic_complexity > args.threshold]
    
    if high_complexity_files:
        for fm in high_complexity_files:
            print(f"   • {fm.filename}: complexitate {fm.cyclomatic_complexity}")
    else:
        print("   Niciun fișier nu depășește pragul de complexitate!")
    
    # Salvează în JSON dacă e solicitat
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(asdict(metrics), f, indent=2, ensure_ascii=False)
        print(f"\n💾 Rezultatele au fost salvate în {args.json}")
    
    # Generează raportul HTML dacă e solicitat
    if args.html:
        project_name = args.project_name or os.path.basename(os.path.abspath(args.project_path))
        html_content = generate_html_report(metrics, project_name)
        
        with open(args.html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\n🌐 Raportul HTML a fost generat: {args.html}")
        
        # Încearcă să deschidă raportul în browser
        try:
            import webbrowser
            file_path = os.path.abspath(args.html)
            webbrowser.open(f'file://{file_path}')
            print(f"   Raportul s-a deschis în browser")
        except Exception as e:
            print(f"   Nu s-a putut deschide automat browserul: {e}")
            print(f"   Deschide manual fișierul: {os.path.abspath(args.html)}")

if __name__ == "__main__":
    main()