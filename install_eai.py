import os
import sys
from os.path import exists, join
from sys import argv

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def parsefile():
    propfile = join(get_script_path(), "domain.properties")
    if exists(propfile):
        global _dict
        _dict = {}
        with open(propfile, 'r') as fo:
            for line in fo:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    _dict[key.strip()] = value.strip()

def printdomain():
    print('\n' + '='*50)
    print("Resumen de Configuración".center(50))
    print('='*50)
    max_len = max(len(k) for k in _dict)
    for key, val in sorted(_dict.items()):
        if 'password' in key.lower():
            print(f"{key.ljust(max_len)} : {'*' * len(val)}")
        else:
            print(f"{key.ljust(max_len)} : {val}")

def validate_domain_properties():
    required_keys = [
        'mwhome', 'wlshome', 'domainroot', 'domain_name',
        'domain_username', 'domain_password', 'admin.port', 'admin.address',
        'database.url', 'database.schema.owner', 'database.schema.password'
    ]
    
    missing_keys = [key for key in required_keys if key not in _dict]
    if missing_keys:
        print(f"ERROR: Faltan propiedades obligatorias: {', '.join(missing_keys)}")
        sys.exit(1)
        
    if _dict.get('domain_password') != _dict.get('domain_confirm_password'):
        print("ERROR: La contraseña y su confirmación no coinciden")
        sys.exit(1)

def configure_database_connection():
    try:
        print("\nConfigurando conexión a base de datos RCU...")
        
        # Configuración común para todos los DataSources
        db_url = _dict['database.url']
        db_driver = 'oracle.jdbc.OracleDriver'
        test_query = 'SQL SELECT 1 FROM DUAL'
        
        # Verificar conexión a la base de datos
        if _dict.get('autoconfig.test_connections', 'true') == 'true':
            print("\nProbando conexión a la base de datos...")
            connect(_dict['database.schema.owner'], _dict['database.schema.password'], db_url)
            print("Conexión exitosa a la base de datos")
        
        # Configurar AutoConfiguration Options
        if _dict.get('autoconfig.enabled', 'true') == 'true':
            print("\nConfigurando AutoConfiguration usando datos RCU...")
            cd('/')
            create('AutoConfig', 'AutoConfig')
            cd('AutoConfig/AutoConfig')
            set('Vendor', _dict['database.vendor'])
            set('Url', db_url)
            set('SchemaOwner', _dict['database.schema.owner'])
            set('SchemaPassword', _dict['database.schema.password'])
            
            # Configurar componentes basados en RCU
            components = _dict.get('rcu.components', '').split(',')
            for component in components:
                if component:
                    schema_prefix = _dict.get('rcu.schema_prefix', 'DEV')
                    schema_user = f"{schema_prefix}_{component}"
                    print(f"\nConfigurando DataSource para {component}...")
                    
                    cd('/')
                    create(f'{component}_DataSource', 'JDBCSystemResource')
                    cd(f'/JDBCSystemResources/{component}_DataSource/JDBCResource/{component}_DataSource')
                    create('myJdbcParams', 'JDBCConnectionPoolParams')
                    set('DriverName', db_driver)
                    set('URL', db_url)
                    set('User', schema_user)
                    set('Password', _dict['database.schema.password'])
                    set('TestTableName', test_query)
                    
                    print(f"DataSource {component}_DataSource configurado")
        
    except Exception as e:
        print(f"ERROR en configuración de base de datos: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def create_domain_infrastructure():
    try:
        # Crear máquinas
        cd('/')
        machines = _dict.get('machines', '').split(',')
        for machine in machines:
            if machine and f"{machine}.Name" in _dict:
                print(f"\nCreando máquina {_dict[f'{machine}.Name']}...")
                create(_dict[f"{machine}.Name"], 'Machine')
        
        # Configurar AdminServer
        print("\nConfigurando AdminServer...")
        cd('/Security/base_domain/User/' + _dict['domain_username'])
        cmo.setPassword(_dict['domain_password'])
        
        cd('/Servers/AdminServer')
        cmo.setName('AdminServer')
        cmo.setListenPort(int(_dict['admin.port']))
        cmo.setListenAddress(_dict['admin.address'])
        
        # Crear Managed Servers
        servers = _dict.get('managedservers', '').split(',')
        for server in servers:
            if server and all(key in _dict for key in [f"{server}.Name", f"{server}.port", f"{server}.address"]):
                print(f"\nCreando Managed Server {_dict[f'{server}.Name']}...")
                create(_dict[f"{server}.Name"], 'Server')
                cd(f'/Servers/{_dict[f"{server}.Name"]}')
                cmo.setListenPort(int(_dict[f"{server}.port"]))
                cmo.setListenAddress(_dict[f"{server}.address"])
        
        # Crear Clusters
        clusters = _dict.get('clusters', '').split(',')
        for cluster in clusters:
            if cluster and f"{cluster}.Name" in _dict:
                print(f"\nCreando cluster {_dict[f'{cluster}.Name']}...")
                create(_dict[f"{cluster}.Name"], 'Cluster')
                
                # Asignar miembros al cluster
                if f"{cluster}.members" in _dict:
                    members = _dict[f"{cluster}.members"].split(',')
                    for member in members:
                        if member and f"{member}.Name" in _dict:
                            print(f"Asignando {_dict[f'{member}.Name']} al cluster...")
                            assign('Server', _dict[f"{member}.Name"], 'Cluster', _dict[f"{cluster}.Name"])
        
    except Exception as e:
        print(f"ERROR al crear infraestructura: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)
def load_templates():
    try:
        print("\nCargando templates...")
        
        # Obtener lista de templates habilitados
        enabled_templates = _dict.get('templates.enabled', 'OSB').split(',')
        
        for template_name in enabled_templates:
            template_key = f"template.{template_name}.path"
            if template_key in _dict:
                template_path = _dict[template_key]
                print(f"\nCargando template {template_name} desde: {template_path}")
                
                # Leer el template
                readTemplate(template_path)
                
                # Registrar componentes asociados
                components_key = f"template.{template_name}.components"
                if components_key in _dict:
                    print(f"Componentes incluidos: {_dict[components_key]}")
                
                print(f"Template {template_name} cargado exitosamente")
            else:
                print(f"Advertencia: No se encontró ruta para template {template_name}")
                
    except Exception as e:
        print(f"ERROR al cargar templates: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def configure_administration_server():
    try:
        print("\nConfigurando Administration Server...")
        
        cd('/Servers/AdminServer')
        
        # Configuración básica
        cmo.setName(_dict.get('admin.server.name', 'AdminServer'))
        cmo.setListenAddress(_dict['admin.server.listen_address'])
        cmo.setListenPort(int(_dict['admin.server.listen_port']))
        
        # Configuración SSL
        if _dict.get('admin.server.ssl_enabled', 'false').lower() == 'true':
            cmo.setSSLEnabled(true)
            cmo.setSSLListenPort(int(_dict.get('admin.server.ssl_port', '11001')))
        
        # Configuración de Server Groups
        server_groups = _dict.get('admin.server.server_groups', '').split(',')
        if server_groups and server_groups[0]:
            cmo.setServerGroups(server_groups)
        
        print(f"Administration Server configurado en {_dict['admin.server.listen_address']}:{_dict['admin.server.listen_port']}")
        
    except Exception as e:
        print(f"ERROR configurando Administration Server: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def configure_node_manager():
    try:
        print("\nConfigurando Node Manager...")
        
        cd('/')
        create('NodeManager', 'NodeManager')
        cd('NodeManager')
        
        # Configuración básica
        set('NMType', _dict.get('node.manager.type', 'Plain'))
        set('ListenAddress', _dict.get('node.manager.listen_address', _dict['admin.server.listen_address']))
        set('ListenPort', int(_dict.get('node.manager.listen_port', '5556')))
        
        # Credenciales
        set('Name', _dict.get('node.manager.username', 'weblogic'))
        set('Password', _dict.get('node.manager.password', _dict['domain_password']))
        
        print("Node Manager configurado exitosamente")
        
    except Exception as e:
        print(f"ERROR configurando Node Manager: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def configure_managed_servers():
    try:
        print("\nConfigurando Managed Servers (nodos)...")
        
        servers = _dict.get('managedservers', '').split(',')
        for server in servers:
            if not server:
                continue
                
            server_name = _dict.get(f"{server}.Name")
            if not server_name:
                continue
                
            print(f"\nConfigurando Managed Server: {server_name}")
            
            cd('/')
            create(server_name, 'Server')
            cd(f'/Servers/{server_name}')
            
            # Configuración básica
            cmo.setListenAddress(_dict[f"{server}.ListenAddress"])
            cmo.setListenPort(int(_dict[f"{server}.ListenPort"]))
            
            # Asignación a máquina
            machine_name = _dict.get(f"{server}.Machine")
            if machine_name:
                cmo.setMachine(getMBean(f'/Machines/{machine_name}'))
            
            # Configuración de Server Groups
            server_groups = _dict.get(f"{server}.ServerGroups", '').split(',')
            if server_groups and server_groups[0]:
                cmo.setServerGroups(server_groups)
            
            print(f"Managed Server {server_name} configurado en {_dict[f'{server}.ListenAddress']}:{_dict[f'{server}.ListenPort']}")
            
    except Exception as e:
        print(f"ERROR configurando Managed Servers: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def configure_clusters():
    try:
        print("\nConfigurando Clusters...")
        
        clusters = _dict.get('clusters', '').split(',')
        for cluster in clusters:
            if not cluster:
                continue
                
            cluster_name = _dict.get(f"{cluster}.Name")
            if not cluster_name:
                continue
                
            print(f"\nConfigurando Cluster: {cluster_name}")
            
            cd('/')
            create(cluster_name, 'Cluster')
            cd(f'/Clusters/{cluster_name}')
            
            # Configuración de dirección de cluster
            cluster_address = _dict.get(f"{cluster}.ClusterAddress")
            if cluster_address:
                cmo.setClusterAddress(cluster_address)
            
            # Configuración de mensajería
            messaging_mode = _dict.get(f"{cluster}.MessagingMode", 'unicast')
            cmo.setMessagingMode(messaging_mode)
            
            if messaging_mode == 'multicast':
                cmo.setMulticastAddress(_dict.get(f"{cluster}.MulticastAddress", '239.192.0.1'))
                cmo.setMulticastPort(int(_dict.get(f"{cluster}.MulticastPort", '7001')))
            
            # Asignación de miembros
            members = _dict.get(f"{cluster}.Members", '').split(',')
            for member in members:
                if member and _dict.get(f"{member}.Name"):
                    print(f"Asignando {_dict[f'{member}.Name']} al cluster...")
                    assign('Server', _dict[f"{member}.Name"], 'Cluster', cluster_name)
            
            print(f"Cluster {cluster_name} configurado exitosamente")
            
    except Exception as e:
        print(f"ERROR configurando Clusters: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def configure_machines():
    try:
        print("\nConfigurando Máquinas...")
        
        machines = _dict.get('machines', '').split(',')
        for machine in machines:
            if not machine:
                continue
                
            machine_name = _dict.get(f"{machine}.Name")
            if not machine_name:
                continue
                
            print(f"\nConfigurando Máquina: {machine_name}")
            
            cd('/')
            create(machine_name, 'Machine')
            cd(f'/Machines/{machine_name}')
            
            # Configuración de Node Manager
            create(machine_name, 'NodeManager')
            cd(f'NodeManager/{machine_name}')
            
            set('ListenAddress', _dict.get(f"{machine}.NodeManagerListenAddress", _dict['admin.server.listen_address']))
            set('ListenPort', int(_dict.get(f"{machine}.NodeManagerListenPort", '5556')))
            
            print(f"Máquina {machine_name} configurada exitosamente")
            
    except Exception as e:
        print(f"ERROR configurando Máquinas: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def main():
    print("\n" + "="*50)
    print("Configuración Completa de Dominio OSB".center(50))
    print("="*50)
    
    # Paso 1: Leer y validar propiedades
    print("\n[Paso 1/7] Leyendo configuración...")
    parsefile()
    validate_domain_properties()
    printdomain()
    
    # Paso 2: Cargar templates
    print("\n[Paso 2/7] Cargando templates...")
    load_templates()
    
    # Paso 3: Configurar conexión a base de datos
    print("\n[Paso 3/7] Configurando base de datos...")
    configure_database_connection()
    
    # Paso 4: Configurar Administration Server
    print("\n[Paso 4/7] Configurando Administration Server...")
    configure_administration_server()
    
    # Paso 5: Configurar Node Manager
    print("\n[Paso 5/7] Configurando Node Manager...")
    configure_node_manager()
    
    # Paso 6: Configurar infraestructura (máquinas, servidores, clusters)
    print("\n[Paso 6/7] Configurando infraestructura...")
    configure_machines()
    configure_managed_servers()
    configure_clusters()
    
    # Paso 7: Guardar dominio
    print("\n[Paso 7/7] Guardando dominio...")
    setOption('OverwriteDomain', 'true')
    setOption('ServerStartMode', 'prod')
    setOption('AppDir', _dict['approot'] + '/' + _dict['domain_name'])
    writeDomain(_dict['domainroot'] + '/' + _dict['domain_name'])
    closeTemplate()
    
    print("\n" + "="*50)
    print("Configuración completada exitosamente!".center(50))
    print("="*50)

if __name__ == "__main__":
    main()