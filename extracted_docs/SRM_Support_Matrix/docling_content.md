## Dell SRM 5.1.1.0 Support Matrix

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

| Chapter 1: System Requirements..................................................................................................                                                           | 5   |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----|
| SRM vApp installation requirements...............................................................................................................................5                         |     |
| SRM binary installation requirements.............................................................................................................................5                         |     |
| Browser requirements........................................................................................................................................................6              |     |
| Secure Remote Services Requirements.........................................................................................................................6                              |     |
| Third-party Tools.................................................................................................................................................................6        |     |
| MySQL....................................................................................................................................................................................6 |     |
| Chapter 2: Supported SolutionPacks ............................................................................................8                                                           |     |
| SolutionPack for Amazon AWS........................................................................................................................................9                       |     |
| SolutionPack for Block Chargeback................................................................................................................................9                         |     |
| SolutionPack for Brocade FC Switch.............................................................................................................................                            | 9   |
| SolutionPack for Cisco MDS/Nexus..............................................................................................................................                             | 11  |
| SolutionPack for Cisco UCS............................................................................................................................................12                   |     |
| SolutionPack for Configuration Compliance................................................................................................................12                                |     |
| SolutionPack for Dell Data Domain................................................................................................................................12                        |     |
| SolutionPack for Dell Data Protection Advisor...........................................................................................................                                   | 13  |
| SolutionPack for Dell ECS................................................................................................................................................13                |     |
| SolutionPack for Hitachi Device Manager...................................................................................................................                                 | 13  |
| SolutionPack for HP 3PAR StoreServ..........................................................................................................................                               | 14  |
| SolutionPack for HPE Nimble..........................................................................................................................................14                    |     |
| SolutionPack for Huawei Oceanstor.............................................................................................................................                             | 15  |
| SolutionPack for HP StorageWorks..............................................................................................................................                             | 15  |
| SolutionPack for IBM DS..................................................................................................................................................15                |     |
| SolutionPack for IBM LPAR.............................................................................................................................................15                   |     |
| SolutionPack for IBM SAN Volume Controller/Storwize ........................................................................................16                                             |     |
| SolutionPack for IBM XIV................................................................................................................................................                   | 16  |
| SolutionPack for IBM FlashSystem................................................................................................................................17                         |     |
| SolutionPack for Kubernetes...........................................................................................................................................17                   |     |
| SolutionPack for Microsoft Azure..................................................................................................................................17                       |     |
| SolutionPack for Microsoft Hyper-V.............................................................................................................................17                          |     |
| SolutionPack for Microsoft SQL Server.......................................................................................................................18                             |     |
| SolutionPack for NetApp FAS.........................................................................................................................................18                     |     |
| SolutionPack for Oracle Database.................................................................................................................................                          | 18  |
| SolutionPack for Oracle MySQL Database..................................................................................................................19                                 |     |
| SolutionPack for Physical Hosts.....................................................................................................................................19                     |     |
| SolutionPack for Dell PowerEdge..................................................................................................................................                          | 21  |
| SolutionPack for Dell PowerFlex....................................................................................................................................                        | 21  |
| SolutionPack for Dell PowerScale..................................................................................................................................21                       |     |
| SolutionPack for Dell PowerStore..................................................................................................................................21                       |     |
| SolutionPack for Dell PowerSwitch..............................................................................................................................22                          |     |
| SolutionPack for Dell PowerVault.................................................................................................................................                          | 22  |
| SolutionPack for Pure Storage......................................................................................................................................                        | 22  |
| SolutionPack for Dell RecoverPoint..............................................................................................................................23                         |     |

| SolutionPack for Dell SC Series.....................................................................................................................................23      |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| SolutionPack for Dell Unity............................................................................................................................................. 23 |
| SolutionPack for Dell EMC VMAX.................................................................................................................................23           |
| SolutionPack for Dell VMAX/PowerMax.....................................................................................................................24                  |
| SolutionPack for VMware vSphere vSAN and VxRail..............................................................................................25                             |
| SolutionPack for Dell VPLEX..........................................................................................................................................25     |
| Dell SolutionPack for VxRail........................................................................................................................................... 26  |
| SolutionPack for Dell EMC XtremIO.............................................................................................................................26            |
| Chapter 3: Supported password Management Software.............................................................. 27                                                          |
| Chapter 4: Documentation Feedback...........................................................................................28                                              |

This chapter includes the following topics :

## Topics:

- SRM vApp installation requirements
- SRM binary installation requirements
- Browser requirements
- Secure Remote Services Requirements
- Third-party Tools
- MySQL

## SRM vApp installation requirements

The following VMware vSphere versions are supported for SRM vApp installation.

- VMware vSphere 6.5u1
- VMware vSphere 6.7
- VMware vSphere 7.0
- VMware vSphere 8.0
- VMware vSphere 9.0

## SRM binary installation requirements

The following operating systems are supported for SRM binary installation.

## Table 1. Supported Operating Systems

| Operating System                    | Version                                                                                                                                                                                           |
|-------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Red Hat Enterprise Linux            | 7 (64-bit), 8.2(64-bit), 8.4(64-bit), 8.5(64-bit), 8.6(64-bit), 8.7(64-bit), 8.8(64-bit), 8.9(64-bit), 8.10(64-bit), 9.0(64-bit), 9.1(64-bit), 9.2(64-bit), 9.3(64-bit), 9.4(64-bit), 9.5(64-bit) |
| SUSE Linux Enterprise Server (SLES) | 12 SP4 (64-bit), 12 SP5 (64-bit), 15 SP2 (64-bit), 15 SP3(64-bit), SP4(64-bit), SP5(64-bit), 15 SP6(64- bit)                                                                                      |
| Microsoft Windows                   | Server 2012, Server 2012 R2, Server 2016, Server 2019, Server 2022, Server 2025                                                                                                                   |

<!-- image -->

NOTE: The existing customers can avail support for the CentOS platform. As it is deprecated the support for this platform is provided through RPQ request, so users must raise an RPQ request for any new CentOS deployments.

## System Requirements

## Browser requirements

SRM supports the following browser versions.

## Table 2. Supported browsers

| Browser           | Version   | Operating System   | Notes        |
|-------------------|-----------|--------------------|--------------|
| Google Chrome     | Latest    | Windows, Linux     | Full support |
| Internet Explorer | 11        | Windows            | Full support |
| Microsoft Edge    | Latest    | Windows            | Full support |
| Mozilla Firefox   | Latest    | Windows, Linux     | Full support |
| Apple Safari      | Latest    | Mac OS X and iOS   | Full support |

Full support includes:

- Report viewing
- Browsing
- Support for interactive tables and graphs
- Topology maps
- Administration tasks such as user management, enrichment UI, and alerting UI

NOTE: SRM is an HTML/JavaScript only web application. Installing Flex, Flash or Java is not required.

## Secure Remote Services Requirements

The following Embedded Service Enabler (ESE) (previously known as SupportAssist) versions are supported.

## Table 3. Supported ESE versions

| ESE version        | Port   | Notes                                                                             |
|--------------------|--------|-----------------------------------------------------------------------------------|
| Linux: 4.12.5.13   | 9443   | Used for communication between Frontend host and Dell Technologies Connectivity . |
| Windows: 4.12.5.13 |        |                                                                                   |

## Third-party Tools

The following third-party tools are supported.

## Table 4. Supported third-party tools

| Tools   |   Version | Notes                                                                                                                                                                        |
|---------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PuTTY   |      0.75 | Minimum version that is required to support modified SSH configuration in SLES15 SP4. The older PuTTY versions do not work as the SSH cryptographic settings are deprecated. |

## MySQL

This section describes the requirements for the latest version of MySQL.

MySQL's latest version requires the following ncurses and VC++ versions:

- ncurses-libs-6.2-10.20210508.el9.x86\_64
- ncurses-compat-libs-6.2-10.20210508.el9.x86\_64

For Windows:

Microsoft Visual C++ 2019 redistributable package is required for the latest version of MySQL.

This chapter includes the following topics:

## Topics:

- SolutionPack for Amazon AWS
- SolutionPack for Block Chargeback
- SolutionPack for Brocade FC Switch
- SolutionPack for Cisco MDS/Nexus
- SolutionPack for Cisco UCS
- SolutionPack for Configuration Compliance
- SolutionPack for Dell Data Domain
- SolutionPack for Dell Data Protection Advisor
- SolutionPack for Dell ECS
- SolutionPack for Hitachi Device Manager
- SolutionPack for HP 3PAR StoreServ
- SolutionPack for HPE Nimble
- SolutionPack for Huawei Oceanstor
- SolutionPack for HP StorageWorks
- SolutionPack for IBM DS
- SolutionPack for IBM LPAR
- SolutionPack for IBM SAN Volume Controller/Storwize
- SolutionPack for IBM XIV
- SolutionPack for IBM FlashSystem
- SolutionPack for Kubernetes
- SolutionPack for Microsoft Azure
- SolutionPack for Microsoft Hyper-V
- SolutionPack for Microsoft SQL Server
- SolutionPack for NetApp FAS
- SolutionPack for Oracle Database
- SolutionPack for Oracle MySQL Database
- SolutionPack for Physical Hosts
- SolutionPack for Dell PowerEdge
- SolutionPack for Dell PowerFlex
- SolutionPack for Dell PowerScale
- SolutionPack for Dell PowerStore
- SolutionPack for Dell PowerSwitch
- SolutionPack for Dell PowerVault
- SolutionPack for Pure Storage
- SolutionPack for Dell RecoverPoint
- SolutionPack for Dell SC Series
- SolutionPack for Dell Unity
- SolutionPack for Dell EMC VMAX
- SolutionPack for Dell VMAX/PowerMax
- SolutionPack for VMware vSphere vSAN and VxRail
- SolutionPack for Dell VPLEX
- Dell SolutionPack for VxRail
- SolutionPack for Dell EMC XtremIO

## Supported SolutionPacks

## SolutionPack for Amazon AWS

SRM supports the following Amazon AWS models.

Table 5. Support for Amazon AWS

| Supported Family or Models                                                                            | Prerequisites                                                                                                     | Ports          |
|-------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|----------------|
| Amazon Simple Storage Service (S3), Billing and Cost, Estimate Reports, CloudWatch Monitoring Service | AWS Command Line Interface (CLI), Windows binary installation requires Windows Management Framework 3.0 or later. | Not applicable |

## SolutionPack for Block Chargeback

Block Chargeback supports the following Dell and third-party arrays.

Table 6. Support for Block Chargeback

| Supported Family or Models                                                                                                                                                                                | Prerequisites                                                  |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------|
| Chargeback supports Dell arrays (VMAX, Unity, VPLEX, PowerFlex, PowerStore, PowerMax and XtremIO), Dell array SC Series, and third-party arrays (HP Arrays, HDS, NetApp, and IBM XIV, IBM SVC, IBM DS8K). | Data should be discovered as part of an individual collection. |

<!-- image -->

NOTE: By default, the Chargeback task is set to run once a day. Chargeback task can be run on demand to reflect data in the reports.

## SolutionPack for Brocade FC Switch

SRM supports the following Brocade switches.

## SMI-S only

SolutionPack for Brocade FC Switch discovers switch topology, performance, and zoning details through SMI-S.

Table 7. Support for Brocade fabric

| Supported Family or Models                                                                                                                       | Prerequisites                                                                             | Ports          |
|--------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|----------------|
| For the supported models, see Dell EMC Connectrix Manager Converged Network Edition Professional, Professional Plus, and Enterprise User Guide . | CMCNE/BNA 12.1.6, 12.3.x, 12.4.x, 14.0, 14.0.1, 14.1, 14.2, 14.4.1, 14.4.2, 14.4.3,14.4.5 | Not applicable |

<!-- image -->

## NOTE:

- For all versions of CMCNE/BNA, Dell SRM does not support Single Sign On and Launch-in-Context.
- Dell SRM does not support Administrative Domains features.
- Performance Metrics is not collected for Brocade AG Devices and FCoE ports.
- Discovery support is limited to FC and FCoE ports. Discovery of other protocols or routing is not supported.
- CPU Utilization and Memory Utilization are not populated for Brocade switches.
- Name Server Database and Ethernet ports details are not discovered.
- To populate Alerts in Dell SRM, configure the SNMP trap recipient on each switch. For more information, see Dell SRM Alerting Guide available at Dell Support Site.
- Passive host details are not derived from the peer zones.

## SNMP + SMI-S (Zoning discovery only through SMI-S)

SolutionPack for Brocade FC Switch discovers switch topology and performance metrics through SNMP and restricts SMI-S discovery to zoning details only. SNMP does not support zoning discovery.

This discovery approach is supported for backward compatibility with previous versions.

Table 8. Support for Brocade fabric

| Supported Family or Models                                                       | Prerequisites                                                                                                                                                                                                                                                                                                                    | Port     |
|----------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| All Brocade switches that are running FOS 6.4.3g, 7.2.1g, 7.3, 7.4.2a, or later. | Supported MIBs: SW-MIB FCMGMT-MIB FIBRE- CHANNEL-FE-MIB IANAifType-MIB IF-MIB IP-MIB RFC1213-MIB SNMPv2-SMI-MIB Providers: CMCNE/BNA 12.1.6, 12.3.x, 12.4.x, 14.0, 14.0.1, 14.1, 14.2, 14.4.1, 14.4.2, 14.4.3, 14.4.5 Some switch models might not have all the MIBs listed in that case, those capabilities are not discovered. | 161 SNMP |

<!-- image -->

## NOTE:

- Performance Metrics is not collected for Brocade AG Devices.
- CPU Utilization and Memory Utilization are populated for Brocade switches running firmware version FOS 6.3 and later. A Fabric Watch license should be installed on the switches to fetch CPU and Memory utilization metrics.
- Discovery is limited to FC blades. Discovery supports only the E, F, and G ports on the blades.
- Dell SRM does not support Administrative Domains features.
- For all versions of CMCNE/BNA, Dell SRM does not support Single Sign On and Launch-in-Context.
- Passive host details are not derived from the peer zones.

## REST

SolutionPack for Brocade FC Switch discovers switch topology, performance, and zoning details through Fabric OS (FOS) REST API .

Table 9. Support for Brocade fabric

| Supported Family or Models                                                                                            | Prerequisites                                                                                                                                                                                                                                                   | Port                |
|-----------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------|
| Brocade switches with FOS Version of 8.2.1c or later, 9.1.1b, 9.1.1c, 9.2.0a, 9.2.1, 9.2.1b, and 9.2.2 are supported. | 1. Minimum REST sessions count required on the switch is 3. 2. Minimum sampling request count that is required on the switch is 39 in the Non-VF switch. 3. Minimum sampling request count that is required on the VF enabled switch is Number of VFs * 9 + 30. | 80 and SSL port 443 |

Discovery support is limited to FC ports only.

<!-- image -->

## SANNAV

SolutionPack for Brocade FC Switch discovers switch and zoning details through SANnav management portal.

Table 10. Support for Brocade fabric

| Supported Family or Models                                                                              | Prerequisites                                                |   Port |
|---------------------------------------------------------------------------------------------------------|--------------------------------------------------------------|--------|
| Brocade switches with FOS Versions of 7.4.x, 8.x, 9.0, 9.1.1b, 9.1.1c, 9.2.0a, 9.2.1, 9.2.1b, and 9.2.2 | SANnav 2.3.0, SANnav 2.3.1, SANnav 2.3.1b, and SANnav 2.4.0. |    443 |

<!-- image -->

## NOTE:

- Passive host details are not derived from the peer zones.
- Performance data is not supported.
- SANnav does not support CyberArk.
- Brocade FRUs (Fan, Power Supply, Temperature) are not supported.
- FRU Blade is not supported.
- Port Symbolic Name property for Nameserver is not supported.
- Maximum blade property is not supported.
- Alerts are not supported.
- Situation to Watch and Error Reports are not supported.

## SolutionPack for Cisco MDS/Nexus

SRM supports the following collection interfaces for Cisco MDS and Nexus.

## Table 11. Support for Cisco MDS and Nexus

| Supported Collection Interfaces   | Prerequisites                                                                                                                                                                                                                                                                                                               | Ports    |
|-----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| Cisco MDS Cisco ONS Cisco Nexus   | Supported MIBs: ● CISCO-FLASH-MIB ● CISCO-NS-MIB ● CISCO-DM-MIB ● CISCO-ENTITY-SENSOR-MIB ● ENTITY-MIB ● CISCO-FC-FE-MIB ● IF-MIB ● CISCO-ENTITY-FRU-CONTROL-MIB ● CISCO-VSAN-MIB ● CISCO-DM-MIB ● CISCO-ZS-MIB ● CISCO-SYSTEM-EXT-MIB ● SNMPv2-MIB ● CISCO-FCS-MIB ● CISCO-FEATURE-CONTROL-MIB ● CISCO-FC-DEVICE-ALIAS-MIB | 161 SNMP |

<!-- image -->

## NOTE:

- Some switch models might not have all the listed MIBs. In that case, those capabilities are not discovered.
- Discovery is limited to FC and FCoE ports only.
- Dell SRM discovers Cisco Device Aliases that participates in Active Zoneset.
- Dell SRM does not support discovery of VDC (virtual device context) and Fabric extenders.
- Switches that are running NX-OS 5.2(x) and 6.2(x) code are recommended to upgrade to 5.2(8d) or later and 6.2(11) or later.

## SolutionPack for Cisco UCS

SRM supports the following collection interfaces for Cisco UCS.

## Table 12. Support for Cisco UCS

| Supported Collection Interfaces                                          | Ports   |
|--------------------------------------------------------------------------|---------|
| Cisco UCS Manager 2.0 and later, Cisco UCS C-Series (CIMC) 1.4 and later | 80, 443 |

## SolutionPack for Configuration Compliance

SRM supports the following Configuration Compliance models.

Table 13. Support for Configuration Compliance

| Supported Family or Models                                                                                                                                                                                                                                                                                               | Prerequisites                                                | Ports          |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------|----------------|
| Compliance rules support: All the supported Physical Hosts, VMware VMs, HyperV VMs Third-party Arrays (NetApp FDvM300, AFF- A250; HDS VSP F700, VSP G1000; HP 3PAR 7400; HP StorageWorks, HPE Nimble CS 700; IBM XIV; IBM SVC 8.5; IBM FlashSystem 5200; Huawei Dorado 8000 V6) Brocade, Cisco, Dell Connectrix switches | Data must be discovered as part of an individual collection. | Not applicable |

<!-- image -->

## NOTE:

- ESM rules are not supported for third-party arrays.

● Policy Administration and Dell Support Matrix Administration reports are not supported in the minimal browse mode.

## SolutionPack for Dell Data Domain

SRM supports the following Dell Data Domain Operating System versions.

## SNMP

Table 14. Support for Dell Data Domain

| Supported Family or Models                                                                                                                                                    | Prerequisites                                                                                                                                         | Ports    |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| Dell Data Domain Operating System 6.2, 7.0,7.1, 7.2 ,7.3,7.4,7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.11, 7.12, 7.13, 8.0, 8.1.0.5, and 8.3 Dell Data Domain Virtual Edition in Cloud | If you are updating from an older version, ensure that the SolutionPack block Generic- SNMP is updated to version 1.2 or later. SNMP must be enabled. | 161 SNMP |

<!-- image -->

NOTE: Archive Tier information is provided over an SNMP agent starting with Data Domain Operating System 5.7. This information is displayed only when archive or retention is enabled on the device. Devices running an earlier version of the Data Domain Operating System cannot display this information even if archive or retention is enabled.

## REST

## Table 15. Support for Dell Data Domain

| Supported Family or Models                                                                        | Prerequisites   | Ports                     |
|---------------------------------------------------------------------------------------------------|-----------------|---------------------------|
| Dell Data Domain Operating System 8.0, 8.1.0.5, and 8.3 Dell Data Domain Virtual Edition in Cloud | N/A             | 3009 HTTPS (Configurable) |

NOTE:

Rest API support is limited to Summary and few Inventory reports.

## SolutionPack for Dell Data Protection Advisor

SRM supports the following Dell Data Protection Advisor models.

Table 16. Support for Dell Data Protection Advisor

| Supported Family or Models                                                  | Ports                 |
|-----------------------------------------------------------------------------|-----------------------|
| DPA 18.1, 18.2, 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9, 19.10 | 9004 HTTP, 9002 HTTPS |

## SolutionPack for Dell ECS

SRM supports the following Dell ECS models.

## Table 17. Support for Dell ECS

| Supported Family or Models                                                                                                    | Ports      |
|-------------------------------------------------------------------------------------------------------------------------------|------------|
| ECS 3.0, 3.1, 3.2, 3.2.1, 3.2.2, 3.3, 3.4, 3.5.0, 3.5.1, 3.6.0, 3.6.1, 3.6.2, 3.7.0, 3.8.0, 3.8.1, 3.9 (Dell ObjectScale 4.0) | 4443 HTTPS |

## SolutionPack for Hitachi Device Manager

SRM supports the following Hitachi Device Manager models.

## XMLAPI and SMI-S

Table 18. Support for Hitachi Device Manager

| Supported Family or Models                                                        | Prerequisites                                                                       | Ports                                |
|-----------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|--------------------------------------|
| AMS200, AMS500, AMS1000 AMS2xxx USP, USP_V HUS, VSP G, VSP F, and VSP 5000 Series | Hitachi Command Suite 7.4.1 or later in 7.x series Hitachi Command Suite 8.x series | 2001 XML API, 5988 SMI-S, 5989 SMI-S |

<!-- image -->

## NOTE:

- NVMe configurations are not supported in the VSP 5000 series array.
- SRM reports Logical Capacities for the below metrics for both VSP F and VSP 5000 series arrays.
- PoolUsedCapacity and PoolFreeCapacity metrics at the array level.
- Capacity, FreeCapacity, and UsedCapacity metrics at the pool level whenever pools are created using FMD drives.
- Capacity, FreeCapacity, and UsedCapacity metrics at the parity group level if the parity group is created with FMD drives.

- Only block mode (not file or object) is supported on HUS arrays.
- Performance statistics are provided for the HUS VM,VSP ,VSP G,VSP F, and VSP 5000 series, through the Embedded SMI-S Provider. For details about enabling Embedded Performance Collection for these models, see SolutionPack Installation Guide .

## REST

SolutionPack for Hitachi Device Manager discovers the Hitachi array topology and capacity metrics through Hitachi Ops Center Configuration Manager REST API and performance metrics through Hitachi Ops Center Analyzer REST API.

Table 19. Support for Hitachi Device Manager

| Supported family or models                  | Pre-requisites                                                                                                                                                        | Ports                                                                                                                                    |
|---------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| Arrays supported in Ops Center suite 10.8.1 | The array needs to be registered with the Ops Center Configuration Manager. Configure Probe and RAID Agent for the array on Analyzer for performance data collection. | 23450 will be http and 23451 will be https port for Configuration Manager. 22015 will be http and 22016 will be https port for Analyzer. |

- All the metrics are limited only to SolutionPack level reports.
- Refer to Limitations for REST API-based Hitachi array discovery in SolutionPack guide for detailed information.

## SolutionPack for HP 3PAR StoreServ

SRM supports the following HP 3PAR StorServ models.

Table 20. Support for HP 3PAR StorServ

| Supported Family or Models                                                          | Prerequisites                                                                   | Ports                          |
|-------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|--------------------------------|
| S400X, V400, 7xxx, 8xxx Supported versions of the firmware are: 3.2.1, 3.2.2, 3.3.1 | CIM server is started. Use startcim command on the CLI to start the CIM server. | 22 SSH, 5988 SMI-S, 5989 SMI-S |

## SolutionPack for HPE Nimble

SRM supports the following HPE Nimble models.

Table 21. Support for HPE Nimble

| Supported Family or Models            | Pre-requisite   | Ports                         |
|---------------------------------------|-----------------|-------------------------------|
| Nimble OS 5.0.x , 5.1.x, 5.2.x, 5.3.x | REST API access | 5392 REST API 162 SNMP 22 SSH |

<!-- image -->

## NOTE:

- Replication feature is not supported.
- iSCSI reporting is not supported.

## SolutionPack for Huawei Oceanstor

SRM supports the following Huawei Oceanstor models.

Table 22. Support for Huawei Oceanstor

| Supported Platform Versions     | Pre-requisites                                    |   Ports |
|---------------------------------|---------------------------------------------------|---------|
| Huawei OceanStor Dorado 8000 V6 | REST API must be enabled on the Huawei Oceanstor. |     443 |

## SolutionPack for HP StorageWorks

SRM supports the following HP StorageWorks models.

Table 23. Support for HP StorageWorks

| Supported Family or Models              | Prerequisites                                                               | Ports                                |
|-----------------------------------------|-----------------------------------------------------------------------------|--------------------------------------|
| P9500, XP24K/20K, XP10K/SVS200, and XP7 | HP Command View Advanced Edition Suite 7.4.1 or later installed on the host | 2001 XML API, 5988 SMI-S, 5989 SMI-S |

NOTE: Performance statistics are provided for the P9500 through the Embedded SMI-S Provider. For details about enabling Embedded Performance Collection for this model, see Dell SRM SolutionPack Guide .

## SolutionPack for IBM DS

SRM supports the following IBM DS models.

Table 24. Support for IBM DS

| Supported Family or Models   | Prerequisites     | Ports      |
|------------------------------|-------------------|------------|
| DS 8000 Series               | CIM Agent running | 6989 HTTPS |

## SolutionPack for IBM LPAR

SRM supports the following IBM P Series models.

Table 25. Support for IBM P Series

| Supported Family or Models                | Prerequisites                                                                                                                                                                                                                                  |   Ports |
|-------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| All P Series servers, HMC version 8, or 9 | Installation of SolutionPack for IBM LPAR with Hardware management Console (HMC) credentials. HMC can also be discovered using SSH public- private key pair. For more information, see SRM SolutionPack Installation and Configuration Guide . |      22 |

Table 26. Support for LPAR (VIOS/VIOC)

| Supported Operating Systems   | Prerequisites                                                                                                                                                                                                                                                                                         |   Ports |
|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| IBM AIX 7.1, 7.2, 7.3         | Installation of SolutionPack for Physical Hosts. Physical Host SolutionPack Script must be installed on the Generic RSC collector that is used for physical host discovery. Admin user credentials are not required to discover VIO Servers. INQ 9.0.0.0 is available from: ftp.emc.com/pub/symm3000/ |      22 |

## Table 26. Support for LPAR (VIOS/VIOC)

| Supported Operating Systems   | Prerequisites                              | Ports   |
|-------------------------------|--------------------------------------------|---------|
|                               | inquiry/ Perl interpreter 5.6.1 or later . |         |

<!-- image -->

## NOTE:

- SolutionPack for IBM LPAR collects information only from HMC.
- To discover VIO Server and LPAR information, use SolutionPack for Physical Hosts.
- INQ is pushed to both VIO Servers and Clients.
- The Live Partition Mobility (LPM) feature on IBM LPAR causes floating CPU and memory. The agentless collection script does not capture this phenomenon. So, the SolutionPack for IBM LPAR does not support dynamic refresh on LPARs occurring due to the LPM capability on AIX or Linux LPAR.
- INQ 9.0.0.0 is supported only on 64-bit Operating System platforms. INQ 7.6.2 must be manually copied onto 32-bit target hosts.

## SolutionPack for IBM SAN Volume Controller/ Storwize

SRM supports the following IBM SAN Volume Controller/Storwize models.

Table 27. Support for IBM SAN Volume Controller/Storwize

| Supported Family or Models                  | Prerequisites              | Ports              |
|---------------------------------------------|----------------------------|--------------------|
| V7000 V7.4, V7.8.x, 8.2, 8.3, 8.4, 8.5, 8.6 | IBM SMI-S Provider running | 22 SSH ,5989 HTTPS |

<!-- image -->

## NOTE:

- The SolutionPacks, Dell EMC VMAX, Dell EMC Unity, IBM XIV, NetApp, HP 3PAR, and Hitachi Device Manager support Backend Array.
- The SolutionPacks, Dell EMC XtremIO, HP StorageWorks, Dell PowerFlex, Dell PowerScale, and IBM DS do not support Backend Array.
- Internal Storage is not supported in the Raw Capacity Usage and the Configured Usable reports. Service Level and Chargeback are not supported for mdisks (Virtual Disks) based on internal storage.
- Replication is not supported.

## SolutionPack for IBM XIV

SRM supports the following IBM XIV models.

## Table 28. Support for IBM XIV

| Supported Family or Models   | Prerequisites     | Ports    |
|------------------------------|-------------------|----------|
| IBM XIV                      | CIM Agent running | 5989 SSL |

## SolutionPack for IBM FlashSystem

SRM supports the following IBM FlashSystem models.

## Table 29. Support for IBM FlashSystem

| Supported Family or Models                | Prerequisites                      | Ports   |
|-------------------------------------------|------------------------------------|---------|
| Flash Array A9000(A-Series) : 415, 425    | Any latest XCLI must be installed. | 7778    |
| Flash Array (FS-Series) : 9100/9200, 5200 | N/A                                | 7443    |
| Version: 8.5.0.0 and below                |                                    | SSH 22  |

## SolutionPack for Kubernetes

SRM supports the following Kubernetes models.

## Table 30. Support for Kubernetes

| Supported Family or Models                                                                         | Prerequisites                                                                                                                                    |   Ports |
|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| Kubernetes 1.25, 1.26, 1.27, 1.28, 1.29, 1.30, 1.31, 1.32 Platform: Baremetal Server, Linux (RHEL) | For discovery, master node with a service account has access to all APIs and namespaces. For Performance, Metrics API should be enabled at node. |    6443 |

## SolutionPack for Microsoft Azure

Dell SRM supports the following Microsoft Azure versions.

## Table 31. SolutionPack for Microsoft Azure

| Supported Family or Models   | Prerequisites                                                                                                                                                                                         | Ports   |
|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| N/A                          | ● Create an Azure Service Principal with scope at Resource Group level or Subscription level . ● Storage Blob Data Owner Role is required for Azure Service Principal to fetch data related to Blobs. | N/A     |

## SolutionPack for Microsoft Hyper-V

SRM supports the following Microsoft Hyper-V models.

## Table 32. Support for Microsoft Hyper-V

| Supported Family or Models                                                                                                                          | Prerequisites       | Ports          |
|-----------------------------------------------------------------------------------------------------------------------------------------------------|---------------------|----------------|
| Hyper-V on Windows 2012 R2, Hyper-V on Windows 2016 R2 Hyper-V on Windows Server 2019 Hyper-V on Windows Server 2022 Hyper-V on Windows Server 2025 | Requires PowerShell | Not applicable |

NOTE:

Microsoft Hyper-V SolutionPack can only be installed on a Windows collector host.

## SolutionPack for Microsoft SQL Server

SRM supports the following Microsoft SQL Server models.

Table 33. Support for Microsoft SQL Server

| Supported Family or Models                                                                               | Prerequisites                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |   Ports |
|----------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| SQL Server 2012, SQL Server 2014, SQL Server 2016, SQL Server 2017, SQL Server 2019, and SQL Server 2022 | SQL Authentication: SQL authentication works with users having system administrator privileges or with an unprivileged account. For more information about configuring the SolutionPack with an unprivileged account, see Dell SRM SolutionPack Guide . SQL authentication with SSL is also supported. Windows Authentication: Windows user account must be imported into the Microsoft SQL Server with settings similar to the following: ● Server roles of public ● Securable grants for Connect SQL, View any definitions, and View server state Windows authentication with SSL is also supported. |    1433 |

Table 34. End-to-end capacity use cases

| Supported                | Not Supported                                                                            |
|--------------------------|------------------------------------------------------------------------------------------|
| MS-SQL Server > FS > LUN | MS-SQL Server > VMDK                                                                     |
| MS-SQL Server > RDM      | MS-SQL > FS using VPLEX supported for End-to-end capacity but not supported for topology |

## SolutionPack for NetApp FAS

SRM supports the following NetApp FAS models.

Table 35. Support for NetApp FAS

| Supported Family or Models                                                                                                                                                                             | Prerequisites   | Ports   |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|---------|
| NetApp FAS ONTAP versions C-mode: 9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6 , 9.7, 9.8, 9.9, 9.10, 9.11.x, 9.12.x, 9.13.x, 9.14.x, 9.15.x, 9.16.x (supported model: FAS SAN, AFF) ONTAP Select: 9.8P.4 onwards | Not applicable  | 22 SSH  |

## SolutionPack for Oracle Database

SRM supports the following Oracle Database models.

Table 36. Support for Oracle Database

| Supported Family or Models   | Prerequisites                                                         | Ports    |
|------------------------------|-----------------------------------------------------------------------|----------|
| Oracle 12, 18, 19, 21c, 23c  | The JDBC driver jar file must be in the …/APG/Databases/JDBC-Drivers/ | 1521 TCP |

## Table 36. Support for Oracle Database

| Supported Family or Models   | Prerequisites                                                      | Ports   |
|------------------------------|--------------------------------------------------------------------|---------|
|                              | Default/lib folder. ORACLE database user credentials are required. |         |

<!-- image -->

## NOTE:

- The SolutionPack for Oracle Database was tested with ojdbc5.jar and ojdbc7.jar on Oracle 10, 11, and 12g versions respectively.
- Work with the database administrator to determine the JDBC driver for the installed version of Oracle. Download the JDBC driver from: www.oracle.com/technetwork/database/features/jdbc .
- For ASM Disk collection, only Oracle instances running Solaris, Windows 2008 R2 or later, and Red Hat Enterprise Server 5, 6, 7 and 8.2 are supported.
- FileSystem information is not supported for Vdisks on VMs.
- ASM Disks on Vdisk are not supported.
- Nonadmin Windows does not support ASM data.

## Table 37. End-to-end topology and capacity for Oracle Database

| Supported                                                        | Not Supported                                                                                                                                                |
|------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Oracle > File System > LUN Oracle > ASM > RDM Oracle > ASM > LUN | Oracle > File System > Datastore Oracle > ASM > VMDK Oracle > ASM or FileSystem using VPLEX supported for End-to-end capacity but not supported for topology |

## SolutionPack for Oracle MySQL Database

SRM supports the following Oracle MySQL Database models.

Table 38. Support for Oracle MySQL Database

| Supported Family or Models        | Prerequisites                                                                                                                                                  | Ports    |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| MySQL 5.7.x, 8.0.x, 8.2, 8.3, 9.0 | Oracle MySQL Database SolutionPack requires MySQL database user login privileges to collect information from MySQL database servers that are running remotely. | 3306 TCP |

## SolutionPack for Physical Hosts

SRM supports the following HP-UX, IBM AIX, Linux, Windows, and Solaris hosts.

Table 39. Support for HP-UX hosts

| Supported Family or Models   | Prerequisites                                                                                                                                                                            |   Ports |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| HP-UX 11iv3 11.31            | PowerPath 5.2 or later must be installed on the host to fetch PowerPath metrics. INQ 9.0.0.0, 9.2 is available from: ftp.emc.com/pub/symm3000/ inquiry/Perl interpreter 5.6.1 or later . |      22 |

## Table 40. Support for IBM AIX hosts

| Supported Family or Models            | Prerequisites                                                                                                                                                                                 |   Ports |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| IBM AIX 7.1, 7.2.x, 7.3, 7.3.2, 7.3.3 | PowerPath 5.7 b194 or later must be installed on the host to fetch PowerPath metrics. INQ 9.0.0.0, 9.2 is available from: ftp.emc.com/pub/symm3000/ inquiry/Perl interpreter 5.6.1 or later . |      22 |

## Table 41. Support for Linux hosts

| Supported Family or Models                                                                                                                                                                               | Prerequisites                                                                                                                                                                                                                        |   Ports |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| LINUX Red Hat Enterprise Linux AS/ES 7.x, 8.2, 8.4 LINUX SUSE ES 12.x, 15.x, 15 SP4 Oracle Linux 7.x, 8.x, 9.0 RHEL 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 9.0, 9.1, 9.2, 9.3, 9.4, 9.5 SLES 15 SP5, SLES 15 SP6 | PowerPath 5.7 or later must be installed on the host to fetch PowerPath metrics. INQ 9.0.0.0, 9.2 is available from: ftp.emc.com/pub/symm3000/inquiry/ Perl interpreter 5.6.1 or later . Perl modules must be installed on the host. |      22 |

## Table 42. Support for Windows hosts

| Supported Family or Models                                                                       | Prerequisites                                                                                                     | Ports                 |
|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|-----------------------|
| Windows Server 2012, 2012 R2, 2016, 2019, 2022 Standard Enterprise, 2025 and Datacenter versions | PowerPath 5.7 or later must be installed on the host to fetch PowerPath metrics. Requires PowerShell 2.0 or later | 5986 HTTPS, 5985 HTTP |

## Table 43. Support for Dell SRM Windows Host Agent

| Supported Family or Models                                                                                | Prerequisites                                                                                                     | Ports    |
|-----------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|----------|
| Windows Server 2012, Windows Server 2012 R2, 2016, 2019, 2022 Standard Enterprise and Datacenter versions | PowerPath 5.7 or later must be installed on the host to fetch PowerPath metrics. Requires PowerShell 2.0 or later | 5989 SSH |

## Table 44. Support for Solaris hosts

| Supported Family or Models   | Prerequisites                                                                                                                                                                                      |   Ports |
|------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| Solaris 9, 10, 11            | PowerPath 5.5 P02 HF02 or later must be installed on the host to fetch PowerPath metrics. INQ 9.0.0.0, 9.2 is available from: ftp.emc.com/pub/ symm3000/inquiry/ Perl interpreter 5.6.1 or later . |      22 |

<!-- image -->

## NOTE:

- For more information about port configuration, see Dell SRM Ports Usage and Worksheet .
- INQ 9.0.0.0, 9.2 is supported only on 64-bit operating system platforms. INQ 7.6.2 must be manually copied onto 32-bit target hosts.
- The PowerPath Support Matrix on the Dell Online Support Site provides more details.
- For RHEL 9.2 and 9.3, install the perl-Sys-Hostname module on the host if the module is missing on the host.
- It is recommended to use agentless mode for AIX device discovery.

## SolutionPack for Dell PowerEdge

SRM supports the following Dell PowerEdge models.

## Table 45. Support for Dell PowerEdge

| Supported Family or Models   | Prerequisites                                                | Ports   |
|------------------------------|--------------------------------------------------------------|---------|
| iDRAC9 - 6.x and 7.x         | Identify the iDRAC details. Identify the access credentials. | N/A     |

## SolutionPack for Dell PowerFlex

SRM supports the following Dell PowerFlex.

## Table 46. Support for Dell PowerFlex

| Supported Family or Models                                    | Prerequisites                                                                                                                | Ports     |
|---------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|-----------|
| Dell PowerFlex 3.0 ,3.0.1, 3.5.x, 3.6, 3.6.1, 4.0, 4.5, 4.6.2 | Dell PowerFlex REST gateway should be installed on the host and should be configured with PowerFlex Meta Data Manager (MDM). | 443 HTTPS |

<!-- image -->

## NOTE:

- Topology for Dell PowerFlex on VMware and Microsoft Hyper-V is not supported.
- For Dell PowerFlex Node server, reports similar to software-only Dell PowerFlex versions are supported.

## SolutionPack for Dell PowerScale

SRM supports the following Dell PowerScale models.

## Table 47. Support for Dell PowerScale

| Supported Family or Models                                          | Ports      |
|---------------------------------------------------------------------|------------|
| PowerScale OneFS 9.2, 9.3, 9.4, 9.5, 9.6 ,9.7, 9.8, 9.9, 9.10, 9.11 | 8080 HTTPS |

## SolutionPack for Dell PowerStore

SRM supports the following Dell PowerStore models.

Table 48. Support for Dell PowerStore

| Supported Family or Models                                                               | Prerequisites                                                             | Ports                                    |
|------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|------------------------------------------|
| PowerStore T(Unified) and PowerStore X(Unified+) PowerStore 3.0, 3.2, 3.5, 3.6, 4.0, 4.1 | Arrays must be running with PowerStoreOS 1.0.1.x, or later code versions. | 443 or User configured port of the array |

<!-- image -->

## NOTE:

- Only Capacity and Performance metric support for VolumeGroups works with PowerStore running with version 1.0.3.x or later.

- Performance metrics for Filesystems work with PowerStore running with version 2.x or later only.
- Replication is supported for Virtual Volume, Metro, NAS Server, and File System.
- Hypervisors and Virtual Volumes discovery are not supported.
- To populate hardware alerts in Dell SRM, the user must configure the SNMP trap recipient on the PowerStore appliance.

## SolutionPack for Dell PowerSwitch

SRM supports the following Dell PowerSwitch models.

## Table 49. Support for Dell PowerSwitch

| Supported Family or Models                                                                                                       | Prerequisites                                                                                           |   Ports |
|----------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|---------|
| Dell PowerSwitch S-Series (25-100 GbE, 10 GbE) and Z-Series Dell Networking Smartfabric OS10 is supported until version 10.5.6.3 | PowerSwitch is discovered through OS10 RESTCONF API. REST interface must be enabled on the PowerSwitch. |     443 |

<!-- image -->

## NOTE:

- Data flow into global reports is not supported.
- Topology map view is not supported.

## SolutionPack for Dell PowerVault

SRM supports the following Dell PowerVault storage array models.

## Table 50. Support for PowerVault

| Supported Family or Models                                      | Prerequisites   | Ports   |
|-----------------------------------------------------------------|-----------------|---------|
| ME5 Series firmware version 1.2.0.1, 1.2.0.2, 1.2.0.3 , 1.2.1.1 | NA              | NA      |

## SolutionPack for Pure Storage

SRM supports the following Pure Storage models.

## Table 51. Support for pure storage

| Supported Family or Models                                                                                               | Prerequisites   | Ports     |
|--------------------------------------------------------------------------------------------------------------------------|-----------------|-----------|
| Flash Array with Purity/FA version 5.1.10, 6.0.0, 6.1.6, 6.2.10, 6.3.4, 6.4.1, 6.4.7, 6.4.8, 6.4.10, 6.5.1, 6.5.3, 6.6.* | N/A             | 443 HTTPS |

<!-- image -->

## NOTE:

- If version 1.* is supported, the highest supported REST version of 1.* is picked. For example, if the Flash Array supports versions 1.0, 1.1, 1.2, and so on until 2.23, then the version 1.19 is picked for reporting. Support is provided up to 1.19.
- If version 1.* is not supported, the highest REST version of 2.* is picked. Support is provided from 2.23.
- Pure1 is supported only for power consumption details of discovered pure storage arrays in SRM.

## SolutionPack for Dell RecoverPoint

SRM supports the following Dell RecoverPoint models.

## Table 52. Support for Dell RecoverPoint

| Supported Family or Models                      | Ports   |
|-------------------------------------------------|---------|
| RecoverPoint 5.0.x, 5.1.x                       | 443     |
| RecoverPoint for Virtual Machines 5.1, 5.2, 5.3 |         |

## SolutionPack for Dell SC Series

SRM supports the following Dell SC Series.

## Table 53. Support for Dell SC Series

| Supported Family or Models                                  | Prerequisites                                          | Ports      |
|-------------------------------------------------------------|--------------------------------------------------------|------------|
| Dell SC arrays running with 7.1.x, 7.2.x, 7.3.x, 7.4.x, 7.5 | Dell Storage Manager Data Collector must be installed. | 3033 HTTPS |

## SolutionPack for Dell Unity

SRM supports the following Dell Unity models.

## Table 54. Support for Dell Unity

| Supported Family or Models                                                                                                                                                                                             | Prerequisites   |   Ports |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|---------|
| OE 5.0.3, 5.0.4, 5.0.5, 5.0.6, 5.0.7, 5.1.0, 5.1.1, 5.1.2.x, 5.1.3.x, 5.2.0, 5.3.0, 5.4.0, 5.5.0 (Block and File) Used with physical Unity XT and Unity models. UnityVSA (Virtual Storage Appliance) is not supported. | Not applicable  |     443 |

## SolutionPack for Dell EMC VMAX

Describes the prerequisites for support of Dell EMC VMAX.

The following is a list of prerequisites for the support of Dell EMC VMAX models.

Table 55. Support for Dell EMC VMAX

| Supported Collection Interfaces   | Collector                                       | Prerequisites                                                                                                                                    | Ports     |
|-----------------------------------|-------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|-----------|
| VMAX3 family                      | Topology and Capacity Collector                 | SMI-S Provider 8.0.1.x and later.                                                                                                                | 5988/5989 |
| VMAX3 family                      | Performance Collector using Unisphere for VMAX3 | Unisphere for VMAX 8.0.1.x and later provides more overall performance metrics than SMI-S Provider but does not include LUN performance metrics. | 8443      |
| VMAX3 family                      | Performance Collector using SMI-S               | SMI-S Provider 8.0.1.x and later provides fewer overall performance metrics than                                                                 | 5988/5989 |

Table 55. Support for Dell EMC VMAX (continued)

| Supported Collection Interfaces   | Collector   | Prerequisites                                   | Ports   |
|-----------------------------------|-------------|-------------------------------------------------|---------|
|                                   |             | Unisphere but includes LUN performance metrics. |         |

## Comments

- The Workload Distribution Report and Disk Failure Impact Analysis are not supported for VMAX3.
- iSCSI Gatekeepers are supported.
- If performance metrics are required, then you must install Unisphere for VMAX or the SMI-S Provider, or both.
- Do not exceed six medium-sized (30K-40K devices) VMAX arrays for each VMAX collector.
- Any array with more than 30 K devices requires 4 GB of heap size for the collector. For more information, see the Performance and Scalability Guidelines.
- As of the 3.5 release, statistics are available through both SMI-S and Unisphere. However, if both SMI-S and Unisphere are present, Dell SRM does not collect overlapping statistics from both sources. But overlapping statistics are always collected only through Unisphere. In this case, only the LUN statistics come from SMI-S. There are not two sets of same-named but inconsistent statistics.

## Table 56. Guidelines for Gatekeepers

| Gatekeepers that are used to support   |   Minimum Gatekeepers |
|----------------------------------------|-----------------------|
| UniVMAX                                |                     6 |
| Dell SRM                               |                     2 |
| Customer run scripts                   |                     2 |

100 K maximum devices from all arrays, zone to host, where the SMI-S Provider is installed.

## SolutionPack for Dell VMAX/PowerMax

SRM supports the following Dell VMAX/PowerMax models.

Table 57. Support for Dell VMAX/PowerMax

| Supported Family or Models                                                                                                                                                                                                                                                                                                                               | Prerequisites   |   Ports |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|---------|
| ● PowerMax V3, V4, and All Flash array families running ● HYPERMAX OS 5977.952.892 ● PowerMaxOS 5978.144.144 ● PowerMaxOS 5978.221.221 ● PowerMaxOS 5978.444.444 ● PowerMaxOS 5978.479.479 ● PowerMaxOS 5978.669.669 ● PowerMaxOS 5978.711.711 ● PowerMaxOS 5978.714.714 ● PowerMaxOS 10.0.0 ● PowerMaxOS 10.0.1 ● PowerMaxOS 10.1.0 ● PowerMaxOS 10.2.0 | Not applicable  |    8443 |

## Table 58. Collecting performance statistics, capacity, and topology information using Unisphere

| Unisphere   | Notes                                                                                                     |
|-------------|-----------------------------------------------------------------------------------------------------------|
| 9.2.0       | Minimum 9.2.0-4 version is recommended for PowerMax arrays with PowerMaxOS 5978.669.669 and 5978.711.711. |

Table 58. Collecting performance statistics, capacity, and topology information using Unisphere (continued)

| Unisphere   | Notes                                                                               |
|-------------|-------------------------------------------------------------------------------------|
| 10.0.0      | Minimum 10.0.0-2 version is recommended for PowerMax arrays with PowerMaxOS 10.0.0. |
| 10.0.1      | Minimum 10.0.1-0 version is recommended for PowerMax arrays with PowerMaxOS 10.0.1. |
| 10.1.0      | Minimum 10.1.0-0 version is recommended for PowerMax arrays with PowerMaxOS 10.1.0. |
| 10.2.0      | Minimum 10.2.0-0 version is recommended for PowerMax arrays with PowerMaxOS 10.2.0. |

## SolutionPack for VMware vSphere vSAN and VxRail

SRM supports the following VMware vSphere vSAN and VxRail models.

Table 59. Support for VMware vSphere vSAN and VxRail

| Supported Family or Models                                       | Prerequisites                                                                                                                                                                                                                                                | Ports   |
|------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| VMware vCenter Server 6.5, 6.7, 7.0, 8.0 vSAN 6.5, 6.7, 7.0, 8.0 | VMware infrastructure. PowerPath/VE 5.8 or later must be installed on the host to collect PowerPath metrics. Access to vCenter user credentials need a minimum Read-Only role and should be applied at the vCenter level that is propagated to the children. | 443 TCP |

<!-- image -->

NOTE: New Reports added in inventory:

- "Storage Policy" for VMware device
- "VxRail Clusters" for VxRail device

Hardware Alerts/Alarms Support added for VMware vCenter.

- NOTE: SRM is recommending the existing VxRail customers to use the newly enhanced "VMware vSphere vSAN &amp; VxRail" Solution Pack which has more capabilities on the reporting features.

If Both SPs are in use together, then make sure that VxRail Manager IPs discovered in VxRail SP, those same VxRail IPs Should not be present /re-discovered in VMware SP at the same time.

## SolutionPack for Dell VPLEX

SRM supports the following Dell VPLEX models.

Table 60. Support for Dell VPLEX

| Supported Family or Models                                                               | Prerequisites                                                                                                                                       | Ports             |
|------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|
| 6.2, 6.2 SP1 of standalone and two cluster support Metro node: 7.0, 7.1, 8.0, 8.0.1, 9.0 | REST API access, CLI access, and Virtual Volume Perpetual monitor logs (for VPLEX 5.4.x or later), CLI access, and Director Perpetual monitor logs. | 443 HTTPS, 22 SSH |

<!-- image -->

## NOTE:

- Do not run VPLEX 5.2sp1 patch 2 with any version of the product as the VPLEX management server can become unresponsive.
- The SolutionPack Dell EMC VMAX, Dell Unity, NetApp, Dell EMC XtremIO, IBM XIV, Hitachi Device Manager, HP StorageWorks, and HP 3PAR support Backend Arrays.

- The SolutionPack Dell PowerFlex, Dell PowerScale, and IBM DS do not support Backend Array.
- Engine APIs are not supported from Metro node 7.1 onwards.
- VPLEX 6.2.1 supports both one cluster and two cluster modes of discovery. In this context, the two cluster mode refers to VPLEX only, not a Metro node.

## Dell SolutionPack for VxRail

SRM supports the following VxRail models.

## Table 61. Support for VxRail

| Supported Family or Models      | Prerequisites                                                                                                                                                    | Ports   |
|---------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|
| VxRail 4.7.x, 7.0.x, 8.0, 8.0.3 | Access to vCenter user credentials need a minimum Read-Only role and should be applied at the vCenter level that is propagated to the children. REST API access. | 443 TCP |

<!-- image -->

NOTE: Added External VxRails Support in "SolutionPack for VMware vCenter"

New Reports added in inventory:

"Storage Policy" for VMware device

"VxRail Clusters" for VxRail device

Hardware Alerts/Alarms Support added for VMware vCenter.

## NOTE:

- SRM is recommending the existing VxRail customers to use the newly enhanced "VMware vSphere vSAN and VxRail" Solution Pack which has more capabilities on the reporting features.
- If both SPs are in use together, then make sure that VxRail Manager IPs discovered in VxRail SP, those same VxRail IPs Should not be present/rediscovered in VMware SP simultaneously.

## SolutionPack for Dell EMC XtremIO

SRM supports the following Dell EMC XtremIO models.

Table 62. Support for Dell EMC XtremIO

| Supported Family or Models                                                                   | Prerequisites   | Ports     |
|----------------------------------------------------------------------------------------------|-----------------|-----------|
| XtremIO operating system 4.x, 5.x, 6.0, 6.1, 6.2, 6.2.1, and 6.3, 6.3.1, 6.3.2, 6.3.3, 6.4.1 | Not applicable  | 443 HTTPS |

<!-- image -->

## Supported password Management Software

## Table 63. Cyber Ark support

| Supported Software   | Version   | Pre-requisites                                                          |
|----------------------|-----------|-------------------------------------------------------------------------|
| CYBERARK             | 12.6.0    | For more information, refer to the latest Administration guide for SRM. |

## Table 64. Credential Provider versions

| Supported Software   | Version   | Pre-requisites                                                                                                            |
|----------------------|-----------|---------------------------------------------------------------------------------------------------------------------------|
| RHEL 9.0             | 13.0.2    | For configuration with SRM, refer to Dell SRM Administrator Guide. For more information, refer to CyberArk documentation. |
| Windows 2022         | 13        | For configuration with SRM, refer to Dell SRM Administrator Guide. For more information, refer to CyberArk documentation. |

<!-- image -->

NOTE:

Refer to CyberArk Documentation to see more Supported Software (OS) for Credential Provider.

4

## Documentation Feedback

Dell Technologies strives to provide accurate and comprehensive documentation and welcomes your suggestions and comments. You can provide feedback in the following ways:

- Online feedback form Rate this content feedback form is present in each topic of the product documentation web pages. Rate the documentation or provide your suggestions using this feedback form.
- Email-Send your feedback to SRM Doc Feedback. Include the document title, release number, chapter title, and section title of the text corresponding to the feedback.

To get answers to your queries related to Dell SRM through email, chat, or call, go to Dell Technologies Technical Support page.