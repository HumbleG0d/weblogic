#!/bin/bash

# Variables
SCRIPT_PYTHON=script_domain_eai.py
PROPERTIES=domain_eai.properties
DOMAIN_NAME=PostventaEAI_001
ARCHIVO=_WLS_ADMINSERVER000000.DAT
USERNAME=weblogic
PASSWORD=weblogic1
DOMAINS_DIR="/u01/oracle/domains"
SCRIPT_DIR="/var/tmp/script"
WL_BIN_DIR="/u01/oracle/product/wls12214/wlserver/server/bin"

# Función para manejar errores al acceder a directorios
error_acceso_directorio(){
    echo "Error: ($?) $1"
    exit 1
}

# Función para manejar el error al crear un directorio
error_creacion_directorio(){
    if [ $? -ne 0 ]; then
        echo "Error: Falló al crear el directorio: ${LINENO}"
        exit 1
    fi
}

# Función para manejar la ejecucuion del script del dominio
error_instalacion_dominio(){
    if [ $? -ne 0 ]; then
        echo "Error: Falló la instalación del dominio."
        exit 1
    fi
}

echo '===== Creación de la carpeta script ====='

mkdir -p "$SCRIPT_DIR" || error_creacion_directorio

echo 'Directorio creado exitosamente'

echo '===== Copiando los archivos subidos ====='

cd /home/weblogic || error_acceso_directorio "No se pudo acceder al directorio: ${LINENO}"

cp "$SCRIPT_PYTHON" "$SCRIPT_DIR"
cp "$PROPERTIES" "$SCRIPT_DIR"

echo '===== Estableciendo el entorno ====='

cd "$WL_BIN_DIR" || error_acceso_directorio "No se pudo acceder al directorio: ${LINENO}"

. ./setWLSEnv.sh

echo '===== Instalando el dominio ====='

java weblogic.WLST "$SCRIPT_DIR/$SCRIPT_PYTHON"


echo '==== Eliminación del proceso _WLS_ADMINSERVER.DAT ===='

cd "$DOMAINS_DIR/$DOMAIN_NAME/servers/AdminServer/data/store/default" || error_acceso_directorio "No se pudo acceder al directorio: ${LINENO}"


PID=123

while [ -n "$PID" ]; do #Si PID no es vacio , entonces
    PID=$(lsof | grep "$ARCHIVO" | awk '{print $2}')
    if [ -n "$PID" ]; then #Si PID no es vacio , entonces matamos
        echo 'Proceso encontrado. Matando proceso......'
        kill -9 $PID
        #break
    else
        echo 'No se encontraron procesos. Continuando...'
        break
    fi
done

echo '==== Levantamiento de la consola en segundo plano ===='

cd "$DOMAINS_DIR/$DOMAIN_NAME/servers/AdminServer" || error_acceso_directorio "No se pudo acceder al directorio: ${LINENO}"

mkdir -p security || error_creacion_directorio
echo 'Directorio creado exitosamente'

cd security || error_acceso_directorio "No se pudo acceder al directorio: ${LINENO}"

touch boot.properties
echo -e "username=$USERNAME" > boot.properties
echo -e "password=$PASSWORD" >> boot.properties

cd "$DOMAINS_DIR/$DOMAIN_NAME"

./startWebLogic.sh & tail -f nohup.out

echo '==== Instalación exitosa ===='
