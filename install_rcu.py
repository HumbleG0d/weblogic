import os
import sys
from os.path import exists
from sys import argv

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def parse_rcu_properties():
    propfile = get_script_path() + "/rcu.properties"
    if exists(propfile):
        global rcu_props
        rcu_props = {}
        with open(propfile, 'r') as fo:
            lines = fo.readlines()
            for line in lines:
                if "=" in line and not line.strip().startswith('#'):
                    line = line.rstrip()
                    key = line.split('=')[0].strip()
                    value = line.split('=')[1].strip()
                    rcu_props[key] = value

def validate_rcu_properties():
    required_keys = [
        'database.type',
        'database.connectString',
        'database.user',
        'database.password',
        'rcu.prefix',
        'rcu.components'
    ]
    
    missing_keys = [key for key in required_keys if key not in rcu_props]
    if missing_keys:
        print(f"ERROR: Faltan propiedades obligatorias en rcu.properties: {', '.join(missing_keys)}")
        sys.exit(1)
        
    if not rcu_props['database.connectString'].startswith('jdbc:oracle:thin:@//'):
        print("ERROR: Formato incorrecto de database.connectString. Debe ser: jdbc:oracle:thin:@//host:port/service")
        sys.exit(1)

def print_rcu_summary():
    print('\n------------------------------')
    print("RCU Configuration Summary")
    print('------------------------------')
    for key, val in rcu_props.items():
        if 'password' in key.lower():
            print(f"{key} => {'*' * len(val)}")
        else:
            print(f"{key} => {val}")

def add_tablespace_mapping(rcu_command):
    tablespaces = {
        "STB": "OSB1QADB_STB",
        "OPSS": "OSB1QADB_OPSS",
        "UMS": "OSB1QADB_UMS",
        "IAU": "IAU_TBLSP",
        "IAU_APPEND": "OSB1QADB_IAU_APPEND",
        "IAU_VIEWER": "OSB1QADB_IAU_VIEWER",
        "MDS": "OSB1QADB_MDS",
        "WLS": "OSB1QADB_WLS",
        "SOAINFRA": "OSB1QADB_SOAINFRA"
    }
    
    for component, tablespace in tablespaces.items():
        rcu_command.extend(['-componentTablespaceMap', f'{component}:{tablespace}'])
    
    return rcu_command 

def execute_rcu():
    rcu_command = [
        rcu_props.get('rcu.home', '/u01/oracle/product/osb12214/oracle_common/bin/rcu'),
        '-silent',
        '-createRepository',
        '-databaseType', rcu_props['database.type'],
        '-connectString', rcu_props['database.connectString'],
        '-dbUser', rcu_props['database.user'],
        '-dbRole', 'SYSDBA',
        '-schemaPrefix', rcu_props.get('rcu.prefix'),
        '-component', rcu_props['rcu.components'],
        '-f'
    ]
    
    if 'database.password' in rcu_props:
        rcu_command.extend(['-databasePassword', rcu_props['database.password']])

    rcu_command = add_tablespace_mapping(rcu_command)
    
    print("\nEjecutando RCU con los siguientes parámetros:")
    print(' '.join(rcu_command[:4]) + ' ' + ' '.join(['*' * 8 if 'password' in arg.lower() else arg for arg in rcu_command[4:]]))
    
    try:
        # Ejecutar comando RCU
        os.environ['RCU_LOG_LOCATION'] = '/tmp/rcu_logs'
        os.makedirs('/tmp/rcu_logs', exist_ok=True)
        
        import subprocess
        process = subprocess.Popen(rcu_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"ERROR en la ejecución de RCU:\n{stderr.decode()}")
            sys.exit(1)
            
        print("\nRCU ejecutado exitosamente")
        print(stdout.decode())
        
    except Exception as e:
        print(f"ERROR al ejecutar RCU: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("\n=== Script de instalación automática de RCU ===")
    
    # Paso 1: Leer propiedades
    print("\nLeyendo archivo rcu.properties...")
    parse_rcu_properties()
    
    # Paso 2: Validar propiedades
    print("Validando propiedades...")
    validate_rcu_properties()
    
    # Paso 3: Mostrar resumen
    print_rcu_summary()
    
    # Paso 4: Ejecutar RCU
    print("\nIniciando instalación de RCU...")
    execute_rcu()
    
    print("\n=== Proceso completado ===")
