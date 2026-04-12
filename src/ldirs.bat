@echo off

REM --- 1. Log Generators ---
start cmd /k "cd /d %~dp0src\log_generators && python run_all_generators.py"

REM --- 2. Central Auth Service (port 3000) ---
start cmd /k "cd /d %~dp0src\auth_service && python app.py"

REM --- 3. Log Ingestion Service (port 8001) ---
start cmd /k "cd /d %~dp0src\log_ingestion_service && python app.py"

REM --- 4. Log Processing Service (port 8002) ---
start cmd /k "cd /d %~dp0src\log_processing_service && python app.py"

REM --- 5. Detection Service (port 8003) ---
start cmd /k "cd /d %~dp0src\detection_service && python app.py"

REM --- 6. Incident Management Service (port 8004) ---
start cmd /k "cd /d %~dp0src\incident_management && python app.py"

REM --- 7. Response Service (port 8005) ---
start cmd /k "cd /d %~dp0src\response_service && python app.py"

REM --- 8. Notification Service (port 8006) ---
start cmd /k "cd /d %~dp0src\notification_service && python app.py"

REM --- 9. Actuator Service (port 8007) ---
start cmd /k "cd /d %~dp0src\actuator_service && python app.py"

echo All services started in separate terminals!
pause