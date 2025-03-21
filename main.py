from properties_handler import parse_properties_file, export_properties
from domain_operations import create_machine, create_admin, create_managedserver, create_clusters
from pack_unpack import pack_domain, unpack_domain

def main():
    print("Start of the script Execution >>")
    print("Parsing the properties file...")
    properties = parse_properties_file()
    exported = export_properties(properties)

    print("Creating Domain from Domain Template...")
    try:
        readTemplate(exported['wlshome'] + '/common/templates/wls/wls.jar')
    except:
        print("Error Reading the Template", exported['wlshome'])
        print("Dumpstack: \n -------------- \n", dumpStack())
        sys.exit(2)

    print("Creating Machines...")
    create_machine(exported['machines'], properties)

    print("Creating AdminServer...")
    create_admin(exported)

    print("Creating ManagedServers...")
    create_managedserver(exported['servers'], properties)

    print("Creating Clusters...")
    create_clusters(exported['clusters'], properties)

    print("Packaging the Domain...")
    pack_domain(properties)

    print("Unpacking the Domain...")
    unpack_domain(properties ,exported['servers'])

    print("End of Script Execution << \nGood Bye!")

if __name__ == "__main__":
    main()