def create_machine(machines, properties):
    try:
        cd('/')
        for machine in machines:
            print("Creating a New Machine with the following Configuration")
            mn = create(machine, 'Machine')
            machine_name = properties.get(machine + '.Name')
            if machine_name:
                print("\tMachine Name:", machine_name)
                mn.setName(machine_name)
            else:
                print("No machine Name mentioned for", machine)
    except:
        print("Creating Machine failed", machine)
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(2)

def create_admin(properties):
    try:
        print("\nCreating AdminServer with the following Configuration")
        if properties['domain_password'] != properties['domain_confirm_password']:
            print("ERROR: La contraseña y su confirmación no coinciden.")
            sys.exit(1)

        cd('/Security/base_domain/User/' + properties['domain_username'])
        cmo.setPassword(properties['domain_password'])
        cd('/Servers/AdminServer')
        cmo.setName('AdminServer')
        cmo.setListenPort(int(properties['adminPort']))
        cmo.setListenAddress(properties['adminAddress'])
        print("\tAdminServer ListenPort:", properties['adminPort'])
        print("\tAdminServer ListenAddress:", properties['adminAddress'])
    except:
        print("Error while creating AdminServer")
        print("Dumpstack: \n -------------- \n", dumpStack())

def create_managedserver(servers, properties):
    try:
        cd('/')
        for server in servers:
            MSN = properties.get(server + '.Name')
            MSP = properties.get(server + '.port')
            MSA = properties.get(server + '.address')
            MSUser = properties.get(server + '.username')
            MSPass = properties.get(server + '.password')

            print("\nCreating A New Managed Server with following Configuration")
            print("\tServerName:", MSN)
            print("\tServer ListenPort:", MSP)
            print("\tServer ListenAddress:", MSA)
            print("\tNode Manager Username:", MSUser)
            print("\tNode Manager Password: ********")

            sobj = create(MSN, 'Server')
            sobj.setName(MSN)
            sobj.setListenPort(int(MSP))
            sobj.setListenAddress(MSA)

            cd('/Servers/' + MSN)
            cmo.setMachine(getMBean('/Machines/' + properties.get('m2.Name')))
    except:
        print("Error While Creating ManagedServer", server)
        print("Dumpstack: \n -------------- \n", dumpStack())

def create_clusters(clusters, properties):
    try:
        cd('/')
        for cluster in clusters:
            CN = properties.get(cluster + '.Name')
            cobj = create(CN, 'Cluster')
            print("\nCreating a New Cluster with the following Configuration")
            print("\tClusterName:", CN)
    except:
        print("Error while Creating Cluster", cluster)
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(2)