## Copyright 2019 Green River IT as described in LICENSE.txt distributed with this project on GitHub.  
## Start at https://github.com/greenriverit/  

import subprocess
import re
import ipaddress
import os
from os.path import exists
import sys
import time
import glob

# NOTE:  Need to harden all the string processing code below.  This will include:
# --- startIndex calculated programatically for each split of a string
# Consolidate the functions to become more polymorphic.

ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

cidr_subnet_list_kubernetes = []
cidr_vpc_kubernetes = ''
security_group_id_kubernetes_nodes = ''
vpc_id_kubernetes = ''
route_table_id_kubernetes_host = ''

my_peering_connection_id = ''
acceptor_vpc_id = ''
requestor_vpc_id = ''

def checkForErrors(myDecodedLine):
    foundAnExceptionWorthStoppingScript="no"
    if "connectex: No connection could be made because the target machine actively refused it." in myDecodedLine:
        foundAnExceptionWorthStoppingScript="yes"
    if "Error launching source instance: InvalidGroup.NotFound: The security group" in myDecodedLine:
        #This might require special retry logic instead of simply stopping the script as we are doing now.
        foundAnExceptionWorthStoppingScript="yes"
    if foundAnExceptionWorthStoppingScript=="yes":
        print("                                           ")
        print("---- Stopping script due to error. ----")
        print("                                           ")
        exit(1)

## A generic function for deployment of an instance module inside an existing VPC
def addInstanceModule( scriptName, workingDir, pathToIamKeys, igw_id, sg_id, subnetID_holder):
    print("scriptName is: " +scriptName)
    print("workingDir is: " +workingDir)
    print("pathToIamKeys is: " +pathToIamKeys)
    print("igw_id is: " +igw_id)
    print("sg_id is: " +sg_id)
    print("subnetID_holder is: " +str(subnetID_holder))
    callToScript = scriptName+" "+pathToIamKeys+" "+igw_id+" "+sg_id+" "+subnetID_holder[0]
    print("callToScript is: " +callToScript)

    proc = subprocess.Popen( callToScript,cwd=workingDir,stdout=subprocess.PIPE, shell=True)
    while True:
      line = proc.stdout.readline()
      if line:
        thetext=line.decode('utf-8').rstrip('\r|\n')
        decodedline=ansi_escape.sub('', thetext)
        checkForErrors(decodedline)
        print(decodedline)
        if "Outputs:" in decodedline:  
          print("JENGA")
      else:
        break

# A generic instance removal within a pre-existing host
def removeInstanceModule( scriptName, workingDir ): #This function should be replaced with something generic for most destroy operations
    proc = subprocess.Popen( scriptName,cwd=workingDir,stdout=subprocess.PIPE, shell=True)
    while True:
      line = proc.stdout.readline()
      if line:
        thetext=line.decode('utf-8').rstrip('\r|\n')
        decodedline=ansi_escape.sub('', thetext)
        print(decodedline)
        if "Outputs:" in decodedline:  
          print("Outputs are: ")
      else:
        break

def runTerraformOperation( scriptName, workingDir ): 
    proc = subprocess.Popen( scriptName,cwd=workingDir,stdout=subprocess.PIPE, shell=True)
    inCidrBlock='false'
    while True:
      line = proc.stdout.readline()
      if line:
        thetext=line.decode('utf-8').rstrip('\r|\n')
        decodedline=ansi_escape.sub('', thetext)
        print(decodedline)
        checkForErrors(decodedline)
      else:
        break

def checkOutputsOfKubernetesHostNetwork( scriptName, workingDir ): 
    proc = subprocess.Popen( scriptName,cwd=workingDir,stdout=subprocess.PIPE, shell=True)
    inCidrBlock='false'
    while True:
      line = proc.stdout.readline()
      if line:
        thetext=line.decode('utf-8').rstrip('\r|\n')
        decodedline=ansi_escape.sub('', thetext)
        print(decodedline)
        checkForErrors(decodedline)
        if "Outputs:" in decodedline:  
            print("JENGA")
        global cidr_subnet_list_kubernetes
        if "cidr_subnet_list_kubernetes" in decodedline:  
            if not "[" in decodedline:  
                cidr_subnet_line_test = decodedline.findall("(?:\d{1,3}\.){3}\d{1,3}(?:/\d\d?)?",s)
                print("cidr_subnet_line_test is: " +cidr_subnet_line_test)
                try:
                    ip_addr = ipaddress.ip_address(cidr_subnet_line_test)
                    print("ip_addr is: " +ip_addr)
                except ValueError: # handle bad ip
                    print("ERROR PROCESSING IP.")
                cidr_subnet_list_kubernetes.append(decodedline)
            if "[" in decodedline:  
                inCidrBlock='true'
        elif inCidrBlock=='true':
            if "]" in decodedline:
                inCidrBlock='false'
            if inCidrBlock=='true':
                decodedline=decodedline.strip()
                decodedline=decodedline.replace(",","")
                cidr_subnet_line_test = re.findall("(?:\d{1,3}\.){3}\d{1,3}(?:/\d\d?)?",decodedline)
                if len(cidr_subnet_line_test) == 0:
                    print("cidr_subnet_line_test is EMPTY. ")
                elif len(cidr_subnet_line_test) == 1:
                    print("cidr_subnet_line_test is: " +cidr_subnet_line_test[0])
                    cidr_subnet_list_kubernetes.append(cidr_subnet_line_test[0])
                else:
                    print("UNHANDLED EXCEPTION: cidr_subnet_line_test has multiple entries.")
        if "security_group_id_kubernetes_nodes" in decodedline:  
          global security_group_id_kubernetes_nodes
          security_group_id_kubernetes_nodes = decodedline[37:]
        if "cidr_vpc_kubernetes" in decodedline:  
          global cidr_vpc_kubernetes
          matchedSubstring = re.search('\d', decodedline)
          if matchedSubstring:
              myStartidx=matchedSubstring.start()
              print('decodedline is: ' +decodedline)
              print('matchedSubstring.group(0) is: ' +matchedSubstring.group(0))    
              print('myStartidx is: ' +str(myStartidx))
              cidr_vpc_kubernetes = decodedline[myStartidx:]
              print('cidr_vpc_kubernetes is: ' +cidr_vpc_kubernetes)
          else:
              print('The CIDR is not valid.')
        if "vpc_id_kubernetes" in decodedline:  
          global vpc_id_kubernetes
          vpc_id_kubernetes = decodedline[20:]
        if "route_table_id_kubernetes_host" in decodedline:  
          print("                                            ")
          print("decodedline is: " +decodedline)
          startIndex = int(decodedline.find('rtb-'))
          print("startIndex is: " +str(startIndex))
          print("                                            ")
          global route_table_id_kubernetes_host
          route_table_id_kubernetes_host = decodedline[startIndex:]
      else:
        break

def deployVPC_PeeringConnection( scriptName, workingDir ): 
    proc = subprocess.Popen( scriptName,cwd=workingDir,stdout=subprocess.PIPE, shell=True)

    while True:
      line = proc.stdout.readline()
      if line:
        thetext=line.decode('utf-8').rstrip('\r|\n')
        decodedline=ansi_escape.sub('', thetext)
        print(decodedline)
        checkForErrors(decodedline)
        if "Outputs:" in decodedline:  
          print("JENGA")
        if "my_peering_connection_id" in decodedline:
          startIDX = decodedline.find('pcx')
          endIDX = len(decodedline)
          global my_peering_connection_id
          my_peering_connection_id = decodedline[startIDX:endIDX]
          print('my_peering_connection_id is: ' +my_peering_connection_id)
        if "acceptor_vpc_id" in decodedline:
          startIDX = decodedline.find('vpc')
          endIDX = len(decodedline)
          global acceptor_vpc_id
          acceptor_vpc_id = decodedline[startIDX:endIDX]
          print('acceptor_vpc_id is: ' +acceptor_vpc_id)
        if "requestor_vpc_id" in decodedline:
          startIDX = decodedline.find('vpc')
          endIDX = len(decodedline)
          global requestor_vpc_id
          requestor_vpc_id = decodedline[startIDX:endIDX]
          print('requestor_vpc_id is: ' +requestor_vpc_id)
      else:
        break

def replaceVPC( line , replacementString):
    print("line 1 is: " +line)
    firstIndex = line.find('\"')
    print("firstIndex is: " +str(firstIndex))

    if firstIndex != -1: #i.e. if the first quote was found
        secondIndex = line.rfind('\"')
        if firstIndex != -1 and secondIndex != -1: #i.e. both quotes were found
            print('First: ' + str(firstIndex))
            print('Second: ' + str(secondIndex))
            print('First character is: ' +line[firstIndex])
            print('Second character is: ' +line[secondIndex])
            firstPart=line[0:firstIndex+1]
            lastPart=line[secondIndex:-1]
            print('firstPart is: ' +firstPart)
            print('lastPart is: ' +lastPart)
            src=line[firstIndex+1:secondIndex]
            print("src is: " +src)
            print("replacementString is: " +replacementString)
            replacementLine = firstPart+replacementString+lastPart+'\n'
            print('replacementLine is: ' +replacementLine)
            return replacementLine
    return 'error - malformed input string'

def createVpcPeeringRoute(path_to_file, file_name, myRouteName, myRouteTableID, myCidrBlock, myVpcPeeringConnId):  
    fully_qualified_file_name=path_to_file+file_name

    #Delete file if it exists.  Do not truly need to check if exists before trying to os.remove.  
    if exists(fully_qualified_file_name):
        print("fully_qualified_file_name  EXISTS,")
    try:
        os.remove(fully_qualified_file_name)
    except OSError:
        print("fully_qualified_file_name DOES NOT EXIST.")
        pass

    lines = [] # empty list to populate
    newline1 = "resource \"aws_route\" \""+myRouteName+"\" { \n"
    lines.append(newline1)
    newline2 = "    route_table_id = \""+myRouteTableID+"\" \n"
    lines.append(newline2)
    newline3 = "    destination_cidr_block = \""+myCidrBlock+"\" \n"
    lines.append(newline3)
    newline4 = "    vpc_peering_connection_id = \""+myVpcPeeringConnId+"\" \n"
    lines.append(newline4)
    newline6 = "}  \n"
    lines.append(newline6)
    newline7 = "  \n"
    lines.append(newline7)

    with open(fully_qualified_file_name, 'w') as outfile:
        for line in lines:
            outfile.write(line)

def creationLoopForVpcPeeringRoutes(my_cidr_list, my_peering_id, my_path_to_file, target_route_table):
    print("Inside creationLoopForVpcPeeringRoutes ().")
    print("my_cidr_list is: ")
    print(my_cidr_list)
    print("my_peering_id is: "+my_peering_id)
    print("my_path_to_file is: "+my_path_to_file)
    print("target_route_table is: "+target_route_table)
    for my_cidr in my_cidr_list:
        print('    '+my_cidr)
        myRouteName=my_peering_id.replace('-','_')+"_"+(my_cidr.replace('.','-')).replace('/','--')
        print("myRouteName is: " +myRouteName)
        customFileName="route_"+myRouteName+".tf"
        print('customFileName is: ' +customFileName)
        createVpcPeeringRoute(my_path_to_file, customFileName, myRouteName, target_route_table, my_cidr, my_peering_id)

def configureVpcPeeringSecurityGroup(path_to_file, security_group, source_security_group):
    file_name="sgp-"+security_group+"-and-"+source_security_group+".tf"
    fully_qualified_file_name=path_to_file+file_name

    #Delete file if it exists.  Do not truly need to check if exists before trying to os.remove.  
    if exists(fully_qualified_file_name):
        print("fully_qualified_file_name  EXISTS,")
    try:
        os.remove(fully_qualified_file_name)
    except OSError:
        print("fully_qualified_file_name DOES NOT EXIST.")
        pass

    lines = [] # empty list to populate with lines for new file
    newline = "resource \"aws_security_group_rule\" \"peer-ingress-"+security_group+"-and-"+source_security_group+"\" { \n"
    lines.append(newline)
    newline = "    ## Change this to more narrowly restrict access between the Ansible server and Ansible clients. \n"
    lines.append(newline)
    newline = "    description              = \"Allow VPC-peered Administration/Configuration servers and Cluster clients to communicate with each other\" \n"
    lines.append(newline)
    newline = "    type                     = \"ingress\" \n"
    lines.append(newline)
    newline = "    from_port                = 0 \n"
    lines.append(newline)
    newline = "    to_port                  = 0 \n"
    lines.append(newline)
    newline = "    protocol                 = \"-1\" \n" 
    lines.append(newline)
    newline = "    security_group_id        = \""+security_group+"\" \n"
    lines.append(newline)
    newline = "    source_security_group_id = \""+source_security_group+"\" \n"
    lines.append(newline)
    newline = "} \n"
    lines.append(newline)

    with open(fully_qualified_file_name, 'w') as outfile:
        for line in lines:
            outfile.write(line)

def removeVPC_PeeringConnection( scriptName, workingDir ): 
    print("                                               ")
    print("---- Starting To Remove Peering Connection ----")
    print("                                               ")
    proc = subprocess.Popen( scriptName,cwd=workingDir,stdout=subprocess.PIPE, shell=True)

    try: 
        while True:
          line = proc.stdout.readline()
          if line:
            thetext=line.decode('utf-8').rstrip('\r|\n')
            decodedline=ansi_escape.sub('', thetext)
            print(decodedline)
          else:
            break
    except:
        sys.stdout.flush()

    # Wait until process terminates (without using p.wait())
    while proc.poll() is None:
        # Process hasn't exited yet, let's wait some
        time.sleep(0.5)

    # Get return code from process
    return_code = proc.returncode
    print('RETURN CODE IS: ', return_code)
    if return_code==1:
        print("                                            ")
        print("---- Attempt to Remove Peering Connection Failed.  Check to see if it even still exists. ----")
        print("                                            ")
        # Exit with return code from process
        sys.exit(1)    

def removeKubernetesHostNetwork( scriptName, workingDir ): 
    proc = subprocess.Popen( scriptName,cwd=workingDir,stdout=subprocess.PIPE, shell=True)
    while True:
      line = proc.stdout.readline()
      if line:
        thetext=line.decode('utf-8').rstrip('\r|\n')
        decodedline=ansi_escape.sub('', thetext)
        print(decodedline)
        if "Outputs:" in decodedline:  
          print("Outputs are: ")
      else:
        break

def configureVpcPeeringCode( path_to_file, file_name, vpc_acceptor_new, vpc_requestor_new):
    fully_qualified_file_name=path_to_file+file_name
    print("  ==== Inside configureVpcPeeringCode ====  ")
    print("vpc_acceptor_new is: " +vpc_acceptor_new)
    print("vpc_requestor_new is: " +vpc_requestor_new)

    lines = []
    with open(fully_qualified_file_name) as infile:
        for line in infile:
            if "vpc_acceptor" in line:  
                vpc_acceptor_line = replaceVPC(line, vpc_acceptor_new)
                print('vpc_acceptor_line is: ' +vpc_acceptor_line)
                lines.append(vpc_acceptor_line)
            elif "vpc_requestor" in line:  
                vpc_requestor_line = replaceVPC(line, vpc_requestor_new)
                print('vpc_requestor_line is: ' +vpc_requestor_line)
                lines.append(vpc_requestor_line)
            else:
                lines.append(line)

    with open(fully_qualified_file_name, 'w') as outfile:
        for line in lines:
            outfile.write(line)

def removeVPCPeeringConfiguration(path_to_file, file_name, vpc_acceptor_new, vpc_requestor_new):
    fully_qualified_file_name=path_to_file+file_name

    lines = []
    with open(fully_qualified_file_name) as infile:
        for line in infile:
            if "vpc_acceptor" in line:  
                vpc_acceptor_line = replaceVPC(line, vpc_acceptor_new)
                print('vpc_acceptor_line is: ' +vpc_acceptor_line)
                lines.append(vpc_acceptor_line)
            elif "vpc_requestor" in line:  
                vpc_requestor_line = replaceVPC(line, vpc_requestor_new)
                print('vpc_requestor_line is: ' +vpc_requestor_line)
                lines.append(vpc_requestor_line)
            else:
                lines.append(line)

    with open(fully_qualified_file_name, 'w') as outfile:
        for line in lines:
            outfile.write(line)
