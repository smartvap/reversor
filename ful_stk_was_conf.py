############################
# WebSphere Configurations #
############################
# /was7/WebSphere/AppServer/bin/wsadmin.sh -lang jacl -conntype SOAP -host 10.19.244.185 -port 8879 -user wasadmin -password WebJ2ee
# /was7/WebSphere/AppServer/bin/wsadmin.sh -lang jython -conntype SOAP -host 10.19.244.185 -port 8879 -user wasadmin -password WebJ2ee
# /was7/WebSphere/AppServer/bin/wsadmin.sh -lang jython -conntype SOAP -host 10.17.249.115 -port 8879 -user wasadmin -password WebJ2ee

# Global Variables
import java.lang.System as sys
sep = sys.getProperty('line.separator')

def giveupAllChanges():
	AdminConfig.reset()

def getDefaultCellId():
	global cellId
	global cellName
	cellIdArr = AdminConfig.list('Cell').split(sep)
	assert len(cellIdArr) >= 1
	cellId = cellIdArr[0]
	cellName = AdminConfig.showAttribute(cellId, 'name')
	return

def getDmgrNodeName():
	global dmgrNodeName
	nodeNameArr = AdminTask.listNodes().split(sep)
	assert len(nodeNameArr) >= 1
	dmgrNodeName = nodeNameArr[0]
	return

def getDefaultManagedNodeName():
	global managedNodeName
	nodeNameArr = AdminTask.listNodes().split(sep)
	assert len(nodeNameArr) >= 2
	managedNodeName = nodeNameArr[1]
	return

def prerequisite():
	if not 'cellId' in globals().keys():
		getDefaultCellId()
	if not 'dmgrNodeName' in globals().keys():
		getDmgrNodeName()
	if not 'managedNodeName' in globals().keys():
		getDefaultManagedNodeName()
	return

def getClusterIds():
	global clusterIds
	clusterIds = []
	prerequisite()
	clusterStr = AdminConfig.list('ServerCluster', cellId)
	if clusterStr == '':
		print 'No clusters found.'
	else:
		clusterIds = clusterStr.split(sep)
	return

def initClusters():
	global arrClusterName
	arrClusterName = []
	getClusterIds()
	for clusterId in clusterIds:
		arrClusterName.append(AdminConfig.showAttribute(clusterId, 'name'))
	for clusterName in [ 'cluster_icrm', 'cluster_crm3', 'cluster_res', 'cluster_cmop' ]:
		if not clusterName in arrClusterName:
			AdminTask.createCluster('[-clusterConfig [-clusterName ' + clusterName + ' -preferLocal true]]')
			print clusterName + ' created successfully.'
	AdminConfig.save()
	AdminControl.invoke('WebSphere:name=DeploymentManager,process=dmgr,platform=common,node=' + dmgrNodeName +',diagnosticProvider=true,version=7.0.0.45,type=DeploymentManager,mbeanIdentifier=DeploymentManager,cell='+ cellName + ',spec=1.0', 'multiSync', '[false]', '[java.lang.Boolean]')
	return

def initServers():
	initClusters()
	getClusterIds()
	for clusterId in clusterIds:
		clusterName = AdminConfig.showAttribute(clusterId, 'name')
		serverName = clusterName.replace('cluster', 'server')
		serverIdArr = AdminConfig.list('ClusterMember', clusterId).split(sep)
		serverNameArr = []
		for serverId in serverIdArr:
			if serverId != '':
				serverNameArr.append(AdminConfig.showAttribute(serverId, 'memberName'))
		if not serverName in serverNameArr:
			AdminTask.createClusterMember('[-clusterName ' + clusterName + ' -memberConfig [-memberNode ' + managedNodeName + ' -memberName ' + serverName + ' -memberWeight 2 -genUniquePorts true -replicatorEntry false] -firstMember [-templateName default -nodeGroup DefaultNodeGroup -coreGroup DefaultCoreGroup]]')
	AdminConfig.save()
	AdminControl.invoke('WebSphere:name=DeploymentManager,process=dmgr,platform=common,node=' + dmgrNodeName +',diagnosticProvider=true,version=7.0.0.45,type=DeploymentManager,mbeanIdentifier=DeploymentManager,cell=' + cellName + ',spec=1.0', 'multiSync', '[false]', '[java.lang.Boolean]')
	return

def configServers():
	initServers()
	jmxPort = 10990
	for clusterId in clusterIds:
		serverIdArr = AdminConfig.list('ClusterMember', clusterId).split(sep)
		for serverId in serverIdArr:
			serverName = AdminConfig.showAttribute(serverId, 'memberName')
			jmxPort = jmxPort + 1
			AdminTask.setJVMProperties('[-serverName ' + serverName + ' -nodeName ' + managedNodeName + ' -verboseModeClass false -verboseModeGarbageCollection true -verboseModeJNI false -initialHeapSize 4096 -maximumHeapSize 4096 -runHProf false -hprofArguments -debugMode false -debugArgs "-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=7777" -genericJvmArguments "-Xgcpolicy:gencon -Xmn1024m -Xgc:preferredHeapBase=0x100000000 -Xdisableexplicitgc -Djava.awt.headless=true -Ddefault.client.encoding=GBK -Dfile.encoding=GBK -Duser.region=CN -Duser.language=zh -DLANG=zh_CN -agentpath:/home/dynatrace-6.5/agent/lib64/libdtagent.so=name=was,server=127.0.0.1:9998 -Djavax.management.builder.initial= -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=' + '%d' %jmxPort + '" -executableJarFileName -disableJIT false]')
	AdminConfig.save()
	AdminControl.invoke('WebSphere:name=DeploymentManager,process=dmgr,platform=common,node=' + dmgrNodeName +',diagnosticProvider=true,version=7.0.0.45,type=DeploymentManager,mbeanIdentifier=DeploymentManager,cell=' + cellName + ',spec=1.0', 'multiSync', '[false]', '[java.lang.Boolean]')
	return

def removeAllClusters():
	getClusterIds()
	for clusterId in clusterIds:
		AdminTask.deleteCluster('[-clusterName ' + AdminConfig.showAttribute(clusterId, 'name') + ' ]')
	AdminConfig.save()
	AdminControl.invoke('WebSphere:name=DeploymentManager,process=dmgr,platform=common,node=' + dmgrNodeName +',diagnosticProvider=true,version=7.0.0.45,type=DeploymentManager,mbeanIdentifier=DeploymentManager,cell=' + cellName + ',spec=1.0', 'multiSync', '[false]', '[java.lang.Boolean]')
	return

def globalSecurity():
	try:
		AdminTask.applyWizardSettings('[-secureApps false -secureLocalResources false -adminPassword WebJ2ee -userRegistryType WIMUserRegistry -adminName wasadmin ]')
		AdminConfig.save()
	except:
		print '未知异常'
	return

def initJ2CAccts():
	if not 'mapJ2C' in globals().keys():
		global mapJ2C
		mapJ2C = {}
		mapJ2C['SMSHALL'] = { 'user' : 'SMSHALL', 'password' : 'ABC_abc1', 'description' : '营销' }
		mapJ2C['arrear'] = { 'user' : 'arrear', 'password' : 'xBc20kM60', 'description' : '清欠' }
		mapJ2C['basqry'] = { 'user' : 'basqry', 'password' : 'n#1wQT4', 'description' : '数据共享中心' }
		mapJ2C['gm'] = { 'user' : 'tbcs', 'password' : 'rp6lv9vm', 'description' : '短厅' }
		mapJ2C['icdpub'] = { 'user' : 'icdpub', 'password' : 'xrfwl6o8', 'description' : '基础公共' }
		mapJ2C['im'] = { 'user' : 'im', 'password' : 'ac0d4f9_8', 'description' : '资源库存' }
		mapJ2C['newrpt'] = { 'user' : 'newrpt', 'password' : 'h895fdq6', 'description' : '报表' }
		mapJ2C['ngsettle'] = { 'user' : 'ngsettle', 'password' : 'z4e_4rtx', 'description' : '酬金' }
		mapJ2C['reward_coms'] = { 'user' : 'settle', 'password' : 'vg7b_4rj', 'description' : 'openchannel' }
		mapJ2C['sdsettle'] = { 'user' : 'sdsettle', 'password' : 'txsw866r', 'description' : '结算' }
		mapJ2C['sms'] = { 'user' : 'tbcs', 'password' : 'xBc26kM96', 'description' : '客服短信' }
		mapJ2C['srp'] = { 'user' : 'srp', 'password' : 'vs8BY426', 'description' : '开通' }
		mapJ2C['tbcs'] = { 'user' : 'tbcs', 'password' : 'cg6n5e3r', 'description' : '营业' }
		mapJ2C['tbcs_emg'] = { 'user' : 'tbcs', 'password' : 'cg6n5e3r', 'description' : '营业应急' }
		mapJ2C['unisettle'] = { 'user' : 'unisettle', 'password' : 'wr4t_3vkx@', 'description' : '量化薪酬' }
	return

def removeJ2C():
	initJ2CAccts()
	prerequisite()
	for key, value in mapJ2C.items():
		try:
			AdminTask.deleteAuthDataEntry('[-alias ' + dmgrNodeName + '/' + key + ' ]')
		except:
			print 'J2C认证数据 ' + dmgrNodeName + '/' + key + ' 不存在或无法移除.'
	AdminConfig.save()
	AdminControl.invoke('WebSphere:name=DeploymentManager,process=dmgr,platform=common,node=' + dmgrNodeName +',diagnosticProvider=true,version=7.0.0.45,type=DeploymentManager,mbeanIdentifier=DeploymentManager,cell=' + cellName + ',spec=1.0', 'multiSync', '[false]', '[java.lang.Boolean]')
	return

def initJ2C():
	initJ2CAccts()
	prerequisite()
	for key, value in mapJ2C.items():
		try:
			AdminTask.createAuthDataEntry('[-alias ' + key + ' -user ' + value['user'] + ' -password ' + value['password'] + ' -description ' + value['description'] + ' ]')
		except:
			print 'J2C认证数据 ' + dmgrNodeName + '/' + key + ' 已存在或无法创建.'
	AdminConfig.save()
	AdminControl.invoke('WebSphere:name=DeploymentManager,process=dmgr,platform=common,node=' + dmgrNodeName +',diagnosticProvider=true,version=7.0.0.45,type=DeploymentManager,mbeanIdentifier=DeploymentManager,cell=' + cellName + ',spec=1.0', 'multiSync', '[false]', '[java.lang.Boolean]')
	return

# 删除所有非内置JDBC Provider
def removeNonBuiltInJDBCProvider():
	getClusterIds()
	providerIdArr = AdminConfig.list('JDBCProvider', cellId).split(sep)
	# 删除所有Providers
	for providerId in providerIdArr:
		if providerId.find('builtin_') == -1:
			AdminConfig.remove(providerId)
	# 删除Providers相关变量
	for clusterId in clusterIds:
		varIds = AdminConfig.list('VariableSubstitutionEntry', clusterId).split(sep)
		for varId in varIds:
			if varId != '' and AdminConfig.showAttribute(varId, 'symbolicName') == 'ORACLE_JDBC_DRIVER_PATH':
				AdminConfig.remove(varId)
	AdminConfig.save()
	AdminControl.invoke('WebSphere:name=DeploymentManager,process=dmgr,platform=common,node=' + dmgrNodeName +',diagnosticProvider=true,version=7.0.0.45,type=DeploymentManager,mbeanIdentifier=DeploymentManager,cell=' + cellName + ',spec=1.0', 'multiSync', '[false]', '[java.lang.Boolean]')
	return

# JDBC Provider
def initJdbcProvider():
	getClusterIds()
	mapCluster = {}
	for clusterId in clusterIds:
		clusterName = AdminConfig.showAttribute(clusterId, 'name')
		# 1. 获取当前集群的变量映射表
		varMapIds = AdminConfig.list('VariableMap', clusterId)
		if varMapIds == '':
			continue
		varMapId = varMapIds.split(sep)[0]
		try:
			# 2. 创建变量
			AdminConfig.create('VariableSubstitutionEntry', varMapId, '[[symbolicName "ORACLE_JDBC_DRIVER_PATH"] [description ""] [value "/was7/WebSphere/AppServer/lib"]]')
			AdminConfig.save()
		except:
			print '变量' + clusterName + '.ORACLE_JDBC_DRIVER_PATH 已存在或无法创建.'
		try:
			# 3. 创建non-XA JDBC Provider
			AdminTask.createJDBCProvider('[-scope Cluster=' + clusterName + ' -databaseType Oracle -providerType "Oracle JDBC Driver" -implementationType 连接池数据源 -name "Oracle JDBC Driver" -description "Oracle JDBC Driver" -classpath [${ORACLE_JDBC_DRIVER_PATH}/ojdbc6.jar ] -nativePath "" ]')
		except:
			print 'Oracle JDBC Driver 已存在或无法创建.'
		try:
			# 4. 创建XA JDBC Provider
			AdminTask.createJDBCProvider('[-scope Cluster=' + clusterName + ' -databaseType Oracle -providerType "Oracle JDBC Driver" -implementationType "XA 数据源" -name "Oracle JDBC Driver (XA)" -description "Oracle JDBC Driver (XA)" -classpath [${ORACLE_JDBC_DRIVER_PATH}/ojdbc6.jar ] -nativePath "" ]')
		except:
			print 'Oracle JDBC Driver (XA) 已存在或无法创建.'
	AdminConfig.save()
	AdminControl.invoke('WebSphere:name=DeploymentManager,process=dmgr,platform=common,node=' + dmgrNodeName +',diagnosticProvider=true,version=7.0.0.45,type=DeploymentManager,mbeanIdentifier=DeploymentManager,cell=' + cellName + ',spec=1.0', 'multiSync', '[false]', '[java.lang.Boolean]')
	return
	
#	AdminConfig.remove('(cells/sles11Cell01/clusters/cluster1|resources.xml#CMPConnectorFactory_1546828590723)')  
#	AdminConfig.remove('(cells/sles11Cell01/clusters/cluster1|resources.xml#JDBCProvider_1546484386143)')
#	AdminConfig.save()

def initJDBCDataSource():
	getClusterIds()
	providerDict = {}
	dataSourceDict = {}
	for clusterId in clusterIds:
		providerIdArr = AdminConfig.list('JDBCProvider', clusterId).split(sep)
		for providerId in providerIdArr:
			if providerId.find('builtin_') == -1:
				clusterName = AdminConfig.showAttribute(clusterId, 'name')
				providerDict[clusterName + '_' + AdminConfig.showAttribute(providerId, 'name')] = providerId
	dataSourceDict['arrearPool1|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/arrearPool1', 'authAlias' : dmgrNodeName + '/arrear', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.245.10)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.245.12)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=oraqq1)))' }
	dataSourceDict['arrearPool2|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/arrearPool2', 'authAlias' : dmgrNodeName + '/arrear', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.245.12)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.245.10)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=oraqq1)))' }
	dataSourceDict['cspparam|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'cspparam', 'authAlias' : dmgrNodeName + '/icdpub', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['csppub|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'csppub', 'authAlias' : dmgrNodeName + '/icdpub', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['emgPool1|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/emgPool1', 'authAlias' : dmgrNodeName + '/tbcs_emg', 'url' : 'jdbc:oracle:thin:@10.19.242.18:1521:oyj1' }
	dataSourceDict['emgPool2|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/emgPool2', 'authAlias' : dmgrNodeName + '/tbcs_emg', 'url' : 'jdbc:oracle:thin:@10.19.242.19:1521:oyj2' }
	dataSourceDict['emgPool3|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/emgPool3', 'authAlias' : dmgrNodeName + '/tbcs_emg', 'url' : 'jdbc:oracle:thin:@10.19.242.28:1521:oyj3' }
	dataSourceDict['emgPool4|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/emgPool4', 'authAlias' : dmgrNodeName + '/tbcs_emg', 'url' : 'jdbc:oracle:thin:@10.19.242.29:1521:oyj4' }
	dataSourceDict['gmPool1|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/gmPool1', 'authAlias' : dmgrNodeName + '/gm', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.253.13)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.253.15)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=pdb_duanting)))' }
	dataSourceDict['gmPool2|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/gmPool2', 'authAlias' : dmgrNodeName + '/gm', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.253.15)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.253.13)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=pdb_duanting)))' }
	dataSourceDict['invPool1|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/invPool1', 'authAlias' : dmgrNodeName + '/im', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=ozy1a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=ozy1b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orazy1)))' }
	dataSourceDict['invPool1|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/invPool1', 'authAlias' : dmgrNodeName + '/im', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=ozy1a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=ozy1b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orazy1)))' }
	dataSourceDict['invPool2|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/invPool2', 'authAlias' : dmgrNodeName + '/im', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=ozy1b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=ozy1a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orazy1)))' }
	dataSourceDict['invPool2|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/invPool2', 'authAlias' : dmgrNodeName + '/im', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=ozy1b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=ozy1a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orazy1)))' }
	dataSourceDict['ngsettle|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'ngsettle', 'authAlias' : dmgrNodeName + '/unisettle', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=10.17.248.131)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=10.17.248.132)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=oraqd1)))' }
	dataSourceDict['openServerPool1|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/openServerPool1', 'authAlias' : dmgrNodeName + '/srp', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=okt1a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=okt1b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orakt1)))' }
	dataSourceDict['openServerPool2|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/openServerPool2', 'authAlias' : dmgrNodeName + '/srp', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=okt2a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=okt2b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orakt2)))' }
	dataSourceDict['pangu1|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/pangu1', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['pangu2|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/pangu2', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['pangu3|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/pangu3', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy2)))' }
	dataSourceDict['pangu4|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/pangu4', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy2)))' }
	dataSourceDict['pangu5|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/pangu5', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['pangu6|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/pangu6', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['pangu7|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/pangu7', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy4)))' }
	dataSourceDict['pangu8|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/pangu8', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy4)))' }
	dataSourceDict['reportPool1|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/reportPool1', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['reportPool1|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/reportPool1', 'authAlias' : dmgrNodeName + '/newrpt', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.242.124)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.242.126)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=oracz1)))' }
	dataSourceDict['reportPool2|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/reportPool2', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy2)))' }
	dataSourceDict['reportPool2|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/reportPool2', 'authAlias' : dmgrNodeName + '/newrpt', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.242.126)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.242.124)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=oracz1)))' }
	dataSourceDict['reportPool3|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/reportPool3', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['reportPool4|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/reportPool4', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy4)))' }
	dataSourceDict['sd_dsc|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'sd_dsc', 'authAlias' : dmgrNodeName + '/basqry', 'url' : 'jdbc:oracle:thin:@10.19.253.6:1521:jfsvc' }
	dataSourceDict['settlePool2|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/settlePool2', 'authAlias' : dmgrNodeName + '/sdsettle', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.242.42)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.242.40)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orajs1)))' }
	dataSourceDict['share|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'share', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['share|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'share', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['smsPool1|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/smsPool1', 'authAlias' : dmgrNodeName + '/sms', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.242.110)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.242.112)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=oradx1)))' }
	dataSourceDict['smsPool2|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/smsPool2', 'authAlias' : dmgrNodeName + '/sms', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.242.112)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=10.19.242.110)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=oradx1)))' }
	dataSourceDict['smshallPool|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/smshallPool', 'authAlias' : dmgrNodeName + '/SMSHALL', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION =(LOAD_BALANCE=off)(FAILOVER=on)(ADDRESS = (PROTOCOL = TCP)(HOST = 134.80.172.129)(PORT = 1521)) (ADDRESS = (PROTOCOL = TCP)(HOST = 134.80.172.130)(PORT = 1521))(CONNECT_DATA =(service_name = svcznyx)))' }
	dataSourceDict['tbcsPool1|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool1', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['tbcsPool1|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool1', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['tbcsPool1|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool1', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['tbcsPool2|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool2', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['tbcsPool2|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool2', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['tbcsPool2|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool2', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['tbcsPool3|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool3', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy2)))' }
	dataSourceDict['tbcsPool3|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool3', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy2)))' }
	dataSourceDict['tbcsPool3|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool3', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy2)))' }
	dataSourceDict['tbcsPool4|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool4', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy2)))' }
	dataSourceDict['tbcsPool4|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool4', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy2)))' }
	dataSourceDict['tbcsPool4|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool4', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy2)))' }
	dataSourceDict['tbcsPool5|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool5', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['tbcsPool5|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool5', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['tbcsPool5|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool5', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['tbcsPool6|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool6', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['tbcsPool6|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool6', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['tbcsPool6|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool6', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['tbcsPool7|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool7', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy4)))' }
	dataSourceDict['tbcsPool7|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool7', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy4)))' }
	dataSourceDict['tbcsPool7|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool7', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy4)))' }
	dataSourceDict['tbcsPool8|cluster_icrm'] = { 'driverId' : providerDict['cluster_icrm_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool8', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy4)))' }
	dataSourceDict['tbcsPool8|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool8', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy4)))' }
	dataSourceDict['tbcsPool8|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver'], 'providerType' : 'Oracle JDBC Driver', 'jndiName' : 'jdbc/tbcsPool8', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy4)))' }
	dataSourceDict['tbcsXaPool1|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool1', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['tbcsXaPool1|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool1', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['tbcsXaPool2|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool2', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['tbcsXaPool2|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool2', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy1a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy1)))' }
	dataSourceDict['tbcsXaPool3|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool3', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy2)))' }
	dataSourceDict['tbcsXaPool3|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool3', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy2)))' }
	dataSourceDict['tbcsXaPool4|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool4', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy2)))' }
	dataSourceDict['tbcsXaPool4|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool4', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy2a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy2)))' }
	dataSourceDict['tbcsXaPool5|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool5', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['tbcsXaPool5|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool5', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['tbcsXaPool6|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool6', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['tbcsXaPool6|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool6', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy3a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy3)))' }
	dataSourceDict['tbcsXaPool7|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool7', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy4)))' }
	dataSourceDict['tbcsXaPool7|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool7', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4a.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4b.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy4)))' }
	dataSourceDict['tbcsXaPool8|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool8', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy4)))' }
	dataSourceDict['tbcsXaPool8|cluster_cmop'] = { 'driverId' : providerDict['cluster_cmop_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool8', 'authAlias' : dmgrNodeName + '/tbcs', 'url' : 'jdbc:oracle:thin:@(DESCRIPTION= (LOAD_BALANCE=off)(FAILOVER=on) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4b.ora.boss)(PORT=1521)) (ADDRESS=(PROTOCOL=TCP)(HOST=oyy4a.ora.boss)(PORT=1521)) (CONNECT_DATA=(SERVICE_NAME=orayy4)))' }
	dataSourceDict['tbcsXaPool9|cluster_res'] = { 'driverId' : providerDict['cluster_res_Oracle JDBC Driver (XA)'], 'providerType' : 'Oracle JDBC Driver (XA)', 'jndiName' : 'cmop/tbcsXaPool9', 'authAlias' : dmgrNodeName + '/reward_coms', 'url' : 'jdbc:oracle:thin:@(description =(load_balance=off)(failover=on)(connect_timeout=1)(retry_count=3)(address_list =(address = (protocol = tcp)(host = 134.80.172.129)(port = 1521))(address = (protocol = tcp)(host = 134.80.172.130)(port = 1521))(address = (protocol = tcp)(host = 134.80.172.131)(port = 1521)))(connect_data =(service_name = oraqd)))' }
	
	for key, value in dataSourceDict.items():
		if value['providerType'] == 'Oracle JDBC Driver':
			retVal = AdminTask.createDatasource('"' + value['driverId'] + '"', '[-name ' + key.split('|')[0] + ' -jndiName ' + value['jndiName'] + ' -dataStoreHelperClassName com.ibm.websphere.rsadapter.Oracle11gDataStoreHelper -containerManagedPersistence true -componentManagedAuthenticationAlias ' + value['authAlias'] + ' -configureResourceProperties [[URL java.lang.String "' + value['url'] + '"]]]')
		else:
			dataSourceId = AdminTask.createDatasource('"' + value['driverId'] + '"', '[-name ' + key.split('|')[0] + ' -jndiName ' + value['jndiName'] + ' -dataStoreHelperClassName com.ibm.websphere.rsadapter.Oracle11gDataStoreHelper -containerManagedPersistence true -componentManagedAuthenticationAlias ' + value['authAlias'] + ' -xaRecoveryAuthAlias ' + value['authAlias'] + ' -configureResourceProperties [[URL java.lang.String "' + value['url'] + '"]]]')
			AdminConfig.create('MappingModule', dataSourceId, '[[authDataAlias ' + value['authAlias'] + '] [mappingConfigAlias ""]]')
			cmpConnFactArr = AdminConfig.list('CMPConnectorFactory').split(sep)
			for cmpConnFact in cmpConnFactArr:
				if AdminConfig.showAttribute(cmpConnFact, 'name') == key + '_CF':
					AdminConfig.modify(cmpConnFact, '[[name "' + key + '_CF"] [authDataAlias "' + value['authAlias'] + '"] [xaRecoveryAuthAlias "' + value['authAlias'] + '"]]')
			AdminConfig.create('MappingModule', cmpConnFact, '[[authDataAlias ' + value['authAlias'] + '] [mappingConfigAlias ""]]')
	AdminConfig.save()
	AdminControl.invoke('WebSphere:name=DeploymentManager,process=dmgr,platform=common,node=' + dmgrNodeName +',diagnosticProvider=true,version=7.0.0.45,type=DeploymentManager,mbeanIdentifier=DeploymentManager,cell=' + cellName + ',spec=1.0', 'multiSync', '[false]', '[java.lang.Boolean]')
	return

# 移除所有共享库
def removeSharedLibs():
	prerequisite()
	libIds = AdminConfig.list('Library', cellId)
	if libIds == '':
		return
	libIdArr = libIds.split(sep)
	for libId in libIdArr:
		AdminConfig.remove(libId)
	AdminConfig.save()
	AdminControl.invoke('WebSphere:name=DeploymentManager,process=dmgr,platform=common,node=' + dmgrNodeName +',diagnosticProvider=true,version=7.0.0.45,type=DeploymentManager,mbeanIdentifier=DeploymentManager,cell=' + cellName + ',spec=1.0', 'multiSync', '[false]', '[java.lang.Boolean]')
	return

# 初始化共享库
def initSharedLibs():
	# 请拷贝源端生成的脚本到此处
	AdminConfig.create('Library', AdminConfig.getid('/Cell:sles11Cell01/ServerCluster:cluster_icrm/'), '[[nativePath ""] [name "BOSSCACHE"] [isolatedClassLoader true] [description "for C12L05"] [classPath "/was7/nglib/WEB-INF/lib/boss-cache.jar"]]')
	AdminConfig.create('Library', AdminConfig.getid('/Cell:sles11Cell01/ServerCluster:cluster_icrm/'), '[[nativePath ""] [name "iCrmLib"] [isolatedClassLoader false] [description ""] [classPath "/was7/iCrmLib/WEB-INF/lib"]]')
	AdminConfig.create('Library', AdminConfig.getid('/Cell:sles11Cell01/ServerCluster:cluster_icrm/'), '[[nativePath ""] [name "nglib"] [isolatedClassLoader false] [description "2012.07.13"] [classPath "/was7/nglib/WEB-INF/lib/"]]')
	AdminConfig.create('Library', AdminConfig.getid('/Cell:sles11Cell01/ServerCluster:cluster_res/'), '[[nativePath ""] [name "iCrmLib"] [isolatedClassLoader false] [description ""] [classPath "/was7/iCrmLib/WEB-INF/lib"]]')
	AdminConfig.create('Library', AdminConfig.getid('/Cell:sles11Cell01/ServerCluster:cluster_res/'), '[[nativePath ""] [name "nglib"] [isolatedClassLoader false] [description ""] [classPath "/was7/nglib/WEB-INF/lib/"]]')
	AdminConfig.create('Library', AdminConfig.getid('/Cell:sles11Cell01/ServerCluster:cluster_res/'), '[[nativePath ""] [name "openchannelLib"] [isolatedClassLoader false] [description ""] [classPath "/was7/openchannelLib/WEB-INF/lib"]]')
	AdminConfig.create('Library', AdminConfig.getid('/Cell:sles11Cell01/ServerCluster:cluster_cmop/'), '[[nativePath ""] [name "nglib"] [isolatedClassLoader false] [description ""] [classPath "/was7/nglib/WEB-INF/lib/"]]')
	AdminConfig.create('Library', AdminConfig.getid('/Cell:sles11Cell01/ServerCluster:cluster_cmop/'), '[[nativePath ""] [name "openchannelLib"] [isolatedClassLoader false] [description "20161228"] [classPath "/was7/openchannelLib/WEB-INF/lib"]]')
	AdminConfig.save()
	AdminControl.invoke('WebSphere:name=DeploymentManager,process=dmgr,platform=common,node=' + dmgrNodeName +',diagnosticProvider=true,version=7.0.0.45,type=DeploymentManager,mbeanIdentifier=DeploymentManager,cell=' + cellName + ',spec=1.0', 'multiSync', '[false]', '[java.lang.Boolean]')
	return