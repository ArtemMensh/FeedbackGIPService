#!/bin/bash

APP_NAME="flask_service"           # Название вашего приложения (можно изменить)
APP_DIR="/home/arttrit/FeedbackGIPService"        # Путь к вашему Flask приложению
APP_SCRIPT="main.py"                # Имя файла вашего Flask приложения
LOG_FILE="/home/arttrit/FeedbackGIPService/flask_service.log"  # Путь к файлу лога
PID_FILE="/tmp/flask_service.pid"      # PID файл для процесса

# Функция для запуска сервиса
start_service() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE"); then
        echo "$APP_NAME is already running." | tee -a "$LOG_FILE"
    else
        echo "Starting $APP_NAME..." | tee -a "$LOG_FILE"
        cd "$APP_DIR"
        nohup python3 "$APP_SCRIPT" > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "$APP_NAME started with PID $(cat $PID_FILE)." | tee -a "$LOG_FILE"
    fi
}

# Функция для остановки сервиса
stop_service() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE"); then
        echo "Stopping $APP_NAME..." | tee -a "$LOG_FILE"
        kill $(cat "$PID_FILE")
        rm -f "$PID_FILE"
        echo "$APP_NAME stopped." | tee -a "$LOG_FILE"
    else
        echo "$APP_NAME is not running." | tee -a "$LOG_FILE"
    fi
}

# Функция для проверки статуса сервиса
status_service() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE"); then
        echo "$APP_NAME is running with PID $(cat $PID_FILE)." | tee -a "$LOG_FILE"
    else
        echo "$APP_NAME is not running." | tee -a "$LOG_FILE"
    fi
}

# Функция для перезапуска сервиса
restart_service() {
    echo "Restarting $APP_NAME..." | tee -a "$LOG_FILE"
    stop_service
    start_service
}

# Логика команд
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
