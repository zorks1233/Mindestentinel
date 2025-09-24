@echo off
REM Mindestentinel - Projektstruktur Setup (Windows Batch)
REM Ausführen: doppelklick oder in cmd: setup_project.bat

SET ROOT=%~dp0Mindestentinel
echo Erzeuge Projektverzeichnis: %ROOT%

REM Hauptverzeichnisse
mkdir "%ROOT%"
cd /d "%ROOT%"

mkdir config
mkdir data
mkdir data\models
mkdir data\models\pretrained
mkdir data\models\custom
mkdir data\models\external
mkdir data\raw_data
mkdir data\knowledge
mkdir logs
mkdir docs
mkdir plugins
mkdir scripts
mkdir admin_console
mkdir admin_console\commands
mkdir src
mkdir src\core
mkdir src\modules
mkdir src\modules\utils
mkdir src\api
mkdir src\admin
mkdir src\simulation
mkdir tests

REM Erzeuge Dateien in config
echo # Hauptkonfiguration > config\config.yaml
echo # Regeln/Gesetze > config\rules.yaml
echo # Zusätzliche Einstellungen > config\settings.yaml
echo # Quantum Einstellungen > config\quantum.yml

REM Lege README, LICENSE, requirements an
echo Mindestentinel - Alpha Projekt > README.md
echo MIT License > LICENSE
echo python>=3.12> requirements.txt

REM Leere Dateien in src/core
echo # core package > src\core\__init__.py
echo # ai_engine > src\core\ai_engine.py
echo # self_learning > src\core\self_learning.py
echo # knowledge_base > src\core\knowledge_base.py
echo # task_management > src\core\task_management.py
echo # system_monitor > src\core\system_monitor.py
echo # data_compression > src\core\data_compression.py
echo # optimization > src\core\optimization.py
echo # quantum_computing > src\core\quantum_computing.py
echo # neural_quantum > src\core\neural_quantum.py
echo # cognitive_core > src\core\cognitive_core.py
echo # rule_engine > src\core\rule_engine.py
echo # protection_module > src\core\protection_module.py
echo # vision_audio > src\core\vision_audio.py
echo # data_ingestion > src\core\data_ingestion.py
echo # quantum_core > src\core\quantum_core.py

REM Leere Dateien in src/modules and utils
echo # utils package > src\modules\__init__.py
echo # file utils > src\modules\utils\file_utils.py
echo # gpu utils > src\modules\utils\gpu_utils.py
echo # cpu utils > src\modules\utils\cpu_utils.py
echo # ram utils > src\modules\utils\ram_utils.py
echo # image utils > src\modules\utils\image_utils.py
echo # audio utils > src\modules\utils\audio_utils.py
echo # compression utils > src\modules\utils\compression_utils.py
echo # security utils > src\modules\utils\security_utils.py

REM API
echo # api package > src\api\__init__.py
echo # rest api > src\api\rest_api.py
echo # websocket api > src\api\websocket_api.py
echo # auth > src\api\auth.py
echo # api utils > src\api\api_utils.py

REM Admin & Simulation & Modules
echo # admin package > src\admin\__init__.py
echo # admin console > src\admin\admin_console.py
echo # monitor > src\admin\monitor.py
echo # diagnostics > src\admin\diagnostics.py

echo # simulation package > src\simulation\__init__.py
echo # world sim > src\simulation\world_sim.py
echo # skill sim > src\simulation\skill_sim.py

REM Plugins
echo # plugins init > plugins\__init__.py
echo # example plugin > plugins\example_plugin.py
echo # vision plugin > plugins\vision_plugin.py
echo # audio plugin > plugins\audio_plugin.py
echo # external model plugin > plugins\external_model_plugin.py
echo # huggingface plugin > plugins\huggingface_plugin.py

REM Admin console commands
echo # start_model command > admin_console\commands\start_model.py
echo # stop_model command > admin_console\commands\stop_model.py
echo # optimize_model command > admin_console\commands\optimize_model.py
echo # load_plugin command > admin_console\commands\load_plugin.py
echo # run_simulation command > admin_console\commands\run_simulation.py
echo # monitor_ai command > admin_console\commands\monitor_ai.py
echo # quantum_control command > admin_console\commands\quantum_control.py

REM Scripts
echo # start_ai script > scripts\start_ai.sh
echo # train_model > scripts\train_model.py
echo # compress_data > scripts\compress_data.py
echo # generate_reports > scripts\generate_reports.py
echo # optimize_ai > scripts\optimize_ai.py
echo # quantum_run > scripts\quantum_run.py

REM Tests
echo # tests init > tests\__init__.py
echo # test placeholders > tests\test_ai_brain.py
echo # test placeholders > tests\test_self_learning.py
echo # test placeholders > tests\test_rule_engine.py
echo # test placeholders > tests\test_quantum.py
echo # test placeholders > tests\test_vision_audio.py

echo Fertig. Projektstruktur erstellt in %ROOT%
pause
