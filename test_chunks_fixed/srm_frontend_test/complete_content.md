## Dell SRM

Guidelines for Deploying Additional Frontend Servers

<!-- image -->

## Notes, cautions, and warnings

<!-- image -->

NOTE:

A NOTE indicates important information that helps you make better use of your product.

CAUTION: A CAUTION indicates either potential damage to hardware or loss of data and tells you how to avoid the problem.

WARNING: A WARNING indicates a potential for property damage, personal injury, or death.

© 2016-2024 Dell Inc. or its subsidiaries. All rights reserved. Dell Technologies, Dell, and other trademarks are trademarks of Dell Inc. or its subsidiaries. Other trademarks may be trademarks of their respective owners.

## Contents

| Chapter 1: Introduction................................................................................................................. 4                                                 |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Audience................................................................................................................................................................................ 4 |
| Introduction...........................................................................................................................................................................4   |
| Chapter 2: Architecture overview..................................................................................................5                                                        |
| Additional frontend server deployment..........................................................................................................................5                           |
| Additional frontend server configuration.......................................................................................................................6                           |
| Chapter 3: Configuring the SRM management functions............................................................... 7                                                                       |
| Adding MySQL grants to the databases........................................................................................................................ 7                             |
| Configuring compliance......................................................................................................................................................8              |
| LDAP authentication...........................................................................................................................................................8            |
| Import-Properties task.......................................................................................................................................................8             |
| Activate the new configuration settings ...................................................................................................................... 9                           |
| Chapter 4: Configuring the shared reports and tasks...................................................................10                                                                   |
| Consolidate the scheduled reports................................................................................................................................10                        |
| Configuring an NFS share for the user reports..........................................................................................................10                                  |
| Consolidate the scheduled reports................................................................................................................................12                        |
| Additional frontend server tasks.................................................................................................................................... 13                    |
| Chapter 5: Documentation Feedback........................................................................................... 14                                                            |
| Appendix A: F5 load balancer configuration.................................................................................15                                                              |
| Appendix B: HAProxy load balancer configuration....................................................................... 16                                                                  |
| Appendix C: FAQ..........................................................................................................................18                                                |
| SolutionPacks report installation....................................................................................................................................18                    |
| SolutionPacks upload........................................................................................................................................................ 18            |
| SolutionPacks formula...................................................................................................................................................... 18             |
| SolutionPacks property-mapping...................................................................................................................................18                        |

## Introduction

This document describes how to deploy Additional Frontend Servers in an Dell SRM installation. You can easily extend the procedures in this document to cover installations that require more than two Frontend Servers. Dell Technologies recommends that each Frontend Server should serve no more than 10 concurrent and active users.

This document replaces all previously-published documents on configuring multiple Dell SRM Frontend Servers.

## Topics:

- Audience
- Introduction

## Audience

This topic briefs about the target audience for this document.

This document is intended for anyone planning to deploy Additional Frontend Servers in a Dell SRM installation.

This document assumes that the primary Frontend Server is already installed and running. This Frontend Server (which is the first Frontend Server to be installed) is the user interface for the product.

See the Dell SRM Installation and Configuration guide for details on deploying the Frontend Server.

## Introduction

Introduction to guidelines for deploying additional frontend servers.

The performance and scalability guidelines recommend that you have one Frontend Server for every 10 active and concurrent users. If you plan on having more than 10 users, you must deploy more Frontend Servers. Using a load balancer to distribute processing among multiple Frontend Servers is highly recommended. Another use case for deploying additional Frontend Servers is to offload the scheduled report from the Primary Frontend Server to improve UI performance.

Although this guide covers the F5 and HAproxy load balancers, you can use the load balancer of your choice. These two load balancers are provided as examples in the section 'Architecture with network Load Balancers.'

In a multiple Frontend Server environment, only one Frontend Server should handle the web- applications that are listed under the Administrator panel. These web-applications are:

- Alerting-Frontend
- APG-Web-Service
- Administration
- Compliance Frontend
- Device-Discovery
- MIB-Browser

The first installed Frontend Server is now called the Primary Frontend Server and the subsequent Frontend Server installed is called the Additional Frontend Server. The Primary Frontend Server provides all the SRM functionality (user and Administration) while the Additional Frontend Server only provides user functions.

When a user logs in to an Additional Frontend Server, all user-related reports and functions are available through the Additional Frontend Server the user logged into. If the user is in the Administration UI and selects any of the administration functions available in this UI, the user will be redirected to the Primary Frontend Server and forced to log in again to the Primary Frontend Server.

## Architecture overview

Without network load balancers, the user would log into one of the installed Frontend Servers (Primary or Additional). Users are typically assigned to a frontend for SRM environments that have greater than 10 concurrent user activity.

## Topics:

- Additional frontend server deployment
- Additional frontend server configuration

## Additional frontend server deployment

You can install the Additional Frontend Server from the 1VM vApp deployment software or using the binary deployment software. Run the Frontend and all Database servers as Linux operating system servers when the metric count is greater than 5M:

Ensure the Frontend Server is installed as described in the Dell SRM Installation and Configuration Guide. After the deployment of Additional Frontend Server if the existing SRM Servers are in a vApp folder, move the new Additional Frontend Server into the vApp folder and edit the vApp Start-up order to start the Additional Frontend Server with the Primary Frontend Server.

```
lppa028:~ # manage-modules.sh list installed Installed Modules: Identifier                        Instance                     : Category --------------------              ------------                 ---------------*administration-tool              Default                      : Tools *alerting-frontend                alerting-frontend            : Web-Applications *centralized-management           centralized-management       : Web-Applications *compliance-frontend              compliance-frontend          : Web-Applications *device-discovery                 device-discovery             : Web-Applications *diagnostic-tools                 Default                      : Tools *esrs-manager                     Default                      : Tools *formulas-resources               Default                      : Custom *frontend                         APG                          : Web-Applications *frontend-report-generator        Default                      : Tools *frontend-ws                      APG-WS                       : Web-Applications *generic-usage-intelligence       Generic-Usage-Intelligence   : Block *java                             8.0.72                       : Java *jdbc-drivers                     Default                      : Databases *license-manager                  Default                      : Tools *mib-browser                      mib-browser                  : Web-Applications *module-manager                   1.9                          : Tools *property-store                   Default                      : Databases *srm                              Default                      : Product *task-scheduler                   Default                      : Tools *tomcat                           Default                      : Web-Servers *usage-intelligence               Generic-Usage-Intelligence   : Tools *vapp-manager                     Default                      : Tools *webapps-resources                Default                      : Custom *webservice-gateway               Default                      : Tools *whatif-scenario-cli              Default                      : Tools lppa028:~ # manage-modules.sh service status all *Checking 'webservice-gateway Default'...                                      [ running ] *Checking 'tomcat Default'...                                                  [ running ] *Checking 'task-scheduler Default'...                                          [ running ] lppa028:~ #
```

## Additional frontend server configuration

## Steps

1. Manually start the Save Frontend VM.
2. Copy the files that are listed below from the Primary Frontend Server to the Additional Frontend Server.
3. NOTE: You can use the scp command to do it or WinSCP. Dell Technologies recommends that you back up the files on the Additional Frontend Server before overwriting them.
4. …/APG/Web-Servers/Tomcat/&lt;instance-name&gt;/conf/server.xml
5. …/APG/Web-Servers/Tomcat/&lt;instance-name&gt;/conf/Catalina/localhost/APG.xml
6. …/APG/Web-Servers/Tomcat/&lt;instance-name&gt;/conf/Catalina/localhost/APG-WS.xml
7. …/APG/Tools/Frontend-Report-Generator/&lt;instance-name&gt;/conf/report-generation- config.xml
8. …/APG/Tools/Administration-Tool/&lt;instance-name&gt;/conf/master-accessor-service-conf.xml
9. …/APG/Tools/WhatIf-Scenario-CLI/&lt;instance-name&gt;/conf/whatif-scenario-cli-conf.xml

<!-- image -->

## Configuring the SRM management functions

The Dell SRM management functions are always run from the Primary Frontend Server. When a user logs into an Additional Frontend Server and selects an Administration function, the user is redirected to the Primary Frontend Server and is forced to log in again.

This redirection is accomplished by editing the common.properties file in the following location:../APG/WebApplications/Admin-UI/admin/conf/common.properties

Following line should be changed in the file: apg.admin.url=https://&lt;FQDNPrimaryFrontendserver&gt;:58443/ admin/

## Topics:

- Adding MySQL grants to the databases
- Configuring compliance
- LDAP authentication
- Import-Properties task
- Activate the new configuration settings

## Adding MySQL grants to the databases

The new Additional Frontend Servers must be granted permission for access to all the databases on the Primary Backend and apg databases on the Additional Backend Servers.

Run this command to grant remote access to databases &lt;Database&gt; on the Primary Backend Server Primary Backend Server from the Additional Frontend Server &lt;Host FQDN&gt;.

```
./mysql-command-runner.sh -c /opt/APG/Tools/MySQL-Maintenance-Tool/Default/conf/mysqlroot-mysql.xml  -Q "CREATE USER 'apg'@'<Host FQDN>' IDENTIFIED WITH mysql_native_password AS '*FA71926E39A02D4DA4843003DF34BEADE3920AF3'"; ./mysql-command-runner.sh -c /opt/APG/Tools/MySQL-Maintenance-Tool/Default/conf/mysqlroot-mysql.xml  -Q "GRANT ALL PRIVILEGES ON apg.* to 'apg'@'<Host FQDN>';" ./mysql-command-runner.sh -c /opt/APG/Tools/MySQL-Maintenance-Tool/Default/conf/mysqlroot-mysql.xml  -Q "GRANT ALL PRIVILEGES ON compliance.* to 'apg'@'<Host FQDN>';" ./mysql-command-runner.sh -c /opt/APG/Tools/MySQL-Maintenance-Tool/Default/conf/mysqlroot-mysql.xml  -Q "GRANT ALL PRIVILEGES ON events.* to 'apg'@'<Host FQDN>';" ./mysql-command-runner.sh -c /opt/APG/Tools/MySQL-Maintenance-Tool/Default/conf/mysqlroot-mysql.xml  -Q "GRANT ALL PRIVILEGES ON master.* to 'apg'@'<Host FQDN>';" ./mysql-command-runner.sh -c /opt/APG/Tools/MySQL-Maintenance-Tool/Default/conf/mysqlroot-mysql.xml  -Q "GRANT ALL PRIVILEGES ON topology.* to 'apg'@'<Host FQDN>';"
```

Run these four commands to grant remote access to apg databases &lt;Database&gt; on the Additional Backend Servers from the Additional Frontend Server &lt;Host FQDN&gt;.

```
./mysql-command-runner-apg1.sh -c /opt/APG/Tools/MySQL-Maintenance-Tool/apg1/conf/mysqlroot-mysql.xml -Q "CREATE USER 'apg'@'<Host FQDN>' IDENTIFIED WITH mysql_native_password AS '*FA71926E39A02D4DA4843003DF34BEADE3920AF3'";
```

```
./mysql-command-runner-apg1.sh -c /opt/APG/Tools/MySQL-Maintenance-Tool/apg1/conf/mysqlroot-mysql.xml -Q "GRANT ALL PRIVILEGES ON apg1.* to 'apg'@'<Host FQDN>';" ./mysql-command-runner-apg2.sh -c /opt/APG/Tools/MySQL-Maintenance-Tool/apg2/conf/mysqlroot-mysql.xml -Q "GRANT ALL PRIVILEGES ON apg2.* to 'apg'@'<Host FQDN>';" ./mysql-command-runner-apg3.sh -c /opt/APG/Tools/MySQL-Maintenance-Tool/apg3/conf/mysqlroot-mysql.xml -Q "GRANT ALL PRIVILEGES ON apg3.* to 'apg'@'<Host FQDN>';" ./mysql-command-runner-apg4.sh -c /opt/APG/Tools/MySQL-Maintenance-Tool/apg4/conf/mysqlroot-mysql.xml -Q "GRANT ALL PRIVILEGES ON apg4.* to 'apg'@'<Host FQDN>';"
```

## Configuring compliance

If Compliance has been installed, run this command on the Additional Frontend Server:

```
…/APG/bin/administration-tool.sh updateModule -module [ -name 'storage_compliance' -url 'http://<FQDN-Primary-Frontend-server>:58080/compliance-frontend/' ]
```

## LDAP authentication

If LDAP authentication has been configured on the Primary Frontend Server, the Realms- configuration and certs files must be copied to the Additional Frontend Servers.

Copy the Realm-configuration File from the Primary Frontend Server to the Additional Frontend Servers:

…/APG/Web-Servers/Tomcat/Default/conf/realms-configuration.xml

Copy the certificate file from the Primary Frontend Server to the Additional Frontend Server:

…APG/Java/Sun-JRE/&lt;Java version&gt;/lib/security

## Import-Properties task

Each Frontend Server has to run the import-property task. If the import-properties task completes in under 30 minutes, then use the defaults. If the import-properties task takes 30 minutes or longer to complete, use a 1 hour start time difference for the import-properties task on the Additional Frontend Server task from the Primary Frontend Server task.

<!-- image -->

NOTE: If there are multiple Additional Frontend Servers, then adjustment of the import-properties Task start time must be staggered so as not to impact the database performance.

The import-properties task operation could cause a reduced performance of the database servers, especially if the databases are very large and multiple import-properties task instances are running simultaneously. As a consequence, you should edit the import property task and delay the execution of the scripts with respect to each other. The delay must be inserted only if the import tasks take longer than 30 minutes to complete.

Edit the import-properties.task file: …APG/Databases/APG-Property-Store/&lt;instance-name&gt;/conf/importproperties.tas

On the Primary Frontend Server , this is the default configuration for under 1 hour:

```
<!-If the average of the last 5 executions takes < 1 hour, schedule at 5:00AM and 12:00PM --> <conditional condition="slidingFinishedAverageDuration &lt; 3600000"> <schedule cron="0 5,12 * * *" xsi:type="schedule-repeated" disabled="false"></schedule> </conditional>
```

On the Additional Frontend Server , change the under 1 hour default setting to:

```
<!-If the average of the last 5 executions takes < 1 hour, schedule at 1:00AM, 6:00AM, 1:00PM, 6:00PM --> <conditional condition="slidingFinishedAverageDuration &lt; 3600000"> <schedule cron="1 6,13 * * *" xsi:type="schedule-repeated" disabled="false"></schedule> </conditional>
```

On the Additional Frontend Server , change the under 1 hour default setting to:

```
<!-If the average of the last 5 executions takes < 1 hour, schedule at 2:00AM, 7:00AM, 2:00PM, 7:00PM --> <conditional condition="slidingFinishedAverageDuration &lt; 3600000"> <schedule cron="2 7,14 * * *" xsi:type="schedule-repeated" disabled="false"></schedule> </conditional>
```

## Activate the new configuration settings

## About this task

After the configuration changes have been made, the Additional Frontend Server must be added to the Dell SRM Server Configuration and Tomcat Service on the Additional Frontend Server(s) must be restarted.

## Steps

1. From the Dell SRM Primary Frontend Server, select Administration .
2. To register a new Additional Frontend Server(s), go to CONFIG &gt; Settings &gt; Configure Servers &gt; Register a Server .
3. Install the System Health Data Collector on the Additional Frontend Server.
4. Restart the Tomcat Service on the Additional Frontend Server(s).
5. Log in on the Additional Frontend.

<!-- image -->

## Configuring the shared reports and tasks

The remainder of the Additional Frontend Server configuration is for sharing the User Reports and to establish an Additional Frontend Server as the Report Scheduler.

## Topics:

- Consolidate the scheduled reports
- Configuring an NFS share for the user reports
- Consolidate the scheduled reports
- Additional frontend server tasks

## Consolidate the scheduled reports

Dell Technologies recommends consolidating the scheduling of reports to an Additional Frontend Server. Follow the procedure in this section to consolidate the already scheduled reports to the Additional Frontend Server.

## About this task

If scheduling of reports will be distributed across all Frontend Servers (Primary and Additional) then skip this section.

## Steps

1. On the Primary Frontend Server, go to the scheduled reports directory: cd /opt/APG/Tools/Task-Scheduler/Default/data/task\_repository/scheduled-reports/
2. Copy the files from the scheduled-reports directory on the Primary Frontend Server to the same directory of the Additional Frontend Server.
3. scp -R * root@Additional FE:/opt/APG/Tools/Task-scheduler/Default/data/ NOTE: If the scheduled-reports folder is missing, then copy the folder from the Primary Frontend Server. The folder will
4. be missing if no reports have been scheduled from the new Additional Frontend Server.

<!-- image -->

Review the scheduled-reports directory to have all the files that are consolidated from the Primary Frontend Server to the Additional Frontend Server

3. Remove the scheduled-reports director from the Primary Frontend Server. cd …/APG/Custom/WebApps-Resources/Default/scheduling
4. Edit scheduling-servers.xml and change: url="https://localhost:48443/" --&gt; url=https://&lt;Additional FQDN&gt;:48443/
5. On the Additional Frontend Server, go to the scheduled reports directory: /opt/APG/Tools/Task-Scheduler/Default/data/task\_repository/
6. Change the files (and the scheduled-reports directory is it was copied to the Additional Frontend Server) to be owned by apg.

chown apg:apg -R *

## Configuring an NFS share for the user reports

## Prerequisites

The Dell SRM folder apg-reports must be shared across all Frontend Servers to provide the users access to their reports regardless of which Frontend Server they are connected to. To accomplish this, an NFS Share is required from a NAS Server, exported with Read/Write permissions for each Frontend Server.

- NOTE: The NFS Share should be a minimum of 1 GB and have the abilities to expand at the NAS server. For the average customer environment, 1 GB should be sufficient, but for a larger user environment, you may want to start with a 3 GB or 5 GB NFS file system.
- NOTE: Dell does not support installing an NFS Server on the Linux vApp VM.

Once the NFS File System has been established and exported, follow these steps to add the NFS share to Dell SRM.

- NOTE: For the example configuration below, the NFS Share is name SRM-FE-apg-reports-nfs.

## About this task

Preserve the data on the Primary Frontend Server if the SRM is not a new configuration. If this is a new environment, then skip step 1:

## Steps

1. On the Primary Frontend Server, rename the apg-report director to: apg-reports-old

…/APG/Web-Servers/Tomcat/Default/temp/apg-reports

2. On all the Frontend Servers, edit the /etc/fstab file.
3. Add this line to the bottom of the fstab file on all Frontend Servers and save:

&lt;nas Ip-Address&gt;:/SRM-FE-apg-reports-nfs /opt/APG/nfs-shared/apg-reports nfs defaults

```
Ippa028:/etc # more fstab Devpts   / dev/ pts          devpts  mode=0620, gid=5  0  0 proc     /proc               proc        defaults      0  0 Sysfs    / sys               sysfs       noauto        0  0 debugfs  /sys/kernel/debug   debugfs   noauto          0  0 Usbfs    /proc/bus/usb       usbfs  noauto             0  0 tmpfs    /run                tmpfs    noauto           0  0 /dev/systemVG/LVRoot / xfs defaults  1  1 /dev/sda1 /boot ext3 defaults  1  2 /dev/mapper/systemVG-Lvswap none swap defaults  0  0 10.247.25.121:/SRM-FE=apg-reports-nfs  /opt/APG/nfs-shared/apg-reports nfs defaults 1  1
```

4. Create a new directory on /opt/APG ➔ mkdir nfs-shared .
5. Go to /opt/APG/nfs-shared ➔ mkdir apg-reports.
6. Cd Change owner ➔ chown -R apg:apg *
7. Mount the NFS share ➔ mount /opt/APG/nfs-shared/apg-reports.
8. Go to ➔ /opt/APG/Web-Servers/Tomcat/Default/temp.
9. Delete apg-reports if the directory exists ➔ mkdir apg-reports .
10. To create a symbolic link ➔ ln -s /opt/APG/nfs-shared/apg-reports.
11. Verify the symbolic link with ➔ ls -l

```
Ippa028:/opt/APG/nfs-shared # mount /opt/APG/nfs-shared/apg-reports Ippa028:/opt/ APG/nfs-shared # df -h Filesystem                              Size   Used     Avail     Use%     Mounted on rootfs                                  120G   11G       110G       9%       / devtmpfs                                7.9G   100K      7.9G       1%       /dev tmpfs                                   7.9G     0       7.9G       0%       /dev/shm tmpfs                                   7.9G    64K      7.9G       1%       /run tmpfs                                   7.9G    64K      7.9G       1%       /var/run /dev/mapper/ systemVG-LVRoot            120G    11G      110G       9%       / 10.247.25.121:/SRM-FE-apg-reports=nfs  1009M   768K     1008M       1%       /opt/AGP/ nfs-shared/apg-reports Ippa028: /opt/APG/nfs-shared #
```

```
Ippa028 : / opt/ AEG/ Web-servers/ Tomcat/ Default/ temp # In -s /opt/AEG/nfs-shared/ apg-reports Ippa02E : / opt/ÄPG/Web-Servers/Tomcat/DefauIt/temp # Is -1 total 0
```

```
drwxr-xr-x  2  apg  apg   6 May    4   13:19 apg-mib-browser-1462382370077 Irwxrwxrwx  1  root root  31 May   4   15:50 apg-reports ->  /opt/APG/nfs-shared/apgreports drwxr-xr-x  2  apg  apg   6 May    4   13:18 jna-96792 -rw-r-----  1  apg  apg   0 May    4   09:45  safeToDelete.tmp
```

12. Go to the apg-report directory ➔ /opt/APG/Web-Servers/Tomcat/Default/temp/apg- reports.
13. Verify that the NFS share has R/W privileges by creating a file from each of the Frontend Servers. You should have a minimum of two test files in the apg-reports folder ➔ touch test-file# .
14. Verify that these files are seen from each of the Frontend Servers.
15. On the Primary Frontend Server, go to apg-reports-old.

Now copy the data from the apg-reports-old directory to the NFS Share apg-reports. cp -R * /opt/APG/WebServers/Tomcat/Default/temp/apg-reports

16. Ensure that the files are owned by apg user ➔ chown apg:apg -R *
17. Remove the test-files ➔ rm test*
18. After the reports have been copied to the NFS Share, the apg-reports-old directory can be removed with ➔ rm -r /opt/APG/Web-Servers/Tomcat/Default/temp/apg-reports-old

```
Ippa 028: /opt/APG/Web-Servers/ Tomcat/ Default/ temp/ apg-reports # Is -als total 24 8 drwxr-xr-x  6  apg   apg   1024 May    4  16:00  . 0 drwxr-xr-x  3  root  root    24 May    4  15:44  . . 8 drwxr-xr-x  2  apg   apg   1024 May    4  15:35 . etc 0 -rw-r--r--  1  apg   ap       0 May    4  15:57 test-file-1 0  -rw-r--r-- 1  apg   apg      0 May    4  15:56 test-file-2 8 drwxr-xr-x  2  apg   apg   1024 May    4  16:00 user-1 0 drwxr-xr-x  2  apg   apg     80 May    4  16:00 user-7
```

## Consolidate the scheduled reports

Dell Technologies recommends consolidating the scheduling of reports to an Additional Frontend Server. Follow the procedure in this section to consolidate the already scheduled reports to the Additional Frontend Server.

## About this task

If scheduling of reports will be distributed across all Frontend Servers (Primary and Additional) then skip this section.

## Steps

1. On the Primary Frontend Server, go to the scheduled reports directory:

cd /opt/APG/Tools/Task-Scheduler/Default/data/task\_repository/scheduled-reports/

2. Copy the files from the scheduled-reports directory on the Primary Frontend Server to the same directory of the Additional Frontend Server.

scp -R * root@Additional FE:/opt/APG/Tools/Task-scheduler/Default/data/

<!-- image -->

- NOTE: If the scheduled-reports folder is missing, then copy the folder from the Primary Frontend Server. The folder will be missing if no reports have been scheduled from the new Additional Frontend Server.

Review the scheduled-reports directory to have all the files that are consolidated from the Primary Frontend Server to the Additional Frontend Server

3. Remove the scheduled-reports director from the Primary Frontend Server.

cd …/APG/Custom/WebApps-Resources/Default/scheduling

4. Edit scheduling-servers.xml and change: url="https://localhost:48443/" --&gt; url=https://&lt;Additional FQDN&gt;:48443/
5. On the Additional Frontend Server, go to the scheduled reports directory:

/opt/APG/Tools/Task-Scheduler/Default/data/task\_repository/

6. Change the files (and the scheduled-reports directory is it was copied to the Additional Frontend Server) to be owned by apg.

chown apg:apg -R *

## Additional frontend server tasks

This section describes the additional frontend server tasks that must be disabled.

## About this task

On the additional frontend server, these tasks must be disabled:

- Dell SupportAssist
- Online Update
- Tools - usage-intelligence

## Steps

1. After all the changes are completed reboot the Primary Frontend Server and the Additional Frontend Server reboot
2. Verify that the NAS file system is established after a server start up df -h
3. Log in to the Primary and Additional Frontend Server with a user that has scheduled and stored reports.
4. Review the OTB reports. Review the user's reports.
5. Run the import properties task on the Primary Frontend Server and the Additional Frontend Servers.
6. Test the Scheduling of a report.
7. Log in with a user that has Global Admin privileges.
8. Select a UI administration function and ensure that the UI is redirected to the Primary Frontend Server.

<!-- image -->

## Documentation Feedback

Dell Technologies strives to provide accurate and comprehensive documentation and welcomes your suggestions and comments. You can provide feedback in the following ways:

- Online feedback form Rate this content feedback form is present in each topic of the product documentation web pages. Rate the documentation or provide your suggestions using this feedback form.
- Email-Send your feedback to SRM Doc Feedback. Include the document title, release number, chapter title, and section title of the text corresponding to the feedback.

To get answers to your queries related to Dell SRM through email, chat, or call, go to Dell Technologies Technical Support page.

<!-- image -->

A

## F5 load balancer configuration

Parameters that you need to tweak for an F5 Load balancer configuration are:

Table 1. F5 Load Balancer Configuration

| Configuration Name    | Value                                                           |
|-----------------------|-----------------------------------------------------------------|
| Server pool           | Hostname and IP-Address of each Dell SRM Frontend Server        |
| Persistence type      | Destination address affinity persistence (Sticky)               |
| Load balancing method | Least connections (member) and least connections (node)         |
| Action on shutdown    | Load balancing method                                           |
| Health monitors       | Associate with pool. If not possible associate with each member |

<!-- image -->

## HAProxy load balancer configuration

When using a Network Load Balancer (F5) or Appliance-based Web Proxy (HAProxy), the Dell SRM URL is redirected to any Frontend Server. For Administrators, these functions will redirect the user to the Primary Frontend Server.

HAProxy is open source software. The following code sample shows how to configure HAProxy to balance the load across all Frontend Servers.

```
global log /dev/log local0 info log /dev/log local0 notice chroot /var/lib/haproxy pidfile                /var/run/haproxy.pid maxconn 5000 user                   haproxy group                  haproxy daemon # turn on stats unix socket stats socket /etc/haproxy/haproxy.sock level admin defaults mode                   http log                    global option                 httplog option                 dontlognull option http-server-close option forwardfor      except 127.0 0.0/8 option                 redispatch retries                  3 timeout http-request    10s timeout queue            1m timeout connect         10s timeout client           1m timeout server           1m timeout http-keep-alive 10s timeout check           10s maxconn                 3000 frontend http-in bind *:80 acl url_static       path_beg -i       /administration acl url_static       path_beg          -i /alerting-frontend acl url_static       path_beg          -i /compliance-frontend acl url_static       path_beg          -i /device-discovery acl url_static       path_beg          -i /snmpconfig use_backend static   if url_static default_backend      app backend static balance     roundrobin option      forwardfor option http-server-close appsession JSESSIONID len 52 timeout 14400000 # Main admin server server    m_frontend    backend:58080    weight   256   check # HA admin server server    s_frontend    frontend:58080   weight    2    check backend     app balance     roundrobin option      forwardfor option http-server-close appsession JSESSIONID len 52 timeout 14400000 # No.1 APG server server    frontend      backend:58080    check inter 5000 # No.2 APG server server    frontend2     frontend:58080   check inter 5000 # No.3 APG server server    frontend3     frontend2:58080 check inter 5000
```

listen stats bind *:88 stats enable stats uri /

Frequently asked questions.

## Topics:

- SolutionPacks report installation
- SolutionPacks upload
- SolutionPacks formula
- SolutionPacks property-mapping

## SolutionPacks report installation

The SolutionPack Reports are installed on the Frontend Server. The Primary Frontend Server should be selected in the interactive installation window for SolutionPacks. The report is transferred from the Frontend Server to the MySQL database and will be visible on all Frontend Servers.

## SolutionPacks upload

Since administration performs the upload, the operation takes place on the Primary Frontend Server. The package file is saved locally and can only be installed from this Primary Frontend Server. If the Primary Frontend Server is in a high availability solution, the folder must be updated as well.

## SolutionPacks formula

A SolutionPack can have a local formula that is built in a java file used in the reports. The formula is installed on the Frontend Server pointed to during installation. The SolutionPack that has a custom formula contains a java file in the blocks\reports\templates\arp\_formulas folder. Currently, the only SolutionPack affected is the Dell SolutionPack which uses the formula.

## SolutionPacks property-mapping

If the SolutionPack uses events, then the report has an XML file for property mapping that is saved on the pointed to Frontend Server only.

<!-- image -->

C

<!-- image -->

## FAQ