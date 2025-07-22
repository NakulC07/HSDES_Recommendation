@echo off

REM Run GENI token generator
python geni_token_generator.py

REM Run NGA_Extraction_runner.py
python NGA_Extraction_runner.py

REM Run Extraction_Daily_runner.py
python Extraction_Daily_runner.py

REM Run Error_lookup_runner.py
python Error_lookup_runner.py
