## Copyright 2019 Green River IT as described in LICENSE.txt distributed with this project on GitHub.  
## Start at https://github.com/greenriverit/  
  
import subprocess
import re
import networkdeploymentfunctions as ndf
import os

###############################################################################
### 1. Remove the VPC Peering
###############################################################################
ndf.removeVPC_PeeringConnection( 'python3 pipeline-vpc-peering-destroy.py', os.environ['TF_VAR_PATH_TO_CALL_TO_PEERING_MODULE'])  
print("                                  ")
print("  **** Finished Removing VPC Peering Connection. ****")
print("                                  ")

###############################################################################
### 2. Remove the Kubernetes Host Network
###############################################################################
ndf.removeKubernetesHostNetwork( 'python3 pipeline-kubeadm-network-destroy.py', os.environ['TF_VAR_PATH_TO_CALL_TO_K8S_MODULE'])  
print("                                  ")
print("  **** Finished Removing Kubernetes Host Network. ****")
print("                                  ")

###############################################################################
### 3. Remove Config from VPC Peering Connection 
###############################################################################
ndf.removeVPCPeeringConfiguration(os.environ['TF_VAR_PATH_TO_CALL_TO_PEERING_MODULE'], 'main.tf', '', '')
print("                                  ")
print("  **** Finished Removing Config from VPC Peering Code. ****")
print("                                  ")

###############################################################################
### 4. Remove k8sadmin instance if still present 
###############################################################################
path_to_call_to_k8sadmin_module = "/home/terraform-host/projects/terraform/k8sadmin/call-to-module/kubernetes-admin-client-aws-call-to-module/" 
command_to_remove_k8sadmin_module = "python3 pipeline-k8sadmin-instance-destroy.py" 

ndf.removeInstanceModule( command_to_remove_k8sadmin_module, path_to_call_to_k8sadmin_module )
print("                                  ")
print("  **** Finished Removing k8sadmin instance if it still existed. ****")
print("                                  ")
