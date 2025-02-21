@echo off

REM Run NGA_DB_runner.py
python NGA_DB_runner.py

REM Run Extraction_DB_runner.py
python Extraction_DB_runner.py

REM Run HSDES_Extraction_runner.py
python HSDES_Extraction_runner.py

REM Run mlaas_runner.py
python mlaas_runner.py

REM Run Combine.py
python Combine.py

REM Run visualization_runner.py
python visualization_runner.py
