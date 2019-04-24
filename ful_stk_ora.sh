################################
# Oracle 11.2.0.4 on sles11sp4 #
################################

# accounts
mkdir -p /oracle
groupadd dba
groupadd oinstall
useradd -g oinstall -G dba oracle
echo 'oracle:o91erm*KV' > passwd.out
chpasswd < passwd.out
mkdir /home/oracle
chown -R oracle:oinstall /home/oracle
chown -R oracle:oinstall /oracle

# install required rpms
zypper --quiet install linux-kernel-headers glibc-devel gcc43 gcc libstdc++43-devel gcc43-c++ gcc-c++ sysstat libaio-devel libstdc++-devel unixODBC unixODBC-devel

# system configurations
sysctl -w kernel.shmall=2097152
sysctl -w kernel.shmmax=2147483648
sysctl -w kernel.shmmni=4096
sysctl -w sem=250 32000 100 128
sysctl -w net.core.rmem_default=4194304
sysctl -w net.core.rmem_max=4194304
sysctl -w fs.file-max=6815744
sysctl -w net.ipv4.ip_local_port_range=9000 65500
sysctl -w net.core.wmem_max=1048576
sysctl -w fs.aio-max-nr=1048576
sed -i "/^oracle soft nproc/d" /etc/security/limits.conf
sed -i "/^oracle hard nproc/d" /etc/security/limits.conf
sed -i "/^oracle soft nofile/d" /etc/security/limits.conf
sed -i "/^oracle hard nofile/d" /etc/security/limits.conf
cat >> /etc/security/limits.conf <<!
oracle soft nproc 2047
oracle hard nproc 16384
oracle soft nofile 1024
oracle hard nofile 65536
!
# ulimit configs, cannot be undone automatically
if [ `grep "oracle" /etc/profile | wc -l` -eq 0 ]; then
cat >> /etc/profile <<!
if [ $USER = "oracle" ]; then
   if [ $SHELL = "/bin/ksh" ]; then
      ulimit -p 16384
      ulimit -n 65536
   else
      ulimit -u 16384 -n 65536
   fi
fi
!
fi
if [ `grep "127.0.0.1" /etc/hosts | grep \`hostname\` | wc -l` -eq 0 ]; then
   echo -e "127.0.0.1\t`hostname`" >> /etc/hosts
fi
if [ `grep "/dev/shm" /etc/fstab | wc -l` -eq 0 ]; then
   echo "tmpfs                /dev/shm             tmpfs      defaults,size=1024m   0 0" >> /etc/fstab
   mount -o remount /dev/shm
fi

# Reponse file
chown -R oracle:oinstall /home/database
su - oracle
cd /home/database
./runInstaller -silent -responseFile /home/database/response/db_install.rsp
# ^D or sudo su
/oracle/inventory/orainstRoot.sh
/oracle/product/11.2.0/root.sh
#
sed -i "/^export ORACLE_BASE/d" /etc/profile
sed -i "/^export ORACLE_HOME/d" /etc/profile
sed -i "/^export ORACLE_SID/d" /etc/profile
sed -i "/^export PATH=\$PATH:\$ORACLE_HOME\/bin/d" /etc/profile
export ORACLE_BASE=/oracle
export ORACLE_HOME=$ORACLE_BASE/product/11.2.0
export ORACLE_SID=orcl
cat >> /etc/profile <<!
export ORACLE_BASE=/oracle
export ORACLE_HOME=$ORACLE_BASE/product/11.2.0
export ORACLE_SID=orcl
export PATH=$PATH:$ORACLE_HOME/bin
!

# 修改监听端口号为8080，静态注册监听
cat > /etc/profile <<!
LISTENER =
  (DESCRIPTION_LIST =
    (DESCRIPTION =
      (ADDRESS = (PROTOCOL = IPC)(KEY = EXTPROC1521))
      (ADDRESS = (PROTOCOL = TCP)(HOST = localhost)(PORT = 8080))
    )
  )

ADR_BASE_LISTENER = /oracle

SID_LIST_LISTENER =
  (SID_LIST =
    (SID_DESC =
      (GLOBAL_DBNAME=orcl)
      (SID_NAME = orcl)
      (ORACLE_HOME = /oracle/product/11.2.0 )
    )
    )
  )
!

