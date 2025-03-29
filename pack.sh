#!/bin/bash

#Variables
DOMAIN_NAME=PostventaEAI_001
JAR_FILE_NAME=PostventaEAI_001.jar
UNPACK_FILE=unpack.sh
COMMON_DIR="/u01/oracle/product/wls12214/oracle_common/common/bin"
DOMAIN_DIR="/u01/oracle/domains"
NODE_USER=
NODE_IP=


error_acceso_directorio(){
    echo "Error: ($?) $1"
    exit 1
}

echo '===== Iniciando el enpaquetado..... ====='

cd "$COMMON_DIR" || error_acceso_directorio

/pack.sh -domain="$DOMAIN_DIR/$DOMAIN_NAME" -template="$DOMAIN_DIR/$JAR_FILE_NAME" -managed=true -template_name="$DOMAIN_NAME"

echo '==== Copiando el pack generado ====='

cd "$DOMAIN_DIR" || error_acceso_directorio
cp "$JAR_FILE_NAME" /home/weblogic

echo '==== Transfiriendo el pack .... ====='

deploy_to_node() {
    local NODE_IP=$1
    
    echo "[$(date '+%H:%M:%S')] Procesando nodo: $NODE_IP" | tee -a $LOG_FILE
    
    echo "==== Transfiriendo pack al nodo $NODE_IP ====" | tee -a $LOG_FILE

   ssh -tt -o StrictHostKeyChecking=no $NODE_USER@$NODE_IP << EOF
    echo "Autenticación exitosa en $NODE_IP"

    # Copiando archivos
    scp -o StrictHostKeyChecking=no "/home/weblogic/$JAR_FILE_NAME" "/home/weblogic/"
    scp -o StrictHostKeyChecking=no "/home/weblogic/$UNPACK_FILE" "/home/weblogic/"

    # Validar transferencia
    if [ ! -f "/home/weblogic/$JAR_FILE_NAME" ]; then
        echo "ERROR: Archivo no llegó a $NODE_IP"
        exit 1
    fi

    # Dar permisos de ejecución y ejecutar unpack
    chmod +x /home/weblogic/$UNPACK_FILE
    bash /home/weblogic/$UNPACK_FILE || {
        echo "ERROR: Unpack falló en $NODE_IP"
        exit 1
    }

    echo "Proceso completado en $NODE_IP"
EOF
}

echo "Inicio de despliegue: $(date)" | tee -a $LOG_FILE

if [ ! -f "/home/weblogic/$JAR_FILE_NAME" ]; then
    echo "ERROR: El archivo $JAR_FILE_NAME no existe en el Admin" | tee -a $LOG_FILE
    exit 1
fi

pids=()
for NODE_IP in "${NODES[@]}"; do
    deploy_to_node "$NODE_IP" &
    pids+=($!)
done

for pid in "${pids[@]}"; do
    wait "$pid" || {
        echo "ALERTA: Al menos un nodo falló" | tee -a $LOG_FILE
        exit 1
    }
done

echo "Despliegue completado en TODOS los nodos: $(date)" | tee -a $LOG_FILE