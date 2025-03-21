import subprocess

def pack_domain(props):
    try:
        domain_home = props['domainroot'] + '/' + props['domain_name']
        template_path = domain_home + '.jar'
        pack_script = props['wlshome'] + '/common/bin/pack.sh'

        command = [
            pack_script,
            '-domain=' + domain_home,
            '-template=' + template_path,
            '-managed=true',
            '-template_name=' + props['domain_name']]
        subprocess.run(command, check=True)
        print(f"Dominio empaquetado en {template_path}.")
    except subprocess.CalledProcessError as e:
        print(f"Error al empaquetar el dominio: {e}")
        sys.exit(1)

def unpack_domain(props, servers):
    try:
        template_path = props['domainroot'] + '/' + props['domain_name'] + '.jar'
        unpack_script = props['wlshome'] + '/common/bin/unpack.sh'
        domain_home = props['domainroot'] + '/' + props['domain_name']

        for server in servers:
            node_ip = props.get(server + '.address')
            node_user = props.get(server + '.username')

            # Transferir el archivo .jar al nodo
            subprocess.run(['scp', template_path, f"{node_user}@{node_ip}:{template_path}"], check=True)

            # Ejecutar UNPACK en el nodo
            ssh_command = f"mkdir -p {domain_home} && {unpack_script} -domain={domain_home} -template={template_path}"
            subprocess.run(['ssh', f"{node_user}@{node_ip}", ssh_command], check=True)
            print(f"Dominio descomprimido en {node_ip}:{domain_home}.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error al descomprimir el dominio: {e}")
        sys.exit(1)