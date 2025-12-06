
@echo off
REM 切换到第一个IP配置
set IP1=192.168.100.7
set MASK1=255.255.255.0
set GW1=192.168.100.1

REM 切换到第二个IP配置
set IP2=192.168.0.141
set MASK2=255.255.255.0
set GW2=192.168.0.1

REM 选择配置
echo 选择配置:
echo 1. 配置1: %IP1%
echo 2. 配置2: %IP2%
echo 3. 自动获取IP地址和DNS服务器地址
set /p choice=请输入1, 2或3并按回车: 

REM   netsh interface ip set dns name="以太网 3" addr=8.8.8.8  source=static register=PRIMARY  这样可以设置DNS

if %choice%==1 (
    netsh interface ip set address name="以太网 3" static %IP1% %MASK1% %GW1%
    netsh interface ip set dns name="以太网 3" source=static register=PRIMARY
    echo 已切换到配置1
) else if %choice%==2 (
    netsh interface ip set address name="以太网 3" static %IP2% %MASK2% %GW2%
    netsh interface ip set dns name="以太网 3"  addr=192.168.0.1  source=static register=PRIMARY
    echo 已切换到配置2
) else if %choice%==3 (
    netsh interface ip set address name="以太网 3" source=dhcp
    netsh interface ip set dns name="以太网 3" source=dhcp
    echo 已切换到自动获取IP地址和DNS服务器地址
) else (
    echo 无效选择
)

pause
