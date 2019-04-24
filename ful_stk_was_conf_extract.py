####################################
# WebSphere Configurations Extract #
####################################

# /was7/WebSphere/AppServer/bin/wsadmin.sh -lang jython -conntype SOAP -host 10.17.249.115 -port 8879 -user wasadmin -password WebJ2ee

import java.lang.System as sys
sep = sys.getProperty('line.separator')
def prtDataSources():
	for dataSourceId in AdminConfig.list('DataSource', AdminConfig.getid( '/Cell:c4w01Cell01/')).split(sep):
		if AdminConfig.showAttribute(dataSourceId, 'provider').find('builtin_') == -1:
			name = AdminConfig.showAttribute(dataSourceId, 'name')
			driverId = AdminConfig.showAttribute(dataSourceId, 'provider')
			providerType = AdminConfig.showAttribute(driverId, 'providerType')
			jndiName = AdminConfig.showAttribute(dataSourceId, 'jndiName')
			authAlias = AdminConfig.showAttribute(dataSourceId, 'authDataAlias')
			propSet = AdminConfig.showAttribute(dataSourceId, 'propertySet')
			resProp = AdminConfig.showAttribute(propSet, 'resourceProperties')
			iStart = resProp.find('URL(') + 3
			iEnd = resProp.find(')', iStart) + 1
			url = AdminConfig.showAttribute(resProp[iStart:iEnd], 'value')
			print name + ',' + driverId + ',' + providerType + ',' + jndiName + ',' + authAlias + ',' + url
	return

# 获取默认的单元ID
def getDefaultCellId():
	global cellId
	global cellName
	cellIdArr = AdminConfig.list('Cell').split(sep)
	assert len(cellIdArr) >= 1
	cellId = cellIdArr[0]
	cellName = AdminConfig.showAttribute(cellId, 'name')
	return

# 获取所有集群ID
def getClusterIds():
	if not 'cellId' in globals().keys():
		getDefaultCellId()
	global clusterIds
	clusterIds = []
	clusterStr = AdminConfig.list('ServerCluster', cellId)
	if clusterStr == '':
		print 'No clusters found.'
	else:
		clusterIds = clusterStr.split(sep)
	return

# 打印共享库初始化脚本，可在目标端执行此输出脚本
def prtSharedLibScripts():
	if not 'clusterIds' in globals().keys():
		getClusterIds()
	dstCellName = 'sles11Cell01' # 此处请根据目标端情况进行修改
	for clusterId in clusterIds: # 对于源端所有集群
		clusterName = AdminConfig.showAttribute(clusterId, 'name') # 获取集群ID
		if clusterName == 'cluster1': # 映射处理
			clusterName = 'cluster_icrm'
		if clusterName == 'cluster2': # 映射处理
			clusterName = 'cluster_res'
		libIds = AdminConfig.list('Library', clusterId).split(sep)
		for libId in libIds:
			classPath = AdminConfig.showAttribute(libId, 'classPath')
			description = AdminConfig.showAttribute(libId, 'description')
			if not description:
				description = ''
			isolatedClassLoader = AdminConfig.showAttribute(libId, 'isolatedClassLoader')
			name = AdminConfig.showAttribute(libId, 'name')
			nativePath = AdminConfig.showAttribute(libId, 'nativePath')
			if nativePath == '[]':
				nativePath = ''
			print 'AdminConfig.create(\'Library\', AdminConfig.getid(\'/Cell:' + dstCellName + '/ServerCluster:' + clusterName + '/\'), \'[[nativePath "' + nativePath + '"] [name "' + name + '"] [isolatedClassLoader ' + isolatedClassLoader + '] [description "' + description + '"] [classPath "' + classPath + '"]]\')'
	return
	# AdminConfig.create('Library', AdminConfig.getid('/Cell:sles11Cell01/ServerCluster:cluster_cmop/'), '[[nativePath ""] [name "sss"] [isolatedClassLoader false] [description ""] [classPath "/was7"]]')