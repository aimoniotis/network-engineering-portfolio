@echo off
:: Optional – show timestamp when the task starts
echo Task started at %DATE% %TIME%

:: Run backup script SSH
echo Running backup script...
%PYTHON_EXEC% "C:\your\path\to\SSH_Backup_Script.py"

:: Run backup script TELNET
echo Running backup script...
%PYTHON_EXEC% "C:\your\path\to\Telnet_Backup_Script.py"

:: Run report generation script
echo Generating backup report...
%PYTHON_EXEC% "C:\your\path\to\generate_report.py" >> "C:\your\path\to\report_log.txt"

echo Task completed at %DATE% %TIME%
pause