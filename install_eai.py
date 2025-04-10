import os
import sys
from os.path import exists, join
from sys import argv

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def parse_properties():
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

def validate_properties():
    required_keys = [
        'osbhome', 'domainroot', 'approot',
        'rcu.schema_prefix', 'database.url',
        'domain_name', 'domain_username', 'domain_password',
        'admin.port', 'admin.address',
        'template.OSB.path'
    ]
    
    missing_keys = [key for key in required_keys if key not in _dict]
    if missing_keys:
        print(f"ERROR: Faltan propiedades obligatorias: {', '.join(missing_keys)}")
        sys.exit(1)
        
    if _dict.get('domain_password') != _dict.get('domain_confirm_password'):
        print("ERROR: La contraseña y su confirmación no coinciden")
        sys.exit(1)

def print_configuration():
    print('\n' + '='*60)
    print("Configuración del Dominio OSB".center(60))
    print('='*60)
    max_len = max(len(k) for k in _dict)
    for key, val in sorted(_dict.items()):
        if 'password' in key.lower():
            print(f"{key.ljust(max_len)} : {'*' * len(val)}")
        else:
            print(f"{key.ljust(max_len)} : {val}")

def load_osb_templates():
    try:
        print("\nCargando templates para OSB...")
        
        # Template principal de OSB
        osb_template = _dict['template.OSB.path']
        print(f"\nCargando template OSB desde: {osb_template}")
        readTemplate(osb_template)
        
        # Templates adicionales (JRF es requerido para OSB)
        additional_templates = [
            'template.JRF.path',
            'template.ODSI.path',
            'template.WSMPM.path'
        ]
        
        for template_key in additional_templates:
            if template_key in _dict:
                print(f"\nCargando template adicional: {template_key.split('.')[1]}")
                print(f"Ruta: {_dict[template_key]}")
                addTemplate(_dict[template_key])
                
    except Exception as e:
        print(f"ERROR al cargar templates: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def configure_datasources():
    try:
        print("\nConfigurando DataSources para componentes OSB...")
        
        db_url = _dict['database.url']
        db_driver = 'oracle.jdbc.OracleDriver'
        test_query = 'SQL SELECT 1 FROM DUAL'
        
        # Componentes basados en RCU
        components = _dict.get('rcu.components', '').split(',')
        for component in components:
            if not component:
                continue
                
            schema_prefix = _dict.get('rcu.schema_prefix', 'OSB_QA')
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
        print(f"ERROR al configurar DataSources: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def configure_administration_server():
    try:
        print("\nConfigurando Administration Server...")
        
        cd('/Servers/AdminServer')
        cmo.setName('AdminServer')
        cmo.setListenAddress(_dict['admin.address'])
        cmo.setListenPort(int(_dict['admin.port']))
        
        # Configuración de seguridad
        cd('/Security/' + _dict['domain_name'] + '/User/' + _dict['domain_username'])
        cmo.setPassword(_dict['domain_password'])
        
        print(f"AdminServer configurado en {_dict['admin.address']}:{_dict['admin.port']}")
        
    except Exception as e:
        print(f"ERROR configurando AdminServer: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def configure_managed_servers():
    try:
        print("\nConfigurando Managed Servers...")
        
        servers = _dict.get('managedservers', '').split(',')
        for server in servers:
            if not server:
                continue
                
            server_name = _dict.get(f"{server}.Name")
            if not server_name:
                continue
                
            print(f"\nCreando Managed Server: {server_name}")
            
            cd('/')
            create(server_name, 'Server')
            cd(f'/Servers/{server_name}')
            cmo.setListenPort(int(_dict[f"{server}.port"]))
            cmo.setListenAddress(_dict[f"{server}.address"])
            
            # Asignar a máquina si está configurada
            machine_name = _dict.get(f"{server}.Machine")
            if machine_name:
                cmo.setMachine(getMBean(f'/Machines/{machine_name}'))
            
            print(f"Managed Server {server_name} creado en {_dict[f'{server}.address']}:{_dict[f'{server}.port']}")
            
    except Exception as e:
        print(f"ERROR creando Managed Servers: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def configure_cluster():
    try:
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
            
            # Asignar miembros al cluster
            members = _dict.get(f"{cluster}.members", '').split(',')
            for member in members:
                if member and _dict.get(f"{member}.Name"):
                    print(f"Asignando {_dict[f'{member}.Name']} al cluster...")
                    assign('Server', _dict[f"{member}.Name"], 'Cluster', cluster_name)
            
            print(f"Cluster {cluster_name} configurado con {len(members)} miembros")
            
    except Exception as e:
        print(f"ERROR configurando Cluster: {str(e)}")
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
                
            print(f"\nCreando Máquina: {machine_name}")
            
            cd('/')
            create(machine_name, 'Machine')
            cd(f'/Machines/{machine_name}')
            
            # Configurar Node Manager para la máquina
            create(machine_name, 'NodeManager')
            cd(f'NodeManager/{machine_name}')
            set('ListenAddress', machine_name)  # Usamos el nombre como dirección
            set('ListenPort', 5556)  # Puerto por defecto
            
            print(f"Máquina {machine_name} configurada con Node Manager")
            
    except Exception as e:
        print(f"ERROR configurando Máquinas: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def create_domain():
    try:
        print("\nCreando dominio OSB...")
        
        setOption('OverwriteDomain', 'true')
        setOption('ServerStartMode', 'prod')
        setOption('AppDir', _dict['approot'] + '/' + _dict['domain_name'] + '/applications')
        writeDomain(_dict['domainroot'] + '/' + _dict['domain_name'])
        closeTemplate()
        
        print(f"\nDominio {_dict['domain_name']} creado exitosamente en {_dict['domainroot']}")
        
    except Exception as e:
        print(f"ERROR al crear dominio: {str(e)}")
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(1)

def main():
    print("\n" + "="*60)
    print("Instalación de Dominio OSB".center(60))
    print("="*60)
    
    # Paso 1: Leer y validar propiedades
    print("\n[Paso 1/7] Leyendo configuración...")
    parse_properties()
    validate_properties()
    print_configuration()
    
    # Paso 2: Cargar templates
    print("\n[Paso 2/7] Cargando templates OSB...")
    load_osb_templates()
    
    # Paso 3: Configurar Administration Server
    print("\n[Paso 3/7] Configurando Administration Server...")
    configure_administration_server()
    
    # Paso 4: Configurar Managed Servers
    print("\n[Paso 4/7] Configurando Managed Servers...")
    configure_managed_servers()
    
    # Paso 5: Configurar Cluster
    print("\n[Paso 5/7] Configurando Cluster...")
    configure_cluster()
    
    # Paso 6: Configurar DataSources
    print("\n[Paso 6/7] Configurando DataSources...")
    configure_datasources()
    
    # Paso 7: Crear dominio
    print("\n[Paso 7/7] Creando dominio...")
    create_domain()
    
    print("\n" + "="*60)
    print("Instalación completada exitosamente!".center(60))
    print("="*60)

if __name__ == "__main__":
    main()