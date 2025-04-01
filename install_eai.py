import os
import sys
from os.path import exists
from sys import argv

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def parsefile():
    propfile = get_script_path() + "/domain.properties"
    if exists(propfile):
        global _dict
        _dict = {}
        with open(propfile, 'r') as fo:
            lines = fo.readlines()
            for line in lines:
                if "=" in line and not line.strip().startswith('#'):
                    line = line.rstrip()
                    key = line.split('=')[0].strip()
                    value = line.split('=')[1].strip()
                    _dict[key] = value

def printdomain():
    print('\n------------------------------')
    print("Properties Information")
    print('------------------------------')
    for key, val in _dict.items():
        if 'password' in key.lower():
            print(f"{key} => {'*' * len(val)}")
        else:
            print(f"{key} => {val}")

def export_properties():
    global mwhome, wlshome, domainroot, approot
    global domainName, domain_username, domain_password, domain_confirm_password
    global adminPort, adminAddress, machines, servers, clusters
    
    mwhome = _dict.get('mwhome')
    wlshome = _dict.get('wlshome')
    domainroot = _dict.get('domainroot')
    approot = _dict.get('approot')
    domainName = _dict.get('domain_name')
    domain_username = _dict.get('domain_username')
    domain_password = _dict.get('domain_password')
    domain_confirm_password = _dict.get('domain_confirm_password')
    adminPort = _dict.get('admin.port')
    adminAddress = _dict.get('admin.address')
    machines = _dict.get('machines', '').split(',')
    servers = _dict.get('managedservers', '').split(',')
    clusters = _dict.get('clusters', '').split(',')

def validate_domain_properties():
    required_keys = [
        'mwhome', 'wlshome', 'domainroot',
        'domain_name', 'domain_username', 'domain_password',
        'admin.port', 'admin.address'
    ]
    
    missing_keys = [key for key in required_keys if key not in _dict]
    if missing_keys:
        print(f"ERROR: Faltan propiedades obligatorias: {', '.join(missing_keys)}")
        sys.exit(1)
        
    if _dict.get('domain_password') != _dict.get('domain_confirm_password'):
        print("ERROR: La contraseña y su confirmación no coinciden")
        sys.exit(1)

def configure_datasources():
    try:
        print("\nConfigurando DataSources para componentes OSB...")
        
        # Configuración común para todos los DataSources
        db_url = _dict.get('database.url')
        db_driver = 'oracle.jdbc.OracleDriver'
        test_query = 'SQL SELECT 1 FROM DUAL'
        
        # Lista de componentes que necesitan DataSources
        components = ['SOAINFRA', 'ORASDPM', 'ORASDPS', 'MDS', 'OPSS']
        
        for component in components:
            schema_prefix = _dict.get('rcu.schema_prefix', 'OSB')
            schema_user = f"{schema_prefix}_{component}"
            schema_password = _dict.get('database.schema.password')
            
            print(f"\nCreando DataSource para {component}...")
            
            cd('/')
            create(f'{component}_DataSource', 'JDBCSystemResource')
            cd(f'/JDBCSystemResources/{component}_DataSource/JDBCResource/{component}_DataSource')
            create('myJdbcParams', 'JDBCConnectionPoolParams')
            set('DriverName', db_driver)
            set('URL', db_url)
            set('User', schema_user)
            set('Password', schema_password)
            set('TestTableName', test_query)
            
            print(f"DataSource {component}_DataSource configurado")
            
    except Exception as e:
        print(f"ERROR al configurar DataSources: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def read_template():
    try:
        template_path = _dict.get('template')
        if not template_path:
            template_path = f"{mwhome}/osb/common/templates/wls/osb.jar"
            
        print(f"\nLeyendo template desde: {template_path}")
        readTemplate(template_path)
    except:
        print("Error leyendo el template")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(2)

def create_machine():
    try:
        cd('/')
        for machine in machines:
            if not machine: continue
            
            print("\nCreando nueva máquina...")
            machine_name = _dict.get(f"{machine}.Name")
            if machine_name:
                create(machine_name, 'Machine')
                print(f"Máquina creada: {machine_name}")
            else:
                print(f"No se especificó nombre para la máquina {machine}")
    except:
        print("Error creando máquina")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(2)

def create_admin():
    try:
        print("\nConfigurando AdminServer...")
        
        cd('/Security/base_domain/User/' + domain_username)
        cmo.setPassword(domain_password)
        
        cd('/Servers/AdminServer')
        cmo.setName('AdminServer')
        cmo.setListenPort(int(adminPort))
        cmo.setListenAddress(adminAddress)
        
        print(f"AdminServer configurado en {adminAddress}:{adminPort}")
    except:
        print("Error configurando AdminServer")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def create_managedserver():
    try:
        cd('/')
        for server in servers:
            if not server: continue
            
            server_name = _dict.get(f"{server}.Name")
            server_port = _dict.get(f"{server}.port")
            server_address = _dict.get(f"{server}.address")
            
            if server_name and server_port and server_address:
                print(f"\nCreando Managed Server: {server_name}")
                create(server_name, 'Server')
                cd(f'/Servers/{server_name}')
                cmo.setListenPort(int(server_port))
                cmo.setListenAddress(server_address)
                print(f"Managed Server {server_name} creado en {server_address}:{server_port}")
    except:
        print("Error creando Managed Server")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def create_clusters():
    try:
        cd('/')
        for cluster in clusters:
            if not cluster: continue
            
            cluster_name = _dict.get(f"{cluster}.Name")
            if cluster_name:
                print(f"\nCreando cluster: {cluster_name}")
                create(cluster_name, 'Cluster')
                print(f"Cluster {cluster_name} creado")
    except:
        print("Error creando cluster")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(2)

def commit_writedomain():
    try:
        print("\nGuardando configuración del dominio...")
        setOption('OverwriteDomain', 'true')
        setOption('ServerStartMode', 'prod')
        setOption('AppDir', approot + '/' + domainName)
        writeDomain(domainroot + '/' + domainName)
        closeTemplate()
        print(f"Dominio {domainName} creado en {domainroot}")
    except:
        print("Error guardando dominio")
        print("Dumpstack: \n -------------- \n", dumpStack())
        undo('false', 'y')
        stopEdit()
        sys.exit(1)

def start_AdminServer():
    try:
        print("\nIniciando AdminServer...")
        domain_path = domainroot + '/' + domainName
        managementurl = f"t3://{adminAddress}:{adminPort}"
        log_file = f"{domain_path}/servers/AdminServer/logs/AdminServer.log"
        
        print(f"URL de gestión: {managementurl}")
        print(f"Log file: {log_file}")
        
        startServer('AdminServer', domainName, managementurl, 
                   domain_username, domain_password, 
                   domain_path, 'true', 60000, serverLog=log_file)
        
        print("AdminServer iniciado correctamente")
    except:
        print("Error iniciando AdminServer")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

if __name__ != "__main__":
    print("\n=== Inicio de creación de dominio OSB ===")
    
    # Paso 1: Leer y validar propiedades
    parsefile()
    export_properties()
    validate_domain_properties()
    printdomain()
    
    # Paso 2: Crear dominio desde template
    read_template()
    
    # Paso 3: Configurar componentes
    create_machine()
    create_admin()
    create_managedserver()
    create_clusters()
    
    # Paso 4: Configurar DataSources para OSB
    configure_datasources()
    
    # Paso 5: Guardar dominio
    commit_writedomain()
    
    # Paso 6: Iniciar AdminServer
    start_AdminServer()
    
    print("\n=== Dominio OSB creado exitosamente ===")
    sys.exit(0)

if __name__ == "__main__":
    print("Este script debe ejecutarse con WLST de WebLogic")
    print("Uso: wlst.sh create_osb_domain.py")