## Copyright 2019 Green River IT as described in LICENSE.txt distributed with this project on GitHub.  
## Start at https://github.com/greenriverit/  
  
import subprocess
import re
import networkdeploymentfunctions as ndep
import networkvalidation as nval
import time
import os
  
###############################################################################################
## FUNCTIONS BELOW NEED TO BE MOVED OUT INTO SEPARATE MODULES AND THEN IMPORTED BY REFERENCE.
## THIS IS STILL A PROTOTYPE OF A REFERENCE ARCHITECTURE.  
###############################################################################################

#################################################################################
#################################################################################
#### Variable definition for function calls
#################################################################################
#################################################################################

path_to_acm_peering_config_module="/home/terraform-host/projects/terraform/vpc-peering-config/acceptor-acm/module-vpc-peering-config/"
path_to_call_to_acm_peering_config_module = "/home/terraform-host/projects/terraform/vpc-peering-config/acceptor-acm/call-to-module-vpc-peering-config/"

path_to_k8s_peering_config_module="/home/terraform-host/projects/terraform/vpc-peering-config/requestor-k8s/module-vpc-peering-config/"

path_to_call_to_k8sadmin_module = "/home/terraform-host/projects/terraform/k8sadmin/call-to-module/kubernetes-admin-client-aws-call-to-module/" 
command_to_call_k8sadmin_module = "python3 pipeline-k8sadmin-instance-apply.py" 
  
myRegion="us-west-2"

################################################################################  
### 1. DEPLOY THE KUBERNETES HOST NETWORK
################################################################################  
ndep.runTerraformOperation( os.environ['TF_VAR_COMMAND_TO_CALL_K8S_MODULE'], os.environ['TF_VAR_PATH_TO_CALL_TO_K8S_MODULE'])
ndep.checkOutputsOfKubernetesHostNetwork('python3 pipeline-kubeadm-network-output.py', os.environ['TF_VAR_PATH_TO_CALL_TO_K8S_MODULE'])
nval.validateKubernetesHostNetwork(ndep.cidr_subnet_list_kubernetes, ndep.security_group_id_kubernetes_nodes, ndep.cidr_vpc_kubernetes, ndep.vpc_id_kubernetes, ndep.route_table_id_kubernetes_host)
print("                                  ")
print("  **** Finished Step 1: Deploying Kubernetes Host Network. ****")
print("                                  ")

################################################################################  
### 2. ADD VPC IDS TO CALL TO THE VPC PEERING MODULE
################################################################################  
import string
import requests

def getLocalVpcID():
    r = requests.get('http://169.254.169.254/latest/meta-data/network/interfaces/macs/')
    macString = str(r.text)
    macString=macString.replace('/','')
    vpcRequest="http://169.254.169.254/latest/meta-data/network/interfaces/macs/"+macString+"/vpc-id"
    vpcIDRaw = requests.get(vpcRequest)
    return str(vpcIDRaw.text)

vpc_acceptor_new=getLocalVpcID()
vpc_requestor_new=ndep.vpc_id_kubernetes
ndep.configureVpcPeeringCode(os.environ['TF_VAR_PATH_TO_CALL_TO_PEERING_MODULE'], 'main.tf', vpc_acceptor_new, vpc_requestor_new)
print("                                  ")
print("  **** Finished Step 2: Adding VPC IDs To The Call To The VPC Peering Module. ****")
print("                                  ")

################################################################################  
### 3. NOW DEPLOY THE VPC PEERING CONNECTION
################################################################################  
ndep.deployVPC_PeeringConnection( os.environ['TF_VAR_COMMAND_TO_CALL_PEERING_MODULE'], os.environ['TF_VAR_PATH_TO_CALL_TO_PEERING_MODULE_SHORT'])
nval.validateVpcPeeringConnection(ndep.my_peering_connection_id, ndep.acceptor_vpc_id, ndep.requestor_vpc_id)
print("                                  ")
print("  **** Finished Step 3: Deploying VPC Peering Connection. ****")
print("                                  ")

################################################################################  
### 4. CONFIGURE THE ACCEPTOR (AGILE CLOUD MANAGER)
################################################################################
import boto3
client = boto3.client('ec2', region_name='us-west-2')
def getRtbId(vpcId,nameTag):
    response = client.describe_route_tables( Filters=[ {'Name': 'vpc-id','Values': [vpcId]}, {'Name': 'tag:Name','Values': [nameTag]} ] )
    rtbId = response['RouteTables'][0]['RouteTableId']
    return rtbId

def getSgId(vpcId,nameTag):
    response = client.describe_security_groups( Filters=[ {'Name': 'vpc-id','Values': [vpcId]}, {'Name': 'tag:Name','Values': [nameTag]} ] )
    sgId = response['SecurityGroups'][0]['GroupId']
    return sgId

def getSubnets(vpcId):
    response = client.describe_subnets( Filters=[ {'Name': 'vpc-id','Values': [vpcId]} ] )
    numSubnets=len(response['Subnets'])
    print("numSubnets is: "+str(numSubnets))
    subnetsList = []
    for i in range(0, numSubnets):
      print("i is: "+str(i))
      thisSubnetCidr = response['Subnets'][i]['CidrBlock']
      print("thisSubnet CidrBlock is: ")
      print(thisSubnetCidr)
      subnetsList.append(thisSubnetCidr)
    return subnetsList

def getSubnetIds(vpcId):
    response = client.describe_subnets( Filters=[ {'Name': 'vpc-id','Values': [vpcId]} ] )
    numSubnets=len(response['Subnets'])
    print("numSubnets is: "+str(numSubnets))
    subnetIdsList = []
    for i in range(0, numSubnets):
      print("i is: "+str(i))
      thisSubnetId = response['Subnets'][i]['SubnetId']
      print("thisSubnet SubnetId is: ")
      print(thisSubnetId)
      subnetIdsList.append(thisSubnetId)
    return subnetIdsList

myRtbNametag="acm-host"
routeTableIdAcmHost=getRtbId(vpc_acceptor_new,myRtbNametag)
mySgNameTag="acm-nodes"
secGroupIdAcmNodes=getSgId(vpc_acceptor_new,mySgNameTag)
mySubnetListAcmHost=getSubnets(vpc_acceptor_new)
mySubnetIdsListAcmHost=getSubnetIds(vpc_acceptor_new)
#Test the following before running the actual validation and deployment.
#//Routes
print("ndep.my_peering_connection_id is: " +ndep.my_peering_connection_id)
print("routeTableIdAcmHost is: " +routeTableIdAcmHost)
print("ndep.cidr_subnet_list_kubernetes is: " +str(ndep.cidr_subnet_list_kubernetes))
#//Security groups
print("path_to_acm_peering_config_module is: " +path_to_acm_peering_config_module)
print("secGroupIdAcmNodes is: " +secGroupIdAcmNodes)
print("ndep.security_group_id_kubernetes_nodes is: " +ndep.security_group_id_kubernetes_nodes)
#The following is the original that we keep, after we confirm that the above variables are created in the test.
nval.validateRoutePreReqsForAcceptorPeeringConnection(ndep.my_peering_connection_id, routeTableIdAcmHost, ndep.cidr_subnet_list_kubernetes)
# PASTE THE PEERING CONNECTION ROUTE(S) INTO THE ACCEPTOR/ANSIBLE 
ndep.creationLoopForVpcPeeringRoutes(ndep.cidr_subnet_list_kubernetes, ndep.my_peering_connection_id, path_to_acm_peering_config_module, routeTableIdAcmHost)
# PASTE KUBERNETES NODE SECURITY GROUP INTO ANSIBLE SECURITY GROUP RULE
ndep.configureVpcPeeringSecurityGroup(path_to_acm_peering_config_module, secGroupIdAcmNodes, ndep.security_group_id_kubernetes_nodes)
print("                                  ")
print("  **** Finished Step 4: Configuring Peering Routes & Security Group In The Acceptor (Agile Cloud Manager). ****")
print("                                  ")

################################################################################  
### 5. CONFIGURE THE REQUESTOR (KUBERNETES)
################################################################################  

print("ndep.my_peering_connection_id is: " +ndep.my_peering_connection_id)
print("ndep.route_table_id_kubernetes_host is: " +ndep.route_table_id_kubernetes_host)
print("mySubnetListAcmHost is: " +str(mySubnetListAcmHost))
print("ndep.my_peering_connection_id is: " +ndep.my_peering_connection_id)
print("os.environ['TF_VAR_PATH_TO_K8S_MODULE'] is: " +os.environ['TF_VAR_PATH_TO_K8S_MODULE'])
print("ndep.route_table_id_kubernetes_host is: " +ndep.route_table_id_kubernetes_host)
print("os.environ['TF_VAR_PATH_TO_K8S_MODULE'] is: " +os.environ['TF_VAR_PATH_TO_K8S_MODULE'])
print("ndep.security_group_id_kubernetes_nodes is: " +ndep.security_group_id_kubernetes_nodes)
print("secGroupIdAcmNodes is: " +secGroupIdAcmNodes)

#The following is the original that we keep, after we confirm that the above variables are created in the test.
nval.validateRoutePreReqsForRequestorPeeringConnection(ndep.my_peering_connection_id, ndep.route_table_id_kubernetes_host, mySubnetListAcmHost)
# PASTE THE PEERING CONNECTION ROUTE INTO THE REQUESTOR/KUBERNETES vpc.tf
ndep.creationLoopForVpcPeeringRoutes(mySubnetListAcmHost, ndep.my_peering_connection_id, path_to_k8s_peering_config_module, ndep.route_table_id_kubernetes_host)
# PASTE ANSIBLE NODE SECURITY GROUP INTO KUBERNETES SECURITY GROUP RULE
ndep.configureVpcPeeringSecurityGroup(path_to_k8s_peering_config_module, ndep.security_group_id_kubernetes_nodes, secGroupIdAcmNodes)
print("                                  ")
print("  **** Finished Step 5: Configuring Peering Routes & Security Group In The Requestor (Kubernetes). ****")
print("                                  ")

################################################################################  
### 6. DEPLOY THE CONFIG TO KUBERNETES HOST NETWORK
################################################################################  
#Note the following merely deploys the config add-on module to supplement the larger k8s host network.  The following does NOT deploy the entire k8s host network.
ndep.runTerraformOperation( os.environ['TF_VAR_COMMAND_TO_APPLY_K8S_PEER_CONFIG'], os.environ['TF_VAR_PATH_TO_CALL_K8SPEERCONFIG_MODULE'])
ndep.checkOutputsOfKubernetesHostNetwork('python3 pipeline-kubeadm-network-output.py', os.environ['TF_VAR_PATH_TO_CALL_TO_K8S_MODULE'])
nval.validateKubernetesHostNetwork(ndep.cidr_subnet_list_kubernetes, ndep.security_group_id_kubernetes_nodes, ndep.cidr_vpc_kubernetes, ndep.vpc_id_kubernetes, ndep.route_table_id_kubernetes_host)
nval.validateRoutesAddedToKubernetesHostNetwork(ndep.route_table_id_kubernetes_host, mySubnetListAcmHost, myRegion)
print("                                  ")
print("  **** Finished Step 6: Deploy the config to the Requestor (Kubernetes) Host Network. ****")
print("                                  ")

################################################################################  
### 7. DEPLOY THE CONFIG TO ACCEPTOR (AGILE CLOUD MANAGER HOST NETWORK)
################################################################################  
ndep.runTerraformOperation( "python3 pipeline-acceptor-peering-config-apply.py", path_to_call_to_acm_peering_config_module)

print("                                  ")
print("  **** Finished Step 7: Deploy the config to the Acceptor (ACM) Host Network. ****")
print("                                  ")

################################################################################  
### 8. DEPLOY THE K8SADMIN MACHINE INSIDE THE ACCEPTOR (AGILE CLOUD MANAGER HOST NETWORK)
################################################################################  
print("secGroupIdAcmNodes is: " +secGroupIdAcmNodes)
print("mySubnetListAcmHost is: " +str(mySubnetListAcmHost))
import boto3

client = boto3.client('ec2', region_name='us-west-2')

def getInternetGatewayId(vpcId):
    response = client.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id','Values': [vpcId]}])
    igId = response['InternetGateways'][0]['InternetGatewayId']
    return igId

myIGId=getInternetGatewayId(vpc_acceptor_new)
print("Internet Gateway myIGId is: "+myIGId)
print("                                                                 ")
ndep.addInstanceModule(command_to_call_k8sadmin_module, path_to_call_to_k8sadmin_module, 'remove-this-later--was-path-to-k8sadmin-iam-keys--now-an-env-variable', myIGId, secGroupIdAcmNodes, mySubnetIdsListAcmHost)

print("                                  ")
print("  **** Finished Step 8: Deploy the k8sadmin machine inside the Acceptor (ACM) Host Network. ****")
print("                                  ")
print("  **** Sleeping 60 seconds to allow the k8sadmin machine to initialize before we try to communicate with it.  **** ")
print("                                  ")
time.sleep(60)
print("  **** Now need to get the private IP of the k8s admin machine.  Then we will scp the key to it.  ")


import boto3

client = boto3.client('ec2', region_name='us-west-2')  
def getK8sadminPrivateIP(vpcId):  
    response = client.describe_instances(Filters=[{'Name': 'vpc-id','Values': [vpcId]},{'Name':'tag:Name','Values':['k8sadmin']}])  
    ipPrivate = response['Reservations'][0]['Instances'][0]['PrivateIpAddress']  
    return ipPrivate  

import subprocess

def transferTheKey(remoteIP, keyToMove, keyToUse, remoteUser):
    commandToTransferKey="scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i "+keyToUse+" "+keyToMove+" "+remoteUser+"@"+remoteIP+":~/"
    proc = subprocess.Popen( commandToTransferKey,stdout=subprocess.PIPE, shell=True)
    while True:
      line = proc.stdout.readline()
      if line:
        thetext=line.decode('utf-8').rstrip('\r|\n')
        decodedline=ansi_escape.sub('', thetext)
        print(decodedline)
        if "Permission denied" in decodedline:  
          print("The check for Permission denied works!  Now in the logical block which can be programmed to handle that.")
      else:
        break

print("vpc_acceptor_new is: "+vpc_acceptor_new)
remoteIP=getK8sadminPrivateIP(vpc_acceptor_new)
print("k8sadmin remoteIP is: "+remoteIP)
keyToMove="/home/terraform-host/stage-keys/kubernetes-host.pem"
keyToUse="/home/terraform-host/.ssh/kubernetes-host.pem"
remoteUser="kubernetes-host"
print("About to transfer the key. ")
transferTheKey(remoteIP,keyToMove,keyToUse,remoteUser)
print("done transferring the key.  ")
print("                                                    ")
print("    ****  Still need to add a task that copies the key into the .ssh folder and makes it read-only after just now having been transfered into the target machine.  ****    ")
print("                                                    ")

####    ###############################################################################################################################
####    ### ADD ADDITIONAL STEPS SUCH AS PING ALL NODES IN NETWORK FROM WITHIN EVERY NODE.  AND RUN/VALIDATE ANSIBLE PLAYBOOKS.  ETC. 
####    ###############################################################################################################################
