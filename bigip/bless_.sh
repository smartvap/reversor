#################
# Bigip reverse #
#################

# Host
# 10.19.195.18
root/Xg6=M-n1

# bigip environment authentications
# 10.19.195.17
root/Nkuz8C#3j
admin/39Fkeu#Te

# dynatrace authentications
# 10.19.195.15
root/Ad29nBcw^

# application deployment folder possiblly
/usr/local/www/tmui
/usr/local/www/waui

# tomcat install dynatrace agent
# remount /usr
mount -o remount,rw /usr
# add the options to /usr/sbin/tomcat
JAVA_OPTS=""-agentpath:/appdata/dynatrace-6.5/agent/lib/libdtagent.so=name=f5_app,server=10.19.195.15:9998" $JAVA_OPTS"
# stop tomcat then it will restart automatically
/usr/sbin/dtomcat stop; tail -f /usr/share/tomcat/logs/catalina.out

# tomcat --> hsql jdbc component --> McpBridge --> mcpd:6666
LICENSE_BLOB
[OBJECT_ID, LICENSE, MANAGER_IP]
[-5, 1111, 12]
[java.lang.Long, java.lang.Object, java.lang.String]

# info
# 2019 Jan 15 23:50:50 c4vlb01 mcpd[6177]: 01070608:0: License is not operational (expired or digital signature does not match contents).
gdb --pid=`ps -ef | grep /usr/bin/mcpd | grep -v grep | awk '{print $2}'`
gcore -o core `ps -ef | grep /usr/bin/mcpd | grep -v grep | awk '{print $2}'`

# xray deployment
# firewall configuration
service iptables status
iptables -I INPUT -p tcp --dport 23946 -j ACCEPT
/etc/rc.d/init.d/iptables save
tmsh create net vlan vlan_195 interfaces add { 1.1 }
tmsh create net self self_195 address 10.19.195.17/26 vlan vlan_195
tmsh create net route default gw 10.19.195.1
tmsh modify net self self_195 allow-service add { tcp:22 tcp:443 tcp:23946 }

delete net route default
nohup ./linux_server -i172.16.134.2 -v -p23946 -PpAsWd_1 1>>ida.out 2>>ida.out &

# crontab -l
MAILTO=""
1-59/10 * * * * /usr/bin/diskmonitor
0 */4 * * * /usr/bin/diskwearoutstat
05 09 * * * /usr/bin/updatecheck -a
05 09 16 * * /usr/bin/phonehome_upload
36 * * * * /usr/bin/copy_rrd save

# 隔离
# lsof -p 6190 | grep -v ESTABLISHED | grep -v LISTEN | grep -v /var/run/mcp
# rpm -qf 
ps -ef | grep runsvdir | grep -v grep | awk '{print $2}' | xargs kill -9
ps -ef | grep "runsv mcpd" | grep -v grep | awk '{print $2}' | xargs kill -9
ps -ef | grep "/usr/bin/mcpd -dbmem 512 -listen 127.0.0.1 -f" | grep -v grep | awk '{print $2}' | xargs kill -9
ps -ef | grep keymgmtd | grep -v grep | awk '{print $2}' | xargs kill -9
ps -ef | grep restjavad | grep -v grep | awk '{print $2}' | xargs kill -9
/usr/bin/mcpd -dbmem 512 -listen 127.0.0.1 -f

# find
for i in `find / -name "*.so*"`; do
if [ ! -f `strings $i | grep 'LICENSE EXPIRED' | awk '{print $1}'` ]; then
echo $i
fi
done

# disassemble
objdump -M intel -d /usr/lib/libmcpdcommon.so > libmcpdcommon.dasm

#   36254a:       0f 95 c0                setne  al
00362530 <_ZN19MCPfflagManagerImpl22license_is_operationalEv>:
  362530:       55                      push   ebp
  362531:       89 e5                   mov    ebp,esp
  362533:       53                      push   ebx
  362534:       83 ec 04                sub    esp,0x4
  362537:       e8 00 00 00 00          call   36253c <_ZN19MCPfflagManagerImpl22license_is_operationalEv+0xc>
  36253c:       5b                      pop    ebx
  36253d:       81 c3 34 cf 2f 00       add    ebx,0x2fcf34
  362543:       e8 fc 03 e3 ff          call   192944 <get_license_operational@plt>
  362548:       85 c0                   test   eax,eax
  36254a:       0f 95 c0                setne  al
  36254d:       83 c4 04                add    esp,0x4
  362550:       5b                      pop    ebx
  362551:       5d                      pop    ebp
  362552:       c3                      ret
  362553:       90                      nop
  362554:       8d b6 00 00 00 00       lea    esi,[esi+0x0]
  36255a:       8d bf 00 00 00 00       lea    edi,[edi+0x0]

# 找到代码段.text入口地址
readelf -a libmcpdcommon.so | more
# Entry point address:               0x19e170
# [11] .text             PROGBITS        0019e170 19e170 389868 00  AX  0   0 16
setne al, 36254a

cp /usr/lib/libmcpdcommon.so /usr/lib/libmcpdcommon.so.ori
cp /appdata/libmcpdcommon.so /usr/lib
ps -ef | grep /usr/bin/mcpd | grep -v grep | awk '{print $2}' | xargs kill -9; /usr/bin/mcpd -dbmem 512 -listen 127.0.0.1 -f

# tcpdump mcpd
tcpdump -i lo port 6666

# ERROR LIST
Jan 19 00:08:26 c4vlb01 err mcpd[7344]: 01180005:3: Evaluation license has expired.
Jan 19 00:08:27 c4vlb01 err chmand[8281]: 01180005:3: Evaluation license has expired.
Jan 19 00:08:28 c4vlb01 err ql[7488]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:00 c4vlb01 err mcpd[8990]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:01 c4vlb01 err chmand[8281]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:01 c4vlb01 err statsd[7059]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:03 c4vlb01 err ql[9180]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:07 c4vlb01 err tmm1[8987]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:07 c4vlb01 err tmm2[8987]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:07 c4vlb01 err tmm[8987]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:07 c4vlb01 err tmm6[8987]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:07 c4vlb01 err tmm3[8987]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:07 c4vlb01 err tmm4[8987]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:07 c4vlb01 err tmm7[8987]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:07 c4vlb01 err tmm5[8987]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:09 c4vlb01 err tmrouted[8187]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:09 c4vlb01 err vxland[6979]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:34 c4vlb01 err ql[9995]: 01180005:3: Evaluation license has expired.
Jan 19 00:09:35 c4vlb01 err merged[6777]: 01180005:3: Evaluation license has expired.
Jan 19 00:10:03 c4vlb01 err promptstatusd[3190]: 01180005:3: Evaluation license has expired.
Jan 19 00:10:03 c4vlb01 err lind[6771]: 01180005:3: Evaluation license has expired.
Jan 19 00:10:04 c4vlb01 err iprepd[13761]: 01180005:3: Evaluation license has expired.
Jan 19 00:10:12 c4vlb01 err tmipsecd[13766]: 01180005:3: Evaluation license has expired.
Jan 19 00:10:20 c4vlb01 err tmm5[18460]: 01180005:3: Evaluation license has expired.
Jan 19 00:10:20 c4vlb01 err tmm1[18460]: 01180005:3: Evaluation license has expired.
Jan 19 00:10:20 c4vlb01 err tmm7[18460]: 01180005:3: Evaluation license has expired.
Jan 19 00:10:20 c4vlb01 err tmm3[18460]: 01180005:3: Evaluation license has expired.
Jan 19 00:10:20 c4vlb01 err tmm4[18460]: 01180005:3: Evaluation license has expired.
Jan 19 00:10:20 c4vlb01 err tmm2[18460]: 01180005:3: Evaluation license has expired.
Jan 19 00:10:20 c4vlb01 err tmm6[18460]: 01180005:3: Evaluation license has expired.
Jan 19 00:10:20 c4vlb01 err tmm[18460]: 01180005:3: Evaluation license has expired.
Jan 19 00:10:29 c4vlb01 err vxland[13769]: 01180005:3: Evaluation license has expired.
Jan 19 00:15:04 c4vlb01 err iprepd[13761]: 01180005:3: Evaluation license has expired.
Jan 19 00:20:04 c4vlb01 err iprepd[13761]: 01180005:3: Evaluation license has expired.

objdump -M intel -d /usr/lib/libfflag_sh.so.1 > libfflag_sh.so.1.dasm

# found /usr/lib/libmcpdcommon.so including the target string
# Jan 19 05:27:28 vlb01 emerg mcpd[5919]: 01070608:0: License is not operational (expired or digital signature does not match contents).
# 查询mcpd主进程相关的Regular File，包含有ELF格式的动态库、data文件等
lsof -p `ps -ef | grep /usr/bin/mcpd | grep -v grep | awk '{print $2}'` | grep ' REG ' | awk '{print $NF}' > mcpd_depends.out
# 对于所有Regular File，需要提取出ELF的动态库
> mcpd_elf.out
for i in `cat mcpd_depends.out`; do
if [ ! -f `file $i | grep 'ELF' | awk '{print $1}'` ]; then
echo $i >> mcpd_elf.out
fi
done
# 对所有ELF文件，若其字符串常量中存在我们需要的内容，则输出
> mcpd_target.out
for i in `cat mcpd_elf.out`; do
if [ ! -f `strings $i | grep 'Dossier error' | awk '{print $1}'` ]; then
echo $i >> mcpd_target.out
fi
done


# objdump -f mcpd
mcpd:     file format elf32-i386
architecture: i386, flags 0x00000112:
EXEC_P, HAS_SYMS, D_PAGED
start address 0x080fd9d0

0820f670 <get_service_check_date_ok>:
 820f670:       55                      push   ebp
 820f671:       89 e5                   mov    ebp,esp
 820f673:       83 ec 08                sub    esp,0x8
 820f676:       e8 d5 1c 00 00          call   8211350 <service_check_date_ok>
 820f67b:       48                      dec    eax
 820f67c:       c9                      leave
 820f67d:       0f 94 c0                sete   al
 820f680:       0f b6 c0                movzx  eax,al
 820f683:       c3                      ret
 820f684:       8d b6 00 00 00 00       lea    esi,[esi+0x0]
 820f68a:       8d bf 00 00 00 00       lea    edi,[edi+0x0]
 
# readelf -d /usr/bin/ql
Dynamic section at offset 0xdb1c contains 23 entries:
  Tag        Type                         Name/Value
 0x00000001 (NEEDED)                     Shared library: [libcrypto.so.10]
 0x00000001 (NEEDED)                     Shared library: [libssl.so.10]
 0x00000001 (NEEDED)                     Shared library: [liberrdefs.so]
 0x00000001 (NEEDED)                     Shared library: [libc.so.6]
 0x0000000c (INIT)                       0x8048c00
 0x0000000d (FINI)                       0x80509ac
 0x6ffffef5 (GNU_HASH)                   0x804818c
 0x00000005 (STRTAB)                     0x8048610
 0x00000006 (SYMTAB)                     0x80481d0
 0x0000000a (STRSZ)                      766 (bytes)
 0x0000000b (SYMENT)                     16 (bytes)
 0x00000015 (DEBUG)                      0x0
 0x00000003 (PLTGOT)                     0x8056c08
 0x00000002 (PLTRELSZ)                   456 (bytes)
 0x00000014 (PLTREL)                     REL
 0x00000017 (JMPREL)                     0x8048a38
 0x00000011 (REL)                        0x8048a18
 0x00000012 (RELSZ)                      32 (bytes)
 0x00000013 (RELENT)                     8 (bytes)
 0x6ffffffe (VERNEED)                    0x8048998
 0x6fffffff (VERNEEDNUM)                 2
 0x6ffffff0 (VERSYM)                     0x804890e
 0x00000000 (NULL)                       0x0
 

for i in `ls /usr/bin/*`; do
if [ `strings $i | grep "get_license_expired" | wc -l` -ne "0" ]; then
echo $i
fi
done

/usr/bin/ipsd
/usr/bin/scriptd
/usr/bin/wocplugin

for i in `find / -name "lib" -type d`; do
for j in `find $i -type f`; do
if [ `strings $j | grep "get_license_expired" | wc -l` -ne "0" ]; then
echo $j
fi
done
done

/usr/lib/libwamcpclient.so
/usr/lib/libicrd.so
/usr/lib/bigipTrafficMgmt.so
/usr/lib/libhal_internal.so.1
/usr/lib/libxconfig.so
/usr/lib/libfflag_sh.so.1
/usr/lib/httpd/modules/mod_xui.so

for i in `find / -name "lib" -type d`; do
for j in `find $i -type f`; do
if [ `strings $j | grep "ModuleNotLicensed" | wc -l` -ne "0" ]; then
echo $j
fi
done
done

for i in `find / -name "bin" -type d`; do
for j in `find $i -type f`; do
if [ `strings $j | grep "ModuleNotLicensed" | wc -l` -ne "0" ]; then
echo $j
fi
done
done

/usr/bin/promptstatusd

00000F58	libc_2.12.so:strchrnul+65	xor     ecx, edx	libmcpdcommon.so:_ZTS16GenericValidatorILZ16cid_license_blobEE+2EC: 44
