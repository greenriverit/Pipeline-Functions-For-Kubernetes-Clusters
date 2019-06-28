## Copyright 2019 Green River IT as described in LICENSE.txt distributed with this project on GitHub.  
## Start at https://github.com/greenriverit/  

import subprocess
import re

ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def checkIfRoutesWereAdded( route_table_id, cidr_subnet_list, myRegion):
    print("Inside checkIfRoutesWereAdded()")
    routeResult="FAIL"  #Start FAIL, then must prove twice success before returning PASS
    for my_cidr in cidr_subnet_list:
        routeResult=checkIfRouteWasAdded(route_table_id, my_cidr, myRegion)
        print("routeResult is: "+routeResult)
        if routeResult=="FAIL":
            return routeResult
    return routeResult

def checkIfRouteWasAdded( rtID, cidrDestination, myRegion):
    print("Inside checkIfRouteWasAdded()")
    myNewCommand="aws --region "+myRegion+" ec2 describe-route-tables --route-table-ids "+rtID+" --filters Name=route.destination-cidr-block,Values="+cidrDestination
    proc = subprocess.Popen( myNewCommand,stdout=subprocess.PIPE, shell=True)
    while True:
      line = proc.stdout.readline()
      if line:
        thetext=line.decode('utf-8').rstrip('\r|\n')
        decodedline=ansi_escape.sub('', thetext)
        if "\"RouteTables\": []" in decodedline:  
          print(decodedline)
          print("No matching routes found! Need to retry.")
          return "FAIL"
        if "\"DestinationCidrBlock\":" in decodedline:  
          if cidrDestination in decodedline:
            print(decodedline)
            return "PASS"
      else:
        return "FAIL"
        break

def validateKubernetesHostNetwork(cidr_sub_list_k8s, sg_k8s_nodes, cidr_vpc_k8s, vpcid_k8s, route_tbl_id_k8s_host):
    success='true'
    print('                                          ')
    print('-------------------------------------------- ')
    print('---- Validating Kubernetes Host Network ---- ')
    print('cidr_subnet_list_kubernetes is: ')
    print(cidr_sub_list_k8s)
    print('security_group_id_kubernetes_nodes is: ' +sg_k8s_nodes)
    print('cidr_vpc_kubernetes is: ' +cidr_vpc_k8s)
    print('vpc_id_kubernetes is: ' +vpcid_k8s)
    print('route_table_id_kubernetes_host is: ' +route_tbl_id_k8s_host)

    if not cidr_sub_list_k8s:  
        print('Exiting because cidr_subnet_list_kubernetes is empty.')
        success='false'
    if sg_k8s_nodes == '':
        print('exiting because security_group_id_kubernetes_nodes is empty.')
        success='false'
    if cidr_vpc_k8s == '':
        print('Exiting because cidr_vpc_kubernetes is empty.')
        success='false'
    if vpcid_k8s == '':
        print('Exiting because vpc_id_kubernetes is empty.')
        success='false'
    if route_tbl_id_k8s_host == '':
        print("Exiting because route_table_id_kubernetes_host is empty.")
        success='false'
    if success=='false':
        print('About to exit 1 from validateKubernetesHostNetwork.')
        exit(1)
    else:  
        print('SUCCESS validateKubernetesHostNetwork.')

def validateRoutesAddedToKubernetesHostNetwork(route_tbl_id_k8s_host, cidr_sub_list_acm, myRegion):
    print("  **** About to validate that routes were added into Kubernetes Host Network. **** ")
    print("                                  ")
    routeResult=checkIfRoutesWereAdded( route_tbl_id_k8s_host, cidr_sub_list_acm, myRegion)
    print("In deploy-network, routeResult is: "+routeResult)
    if routeResult=="FAIL":
        print("Stopping the script because routeResult is: "+routeResult)
        exit(1)
    print("                                  ")
    print("  **** Finished validating that routes were added into Kubernetes Host Network. **** ")
    print("                                  ")

def validateVpcPeeringConnection(my_peering_conn_id, acceptor_vpcid, requestor_vpcid):
    success='true'
    print('                                          ')
    print('----------------------------------------- ')
    print('---- Validating VpcPeeringConnection ---- ')
    print('my_peering_connection_id is: ' +my_peering_conn_id)
    print('acceptor_vpc_id is: ' +acceptor_vpcid)
    print('requestor_vpc_id is: ' +requestor_vpcid)
    if my_peering_conn_id == '':
        print('Exiting because my_peering_connection_id is empty.')
        success='false'
    if acceptor_vpcid == '':
        print('exiting because acceptor_vpc_id is empty.')
        success='false'
    if requestor_vpcid == '':
        print('Exiting because requestor_vpc_id is empty.')
        success='false'
    if success=='false':
        print('About to exit 1 from validateVpcPeeringConnection.')
        exit(1)
    else:  
        print('SUCCESS validateVpcPeeringConnection.')

def validateRoutePreReqsForAcceptorPeeringConnection(my_peering_conn_id, route_tbl_id_acm_host, cidr_sub_list_kubernetes):
    success='true'
    print('                                          ')
    print('----------------------------------------- ')
    print('---- Validating Route PreRequisites For Peering Connection ---- ')
    print('my_peering_connection_id is: ' +my_peering_conn_id)
    print('route_table_id_acm_host is: ' +route_tbl_id_acm_host)
    print('cidr_subnet_list_kubernetes is: ')
    print(cidr_sub_list_kubernetes)

    if my_peering_conn_id == '':
        print('Exiting because my_peering_connection_id is empty.')
        success='false'
    if route_tbl_id_acm_host == '':
        print('exiting because route_table_id_acm_host is empty.')
        success='false'
    if not cidr_sub_list_kubernetes:
        print('Exiting because cidr_subnet_list_kubernetes is empty.')
        success='false'
    if success=='false':
        print('About to exit 1 from validateRoutePreReqsForAcceptorPeeringConnection.')
        exit(1)
    else:  
        print('SUCCESS validateRoutePreReqsForAcceptorPeeringConnection.')

def validateRoutePreReqsForRequestorPeeringConnection(my_peer_conn_id, route_table_id_k8s_host, cidr_subn_list_acm):  
    success='true'
    print('                                          ')
    print('----------------------------------------- ')
    print('---- Validating Route PreRequisites For Requestor Peering Connection ---- ')
    print('my_peering_connection_id is: ' +my_peer_conn_id)
    print('route_table_id_kubernetes_host is: ' +route_table_id_k8s_host)
    print('cidr_subnet_list_acm is: ')
    print(cidr_subn_list_acm)

    if my_peer_conn_id == '':
        print('Exiting because my_peering_connection_id is empty.')
        success='false'
    if route_table_id_k8s_host == '':
        print('exiting because route_table_id_kubernetes_host is empty.')
        success='false'
    if not cidr_subn_list_acm:
        print('Exiting because cidr_subnet_list_acm is empty.')
        success='false'
    if success=='false':
        print('About to exit 1 from validateRoutePreReqsForRequestorPeeringConnection.')
        exit(1)
    else:  
        print('SUCCESS validateRoutePreReqsForRequestorPeeringConnection.')
