## Dell SRM

Windows Host Agent Installation Guide

<!-- image -->

## Notes, cautions, and warnings

<!-- image -->

NOTE:

A NOTE indicates important information that helps you make better use of your product.

CAUTION: A CAUTION indicates either potential damage to hardware or loss of data and tells you how to avoid the problem.

WARNING: A WARNING indicates a potential for property damage, personal injury, or death.

© 2024 Dell Inc. or its subsidiaries. All rights reserved. Dell Technologies, Dell, and other trademarks are trademarks of Dell Inc. or its subsidiaries. Other trademarks may be trademarks of their respective owners.

## Contents

| Tables........................................................................................................................................... 4                                        |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Chapter 1: Purpose and Goals........................................................................................................5                                                      |
| Audience................................................................................................................................................................................ 5 |
| Chapter 2: Introduction.................................................................................................................6                                                  |
| Chapter 3: Pre-Requisites for Windows Host Installation.............................................................. 7                                                                    |
| Installing Windows Host Agent.........................................................................................................................................7                    |
| Install Using Command Prompt with UI Options....................................................................................................7                                          |
| Install Using Command Prompt without UI (quiet mode)....................................................................................8                                                  |
| Verify Installation.................................................................................................................................................................9      |
| Post Installation..................................................................................................................................................................10      |
| Chapter 4: Uninstall Windows Host Agent....................................................................................12                                                              |
| Uninstall Using Programs and Features Window in Control Panel.........................................................................12                                                   |
| Uninstall Using Command Prompt with UI Options...................................................................................................12                                        |
| Uninstall Using Command Prompt without UI (Quiet mode).................................................................................. 13                                                |
| Verify the Uninstallation................................................................................................................................................... 14            |
| Chapter 5: FAQ............................................................................................................................15                                               |
| Customizing port................................................................................................................................................................15         |
| Changing username/password ......................................................................................................................................15                        |
| Migrating Hosts that are discovered using old EHI Agent to SRM Windows Host Agent ..............................15                                                                         |
| Chapter 6: Documentation Feedback........................................................................................... 16                                                            |

4

## Tables

|   1 | Command descriptions..............................................................................................................................................7   |
|-----|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|   2 | Command descriptions............................................................................................................................................. 9   |
|   3 | Command descriptions............................................................................................................................................13    |

Command description..............................................................................................................................................14

## Purpose and Goals

This document describes how to install the SRM Windows Host Agent in the Dell SRM environment. You can easily extend the procedures that are presented in the document to cover all Windows Host Agent Installations.

## Topics:

- Audience

## Audience

This document is intended for anyone planning to install Windows Host Agent in a Dell SRM environment.

## Introduction

The Windows Host Agent is an agent software which simplifies discovery of Windows Physical Hosts. This Installation Guide is added in SRM 4.3 to support the Windows Host Agent Installation.

In the SRM 4.2 and earlier releases there were two approaches used for Windows Host Discovery:

- Agent less Mechanism
- EHI Agent

In SRM 4.3 and later releases, a new agent is introduced (Windows Host Agent) to discover Windows Physical Hosts. Currently there are two Agent based software packages available for Windows Host Discovery which are explained below:

- EHI Agent , is the original Dell Host Interface Agent Solution Pack; this software agent will move to end of life approximately after the SRM 4.3.1 release. But it is still supported and currently used. Additional information can be found in the SRM Solution Pack Guide.
- Windows Host Agent is a new agent based mechanism to discover Windows Host from SRM:
- Data collection is done through the use of SSH.
- Does not require a separate SolutionPack.
- Discovery details for the Host can be provided using Generic RSC Host Configuration.
- Supports Windows Server(s) - 2008 R2 (64-bit), 2012 R2 (64-bit), and 2016 R2 (64-bit).

Recommendations for Agent based Windows Physical Host Discovery :

- If the SRM 4.3 installation is new and the customer wants to go with Agent based discovery, then Dell Technologies recommends to use Windows Host Agent for Windows Physical Host Discovery.
- If the SRM 4.3 installation is an upgrade and starting Windows Physical Host discovery for the first time, and if the customer wants to go with Agent based discovery then Dell Technologies recommends to use Windows Host Agent for Windows Physical Host Discovery.
- If the SRM 4.3 installation is an upgrade, the EHI Agent can stay in place with no change, but customer needs to plan for migration to the new Windows Host Agent as EHI will be deprecated in future.

<!-- image -->

## Pre-Requisites for Windows Host Installation

Follow the below pre-requisites for successful windows host installation.

- Log in to Windows as Administrator or be part of the Administrators group.
- Do not simultaneously use multiple methods of host discovery to prevent duplicate data collection.
- If the EHI Agent is already installed on the Windows host, uninstall it before installing the Windows Host Agent.

## Topics:

- Installing Windows Host Agent
- Verify Installation
- Post Installation

## Installing Windows Host Agent

You can install the Windows Host Agent in two ways:

- Using the command prompt with UI options.
- Using the command prompt without UI options (quiet mode).

## Install Using Command Prompt with UI Options

## Steps

1. Select command prompt and Run as Administrator.
2. Navigate to the MSI folder.
3. Use the following command to install Windows Host Agent:
4. msiexec /i SRM Windows Host Agent.msi /norestart /L*V C:\Temp\log.txt NOTE: The MSI name can vary based upon the release version.

<!-- image -->

## Table 1. Command descriptions

| Command component   | Description                                        |
|---------------------|----------------------------------------------------|
| /i                  | The install flag indicating a normal installation. |

Table 1. Command descriptions (continued)

| Command component          | Description                                                                                                             |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------|
| SRM Windows Host Agent.msi | The name of the MSI                                                                                                     |
| /norestart                 | Do not restart after installation                                                                                       |
| /L*V                       | The flag to enabled logging ( *V indicates Verbose Output)                                                              |
| C:\Temp\log.txt            | Location of the log file You can specify any existing directory. The installation fails if the directory does not exist |

NOTE:

Even without the /norestart option, the installation/uninstallation process does not reboot the Windows host.

4. Select the Destination Folder. (The default location is C:\Program Files\Dell\.)
2. NOTE: If the selected destination folder is C:\Program Files\Dell , the product is installed in the C:\Program Files\Dell\SRM Windows Host Agent\ folder .

<!-- image -->

## Install Using Command Prompt without UI (quiet mode)

## Steps

1. Select command prompt and Run as Administrator.

<!-- image -->

2. Go to the MSI folder.
3. Use the following command to install Windows Host Agent.

msiexec /i SRM Windows Host Agent.msi INSTALLDIR=D:\CustomPath\ /norestart /qn /L*V C: \Temp\log.txt

<!-- image -->

The MSI name can vary based on the release version.

Table 2. Command descriptions

| Command component          | Description                                                                                                              |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------|
| /i                         | The install flag indicating normal installation                                                                          |
| SRM Windows Host Agent.msi | The name of the MSI                                                                                                      |
| INSTALLDIR                 | The install directory with the path followed                                                                             |
| /norestart                 | Do not restart after installation.                                                                                       |
| /qn                        | Quiet mode, No UI                                                                                                        |
| /L*V                       | The flag to enable logging (*V indicates Verbose Output).                                                                |
| C:\Temp\log.txt            | Location of the log file. You can specify any existing directory. The installation fails if the directory does not exist |

## Verify Installation

## Steps

Verify the installation on the target host by checking if the:

- SRM Host Agent service is up and running by opening windows services panel.

<!-- image -->

- runLMD task is created in Task Scheduler.

<!-- image -->

<!-- image -->

## NOTE:

If the SRM Host Agent service is not up and running, and if runLMD task is not created, see the FAQ/Troubleshooting section.

## Post Installation

## Steps

1. Open the SRM Admin page on a browser: https://&lt;&lt;FRONTEND\_HOST&gt;&gt;/admin
2. Go to Discovery &gt; Discovery Center &gt; Manage Discovery .
3. Select Host Configuration and click Add .
4. Specify the discovery mode as HostAgent Windows as given below:

<!-- image -->

5. To discover, add the target host (where Windows Host Agent is already installed).
- Default Credentials: Username: admin , password: #1Password .
- Default Port: 5989

## NOTE:

For details related to customizing Username/Password/Port, see the FAQs section.

If the username, password, or port is customized, enter the customized details in the SRM to discover Windows host.

<!-- image -->

## Uninstall Windows Host Agent

This section provides information about uninstalling windows host agent.

You can uninstall the Windows Host Agent in three ways:

- Using the Programs and Features window in Control Panel.
- Using command prompt with UI options.
- Using command prompt without UI.

## Topics:

- Uninstall Using Programs and Features Window in Control Panel
- Uninstall Using Command Prompt with UI Options
- Uninstall Using Command Prompt without UI (Quiet mode)
- Verify the Uninstallation

## Uninstall Using Programs and Features Window in Control Panel

## Steps

1. Log in to the Windows Host with default administrator credentials (or) as a user who is part of the Administrators group.
2. Open services.msc and stop the service SRM Host Agent.
3. Select the SRM Windows Host Agent program and click Uninstall.

## Uninstall Using Command Prompt with UI Options

## Steps

1. Log in to the Windows Host with default administrator credentials (or) as a user who is part of the Administrators group.
2. Open services.msc and stop the service SRM Host Agent.
3. Select command prompt and Run as Administrator.
4. Navigate to the MSI folder. You should use the same version that was used to install.

<!-- image -->

5. Use the following command to uninstall Windows Host Agent with UI options. msiexec /x SRM Windows Host Agent.msi /norestart /L*V C:\Temp\log.txt

## Table 3. Command descriptions

| Command component          | Description                                                                                                                 |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| /x                         | The flag for Normal uninstallation                                                                                          |
| SRM Windows Host Agent.msi | Name of the MSI                                                                                                             |
| /norestart                 | Do not restart after uninstallation                                                                                         |
| /L*V                       | The flag to enable logging (*V indicates Verbose Output.)                                                                   |
| C:\Temp\log.txt            | Location of the log file. You can specify any existing directory. The uninstallation fails if the directory does not exist. |

6. If the SRM Host Agent service is running during uninstallation, the message shown below is displayed:
7. To proceed with uninstallation, select Automatically close applications and attempt to restart them after setup is complete and click OK .

<!-- image -->

## Uninstall Using Command Prompt without UI (Quiet mode)

## Steps

1. Log in to the Windows Host using default administrator credentials (or) as a user who is part of the Administrators group.
2. Open services.msc and stop the service the SRM Host Agent.
3. Select command prompt and Run as Administrator.

<!-- image -->

4. Go to the MSI folder, where you must use the same version that was used to install.
5. Use the following command to uninstall Windows Host Agent in quiet mode(No UI).

msiexec /x SRM Windows Host Agent.msi /norestart /qn /L*V C:\Temp\log.txt

Table 4. Command description

| Command component          | Description                                                                                                                 |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| /x                         | The uninstall flag indicating Normal uninstallation                                                                         |
| SRM Windows Host Agent.msi | Name of the MSI                                                                                                             |
| /norestart                 | Do not restart after uninstallation.                                                                                        |
| /qn                        | Quiet mode, No UI                                                                                                           |
| /L*V                       | The flag to enable logging (*V indicates Verbose Output).                                                                   |
| C:\Temp\log.txt            | Location of the log file. You can specify any existing directory. The uninstallation fails if the directory does not exist. |

## Verify the Uninstallation

To check that the successful uninstallation of Windows Host Agent follows the below steps.

## Steps

1. Check if the runLMD task is deleted from Task Scheduler.
2. Check if the SRM Host Agent service is deleted from the Windows host.
3. Check if the agent installation directory is cleaned up properly.
4. NOTE: Ensure that the uninstallation is successful and the above check list is met before the next installation; otherwise, the subsequent installation is likely to fail.

## Topics:

- Customizing port
- Changing username/password
- Migrating Hosts that are discovered using old EHI Agent to SRM Windows Host Agent

## Customizing port

1. The SRM Host Agent service runs on 5989 port by default.
2. To customize the port, change the port value in &lt;&gt;\SRM Windows Host Agent\bin\srmhostagentconfig.properties and restart the SRM Host Agent service.

## Changing username/password

1. Upon installation, Windows Host Agent uses default credentials to authenticate connections. [Username: admin, Password: #1Password]
2. Create a user using the createuser.bat file located in the &lt;&gt;\Dell EMC SRM Windows Host Agent\bin\ folder .
3. Upon successful execution of the createuser.bat file, a file that is named user.properties is created under &lt;&gt;\SRM Windows Host Agent\bin\ folder .
4. Use new credentials to discover the Physical Host in SRM.
5. NOTE: The default credentials do not work once the user is created. The user is only for authenticating the SSH server, and the user details scope is limited to this application.

<!-- image -->

## Migrating Hosts that are discovered using old EHI Agent to SRM Windows Host Agent

Use the migration\_util.ps1 utility that is placed under &lt;&gt;\EMC SRM Windows Host Agent\utils\ to migrate Hosts that are discovered using the EHI Agent to SRM Windows Host Agent.

1. Place the script migration\_util.ps1 in any folder on a Windows host where the SRM appliance is accessed.
2. Export the CSV from the SRM appliance Administration &gt; Discovery &gt; Discovery Center &gt; Manage Discovery &gt; HostAgent EHI and place it in the same folder as migration\_util.ps1.
3. Create a backup of this file.
4. Set the permission (if not set) to run the script on Windows PowerShell: set-executionpolicy remotesigned
5. Run the following command on Windows PowerShell: .\migration\_util.ps1
6. The output file is created in the same folder with the name Host configuration.csv and can be imported under Administration &gt; Discovery &gt; Discovery Center &gt; Manage Discovery &gt; Host configuration to the same appliance.
7. NOTE: Newly imported hosts contain the default username, password, and port. If these values are changed at Windows Host, the changed values are used before testing the connectivity.

```
For example: .\migration_util.ps1 .\Host Agent_EHI_discovery.csv
```

<!-- image -->

<!-- image -->

FAQ

<!-- image -->

6

## Documentation Feedback

Dell Technologies strives to provide accurate and comprehensive documentation and welcomes your suggestions and comments. You can provide feedback in the following ways:

- Online feedback form Rate this content feedback form is present in each topic of the product documentation web pages. Rate the documentation or provide your suggestions using this feedback form.
- Email-Send your feedback to SRM Doc Feedback. Include the document title, release number, chapter title, and section title of the text corresponding to the feedback.

To get answers to your queries related to Dell SRM through email, chat, or call, go to Dell Technologies Technical Support page.