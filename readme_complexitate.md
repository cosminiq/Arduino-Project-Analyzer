python '.\Arduino Code Complexity Analyzer.py' C:\Users\cosmi\OneDrive\Desktop\Adafruit_RP2040\src   --html raport.html --json date.json --project-name "Senzor IoT" --threshold 15


Utilizare extinsă:
bash# Generează raport HTML
python arduino_complexity.py /path/to/project --html raport.html

# Raport complet cu JSON și HTML
python arduino_complexity.py /path/to/project \
  --html raport.html \
  --json date.json \
  --project-name "Senzor IoT" \
  --threshold 15
Caracteristicile raportului HTML:

Interfață profesională cu design modern
Codificare prin culori: verde (≤10), galben (11-20), roșu (>20)
Grafic tip donut pentru distribuția complexității
Tabel sortabil cu toate metricile
Recomandări bazate pe rezultate
Auto-deschidere în browser
Timestamp pentru urmărirea versiunilor

Scriptul se deschide automat în browser după generare și oferă o experiență vizuală completă pentru analiza complexității codului Arduino!