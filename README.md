# Arduino Project Analyzer 🔧📊

Un tool puternic în Python pentru analiza și inventarierea proiectelor Arduino C++. Generează rapoarte detaliate HTML cu statistici, grafice și structura proiectului.

## ✨ Funcționalități

### Funcționalități de bază
- **Scanare recursivă** a tuturor fișierelor din proiect
- **Filtrare inteligentă** a fișierelor relevante (.cpp, .h, .ino, etc.)
- **Numărare precisă** a liniilor de cod, comentarii și linii goale
- **Structura proiectului** în format arbore vizual
- **Statistici complete** cu totaluri și distribuții

### Analiză avansată
- **Detectarea funcțiilor** și numărul acestora per fișier
- **Inventarierea include-urilor** și dependințelor
- **Identificarea define-urilor** și macro-urilor
- **Tracking TODO/FIXME** comentarii pentru dezvoltare
- **Analiza complexității** codului
- **Informații fișiere** (mărime, data modificării)

### Raportare HTML
- **Raport HTML interactiv** cu design modern
- **Grafice vizuale** (matplotlib) pentru distribuții
- **Tabele sortabile** cu detalii complete
- **Responsive design** pentru toate dispozitivele
- **Export în multiple formate**

### Filtrare inteligentă
- **Excludere automată** .git, build, libraries
- **Configurație personalizabilă** prin JSON
- **Detectare tip proiect** (Arduino, PlatformIO, ESP32)
- **Suport multiple extensii** de fișiere

## 🚀 Instalare

### Cerințe
- Python 3.6+
- matplotlib
- pathlib (inclus în Python 3.4+)

### Instalare dependințe
```bash
pip install matplotlib
```

### Descărcare
Salvează scriptul `arduino_analyzer.py` și `config.json` în același folder.

## 📖 Utilizare

### Comanda de bază
```bash
python arduino_analyzer.py /path/to/your/arduino/project
```

### Opțiuni disponibile
```bash
python arduino_analyzer.py [project_path] [options]

Options:
  --config CONFIG       Fișier de configurație JSON personalizat
  --output OUTPUT       Numele fișierului HTML de ieșire (default: project_report.html)
  --no-html            Nu genera raportul HTML, doar afișează în consolă
  -h, --help           Afișează acest mesaj de ajutor
```

### Exemple de utilizare

#### Analiză simplă
```bash
python arduino_analyzer.py ./my_arduino_project
```

#### Cu configurație personalizată
```bash
python arduino_analyzer.py ./IoT_Project --config my_config.json
```

#### Raport personalizat
```bash
python arduino_analyzer.py ./RobotController --output robot_report.html
```

#### Doar consolă (fără HTML)
```bash
python arduino_analyzer.py ./QuickTest --no-html
```

## ⚙️ Configurație

Fișierul `config.json` permite personalizarea completă:

```json
{
  "extensions": [".cpp", ".c", ".h", ".hpp", ".ino"],
  "exclude_dirs": [".git", ".vscode", "build", "libraries"],
  "exclude_files": ["*.tmp", "*.bak", "*.log"],
  "project_types": {
    "arduino": [".ino"],
    "platformio": ["platformio.ini"],
    "esp32": ["sdkconfig"]
  }
}
```

### Opțiuni configurabile
- **extensions**: Extensiile de fișiere de analizat
- **exclude_dirs**: Directoare de exclus din analiză
- **exclude_files**: Tipuri de fișiere de ignorat
- **project_types**: Indicatori pentru detectarea tipului de proiect

## 📊 Tipuri de analiză

### Statistici generate
- **Numărul total de fișiere** și linii
- **Distribuția codului** (cod vs comentarii vs linii goale)
- **Inventarul funcțiilor** identificate automat
- **Lista include-urilor** și dependințelor
- **Macro-uri și define-uri** folosite
- **TODO/FIXME tracking** pentru dezvoltare
- **Mărimea proiectului** și folosirea spațiului

### Grafice generate
1. **Distribuția liniilor per fișier** (top 10)
2. **Tipurile de fișiere** (pie chart)
3. **Cod vs Comentarii vs Linii goale** (bar chart)

### Detectare automată tip proiect
- **Arduino Sketch** (.ino files)
- **PlatformIO** (platformio.ini)
- **CMake projects** (CMakeLists.txt)
- **ESP32/ESP8266** (sdkconfig)
- **Makefile projects**

## 📁 Structura output

```
project_report.html          # Raportul principal
charts/                      # Graficele generate
├── lines_distribution.png   # Distribuția liniilor
├── file_types.png          # Tipuri de fișiere
└── line_types.png          # Tipuri de linii
```

## 🎯 Exemple practice

### Pentru proiect Arduino simplu
```bash
python arduino_analyzer.py ./BlinkLED
```
**Output**: Analiză rapidă cu statistici de bază și raport HTML.

### Pentru proiect IoT complex
```bash
python arduino_analyzer.py ./IoT_Weather_Station --config iot_config.json --output weather_analysis.html
```
**Output**: Raport detaliat cu analiza dependințelor și tracking TODO-uri.

### Pentru development rapid
```bash
python arduino_analyzer.py ./TestProject --no-html
```
**Output**: Statistici rapid în consolă pentru dezvoltare iterativă.

## 🔍 Interpretarea rezultatelor

### În consolă
```
📊 REZUMAT PROIECT: MyArduinoProject
====================================
📁 Fișiere analizate: 8
📄 Total linii: 1,247
💻 Linii de cod: 892
💬 Linii comentarii: 203
🔧 Funcții găsite: 23
📦 Include-uri: 15
⚠️  TODO/FIXME: 5
💾 Mărime totală: 45.2 KB
```

### În raportul HTML
- **Statistici vizuale** cu carduri colorate
- **Grafice interactive** pentru distribuții
- **Tabel sortabil** cu toate fișierele
- **Structura arbore** pentru navigare
- **Lista TODO-urilor** pentru tracking

## ⚡ Performance

- **Rapid**: Analizează ~1000 fișiere în <5 secunde
- **Memorie eficientă**: Procesare streaming pentru proiecte mari
- **Scalabil**: Funcționează cu proiecte de orice mărime

## 🛠️ Dezvoltare și extensii

### Adăugarea de noi tipuri de fișiere
Editează `config.json`:
```json
{
  "extensions": [".cpp", ".c", ".h", ".hpp", ".ino", ".pde", ".cc"]
}
```

### Personalizarea excluderilor
```json
{
  "exclude_dirs": [".git", "build", "my_custom_folder"],
  "exclude_files": ["*.backup", "*.old"]
}
```

## 🐛 Troubleshooting

### Erori comune

**ModuleNotFoundError: No module named 'matplotlib'**
```bash
pip install matplotlib
```

**Permission denied**
```bash
chmod +x arduino_analyzer.py
```

**Encoding errors**
- Scriptul gestionează automat encoding-ul UTF-8 și ignoră caracterele problematice

**Fișiere mari**
- Pentru proiecte foarte mari (>10k fișiere), folosește `--no-html` pentru analiză rapidă

## 📝 Licență

MIT License - vezi fișierul LICENSE pentru detalii.

## 🤝 Contribuții

Contribuțiile sunt binevenite! Te rog să:
1. Fork repository-ul
2. Creează un branch pentru feature
3. Commit modificările
4. Push și creează Pull Request

## 📞 Support

Pentru probleme sau întrebări:
- Creează un Issue în repository
- Verifică documentația de troubleshooting
- Consultă exemplele de utilizare

---

**Autor**: Arduino Project Analyzer Team  
**Versiune**: 1.0.0  
**Data**: 2025