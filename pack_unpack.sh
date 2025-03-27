#!/bin/bash

#Variables
DOMAIN_NAME=PostventaEAI_001
JAR_FILE_NAME=PostventaEAI_001.jar
COMMON_DIR="/u01/oracle/product/wls12214/oracle_common/common/bin"
DOMAIN_DIR="/u01/oracle/domains"
NODE_USER=
NODE_IP=


error_acceso_directorio(){
    echo "Error: ($?) $1"
    exit 1
}

#=====ADMIN=====
#TODO: AGREGAR PARA N NODOS 

echo '===== Iniciando el enpaquetado..... ====='

cd "$COMMON_DIR" || error_acceso_directorio

/pack.sh -domain="$DOMAIN_DIR/$DOMAIN_NAME" -template="$DOMAIN_DIR/$JAR_FILE_NAME" -managed=true -template_name="$DOMAIN_NAME"

echo '==== Copiando el pack generado ====='

cd "$DOMAIN_DIR" || error_acceso_directorio
cp "$JAR_FILE_NAME" /home/weblogic

echo '==== Transfierdon el pack al nodo ====='

#validamos si el archivo se encutra
if [ ! -f "$JAR_FILE_NAME" ]; then
    echo "El archivo no existe"
    exit 1
else
    echo "El archivo se encuentra en el directorio"
fi

scp "/home/weblogic/$JAR_FILE_NAME" "$NODE_USER@$NODE_IP:/home/weblogic"


echo '==== Iniciando el unpack..... ===='

ssh ${NODE_USER}@${NODE_IP} 'bash -s' < unpack.sh


#====================================================
#!/bin/bash

#Variables
DOMAIN_NAME=PostventaEAI_001
JAR_FILE_NAME=PostventaEAI_001.jar
COMMON_DIR="/u01/oracle/product/wls12214/oracle_common/common/bin"
DOMAIN_DIR="/u01/oracle/domains"


error_acceso_directorio(){
    echo "Error: ($?) $1"
    exit 1
}


cd "$COMMON_DIR"
./unpack.sh -domain="/filestore/$DOMAIN_NAME" -template="/home/weblogic/$JAR_FILE_NAME"

echo '==== Modificando el nodemananger.properties'

cd "/filestore/$DOMAIN_NAME/nodemanager" || error_acceso_directorio

sed -i 's/SecureListener=true/SecureListener=false/' nodemananger.properties


echo '==== Levantando el nodo ===='

cd .. 
cd bin/
./startNodeManager.sh & tail -f nohup.out





#scp script_local.sh usuario@servidor:~/ && ssh usuario@servidor 'bash ~/script_local.sh'
