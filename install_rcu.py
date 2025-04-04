import os
import sys
import subprocess
from os.path import exists, join
from sys import argv

class RCUInstaller:
    def __init__(self):
        self.rcu_props = {}
        self.required_keys = [
            'database.type', 'database.connectString', 'database.user',
            'database.password', 'rcu.prefix', 'rcu.components',
            'rcu.schema.password', 'rcu.schema.confirm_password'
        ]
        
    def get_script_path(self):
        """Obtiene la ruta del directorio donde se encuentra el script"""
        return os.path.dirname(os.path.realpath(sys.argv[0]))
    
    def parse_rcu_properties(self):
        """Lee y parsea el archivo de propiedades RCU"""
        propfile = join(self.get_script_path(), "rcu.properties")
        if not exists(propfile):
            print(f"ERROR: Archivo {propfile} no encontrado")
            sys.exit(1)
            
        with open(propfile, 'r') as fo:
            for line in fo:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    self.rcu_props[key.strip()] = value.strip()
    
    def validate_properties(self):
        """Valida las propiedades requeridas"""
        missing_keys = [key for key in self.required_keys if key not in self.rcu_props]
        if missing_keys:
            print(f"ERROR: Faltan propiedades obligatorias: {', '.join(missing_keys)}")
            sys.exit(1)
            
        if self.rcu_props['rcu.schema.password'] != self.rcu_props['rcu.schema.confirm_password']:
            print("ERROR: Las contraseñas de schema no coinciden")
            sys.exit(1)
            
        if not self.rcu_props['database.connectString'].startswith('jdbc:oracle:thin:@//'):
            print("ERROR: Formato incorrecto de database.connectString")
            print("Debe ser: jdbc:oracle:thin:@//host:port/service")
            sys.exit(1)
    
    def print_summary(self):
        """Muestra un resumen de la configuración"""
        print("\n" + "="*50)
        print("Resumen de Configuración RCU".center(50))
        print("="*50)
        
        max_len = max(len(k) for k in self.rcu_props)
        for key, value in sorted(self.rcu_props.items()):
            if 'password' in key.lower():
                print(f"{key.ljust(max_len)} : {'*' * len(value)}")
            else:
                print(f"{key.ljust(max_len)} : {value}")
    
    def build_rcu_command(self):
        """Construye el comando RCU"""
        base_cmd = [
            self.rcu_props.get('rcu.home', '/u01/oracle/product/osb12214/oracle_common/bin/rcu'),
            '-silent',
            '-createRepository',
            '-databaseType', self.rcu_props['database.type'],
            '-connectString', self.rcu_props['database.connectString'],
            '-dbUser', self.rcu_props['database.user'],
            '-dbRole', 'SYSDBA',
            '-schemaPrefix', self.rcu_props['rcu.prefix'],
            '-component', self.rcu_props['rcu.components'],
            '-schemaPassword', self.rcu_props['rcu.schema.password'],
            '-f'
        ]
        
        # Agregar password de BD si existe
        if 'database.password' in self.rcu_props:
            base_cmd.extend(['-databasePassword', self.rcu_props['database.password']])
        
        # Agregar mapeo de tablespaces
        for key, value in self.rcu_props.items():
            if key.startswith('tablespace.') and key.endswith('.data'):
                component = key.split('.')[1]
                base_cmd.extend(['-componentTablespaceMap', f"{component}:{value}"])
        
        return base_cmd
    
    def execute_rcu(self):
        """Ejecuta el comando RCU"""
        cmd = self.build_rcu_command()
        log_dir = self.rcu_props.get('rcu.log.dir', '/tmp/rcu_logs')
        
        # Preparar entorno
        os.makedirs(log_dir, exist_ok=True)
        os.environ['RCU_LOG_LOCATION'] = log_dir
        
        # Mostrar comando (sin passwords)
        safe_cmd = []
        for part in cmd:
            if 'password' in part.lower():
                safe_cmd.append('********')
            else:
                safe_cmd.append(part)
        
        print("\nEjecutando comando RCU:")
        print(' '.join(safe_cmd))
        
        # Ejecutar proceso
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Mostrar salida en tiempo real
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            # Verificar resultado
            if process.returncode != 0:
                print("\nERROR en la ejecución de RCU:")
                print(process.stderr.read())
                sys.exit(1)
                
            print("\nRCU ejecutado exitosamente!")
            
        except Exception as e:
            print(f"\nERROR al ejecutar RCU: {str(e)}")
            sys.exit(1)

def main():
    installer = RCUInstaller()
    
    print("\n" + "="*50)
    print("Instalación Automática de RCU".center(50))
    print("="*50)
    
    # Paso 1: Leer propiedades
    print("\n[Paso 1/4] Leyendo configuración...")
    installer.parse_rcu_properties()
    
    # Paso 2: Validar propiedades
    print("[Paso 2/4] Validando configuración...")
    installer.validate_properties()
    
    # Paso 3: Mostrar resumen
    print("[Paso 3/4] Mostrando resumen...")
    installer.print_summary()
    
    # Confirmación antes de ejecutar
    confirm = input("\n¿Desea continuar con la instalación? (s/n): ").lower()
    if confirm != 's':
        print("Instalación cancelada por el usuario")
        sys.exit(0)
    
    # Paso 4: Ejecutar RCU
    print("\n[Paso 4/4] Ejecutando RCU...")
    installer.execute_rcu()
    
    print("\n" + "="*50)
    print("Proceso completado exitosamente!".center(50))
    print("="*50)

if __name__ == "__main__":
    main()