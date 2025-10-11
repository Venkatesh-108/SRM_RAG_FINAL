## Dell SRM 5.1.1.0 Installation and Configuration Guide

5.1.1.0

<!-- image -->

## Notes, cautions, and warnings

<!-- image -->

NOTE:

A NOTE indicates important information that helps you make better use of your product.

CAUTION: A CAUTION indicates either potential damage to hardware or loss of data and tells you how to avoid the problem.

WARNING: A WARNING indicates a potential for property damage, personal injury, or death.

Copyright © 2025 Dell Inc. All Rights Reserved. Dell Technologies, Dell, and other trademarks are trademarks of Dell Inc. or its subsidiaries. Other trademarks may be trademarks of their respective owners.

## Contents

| Figures..........................................................................................................................................5                                                                                                                                                                                                       |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Tables........................................................................................................................................... 6                                                                                                                                                                                                      |
| Chapter 1: Installing the Virtual Appliance..................................................................................... 7                                                                                                                                                                                                                       |
| Dell SRM virtual appliance installation overview..........................................................................................................7                                                                                                                                                                                              |
| Installation checklist............................................................................................................................................................8                                                                                                                                                                      |
| Dell SRM vApp deployment process flow......................................................................................................................9                                                                                                                                                                                             |
| Customizing vApp Configuration .................................................................................................................................. 10                                                                                                                                                                                     |
| Installing the 4VM vApp................................................................................................................................................... 10                                                                                                                                                                            |
| Install additional Dell SRM vApp VMs overview......................................................................................................... 12                                                                                                                                                                                                |
| Deploy Scaleout VMs in Existing vApp......................................................................................................................... 12                                                                                                                                                                                         |
| Deploying Collector vApp VMs in different datacenters..........................................................................................13                                                                                                                                                                                                        |
| Post deployment, pre-startup tasks..............................................................................................................................14                                                                                                                                                                                       |
| Adjusting the VMs............................................................................................................................................................. 15                                                                                                                                                                        |
| 15                                                                                                                                                                                                                                                                                                                                                       |
| Adding disk space..............................................................................................................................................................                                                                                                                                                                          |
| DataStores...........................................................................................................................................................................15 Modifying the start order of the vApps........................................................................................................................15 |

| Installing and configuring the Primary Backend host...............................................................................................                                    | 28                                                                                                                                       |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| Installing and configuring the Additional Backend hosts.........................................................................................                                      | 29                                                                                                                                       |
| Installing and configuring the Collector host..............................................................................................................29                         |                                                                                                                                          |
| Installing and configuring the Frontend host..............................................................................................................30                          |                                                                                                                                          |
| Scaling-out a Dell SRM environment with Additional Backend hosts...................................................................                                                   | 31                                                                                                                                       |
| Scaling-out a Dell SRM environment with Collector hosts.....................................................................................33                                        |                                                                                                                                          |
| Verifying MySQL Database Grants...............................................................................................................................34                      |                                                                                                                                          |
| Updating firewall ports in Red Hat and SLES servers..............................................................................................35                                   |                                                                                                                                          |
| Editing new actions scripts.............................................................................................................................................36            |                                                                                                                                          |
| Verifying that the services are running........................................................................................................................37                     |                                                                                                                                          |
| Troubleshooting service start-up problems on UNIX..........................................................................................37                                         |                                                                                                                                          |
| Troubleshooting service start-up problems on Windows..................................................................................                                                | 37                                                                                                                                       |
| Logging in to the user interface....................................................................................................................................                  | 38                                                                                                                                       |
| Connecting to Administration.........................................................................................................................................38               |                                                                                                                                          |
| Chapter 5: Using the Dell SRM Setup Wizard.............................................................................. 39                                                           | Chapter 5: Using the Dell SRM Setup Wizard.............................................................................. 39              |
| Using the Discovery Wizard............................................................................................................................................39              |                                                                                                                                          |
| Chapter 6: Dell SRM Configuration Tools..................................................................................... 41                                                       | Chapter 6: Dell SRM Configuration Tools..................................................................................... 41          |
| Dell SRM configuration tools...........................................................................................................................................41             |                                                                                                                                          |
| Creating the Dell SRM-Conf-Tools answers file........................................................................................................                                 | 41                                                                                                                                       |
| Chapter 7: Uninstallation.............................................................................................................43                                              | Chapter 7: Uninstallation.............................................................................................................43 |
| Overview............................................................................................................................................................................. | 43                                                                                                                                       |
| Stopping Dell M&R platform services on a UNIX server.........................................................................................43                                       |                                                                                                                                          |
| Uninstalling the product from a UNIX server.............................................................................................................                              | 43                                                                                                                                       |
| Stopping Dell M&R platform services on a Windows server..................................................................................44                                           |                                                                                                                                          |
| Uninstalling the product from a Windows server......................................................................................................44                                |                                                                                                                                          |
| Uninstalling a SolutionPack.............................................................................................................................................44            |                                                                                                                                          |
| Remove a Server and Delete vApp...............................................................................................................................44                      |                                                                                                                                          |
| Appendix A: Unattended Installation............................................................................................46                                                     | Appendix A: Unattended Installation............................................................................................46        |
| Unattended installation....................................................................................................................................................46         |                                                                                                                                          |
| Unattended installation arguments for Linux.............................................................................................................                              | 46                                                                                                                                       |
| Unattended installation arguments for Windows......................................................................................................                                   | 46                                                                                                                                       |
| Appendix B: Documentation Feedback.........................................................................................48                                                         |                                                                                                                                          |

## Figures

|   1 | Dell SRM vApp deployment process flow.......................................................................................................... 10   |
|-----|------------------------------------------------------------------------------------------------------------------------------------------------------|
|   2 | Dell SRM binary deployment process flow........................................................................................................ 24   |

|   1 | Dell SRM Installation checklist................................................................................................................................8         |
|-----|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|   2 | Default usernames and passwords.......................................................................................................................17                 |
|   3 | Installation Options..................................................................................................................................................23 |

This chapter includes the following topics:

## Topics:

- Dell SRM virtual appliance installation overview
- Installation checklist
- Dell SRM vApp deployment process flow
- Customizing vApp Configuration
- Installing the 4VM vApp
- Install additional Dell SRM vApp VMs overview
- Deploy Scaleout VMs in Existing vApp
- Deploying Collector vApp VMs in different datacenters
- Post deployment, pre-startup tasks
- Adjusting the VMs
- Adding disk space
- DataStores
- Modifying the start order of the vApps

## Dell SRM virtual appliance installation overview

You can install Dell SRM as a virtual appliance (vApp) in a supported VMware environment. This guide describes the deployment process using the vSphere vCenter Client. The Dell SRM vApp can also be installed using the vSphere Web-based Client, but the details are different and not in this guide.

The vApp is based on SuSE Enterprise SLES 15 SP4.

The product includes the latest version of MySQL Community Server (GPL).

Do not add any binary VMs into the vApp container (including any Dell SRM binary VMs).

The procedures enable you to install two types of software:

- NOTE: The password policy suggests using passwords with more than 14 characters in length.
- NOTE: For vApp based and SLES-based binary SRM deployments, SRM 5.1.0.0 is supported only on SLES 15 SP4.
- NOTE: SUSE Linux Enterprise 15 guest operating system option is not available in Hardware version 13 (ESXi 6.5) and earlier.
- NOTE: In upgraded setup, Scheduled Report to a remote location using FTP option will not work as FW\_TRUSTED\_NETS in the file /etc/sysconfig/SuSEfirewall2 will be missing because of firewall changes in SLES 15 SP4.

Remote Transfer using FTP to work, Run the following commands in the path /etc/firewalld/zones :

1. firewall-cmd --permanent --zone=trusted --add-source=&lt;ip-of-ftp&gt;
2. firewall-cmd --reload

Once the command is run, a success message is displayed and a trusted.xml file is generated.

## Core software

The core software is a reporting solution that is built on a scalable architecture of backends frontends, and distributed collectors. When you install the core software, you establish the foundation for the product, which provides common capabilities, functions, and user interfaces. Besides, the following separate software products are preinstalled with Dell SRM: Dell SRM 4.7 SOFTWARE IMAGE (453-010-807) and SLES 15 SP4 SW GPL3 OPEN SOURCE SOFTWARE (453-010-808).

## Installing the Virtual Appliance

## SolutionPack

SolutionPack are software components that support Dell and third-party storage infrastructure components. Each SolutionPack enables you to select a specific report in the UI. To learn more about the SolutionPack that Dell SRM supports, see the following documents:

- Dell SRM Support Matrix
- Dell SRM Release Notes
- Dell SRM SolutionPack Guide

Dell SRM vApps are distributed using Open Virtualization Format (.ovf) files. Depending on the environment requirements, use the 4VM vApp .OVF or the 1VM vApp .ovf files.

## 4VM vApp OVF

## 1VM vApp OVF

Enables you to install four VMs (Frontend, Primary Backend, Additional Backend, and one Collector). ADG directory that is used by the auto configuration process of the vApp VMs includes a vApp VM. The 4VM vApp automatically configures the Collector host to have 48 GB of memory and 8 CPUs. The following SolutionPack are preinstalled on the Collector host:

- Brocade FC Switch
- Cisco MDS/Nexus
- Dell PowerScale
- Dell Unity/VNX/VNXe
- Dell EMC VMAX
- Dell VMAX/PowerMax
- VMware vSphere and vSAN
- Dell VPLEX
- Dell EMC XtremIO
- Block Chargeback
- System Health
- Configuration Compliance

Enables you to install a single vApp VM. The options are Frontend, Primary Backend, Additional Backend, Collector, and All-in-One. You can use this option to install additional Collectors and Additional Backend VMs to scale out the existing Dell SRM installation. You can add a single vApp VM (Collector or Additional Backend) to an existing vApp container that was created with the 4VM vApp. When you restart the vApp container, the new VMs are autoconfigured into Dell SRM. The auto configuration process includes an ADG directory that is used by vApp VMs. You can also use the 1VM vApp for small All-In-One proof of concept solutions.

The Collector host that is deployed with the 1VM is configured with 48 GB of memory and 8 CPUs.

Dell SRM vApp VMs have properties that are used to configure the host level networking information. If the vApp VM/folder has to be moved from one vCenter to another, you must use the vCenter export and import procedure. Do not use the vCenter remove from inventory method. For additional details, see Guidelines for Managing VMware vApp Solutions (h15461).

Dell SRM vApps fully support the VM vMotion and Storage vMotion DRS functions within the ESX clusters of vCenter.

## Installation checklist

Below checklist items are required for successful Dell SRM installation.

Table 1. Dell SRM Installation checklist

| Step                               | Description                                                                                                                                                    |
|------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Hardware and software requirements | Ensure you meet the following requirements as described in the compatibility or support matrix. ● Operating system requirements ● Browser requirements ● Tools |
| Download the software              | Download the software from Dell Support Site and obtain required license information.                                                                          |
| Network Requirements               | Identify port availability, IP address, Subnet, and Gateway based on your network configuration.                                                               |

Table 1. Dell SRM Installation checklist (continued)

| Step               | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Network Protection | Add the SRM-related ports to the firewall exclusion list or turn off firewall settings. Ensure the anti-virus does not block any SRM ports.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Installation       | ● Ensure you have Dell SRM OVF or binary installation files based on the installation requirement. ● For 1VM vAPP installation: Ensure to have: ○ 32 GB memory ○ 4 CPUs ● For 4VM vAPP installation: Ensure to have: ○ The vCenter location where you plan to deploy the appliance. ○ A single DataStore required for deployment. ○ Enable DRS. ○ Static IP address for each VM. This IP address must be registered in DNS with forward and reverse lookup before you begin the deployment. ○ Gateway ○ Netmask ○ DNS servers ○ Domain search strings: For a distributed environment, the domains must be entered for each of the Dell SRM servers. |
| Login credentials  | Ensure you have access to the SRM environments with default usernames and passwords.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Documentation      | See Dell Support Site for detailed documentation.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |

NOTE: vApp deployments on VMware vSphere 8.0.1 requires a work around. See Deployment of customized OVA on vCenter 8.0 is missing IP address field under Networking section (93677)

## Dell SRM vApp deployment process flow

You can install Dell SRM as a virtual appliance (vApp) in a supported VMware environment.

The following figure depicts the vApp deployment workflow.

Figure 1. Dell SRM vApp deployment process flow

<!-- image -->

## Customizing vApp Configuration

This section provides information about custom vApp configuration.

Do not install any external packages or software, either by using manual ssh/rpm/zypper or any other means on newly shipped SRM vApp servers.

To install external packages/ software on the servers, it is mandatory to reach out to the support executives for assessment of software and operation system compatibility with vApp and any other recommendations for usage.

- NOTE: There are known limitations regarding Operating system and hence, customizing the vApp could lead to certain Operating system functionality problems.

## Installing the 4VM vApp

You can deploy the Dell SRM 4VM appliance from an OVF template using a vCenter Client. The installer creates the vApp container and deploys 4 vApp VMs (Frontend, Primary Backend, Additional Backend, and one Collector) inside the vApp container.

## Prerequisites

- Gather the following information:
- vCenter location where you plan to deploy the appliance.
- A single DataStore is needed for deployment. After completing the deployment, you can use Storage vMotion to move the VM's storage to different DataStores. Dell provides the final storage size per VM.
- Static IP address for each VM: This IP address must be registered in DNS with forward and reverse lookup before you begin the deployment.
- Gateway
- Netmask
- DNS servers
- Domain search strings. For a distributed Dell SRM environment, the domains for all the Dell SRM servers must be entered for each of the Dell SRM servers.

NOTE: While deploying, SRM 4VM vApp do not use underscore(\_) in the SRM host names.

## Steps

1. Browse to the Support by Product (Dell Support) page for Dell SRM .
2. Click Downloads .
3. Download the Dell SRM &lt;version number&gt; vApp Deployment Zip file.

Each download has a checksum number. Copy the checksum number and validate the integrity of the file using an MD5 checksum utility.

The host being connected to the vCenter should be local to the ESXi servers for the quickest deployment. Locate the 4VM OVF deployment file on the host running the vCenter client or place the files on the DataStore.

4. Open vCenter Client and connect to the vCenter Server that manages the VMware environment.

Do not run vCenter Client on a VPN connection.

For the fastest deployment time, the host running vCenter Client should be local to the ESXi servers.

5. Select where in the vCenter ESXi cluster/server you want to deploy the VMs for Dell SRM.
6. Select File &gt; Deploy OVF Template .
7. In the Source step, locate the *4VM\_vApp.ovf and system.vmdk file.
8. Click Next

.

9. In the OVF Template Details step, review the details of the loaded .OVF file, and then click Next .
10. In the End User License Agreement step, review the license agreement. Click Accept , and then click Next .
11. In the Name and Location step:
- a. Specify a new name or accept the default name for the appliance.
- b. Specify an inventory location for the appliance in the VMware environment.
- c. Click Next .
12. Select the Resource Pool or the folder where the deployment places the Dell SRM VMs, and click Next in the Resource Pool step.
13. In the Storage step, select the destination storage (DataStore) for the virtual machine files and click Next . The compatibility window states if there is insufficient disk space on the selected DataStore, and a warning is displayed

when you click Next .

14. In the Disk Format step, select the storage space provisioning method, and then click Next .

| Option                   | Description                                                                                |
|--------------------------|--------------------------------------------------------------------------------------------|
| Thin-provisioned format  | On-demand expansion of available storage, which is used for newer data store file systems. |
| Thick-provisioned format | Appliance storage that is allocated immediately and reserved as a block.                   |

<!-- image -->

NOTE: Dell SRM is fully supported on thin-provisioned storage at the array or virtualization level. Thin on thin is acceptable, but not recommended.

15. In the Network Mapping step, select a destination network for all of the VMs, and then click Next . With SRM 4.2 onwards, the only option is to place all 4 VMs on the same ESX server network. It is known as the simplified

network deployment.

16. In the IP Address Allocation step, choose the IP allocation policy and IP protocol to use, and then click Next .
17. In the Properties step, provide the values for each of the VMs, and then click Next .
18. In the Ready to Complete step, review the list of properties for the appliance, and then click Finish . A pop-up window opens in vCenter Client showing the deployment progress.
19. After the 4VM deployment finishes, in the Deployment Completed Successfully dialog box, click Close .
20. Before you power on the vApp, make the following changes to the VM configurations:
- To expand the file system, add additional VMDK disks.
- Adjust the vCPU and VM Memory as specified in the Dell SRM design.
21. Use the 1VM OVF to add any Additional Backend VMs and Collector VMs as described in the following section:

## Install additional Dell SRM vApp VMs overview

You can scale Dell SRM larger by adding additional databases (Additional Backends), Collectors, and slave Frontends. Deploying additional VMs are required to scale the Dell SRM environment. This process includes adding Additional Backend and Collector VMs to the existing Dell SRM vApp container and deploying Collector vApp VMs in different data centers.

For POC and lab installs, an All-In-One solution is available. (The All-In-One solution is not supported for managing production environments because it does not scale.)

The vApp is based on SuSE Enterprise SLES 15 SP4.

The product includes the latest version of MySQL Community Server (GPL).

Do not add any binary VMs into the vApp container (including any Dell SRM binary VMs).

The procedures enable you to install two types of software:

## SolutionPacks

Software components that support Dell and third-party storage infrastructure components. Each SolutionPack enables you to select a specific report in the UI. To learn more about the SolutionPacks that Dell SRM supports, see the following documents:

- Dell SRM Support Matrix
- Dell SRM Release Notes
- Dell SRM SolutionPack Guide

Dell SRM vApps are distributed using Open Virtualization Format (.ovf) files. Use the 1VM vApp OVF files to scale out Additional Backends, Collectors, and Frontends.

## 1VM vApp OVF

Enables you to install a single vApp VM. The options are All-in-one, Frontend, Additional Backend, Collector, and Minimal . You can use this option to install additional Collectors and Additional Backend VMs to scale out the existing Dell SRM installation. You can add a single vApp VM (Collector or Additional Backend) to an existing vApp container that was created with the 4VM vApp. When you restart the vApp container, the new VMs are automatically configured into Dell SRM. vApp VMs include an ADG directory that the automatic configuration process uses.

Dell SRM vApp VMs have properties that are used to configure the host level networking information. If the vApp VM/folder has to be moved from one vCenter to another, you must use the vCenter export and import procedure. Do not use the vCenter remove from inventory method.

Dell SRM vApps fully support the VM vMotion and Storage vMotion DRS functions of vCenter.

## Deploy Scaleout VMs in Existing vApp

Dell SRM supports adding additional backends and collectors either inside or outside of the SRM vApp. Use this procedure to deploy scaleout VMs inside of the SRM vApp.

## Prerequisites

1. Log in to the vCenter managing the vApp you want to scale out.
2. Right-click the vApp and select Shut Down . Wait for all VMs in the vApp to shut down completely.

## Steps

1. Browse to the Support by Product page for Dell SRM (Dell Support Page) page.
2. Click Downloads .
3. Download the Dell SRM &lt;version number&gt; vApp Deployment Zip file.

The host being connected to the vCenter should be local to the ESX servers for the quickest deployment. Locate the 1VM OVF deployment file on the host running the vCenter client or place the files on the DataStore.

4. Open the vSphere Client and connect to the vCenter Server that manages the VMware environment.
5. Select the resource pool where you want to deploy the VMs for Dell SRM.
6. Select File &gt; Deploy OVF Template .
7. In the Source step, locate the 1VM OVF file.
8. Click Next .

To save time, deploy the appliance in the same local area network (LAN) that the VMware ESX/ESXi servers share. Deployment takes approximately 5 minutes to 15 minutes. Deployment across a WAN can take 2 hours or more.

9. In the OVF Template Details step, review the details of the loaded .ovf file and click Next .
10. In the End User License Agreement step, review the license agreement, click Accept , and then click Next .
11. In the Name and Location step, accept the default name (Dell SRM) or type a Name for the appliance. Specify an Inventory Location for the appliance in the VMware environment. Click Next .
12. Select the host or cluster where you want to run the deployed template and click Next .
13. Select the destination storage for the virtual machine files and click Next .
14. In the Disk Format step, select the storage space provisioning method and click Next .

| Option                   | Description                                                                                 |
|--------------------------|---------------------------------------------------------------------------------------------|
| Thin-provisioned format  | On-demand expansions of available storage, which is used for newer data store file systems. |
| Thick-provisioned format | Appliance storage that is allocated immediately and reserved as a block.                    |

<!-- image -->

NOTE: Dell Technologies recommends the thin-provisioned format option when the vApp is deployed in a highperformance environment.

15. In the Network Mapping step, select a destination network that has an IP Pool that is associated with it for each of the VMs and click Next .
16. In the IP Address Allocation step, choose the IP allocation policy, the IP protocol to use, and click Next .
17. In the Properties step, provide the values for each of the VMs, and click Next .
18. In the Ready to Complete step, review the list of properties for the appliance and click Finish .

A status bar opens in the vSphere Client showing the deployment progress.

19. Click Close in the Deployment Completed Successfully dialog box.

## Results

1. Wait for all VMs to complete deployment.
2. Modify the start order of the vApp entities as described in Modifying the start order of the vApps.
3. Power on vApp after all deployments are completed. Right-click the vApp and select Power On . A built-in service detects the new VMs and performs the needed configurations.

## Deploying Collector vApp VMs in different datacenters

Use this procedure to deploy remote Collectors in different datacenters.

## Steps

1. Browse to the Support by Product (Support by Product) page for Dell SRM.
2. Click Downloads .
3. Download the Dell SRM &lt;version number&gt; vApp Deployment Zip file. Each download has a checksum number. Copy the checksum number and validate the integrity of the file using an MD5

checksum utility.

The host being connected to the vCenter should be local to the ESX servers for the quickest deployment. Locate the 1VM OVF deployment file on the host running the vCenter client or place the files on the DataStore.

4. Open the vCenter Client and connect to the vCenter Server that manages the VMware environment.
5. Select File &gt; Deploy OVF Template .
6. In the Source step, locate the 1VM OVF file.
7. Click Next .
8. In the OVF Template Details step, review the details of the loaded .ovf file, and click Next .
9. In the End User License Agreement step, review the license agreement. Click Accept , and then click Next .
10. In the Name and Location step:

- a. Specify a new name or accept the default name for the appliance.
- b. In the Inventory Location, select the Datacenter and sub-location where the appliance is deployed. To define the exact location, browse through the folder levels.
- c. Click Next .
11. In the Deployment Configuration step, select the Collector Appliance from the drop-down list.
12. In the Host/Cluster step, select the ESX server or ESX Cluster, and click Next .
13. In the Resource Pool step, select the Resource Pool or the folder where the deployment places the Dell SRM VMs, and click Next .
14. In the Storage step, select the DataStore for the virtual machine files, and then click Next .
15. In the Disk Format step, select the storage space provisioning method, and then click Next .
16. In the Network Mapping step, select a destination network for the VM, and then click Next .
17. In the IP Address Allocation step, choose the Fixed IP allocation policy and the IP protocol to use, and then click Next .
18. In the Properties step, provide the values for each field, and then click Next .
19. In the Ready to Complete step, review the list of properties for the appliance, and then click Finish . A menu that shows the deployment progress opens in vCenter Client.
20. After the deployment finishes, in the Deployment Completed Successfully dialog box, click Close .
21. Repeat these steps for each Collector that is required to install in a remote datacenter.
22. Before you power on the vApp, make the following changes to the VM configurations:
- a. To expand the file system, add additional VMDK disks.
- b. Adjust the vCPU and VM Memory as specified in the Dell SRM design.
23. If you are adding a remote collector that is deployed in a remote datacenter to the Dell SRM vApp, use the steps for adding a collector that is described in Dell SRM configuration tools. These steps finish the collector configuration and add the collector to the Dell SRM UI.

| Option                   | Description                                                                                 |
|--------------------------|---------------------------------------------------------------------------------------------|
| Thin-provisioned format  | On-demand expansions of available storage, which is used for newer data store file systems. |
| Thick-provisioned format | Appliance storage that is allocated immediately and reserved as a block.                    |

## Results

For Collectors installed in a remote datacenter, you are required to use the Dell SRM UI to make some configuration changes to the Load Balancer Connectors, generic-rsc, and generic-snmp installed on each Collector.

## Post deployment, pre-startup tasks

After you have deployed the vApp VMs, but before you start Dell SRM, you must make some configuration changes as specified in the Dell SRM design that is provided by Dell.

## About this task

To complete the configuration changes:

## Steps

1. Adjust the Collector VM memory.
2. Adjust the Collector VM CPUs.
3. To conform to naming policies, change the vApp VM name in vCenter.
4. Increase the VM storage per VM.
5. Move the vApp VM storage to its assigned datastore.
6. Modify the vApp container startup order.

## Adjusting the VMs

The Collectors (and possibly the Frontend) need the number of CPUs, the size, and the memory adjusted based on the Dell SRM design. To make these updates, edit the settings of each Collector vApp VM.

## Steps

1. Change the vApp VMs name to default VM to meet VM naming standards.
2. Edit the VM settings and select the Options tab to make the updates.

## Adding disk space

All vApp VMs are deployed with 132 GB of storage. Each Dell SRM VM needs larger storage. The total Dell SRM VM storage size is based on the Dell SRM design. Edit the settings of each vApp VM and add a VMDK (virtual machine disk). Subtract 132 GB from the total storage size that is specified in the sizing plan that is provided by Dell, and add a VMDK (virtual machine disk) with the size of the additional storage needed. The VM can be running during this process.

## Steps

1. From the vCenter Console, select the individual VM where you want to add new disk storage.
2. Select Edit Settings on the virtual machine and click Add .
3. Select Hard Disk and click Next .
4. Select Create a new virtual disk and click Next .
5. Specify the disk size, the provisioning type, the location of the disk and click Next .
6. Specify the virtual device node (the default value should be OK ) and click Next .
7. Review the options and click Finish .
8. After Dell SRM is up and running, connect to the Linux host. You can access a login prompt through the vCenter Client console or using an SSH tool such as PuTTY.
9. At the root command prompt, type the command expand\_disk.pl .

The script merges the new VMDK with the existing files system while the VM is still running. Use the df -h command when the script is finished to see the new file system size.

NOTE: Using this script extends maximum 1000 GB disk space in one execution.

## DataStores

The 4VM vApp deployment places the 4 VMs on a single DataStore. Migrate the VM from this DataStore to its assigned DataStore. The required storage per Dell SRM VM can be found in the design that is provided by Dell.

For reference, the target storage sizes are as follows:

- Frontend - 320 GB
- Primary Backend - 800 GB and larger
- Additional Backends - 1 TB and larger
- Collector - 300 GB or larger

With the VM in a powered off state, use the Storage vMotion feature to move the VM to a new DataStore.

## Modifying the start order of the vApps

Modify the start order of the vApps in a Dell SRM installation whenever you add a vApp VM to the vApp container.

## Steps

1. Right-click the vApp and select Edit Settings .

2. Browse to the Start Order tab.
3. Move the new VMs into the proper group that is based on the following:
- Group 1: All Additional Backends
- Group 2: Primary Backend
- Group 3: All Collectors
- Group 4: Frontend
4. In the Shutdown Action section, select Guest Shutdown from the Operation list.
5. Change the elapsed time to 600 s.
6. Click OK .

This chapter includes the following topics:

## Topics:

- Starting the vApp
- Dell SRM Passwords
- Verifying that the services are running
- Logging in to the user interface
- Verifying MySQL Database Grants
- Verifying and configuring the user process limits for a vApp installation

## Starting the vApp

The vApp container settings control the Dell SRM startup order.

## Prerequisites

Edit the start-up as described in Post deployment, pre-startup tasks.

## About this task

Always start and stop the vApp using the vApp container. Do not stop any of the individual VMs inside the vApp container. You can start and stop Remote Collectors in other datacenters independently. Use vCenter Client to start the vApp.

The initial startup of Dell SRM takes about 10 minutes for the VMs to be shown as started in vCenter, because it requires an internal configuration process to configure each VM completely. You can monitor this process by opening the vCenter Console for the VM.

## Steps

1. Dell SRM will be ready for login after the additional background processing completes.
2. Log in to the URL https:// &lt;Frontend-hostname&gt; :58443/APG .

## Dell SRM Passwords

Passwords control access to Dell SRM and the internal communications.

The web-based user passwords are managed through the Administration user interface. The Dell SRM internal communications passwords are managed through the System Admin &gt; Settings &gt; Central Configuration Repository . For additional details, see the Security Configuration Guide.

## Table 2. Default usernames and passwords

| Environment                                     | Default username and password                            |
|-------------------------------------------------|----------------------------------------------------------|
| Web-based console that is accessed in a browser | admin / changeme . Ensure that you change this password. |
| ws-user                                         | watch4net                                                |
| MySQL                                           | watch4net                                                |
| apg user                                        | watch4net                                                |
| MySQL root user                                 | watch4net                                                |

## Working with Dell SRM

## Table 2. Default usernames and passwords  (continued)

| Environment                                                                            | Default username and password   |
|----------------------------------------------------------------------------------------|---------------------------------|
| Linux guest Operating System appliance console that is accessed through SSH or vCenter | root / Changeme1!               |

## Verifying that the services are running

Verify that the services are running on each host by obtaining the status.

## Prerequisites

Ensure that you have a login with root, APG, or system administrator privileges. The user apg is the account that the application uses instead of root.

## Steps

1. Type the command for the operating system from the bin directory of the installation:
2. Verify that each service has a status of running in the output.

| Operating system   | Command                               |
|--------------------|---------------------------------------|
| UNIX               | manage-modules.sh service status all  |
| Windows            | manage-modules.cmd service status all |

## Troubleshooting service start-up problems on UNIX

Check the log files when services do not start.

## Prerequisites

Ensure that you have logged in with root to check the log files.

## Steps

- The default path is /opt/APG/ .

The list of available log files vary depending on the type of server (Frontend, Backend, or Collector).

Databases/MySQL/Default/data/[SERVER NAME].err Backends/Alerting-Backend/Default/logs/alerting-0-0.log Backends/APG-Backend/Default/logs/cache-0-0.log Collecting/Collector-Manager/Default/logs/collecting-0-0.log Web-Servers/Tomcat/Default/logs/service.log Tools/Task-Scheduler/Default/logs/scheduler-0-0.log Tools/Webservice-Gateway/Default/logs/gateway-0-0.log

## Logging in to the user interface

Log in to the user interface to use and edit reports, manage users, and customize the interface to meet the needs.

## Steps

1. Open a browser and type the following URL: https:// &lt;Frontend-hostname&gt; :58443/APG
2. Type the login credentials. The default username is admin . The default password is changeme
3. Click Sign In .

.

<!-- image -->

## Verifying MySQL Database Grants

After installing and configuring the Dell SRM hosts, cross-check the grant privileges that are configured for the Dell SRM servers that are listed in the SRM-Conf-Tools configuration file.

## About this task

Database grants for Collector hosts are not required.

Where the script configure grants for Collector hosts, it is not needed and can be ignored or deleted.

NOTE:

For mysql-client.sh to work on RHEL8.x, RHEL9.x and SLES 15 SP4, libncurses.so.x is required.

Example: RHEL 9

sudo ln -s /lib64/libncurses.so.6 /lib64/libtinfo.so.6

## Steps

1. Run the following script:
2. When prompted, select root as the username, mysql for the database, and watch4net as the password.
3. Run the following query:

```
/opt/APG/bin/mysql-client.sh
```

```
mysql> SELECT user, host, db, select_priv, insert_priv, grant_priv FROM mysql.db;
```

## Example

The following table is an example of the configuration that you should see on an Additional Backend host:

<!-- image -->

## Verifying and configuring the user process limits for a vApp installation

Verify and configure the limits for the apg user account on all VMs to a maximum of 512000.

## Prerequisites

Ensure that you have a login with root privileges.

## Steps

1. Edit the security file: vi /etc/security/limits.conf.
2. Update the following lines for APG user to change limits from 65534 to 512000.
- apg hard nofile 512000
- apg soft nofile 512000
- apg hard nproc 512000
- apg soft nproc 512000
3. Save the file.
4. To verify the changes, type the following command: su apg -c 'ulimit -n -u' open files (-n) 512000.

max user processes (-u) 512000.

5. To restart the services, type the following commands from the /opt/APG/bin directory of the installation:

/opt/APG/bin/manage-modules.sh service stop auto

/opt/APG/bin/manage-modules.sh service start auto

/opt/APG/bin/manage-modules.sh service status all

<!-- image -->

## Configuring Remote Collectors

This chapter includes the following topics:

## Topics:

- Adding remote Collectors to the existing Dell SRM deployment.
- Reconfiguring the LBC, Generic-SNMP, and Generic-RSC

## Adding remote Collectors to the existing Dell SRM deployment.

This section provides details on the procedure to add vApp collector and multiple remote vApp collectors to the existing SRM deployments.

## About this task

When you add a vApp Collector VM inside the vApp container, it is configured as a Collector host with all the components. You can add the Collector through Administration Config &gt; Settings &gt; Configure Servers &gt; Register a Server .

If you have multiple remote vApp collectors, you can use the launch-collector-configuration.sh -c /sw/srmhosts script and register the Collectors through Config &gt; Settings &gt; Configure Servers &gt; Register a Server . For details about using the SRM-Config-Tool, see Dell SRM configuration tools.

Database grants for Collector hosts are not required.

Use the following procedure to add a binary Collector.

NOTE: For Windows, use .cmd instead of .sh , and / instead of \ for directories.

## Steps

1. Install the Dell SRM software as described in Installing on Linux or Installing on Windows Server.
2. Configure the binary collectors:
- a. Browse to the following directory:

Linux: cd /opt/APG/bin

Windows: cd Program Files/APG/bin

- b. Run the Collector configuration script:

launch-collector-configuration.sh -c /sw/srm-hosts

- c. Verify that all the services are running:

manage-modules.sh service status all

3. On the Frontend, run the following command:

launch-frontend-scale-collector.sh -c /sw/srm-hosts

4. Verify the Remote Collector configuration through the Dell SRM UI.

## Reconfiguring the LBC, Generic-SNMP, and GenericRSC

If a collector is powered on outside of the vApp, you must reconfigure the Load Balancer Connector, generic-snmp, and generic-rsc.

## Steps

1. Under Config &gt; Settings &gt; Manage Core Components , click Reconfigure icon for a Load Balancer Connector for each remote Collector. Use the following settings:
- Arbiter Configuration- send data to the Primary Backend over port 2020.
- Alerting on data collection- send data to the Primary Backend over port 2010.
- Frontend web service- send data to the Frontend over port 58443.
2. Repeat these steps for each remote Collector's Load Balancer Connector.
3. Under Config &gt; Settings &gt; Manage Core Components click Reconfigure icon for a generic-snmp or generic-rsc instance. Use the following settings:
- Data Configuration: send data to the localhost over port 2020.
- Frontend web service: send data to the Frontend over port 58443.
- Topology Service: send data to the Primary backend.
4. In the SNMP Collector Name field, type the FQDN of the collector host.
5. Repeat the steps for each instance of generic-snmp and generic-rsc.

## Verifying and Configuring the user process limits for a vApp installation

## About this task

Follow the steps mentioned in the Verifying and configuring the user process limits for a vApp installation the verify and configure the user process limits for a vApp installation.

<!-- image -->

## Installing Using the Binary Installer

This chapter includes the following topics:

## Topics:

- Installation options for a standard installation
- Dell SRM binary deployment process flow
- General Dell SRM requirements
- Linux requirements
- Installing on Linux
- Installing on Windows Server
- Configuring binary Dell SRM SRM-Conf-Tools
- Installing and configuring the Primary Backend host
- Installing and configuring the Additional Backend hosts
- Installing and configuring the Collector host
- Installing and configuring the Frontend host
- Scaling-out a Dell SRM environment with Additional Backend hosts
- Scaling-out a Dell SRM environment with Collector hosts
- Verifying MySQL Database Grants
- Updating firewall ports in Red Hat and SLES servers
- Editing new actions scripts
- Verifying that the services are running
- Logging in to the user interface
- Connecting to Administration

## Installation options for a standard installation

Learn how to install the platform using a binary installation package.

The platform infrastructure consists of four types of hosts:

- Frontend host
- Backend host (Primary Backend)
- Minimal host (Additional Backend)
- Collector host
- All-In-One (recommended for POCs and testing only)

NOTE: For vApp based and SLES-based binary SRM deployments, SRM 5.1.0.0 is supported only on SLES 15 SP4.

- NOTE: You can only have one Primary Backend host. You can add Additional Backend hosts with up to four Time-Series databases on each Additional Backend host. Use the Linux operating system for Dell SRM deployments with 5 million metrics or more. Dell Technologies recommends that the core Dell SRM hosts (Frontend, Primary Backend, and Additional Backend hosts). The product includes the latest version of MySQL Community Server (GPL).

## Table 3. Installation Options

| Installation Options         | Frontend         | Primary Backend   | Additional Backend                                    | Collector         |
|------------------------------|------------------|-------------------|-------------------------------------------------------|-------------------|
| Linux Installation Options   | [f]rontend       | [b]ackend         | [m]inimal                                             | [c]ollector       |
| Windows Installation Options | Frontend Modules | Backend Modules   | Base Installation (with none of the modules selected) | Collector Modules |

## Dell SRM binary deployment process flow

The following figure depicts the SRM binary-based deployment workflow.

Figure 2. Dell SRM binary deployment process flow

<!-- image -->

## General Dell SRM requirements

These requirements are for a minimal deployment. In a production environment, the requirements vary depending on the provisioned load, and you must include careful planning and sizing before beginning the deployment.

The Dell SRM Workbench and the SRM Documentation document that is associated with the specific release provides guidance for SolutionPacks and object discovery.

For details about configuring CA SSL certificates, see the SRM Documentation.

The environment must meet the following requirements:

- 64-bit operating system (Linux or Windows)
- Frontend - 16 GB RAM, 4 CPUs, and 320 GB disk storage
- Backends - 24 GB RAM, 4 CPUs, and disk storage determined by the sizing
- Collectors - 16 GB to 64 GB RAM, 4 to 8 CPUs, and 130+ GB disk storage
- Forward and Reverse IP and DNS lookups must work on each server.
- NOTE: The following sections use Linux commands and directories as examples. For Windows, use .cmd instead of .sh , and / instead of \ for directories.

## Linux requirements

The environment must meet the following requirements. Changes should be made to the host, before continuing.

- /tmp folder larger than 2.5 GB
- SWAP files should be at least equal to the RAM size.
- On RedHat-like Linux, the SELinux should be disabled or reconfigured.
- The graphical desktop environment is not required.
- On some Linux distributions:
- MySQL server requires libaio1, libaio-dev, or libaio to start.
- The installation process requires extract.
- On the system, restart the apg services may not start.

## Installing on Linux

You can install the product on supported UNIX/Linux hosts. This procedure specifically uses the Linux installation procedure as an example.

## Prerequisites

- Ensure that you have a login with root privileges. This product must only be installed using root and root privileges.
- Ensure that the ports that are listed in the Ports Usage Matrix are enabled and a host or network firewall does not block them.
- Download the installation file from Dell Support Page, and place it in a folder (for example /sw ) on the server.
- MySQL Database is upgraded to latest version in SRM and Storage Monitoring and Reporting , Latest MySQL version requires Libnuma library to be installed on the system for binary installs on the Linux platform. Without this library, Install and Upgrade to SRM and Storage Monitoring and Reporting 4.4 or later fails. This library is included in vApp. vApp installation/ upgrade will not have this issue.
- NOTE: For vApp based and SLES-based binary SRM deployments, SRM 5.1.0.0 is supported only on SLES 15 SP4.

NOTE:

For mysql-client.sh to work on RHEL8.x, RHEL9.x and SLES 15 SP4,

Example: RHEL 9

sudo ln -s /lib64/libncurses.so.6 /lib64/libtinfo.so.6

## About this task

These instructions are meant to provide a high-level overview of the installation process. Detailed instructions are provided in the following sections.

## Steps

1. Log in to the server as root.
2. Browse to the /sw folder.
3. Change the permissions of the installer. For example: chmod +x &lt;file\_name&gt;.sh
4. Run the installer from the directory. For example: ./&lt;file\_name&gt;.sh
5. Read and accept the End User License Agreement.
6. Accept the default installation directory of /opt/APG or type another location.

## Configuring the user process limits for a Linux installation

Increase the user process limits for the apg user account to a maximum of 512000. This change enables services to open 512000 files and 512000 processes when needed. This step is required for proper functioning of the core software.

## Prerequisites

- Ensure that you have a login with root privileges.
- The core software that is installed on a server running Red Hat Enterprise Linux, SUSE Linux Enterprise Server (SLES), or any other supported Linux operating systems.

## Steps

1. Edit the security file: vi /etc/security/limits.conf .
2. Insert the following lines for the apg user below the line with #&lt;domain&gt; . In this example, the user is apg .

```
apg   hard  nofile  512000 apg   soft  nofile  512000
```

libncurses.so.x is required.

```
apg   hard  nproc   512000 apg   soft  nproc   512000
```

3. Save the file.
4. To verify the changes, type the following command:
5. In the /opt/APG/bin/apg.properties file, edit the hostname to an FQDN hostname:
6. To restart the services, type the following commands from the /opt/APG/bin directory of the installation:

```
su apg -c 'ulimit -n -u' open files                                  (-n)    512000 max user processes         (-u) 512000
```

```
#=================== # Common Properties #=================== hostname=lglba148.lss.emc.com
```

```
/opt/APG/bin/manage-modules.sh service stop all /opt/APG/bin/manage-modules.sh service start all /opt/APG/bin/manage-modules.sh service status all
```

## Configuring virus-scanning software

Running virus-scanning software on directories containing MySQL data and temporary tables can cause issues, both in terms of the performance of MySQL and the virus-scanning software misidentifying the contents of the files as containing spam.

## About this task

After installing MySQL Server, Dell Technologies recommended that you disable virus scanning on the directory that is used to store the MySQL table data (such as /opt/APG/Databases/MySQL/Default/data ). In addition, by default, MySQL creates temporary files in the standard temporary directory. To prevent scanning the temporary files, configure a separate temporary directory for MySQL temporary files and add this directory to the virus scanning exclusion list. To do it, add a configuration option for the tmpdir parameter to the my.ini configuration file.

## Installing on Windows Server

You can install the product on supported Windows Server hosts.

## Prerequisites

- Ensure that the \tmp folder is larger than 2.5 GB.
- Ensure that you have a login with system administrator privileges.
- Ensure that the ports that are listed in the Ports Usage Matrix are enabled and the firewall does not block them.
- Download the installation file from Dell Support Page, and place it in a folder (for example, C:\sw ) on the server.

## About this task

These instructions are meant to provide a high-level overview of the installation process. Detailed instructions are provided in the following sections.

## Steps

1. Browse to the C:\sw folder.
2. Double-click the .exe file.
3. Click Next on the Welcome screen.
4. Read and accept the End User License Agreement. Click I Agree .

5. Select the Destination Folder, and then click Next .
6. Click Install .
7. When the installation is complete, click Next .
8. Click Finish .
9. Verify that the hostname is an FQDN hostname in the Program Files\APG\bin\apg.properties file. If the hostname is a shortname, edit the file to change the hostname to an FQDN.
10. STOP: Repeat the Dell SRM installation and configuration process for all the servers in this deployment before proceeding.
11. Verify that the first line is this host's IP address, FQDN, and shortname in C: \windows\System32\drivers\etc\hosts file is not commented. Edit the file if it is not commented for the first time.
12. Restart the services, and troubleshoot any service that does not show a status of running .

manage-modules.cmd service restart all manage-modules.cmd service status all

## Configuring virus-scanning software

Running virus-scanning software on directories containing MySQL data and temporary tables can cause issues, both in terms of the performance of MySQL and the virus-scanning software misidentifying the contents of the files as containing spam.

## About this task

After installing MySQL Server, Dell Technologies recommends that you disable virus scanning on the directory that is used to store the MySQL table data (such as C:\Program Files\APG\Databases\MySQL\Default\data ). In addition, by default, MySQL creates temporary files in the standard Windows temporary directory. Configure a separate temporary directory for MySQL temporary files and add this directory to the virus scanning exclusion list to prevent scanning the temporary files. To perform this activity, add a configuration option for the tmpdir parameter to the my.ini configuration file.

## Configuring binary Dell SRM SRM-Conf-Tools

SRM-Conf-Tools are scripts that are pre-installed on each SRM host in the /opt/APG/bin directory. These scripts are used to configure the Dell SRM hosts the same way the vApp version is configured.

## About this task

The SRM-Conf-Tools scripts use an answers file to automatically configure the Dell SRM servers. You can use the Dell SRM-Conf-Tools scripts for the following scenarios:

## Steps

1. Initially configure a Frontend, Primary Backend, and Additional Backend servers.
2. Add new Additional Backend servers to an existing Dell SRM environment.
3. Add Collectors to the Frontend. If a Dell SRM-Conf-Tools script configuration fails, run it again could cause a miss-configuration. Clean up the Dell SRM from

that VM/Server and reinstall the product. Refer to Uninstallation

## Creating the Dell SRM-Conf-Tools answers file

Dell SRM-Conf-Tools is a command-line utility that can configure and add a single server or multiple servers to the Dell SRM environment. Dell SRM-Conf-Tools uses an answers file that you create that includes all of the Dell SRM hosts in all of the datacenters where Dell SRM is installed.

## Prerequisites

- The answers file is case sensitive and must be all lowercase.
- Create the file using notepad++ or the Linux VI editor.

- Name the file srm-hosts .

## About this task

The format of the answers file is: server\_type=hostname:os

- server\_type -The four basic types of Dell SRM servers
- Hostname -The server's FQDN. It matches the setting of the hostname variable in the apg.properties file. For Linux servers, it should always be the hostname plus the domain name (FQDN). For Windows, it could be the hostname (shortname) or the FQDN depending on how the Windows server resolution is configured (DNS, Active DNS, or Wins/ NetBios). A Wins resolution uses the hostname (shortname) in uppercase.
- OS -linux-x64 or windows-x64

## For example:

```
frontend=<FE_host>.lss.emc.com:linux-x64 primarybackend=<PBE_host>.lss.emc.com:linux-x64 additionalbackend_1=<ABE_host>.lss.emc.com:linux-x64 collector_1=<COLL_host>.lss.emc.com:linux-x64
```

This answers file can be modified later to add any new Collectors and Additional Backends. When the Dell SRM-Conf-Tools scripts run, they distinguish new servers from existing servers and make the necessary configuration changes.

Since the Dell SRM-Conf-Tools and the answers file are used for configuring additional servers at a later date, Dell Technologies recommends storing the files in a /sw directory in the / directory instead of the /tmp directory. This action should be performed because the /tmp directory could be deleted at any time.

## Installing and configuring the Primary Backend host

## Prerequisites

- Identify the host that you want to configure as the Primary backend host.
- Identify the hosts that you want to configure as the Frontend, Collectors, and Additional backends.
- Ensure that you have created an answers file as described in Creating the Dell SRM-Conf-Tools answers file.
- Minimum system requirements:
- CPU: 4
- Memory: 24 GB (refer to the Dell SRM design document)
- Disk Space: 132 GB (the final storage size per server is adjusted later)

## Steps

1. The base Dell SRM software and OS updates should be completed as described in Installing on Linux.
2. Browse to /opt/APG/bin .
3. Run the Primary Backend configuration script:
4. Restart the services and verify that they are running. Troubleshoot any service that does not show a status of 'running.'
5. Check the DB grants as described in Verifying MySQL Database Grants. (Collectors do not need DB grants.)

```
./launch-primarybackend-configuration.sh -c /sw/srm-hosts
```

```
./manage-modules.sh service stop all ./manage-modules.sh service start all ./manage-modules.sh service status all
```

## Installing and configuring the Additional Backend hosts

## Prerequisites

- Identify the hosts that you want to configure as the Additional Backend host.
- Identify the hosts that you want to configure as the Frontend, Collectors, Primary Backends, and Additional Backends.
- Ensure that you have created an answers file as described in Creating the Dell SRM-Conf-Tools answers file.
- Minimum system requirements:
- 64-bit Operating System
- CPU: 4
- Memory: 24 GB
- Disk Space: 132 GB (the final storage size per server is adjusted later)

## Steps

1. The base Dell SRM software and OS updates should be completed as described in Installing on Linux.
2. Browse to /opt/APG/bin .
3. Run the Additional Backend configuration script:
4. Restart the services and verify that they are running. Troubleshoot any service that does not show a status of 'running.'
5. Check the DB grants as described in Verifying MySQL Database Grants. (Collectors do not need DB grants.)

```
./launch-additionalbackend-configuration.sh -c /sw/srm-hosts
```

```
./manage-modules.sh service stop all ./manage-modules.sh service start all ./manage-modules.sh service status all
```

## Installing and configuring the Collector host

## Prerequisites

- Identify the hosts that you want to configure as the Collector hosts.
- Ensure that you have created an answers file as described in Creating the Dell SRM-Conf-Tools answers file.
- Collector to Mega Collector System Requirements:
- 64 bit operating system (Linux or Windows)
- CPU- 4 to 8
- Memory: 16 GB to 64 GB (refer to the Dell SRM design document)
- Disk Space: 132 GB (the final storage size per server is adjusted later).

## Steps

1. Complete the base Dell SRM software and OS updates should be completed as described in Installing on UNIX and/or Installing on Windows Server.
2. Browse to /opt/APG/bin .
3. Run the Collector configuration script:

```
./launch-collector-configuration.sh -c /sw/srm-hosts
```

4. Restart the services and verify that they are running. Troubleshoot any service that does not show a status of 'running.'
5. Because the Generic-RSC and Generic-SNMP modules are installed by default and if you do not plan to use this collector for host discovery or SNMP discovery, you can choose to remove these modules, remove these modules:

```
./manage-modules.sh service stop all ./manage-modules.sh service start all ./manage-modules.sh service status all
```

```
/opt/APG/bin/manage-modules.sh remove generic-snmp
```

## Installing and configuring the Frontend host

## Prerequisites

- Ensure that the configuration for the Primary Backend host is complete before starting the Frontend configuration.
- Ensure that you have the details of the Frontend host.
- Ensure that you have created an answers file as described in Creating the Dell SRM-Conf-Tools answers file
- Minimum system requirements:
- 64-bit Operating System
- CPU: 4
- Memory: 16 GB
- Disk Space: 132 GB (the final storage size per server is adjusted later)

## Steps

1. The base Dell SRM software and OS updates should be as described in Installing on Linux
2. Browse to /opt/APG/bin .
3. Run the Frontend configuration script:

```
./launch-frontend-configuration.sh -c /sw/srm-hosts
```

During the Frontend configuration, the management-resources are configured on the Primary Backend server. If the Dell SRM ports are not open, then this configuration script fails with this error: "Some operations failed to run successfully." Review the logs and fix any errors manually. Refer to Updating firewall ports in Red Hat and SLES servers to establish the Dell SRM ports on all the Dell SRM servers. Do not try to run this script again. Remove Dell SRM from the server where you are running the script and reinstall Dell SRM. Refer to Uninstallation

4. Restart the services and verify that they are running. Troubleshoot any service that does not show a status of 'running.'
5. Verify that the Dell SRM management resources have been created:

```
./manage-modules.sh service stop all ./manage-modules.sh service start all ./manage-modules.sh service status all
```

```
/opt/APG/bin/manage-resources.sh list
```

The following output shows the management resources on the basis of the example configuration that is used in the document:

```
"dba/APG-DB", "dba/APG-DB-<db_instance>-1", "dba/APG-DB-<db_instance>-2", "dba/APG-DB-<db_instance>-3", "dba/APG-DB-<db_instance>-4", "dba/FLOW-COMPLIANCE-BREACH", "dba/FLOW-COMPLIANCE-CONFIGCHANGE",
```

```
"dba/FLOW-COMPLIANCE-POLICY", "dba/FLOW-COMPLIANCE-RULE", "dba/FLOW-EVENTS-GENERIC", "dba/FLOW-EVENTS-GENERICARCH", "dba/FLOW-OUTAGE-DB", "dba/FLOW-PROSPHERE-ARCH", "dba/FLOW-PROSPHERE-LIVE", "dba/FLOW-RPE2-ARCH", "dba/FLOW-RPE2-LIVE", "dba/FLOW-SOM-ARCH", "dba/FLOW-SOM-LIVE", "dba/FLOW-UCS-LIVE", "dba/FLOW-VMWARE-EVENTS", "dba/FLOW-VMWARE-TASKS", "dba/FLOW-VNX-LIVE", "dba/FLOW-WHATIF-SCENARIOS", "mgmt/APG-DB", "mgmt/APG-DB-<db_instance>-1", "mgmt/APG-DB-<db_instance>-2", "mgmt/APG-DB-<db_instance>-3", "mgmt/APG-DB-<db_instance>-4", "rest/EVENTS", "rest/METRICS"
```

## Results

At this point, the basic Dell SRM configuration is complete and you can log in to the UI. To see the four servers that you just configured, browse to Administration, under SRM Admin UI click System admin &gt; Servers&amp; Modules &gt; Servers .

## Scaling-out a Dell SRM environment with Additional Backend hosts

This process completes the configurations for adding the Additional Backend to the existing Dell SRM environment using the Dell SRM-Conf-Tools. Additional Backend hosts should always be on a Linux OS platform.

## Prerequisites

- Complete the steps that are described in Installing on Linux.
- Identify the host that you want to configure as the Additional Backend host.
- Get the details of the existing Dell SRM environment that you want to scale.
- Minimum system requirements:
- 64-bit operating system
- CPU: 4
- Memory: 24 GB
- Disk space: 132 GB (the final storage size per server is adjusted later)

## Steps

1. Browse to /opt/APG/bin .
2. Modify the Dell SRM-Conf-Tools answer file ( srm-hosts ) as described in Creating the Dell SRM-Conf-Tools answers file.
3. Add the new Additional Backend to the original srm-hosts file in the /sw directory.

In the example, additionalbackend\_2 is the new Additional Backend.

```
frontend=<FE_host>.lss.emc.com:linux-x64 primarybackend=<PBE_host>.emc.com:linux-x64 additionalbackend_1=<ABE_1_host>.lss.emc.com:linux-x64 additionalbackend_2=<ABE_2_host>.lss.emc.com:linux-x64 collector_1=<COLL_host>.lss.emc.com:linux-x64
```

<!-- image -->

NOTE: Only for vApp VM, after adding the additional backends using scale-out scripts, the ovf.properties file will be updated with the property vm\_vmname=SRM .

4. Copy the modified answer file ( srm-hosts ) to these Dell SRM Frontend, Primary Backend, and Additional Backends. (The modified file is not needed on the existing Collector servers.)
5. Browse to /opt/APG/bin .
6. To configure the new Additional Backend host, run the following script:

launch-additionalbackend-configuration.sh -c /sw/srm-hosts

7. Restart the services and verify that they are running. Troubleshoot any service that does not show a status of 'running.'
8. Run the following script on all existing Additional Backend hosts:
9. Run the following script on the Primary Backend host:

```
./manage-modules.sh service stop all ./manage-modules.sh service start all ./manage-modules.sh service status all
```

```
./launch-additionalbackend-scale-additionalbackend.sh -c /sw/srm-hosts
```

./launch-primarybackend-scale-additionalbackend.sh -c /sw/srm-hosts

10. Run the following script on the Master Frontend host:

./launch-frontend-scale-additionalbackend.sh -c /sw/srm-hosts

11. List the Management Resources to verify that the Additional Backends hosts were added:

```
./manage-resources.sh list
```

In this example configuration, the following entries would be added to the list of resources:

```
"dba/APG-DB-lglba250-1", "dba/APG-DB-<db_instance_id>-2", "dba/APG-DB-<db_instance_id>-3", "dba/APG-DB-<db_instance_id>-4", "mgmt/APG-DB-<db_instance_id>-1", "mgmt/APG-DB-<db_instance_id>-2", "mgmt/APG-DB-<db_instance_id>-3", "mgmt/APG-DB-<db_instance_id>-4",
```

12. Restart all the services on the Additional Backend servers, Primary Backend server, and Frontend Server.
13. Log in to Dell SRM and confirm that the new Additional Backend is in the UI.

## Results

The Additional Backend hosts are added to the existing Dell SRM configuration. To see the five servers that you have configured, browse to Administration, under SRM Admin UI click System admin &gt; Servers&amp; Modules &gt; Servers .

## Scaling-out a Dell SRM environment with Collector hosts

This process completes the configurations for adding Collector hosts to the existing Dell SRM environment using the SRMConf-Tools. Collector software can be installed on a Linux or Windows platform. (Currently the Hyper-V SolutionPack requires a Windows platform.)

## Prerequisites

- Complete the steps that are described in Installing on Linux and/or Installing on Windows Server
- Identify the host that you want to configure as the Collector host.
- Get the details of the existing Dell SRM environment that you want to scale.
- Minimum System Requirements:
- 64-bit operating system
- CPU: 4 to 8
- Memory: 16 GB to 64 GB (refer to the Dell SRM design document)
- Disk space: 120 GB (the final storage size per server is adjusted later)

## About this task

NOTE: For Windows, convert .sh to .cmd for the commands and / to \ for directories.

## Steps

1. The base Dell SRM software and OS updates should be completed as described in Installing on Linux or Installing on Windows Server
2. Browse to /opt/APG/bin .
3. Modify the Dell SRM-Conf-Tools answer file ( srm-hosts ) as described in Creating the Dell SRM-Conf-Tools answers file
4. Add the new collector to the srm-hosts file.

In the example, collector\_2 is the new Collector.

```
frontend=<FE_host>.lss.emc.com:linux-x64 primarybackend=<PBE_host>.lss.emc.com:linux-x64 additionalbackend_1=<ABE_1_host>.lss.emc.com:linux-x64 additionalbackend_2=<ABE_2_host>.lss.emc.com:linux-x64 collector_1=<COLL_1_host>.lss.emc.com:linux-x64 collector_2=<COLL_2_host>.lss.emc.com:linux-x64
```

<!-- image -->

NOTE: Only for vApp VM, after adding the additional collectors using scale-out scripts, the ovf.properties file will be updated with the property vm\_vmname=SRM .

5. Copy the modified answer file ( srm-hosts ) to the Dell SRM Frontend (This new file is not needed on the existing Dell SRM servers.)
6. Browse to /opt/APG/bin .
7. To configure the new Collector host, run the following script:
8. Restart the services and verify that they are running. Troubleshoot any service that does not show a status of 'running.'

```
./launch-collector-configuration.sh -c /sw/srm-hosts
```

```
./manage-modules.sh service stop all ./manage-modules.sh service start all ./manage-modules.sh service status all
```

9. Run the following script on each Frontend:

```
./launch-frontend-scale-collector.sh -c /sw/srm-hosts
```

## Results

The Collector hosts are added to the existing Dell SRM configuration. To see the six servers that you have configured, browse to Administration, under SRM Admin UI click System Admin &gt; Servers &amp; Modules &gt; Servers .

## Verifying MySQL Database Grants

After installing and configuring the Dell SRM hosts, cross-check the grant privileges that are configured for the Dell SRM servers that are listed in the SRM-Conf-Tools configuration file.

## About this task

Database grants for Collector hosts are not required.

Where the script configure grants for Collector hosts, it is not needed and can be ignored or deleted.

NOTE: For mysql-client.sh to work on RHEL8.x, RHEL9.x and SLES 15 SP4, libncurses.so.x is required.

Example: RHEL 9

sudo ln -s /lib64/libncurses.so.6 /lib64/libtinfo.so.6

## Steps

1. Run the following script:

/opt/APG/bin/mysql-client.sh

2. When prompted, select root as the username, mysql for the database, and watch4net as the password.
3. Run the following query:

mysql&gt; SELECT user, host, db, select\_priv, insert\_priv, grant\_priv FROM mysql.db;

## Example

The following table is an example of the configuration that you should see on an Additional Backend host:

<!-- image -->

## Updating firewall ports in Red Hat and SLES servers

The Red Hat and SLES operating systems are installed by default with the OS firewall (firewalld) locked down. Only a few basic ports are open (such as SSH). On these operating systems, the firewall must be modified to allow the Dell SRM ports.

## Steps

1. Using a Linux editor, create an xml file and save it as apg.xml in the /etc/firewalld/services directory.
2. Add the following text to the xml file:

```
<?xml version="1.0" encoding="utf-8"?> <service> <short>TEST</short> <description>Add DELL EMC SRM Ports to Red Hat and Firewall</description> <port protocol="tcp" port="58080"/> <port protocol="tcp" port="2000"/> <port protocol="tcp" port="2001"/> <port protocol="tcp" port="2100"/> <port protocol="tcp" port="2101"/> <port protocol="tcp" port="2200"/> <port protocol="tcp" port="2201"/> <port protocol="tcp" port="2300"/> <port protocol="tcp" port="2301"/> <port protocol="tcp" port="2400"/> <port protocol="tcp" port="2401"/> <port protocol="tcp" port="2003"/> <port protocol="tcp" port="2008"/> <port protocol="tcp" port="2009"/> <port protocol="tcp" port="2010"/> <port protocol="tcp" port="2012"/> <port protocol="tcp" port="2020"/> <port protocol="tcp" port="2022"/> <port protocol="tcp" port="2040"/> <port protocol="tcp" port="2041"/> <port protocol="tcp" port="5480"/> <port protocol="tcp" port="5488"/> <port protocol="tcp" port="5489"/> <port protocol="tcp" port="8082"/>
```

```
<port protocol="tcp" port="8189"/> <port protocol="tcp" port="8888"/> <port protocol="tcp" port="8889"/> <port protocol="tcp" port="9996"/> <port protocol="tcp" port="22000"/> <port protocol="tcp" port="22020"/> <port protocol="tcp" port="22020"/> <port protocol="tcp" port="48443"/> <port protocol="tcp" port="52001"/> <port protocol="tcp" port="52004"/> <port protocol="tcp" port="52007"/> <port protocol="tcp" port="52569"/> <port protocol="tcp" port="52755"/> <port protocol="tcp" port="53306"/> <port protocol="tcp" port="58005"/> <port protocol="tcp" port="389"/> <port protocol="tcp" port="58443"/> <port protocol="tcp" port="5988"/> <port protocol="tcp" port="5989"/> <port protocol="tcp" port="5986"/> <port protocol="tcp" port="80"/> <port protocol="tcp" port="443"/> <port protocol="tcp" port="8080"/> <port protocol="tcp" port="2707"/> <port protocol="tcp" port="8443"/> <port protocol="tcp" port="2443"/> <port protocol="tcp" port="4443"/> <port protocol="tcp" port="2682"/> <port protocol="tcp" port="1521"/> <port protocol="tcp" port="9004"/> <port protocol="tcp" port="9002"/> <port protocol="tcp" port="7225"/> <port protocol="tcp" port="58083"/> <port protocol="tcp" port="52755"/> <port protocol="tcp" port="2060"/> <port protocol="tcp" port="3682"/> <port protocol="udp" port="161"/> <port protocol="udp" port="162"/> <port protocol="udp" port="2040"/> <port protocol="udp" port="2041"/> </service>
```

3. Copy the apg.xml file to the /etc/firewalld/services directory.
4. To add the ports to the existing firewall run the following command:
5. Check the status of firewalld:

```
firewall-cmd --permanent --add-service=apg
```

systemctl status firewalld

## Editing new actions scripts

It states that the Frontend Server where the "Actions" directory exists may need to be modified to point to the Primary Backend Server .

## Steps

In the 'conf' file, replace 127.0.0.1 with the primary backend IP address or FQDN:

| Option   | Description                                                                             |
|----------|-----------------------------------------------------------------------------------------|
| Linux    | /opt/APG/Custom/WebApps-Resources/Default/actions/event-mgmt/linux/conf                 |
| Windows  | Program Files\APG\Custom\WebApps-Resources\Default\actions\event- mgmt\windows\conf.cmd |

## Verifying that the services are running

Verify that the services are running on each host by obtaining the status.

## Prerequisites

Ensure that you have a login with root, APG, or system administrator privileges. The user apg is the account that the application uses instead of root.

## Steps

1. Type the command for the operating system from the bin directory of the installation:
2. Verify that each service has a status of running in the output.

| Operating system   | Command                               |
|--------------------|---------------------------------------|
| UNIX               | manage-modules.sh service status all  |
| Windows            | manage-modules.cmd service status all |

## Troubleshooting service start-up problems on UNIX

Check the log files when services do not start.

## Prerequisites

Ensure that you have logged in with root to check the log files.

## Steps

- The default path is /opt/APG/ .

The list of available log files vary depending on the type of server (Frontend, Backend, or Collector).

```
Databases/MySQL/Default/data/[SERVER NAME].err Backends/Alerting-Backend/Default/logs/alerting-0-0.log Backends/APG-Backend/Default/logs/cache-0-0.log Collecting/Collector-Manager/Default/logs/collecting-0-0.log Web-Servers/Tomcat/Default/logs/service.log Tools/Task-Scheduler/Default/logs/scheduler-0-0.log Tools/Webservice-Gateway/Default/logs/gateway-0-0.log
```

## Troubleshooting service start-up problems on Windows

Check the log files when services do not start.

## Prerequisites

Ensure that you have logged in with system administrator credentials to check the log files.

## Steps

- Look for log files in these C:\Program Files\APG directory paths.

The list of available log files vary depending on the type of server (Frontend, Backend, or Collector).

```
Databases\MySQL\Default\data\[SERVER NAME].err. Backends\Alerting-Backend\Default\logs\alerting-0-0.log Backends\APG-Backend\Default\logs\cache-0-0.log Collecting\Collector-Manager\Default\logs\collecting-0-0.log Web-Servers\Tomcat\Default\logs\service.log Tools\Task-Scheduler\Default\logs\scheduler-0-0.log Tools\Webservice-Gateway\Default\logs\gateway-0-0.log
```

## Logging in to the user interface

Log in to the user interface to use and edit reports, manage users, and customize the interface to meet the needs.

## Steps

1. Open a browser and type the following URL: https:// &lt;Frontend-hostname&gt; :58443/APG
2. Type the login credentials. The default username is admin . The default password is changeme .
3. Click Sign In .

NOTE: You are automatically logged off after 4 hours.

<!-- image -->

## Connecting to Administration

Connect to the server so that you can access Administration to install and administer SolutionPacks.

## About this task

Administration is one of the multiple web applications available in Dell M&amp;R platform.

## Steps

1. Open a browser.
2. Type https:// &lt;Frontend-host-IP&gt; :58443/admin

Example:

https://myHost.emc.com:58443/administration

3. Log in. Default username is admin .Default password is changeme .
4. Click Sign In .

You are automatically logged off after 4 hours.

<!-- image -->

## Using the Dell SRM Setup Wizard

This chapter includes the following topic:

## Topics:

- Using the Discovery Wizard

## Using the Discovery Wizard

The Discovery Wizard is a tool to ease the initial deployment and configuration of the most commonly used SolutionPacks. After upgrading to SRM 4.2 or later, you may want to use the Discovery Wizard to quickly enable the SolutionPacks, and add the corresponding devices that you would like to report on. In a few simple steps you can now add the devices, monitor the collection process, and then go to the reports to see the data.

## About this task

These steps use the VMAX 3/VMAX All Flash SolutionPack as an example.

## Steps

1. Log in to the user interface at https://&lt;Frontend-hostname&gt;:58443/APG .

The default username is admin . The default password is changeme .

2. Access the Discovery Wizard from the admin page: Administration &gt; DISCOVERY &gt; Discovery Wizard .
3. On the License page, do one of the following and click Continue .
3. NOTE: To support the XML based license features with SRM, the configuration property must be updated.
- For more details on configuring the XML license property, see Dell SRM Administrator Guide.
- You can add a permanent license by drag-and-dropping the file onto the license box.
4. On the Storage Collection page, do the following and click Continue .
- a. Type the FQDN or IP address of the Unisphere for VMAX host.
- b. Type the login credential and port number.
5. On the Confirm Storage page lists the detected arrays.
- a. Select the arrays from which you want to collect data.

The meter at the bottom indicates how many more volumes you can collect before you exceed the limit.

- b. Click Start Collection &amp; Continue when you have finished adding arrays.
2. NOTE: The Confirm Storage page only applies to VMAX systems.
6. On the Fabric Collection page, select Brocade (SMI-S) or Cisco (SNMP) from the drop-down list. Type the credentials and configuration options for the switch. Click Start Collection &amp; Continue .

Brocade SAN discovery with this wizard is through Brocade SMI-S only. This solution provides limited switch performance and topology information with WWNs. The Brocade SMI-S Data Collector that is deployed with the 4VM Collector is configured to discover everything through SMI-S. When you deploy the Brocade SolutionPack, the SMI-S Data Collector is configured to restrict the data collection to zoning only. It is a best practice to discover the Brocade SAN using SMIS-S for zoning and SNMP for everything else. It provides performance metrics, and the topology shows friendly names.

7. On the Fabric Collection page, select Brocade (SNMP+SMI-S) or Cisco (SNMP) from the drop-down list. Type the credentials and configuration options for the switch. Click Start Collection &amp; Continue . Brocade SAN discovery with this wizard is through Brocade SMI-S &amp; SNMP. This solution provides limited switch performance and topology information with WWNs. The Brocade SMI-S Data Collector that is deployed with the 4VM Collector is configured to discover everything through SMI-S &amp; SNMP. When you deploy the Brocade SolutionPack, the SMI-S Data Collector is configured to restrict the data collection to zoning only. It is a best practice to discover the Brocade

SAN using SMIS-S for zoning and SNMP for everything else. It provides performance metrics, and the topology shows friendly names.

8. Click Start Collection and Continue on the Compute Collection page, type the credentials for the VMware vSphere vSAN &amp; VxRail Server.
9. The Collection Status page displays the status of the data collection and provides links to the next steps. Click Restart to repeat this process for each of the device types.
10. Remove any pre-installed SolutionPacks and collectors that you do not plan to use:
- a. Access the UI at https:// &lt;Frontend-hostname&gt; /APG .
- b. Type the login credentials. The default username is admin . The default password is changeme .
- c. Browse to Administration &gt; Config &gt; SolutionPacks &gt; Installed SolutionPacks .
- d. Click the SolutionPack that you want to uninstall.
- e. Click the Trashcan icon for each component.
- f. Click Remove .
11. See the Dell SRM SolutionPack Guide for details about installing SolutionPacks that were not pre-installed.

This chapter includes the following topics:

## Topics:

- Dell SRM configuration tools
- Creating the Dell SRM-Conf-Tools answers file

## Dell SRM configuration tools

Dell SRM Configuration Tools (SRM-Conf-Tools) are installed with the Dell SRM software in the /opt/APG/bin directory. These tools work with both vApp and binary deployments.

The SRM-Conf-Tools scripts use an answers file to automatically configure the Dell SRM servers. You can use the SRM-ConfTools for the following scenarios:

- Initial configuration of a Frontend, Primary Backend, and Additional Backend servers
- Adding new Additional Backend servers to an existing Dell SRM environment
- Adding new Collectors to an existing Dell SRM environment
- Before you begin, deploy all the Collectors/ Additional Backends in all the remote data centers. They can be Collector/ Additional Backends vApps, or binary Linux or Windows Collectors.
- Binary Collectors/Additional Backends are installed using the Collector/Backend install option for both Linux and Windows. A Collector/Backend configuration script in SRM-Conf-Tools finishes the Collector/Backend configuration so that it is the same as a vApp collector/Backend.

If an SRM-Conf-Tools script configuration fails, you cannot run the script a second time. If the configuration fails, you must clean Dell SRM from the server and reinstall Dell SRM. See Uninstallation.

If you are using vCenter Snapshots, power off the VM and take a snapshot before running the scale-tools script.

## Creating the Dell SRM-Conf-Tools answers file

Dell SRM-Conf-Tools is a command-line utility that can configure and add a single server or multiple servers to the Dell SRM environment. Dell SRM-Conf-Tools uses an answers file that you create that includes all of the Dell SRM hosts in all of the datacenters where Dell SRM is installed.

## Prerequisites

- The answers file is case sensitive and must be all lowercase.
- Create the file using notepad++ or the Linux VI editor.
- Name the file srm-hosts .

## About this task

The format of the answers file is: server\_type=hostname:os

- server\_type -The four basic types of Dell SRM servers
- Hostname -The server's FQDN. It matches the setting of the hostname variable in the apg.properties file. For Linux servers, it should always be the hostname plus the domain name (FQDN). For Windows, it could be the hostname (shortname) or the FQDN depending on how the Windows server resolution is configured (DNS, Active DNS, or Wins/ NetBios). A Wins resolution uses the hostname (shortname) in uppercase.
- OS -linux-x64 or windows-x64

<!-- image -->

6

## Dell SRM Configuration Tools

For example:

```
frontend=<FE_host>.lss.emc.com:linux-x64 primarybackend=<PBE_host>.lss.emc.com:linux-x64 additionalbackend_1=<ABE_host>.lss.emc.com:linux-x64 collector_1=<COLL_host>.lss.emc.com:linux-x64
```

This answers file can be modified later to add any new Collectors and Additional Backends. When the Dell SRM-Conf-Tools scripts run, they distinguish new servers from existing servers and make the necessary configuration changes.

Since the Dell SRM-Conf-Tools and the answers file are used for configuring additional servers at a later date, Dell Technologies recommends storing the files in a /sw directory in the / directory instead of the /tmp directory. This action should be performed because the /tmp directory could be deleted at any time.

This chapter includes the following topics:

## Topics:

- Overview
- Stopping Dell M&amp;R platform services on a UNIX server
- Uninstalling the product from a UNIX server
- Stopping Dell M&amp;R platform services on a Windows server
- Uninstalling the product from a Windows server
- Uninstalling a SolutionPack
- Remove a Server and Delete vApp

## Overview

You can uninstall a SolutionPack and uninstall Dell M&amp;R platform from a UNIX or Windows server.

Stop the Dell M&amp;R platform services before uninstalling Dell M&amp;R platform.

## Stopping Dell M&amp;R platform services on a UNIX server

Use the manage-modules.sh service stop command to stop a specific Dell M&amp;R platform service or to stop all Dell M&amp;R platform services on a UNIX server.

## Prerequisites

Ensure that you have logged in with root or APG privileges.

- NOTE: The list of services varies depending on which type of installation was performed, vApp, collector, backend, and frontend.

## Steps

- Type manage-modules.sh service stop &lt;service\_name&gt; from the bin directory of the installation to stop a specific Dell M&amp;R platform service.

This example shows how to stop all Dell M&amp;R platform services:

./manage-modules.sh service stop all

## Uninstalling the product from a UNIX server

Use this procedure to uninstall the product from the Unix server.

## Prerequisites

Ensure that you have a login with root privileges.

## Uninstallation

## Steps

1. Type rm -rf /opt/APG to remove the installation directory.
2. Restart the server.

## Stopping Dell M&amp;R platform services on a Windows server

Use this procedure to stop Dell M&amp;R platform services from the Windows desktop.

## Prerequisites

To manage services, ensure that you have logged in with system administrator credentials.

<!-- image -->

- NOTE: The list of services varies depending on which type of installation was performed, vApp, collector, backend, and frontend.

## Steps

Type manage-modules.cmd service stop &lt;service\_name&gt; from the bin directory of the installation to stop a specific Dell M&amp;R platform service.

This example shows how to stop all Dell M&amp;R platform services:

./manage-modules.cmd service stop all

## Uninstalling the product from a Windows server

Use this procedure to uninstall the product from the Windows server.

## Prerequisites

Ensure that you have logged in with system administrator credentials.

## Steps

1. Use the Windows Control Panel to uninstall the product.
- a. Click Start &gt; Control Panel &gt; Programs .
- b. Click Uninstall a program .
- c. Select the Watch4net Solutions APG and click Uninstall .
2. Restart the server.

## Uninstalling a SolutionPack

If you no longer want to view the reports of a certain SolutionPack, you can uninstall that SolutionPack from the server.

## Steps

1. Log in with administrator credentials for Dell M&amp;R platform and select Administration .
2. Go to Config &gt; SolutionPacks &gt; Installed SolutionPacks .
3. Select the SolutionPack that you want to uninstall in the Installed SolutionPacks screen.
4. In the Properties area, click Trashcan icon for each instance of the SolutionPackBlock and click Remove .

## Remove a Server and Delete vApp

If a scaled-out collector is no longer in use, you can unregister from the existing Dell SRM deployment, and remove the vApp.

## Steps:

1. SRM Admin page &gt; Configure Servers &gt; Delete the unwanted server (scaled-out collector) &gt; SAVE .
2. NOTE: There is no confirmation notification for the deletion and the server removes at the instant the bin icon is clicked.
2. Login to the Collector console using root, run # manage-modules.sh service remove all
3. Power off the VM.
4. Delete from the disk.

This MUST only be performed on a scaled-out VM (Collector host) that is no longer in use/required.

This appendix includes the following topics:

## Topics:

- Unattended installation
- Unattended installation arguments for Linux
- Unattended installation arguments for Windows

## Unattended installation

Dell EMC M&amp;R 6.7 and higher supports fully unattended installations, which are particularly useful for installing the software on remote systems via scripts. This appendix describes the installation of the platform software, but it does not include the installation and configuration of modules or SolutionPacks.

## Unattended installation arguments for Linux

- --silent
- Runs the setup script in unattended mode. No questions are asked, and the default settings are used.
- --accept-eula
- Accepts the EULA. By providing this switch, you are confirming that you have read and accepted the EULA.
- --install-dir = &lt;path to installation&gt;
- Overrides the default installation location. The default is typically /opt/APG .
- --user = username
- Overrides the default user for installation of the servers. The default is typically apg.
- --script-directory = initd\_directory
- Overrides the default script directory. The default is /etc/init.d .
- --runlevel-directory = rcd\_directory
- Overrides the default runlevels directory (containing rc[0-6].d/ ).
- The default is /etc .
- --install-type = installation\_type
- Overrides the default installation type. The available options are default, minimal, collector, backend, and frontend. The command only considers the first letter, so --install-type=C is equivalent to --install-type=collector . The value of the parameter is not case sensitive.

## To override the default installation and set the installation type to collector:

[root@server ~]# ./linux\_setup.sh -- --install-type=collector

To run a fully unattended installation and install as a collector in an alternate directory:

[root@server ~]# ./linux\_setup.sh -- --accept-eula --silent --install-type=collector -install-dir=/opt/SRM

## Unattended installation arguments for Windows

- /S
- Runs the setup script in unattended mode. No questions are asked, and the default settings are used. It must be the first argument.
- ACCEPTEULA = Yes

<!-- image -->

A

## Unattended Installation

- Accepts the EULA. By providing this switch, you are confirming that you have read and accepted the EULA. If you have not accepted the EULA, the installer refuses to run in unattended mode.
- INSTALL-TYPE = installation\_type
- Overrides the default installation type. The available options are: default, minimal, collector, backend, and frontend. The command only considers the first letter, so INSTALL-TYPE=C is equivalent to INSTALL-TYPE=collector . The value of the parameter is not case sensitive.
- /D
- Sets the default installation directory. It must be the last parameter. It cannot contain any quotes (even if the path contains spaces), and only absolute paths are supported.

## To run a fully unattended installation and install as a collector in an alternate directory:

C:\Users\user1&gt; windows\_setup.exe /S /D=C:\SRM /ACCEPTEULA=Yes /INSTALL-TYPE=collector

## Documentation Feedback

Dell Technologies strives to provide accurate and comprehensive documentation and welcomes your suggestions and comments. You can provide feedback in the following ways:

- Online feedback form Rate this content feedback form is present in each topic of the product documentation web pages. Rate the documentation or provide your suggestions using this feedback form.
- Email-Send your feedback to SRM Doc Feedback. Include the document title, release number, chapter title, and section title of the text corresponding to the feedback.

To get answers to your queries related to Dell SRM through email, chat, or call, go to Dell Technologies Technical Support page.