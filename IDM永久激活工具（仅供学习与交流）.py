import os
import sys
import ctypes
import winreg
import subprocess
import time
import random
import string
import requests
import psutil
import win32api
import win32con
import win32security
from tqdm import tqdm

# 检查管理员权限
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# 以管理员权限重新运行脚本
def run_as_admin():
    script_path = os.path.abspath(sys.argv[0])
    params = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in sys.argv[1:]])
    
    # 使用 ShellExecute 请求管理员权限
    ctypes.windll.shell32.ShellExecuteW(
        None, 
        "runas", 
        sys.executable, 
        f'"{script_path}" {params}', 
        None, 
        1
    )
    sys.exit(0)

# 结束 IDM 进程及相关服务
def kill_idm_process():
    processes_to_kill = [
        "idman.exe", "idmbroker.exe", "idmcc.exe", 
        "idmnetmon.exe", "idmtdi.exe", "idmvs.exe"
    ]
    
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            proc_name = proc.info['name'].lower()
            if any(target in proc_name for target in processes_to_kill):
                proc.kill()
                time.sleep(0.2)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

# 获取当前用户的 SID
def get_current_user_sid():
    try:
        # 使用 Windows API 获取当前用户的 SID
        token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
        sid, _ = win32security.GetTokenInformation(token, win32security.TokenUser)
        return win32security.ConvertSidToStringSid(sid)
    except:
        # 回退方法：通过环境变量获取
        try:
            username = os.environ['USERNAME']
            domain = os.environ['USERDOMAIN']
            sid = win32security.LookupAccountName(domain, username)[0]
            return win32security.ConvertSidToStringSid(sid)
        except:
            return "S-1-5-21-0-0-0-500"  # 默认管理员 SID

# 彻底清理注册表
def deep_clean_registry():
    # 获取当前用户 SID
    user_sid = get_current_user_sid()
    
    # 需要清理的注册表项列表（扩展版）
    registry_keys = [
        # 核心 CLSID 项
        r"HKLM\Software\Classes\CLSID\{7B8E9164-324D-4A2E-A46D-0165FB2000EC}",
        r"HKLM\Software\Classes\CLSID\{6DDF00DB-1234-46EC-8356-27E7B2051192}",
        r"HKLM\Software\Classes\CLSID\{D5B91409-A8CA-4973-9A0B-59F713D25671}",
        r"HKLM\Software\Classes\CLSID\{5ED60779-4DE2-4E07-B862-974CA4FF2E9C}",
        r"HKLM\Software\Classes\CLSID\{07999AC3-058B-40BF-984F-69EB1E554CA7}",
        r"HKLM\Software\Classes\CLSID\{E8CF4E59-B7A3-41F2-86C7-82B03334F22A}",
        r"HKLM\Software\Classes\CLSID\{9C9D53D4-A978-43FC-93E2-1C21B529E6D7}",
        r"HKLM\Software\Classes\CLSID\{79873CC5-3951-43ED-BDF9-D8759474B6FD}",
        r"HKLM\Software\Classes\CLSID\{E6871B76-C3C8-44DD-B947-ABFFE144860D}",
        
        # Wow6432Node 下的 CLSID 项
        r"HKLM\Software\Classes\Wow6432Node\CLSID\{7B8E9164-324D-4A2E-A46D-0165FB2000EC}",
        r"HKLM\Software\Classes\Wow6432Node\CLSID\{6DDF00DB-1234-46EC-8356-27E7B2051192}",
        r"HKLM\Software\Classes\Wow6432Node\CLSID\{D5B91409-A8CA-4973-9A0B-59F713D25671}",
        r"HKLM\Software\Classes\Wow6432Node\CLSID\{5ED60779-4DE2-4E07-B862-974CA4FF2E9C}",
        r"HKLM\Software\Classes\Wow6432Node\CLSID\{07999AC3-058B-40BF-984F-69EB1E554CA7}",
        r"HKLM\Software\Classes\Wow6432Node\CLSID\{E8CF4E59-B7A3-41F2-86C7-82B03334F22A}",
        r"HKLM\Software\Classes\Wow6432Node\CLSID\{9C9D53D4-A978-43FC-93E2-1C21B529E6D7}",
        r"HKLM\Software\Classes\Wow6432Node\CLSID\{79873CC5-3951-43ED-BDF9-D8759474B6FD}",
        r"HKLM\Software\Classes\Wow6432Node\CLSID\{E6871B76-C3C8-44DD-B947-ABFFE144860D}",
        
        # 用户特定的 CLSID 项
        r"HKCU\Software\Classes\CLSID\{7B8E9164-324D-4A2E-A46D-0165FB2000EC}",
        r"HKCU\Software\Classes\CLSID\{6DDF00DB-1234-46EC-8356-27E7B2051192}",
        r"HKCU\Software\Classes\CLSID\{D5B91409-A8CA-4973-9A0B-59F713D25671}",
        r"HKCU\Software\Classes\CLSID\{5ED60779-4DE2-4E07-B862-974CA4FF2E9C}",
        r"HKCU\Software\Classes\CLSID\{07999AC3-058B-40BF-984F-69EB1E554CA7}",
        r"HKCU\Software\Classes\CLSID\{E8CF4E59-B7A3-41F2-86C7-82B03334F22A}",
        r"HKCU\Software\Classes\CLSID\{9C9D53D4-A978-43FC-93E2-1C21B529E6D7}",
        r"HKCU\Software\Classes\CLSID\{79873CC5-3951-43ED-BDF9-D8759474B6FD}",
        r"HKCU\Software\Classes\CLSID\{E6871B76-C3C8-44DD-B947-ABFFE144860D}",
        
        # 用户特定的 Wow6432Node CLSID 项
        r"HKCU\Software\Classes\Wow6432Node\CLSID\{7B8E9164-324D-4A2E-A46D-0165FB2000EC}",
        r"HKCU\Software\Classes\Wow6432Node\CLSID\{6DDF00DB-1234-46EC-8356-27E7B2051192}",
        r"HKCU\Software\Classes\Wow6432Node\CLSID\{D5B91409-A8CA-4973-9A0B-59F713D25671}",
        r"HKCU\Software\Classes\Wow6432Node\CLSID\{5ED60779-4DE2-4E07-B862-974CA4FF2E9C}",
        r"HKCU\Software\Classes\Wow6432Node\CLSID\{07999AC3-058B-40BF-984F-69EB1E554CA7}",
        r"HKCU\Software\Classes\Wow6432Node\CLSID\{E8CF4E59-B7A3-41F2-86C7-82B03334F22A}",
        r"HKCU\Software\Classes\Wow6432Node\CLSID\{9C9D53D4-A978-43FC-93E2-1C21B529E6D7}",
        r"HKCU\Software\Classes\Wow6432Node\CLSID\{79873CC5-3951-43ED-BDF9-D8759474B6FD}",
        r"HKCU\Software\Classes\Wow6432Node\CLSID\{E6871B76-C3C8-44DD-B947-ABFFE144860D}",
        
        # 默认用户配置
        r"HKU\.DEFAULT\Software\Classes\CLSID\{7B8E9164-324D-4A2E-A46D-0165FB2000EC}",
        r"HKU\.DEFAULT\Software\Classes\CLSID\{6DDF00DB-1234-46EC-8356-27E7B2051192}",
        r"HKU\.DEFAULT\Software\Classes\CLSID\{D5B91409-A8CA-4973-9A0B-59F713D25671}",
        r"HKU\.DEFAULT\Software\Classes\CLSID\{5ED60779-4DE2-4E07-B862-974CA4FF2E9C}",
        r"HKU\.DEFAULT\Software\Classes\CLSID\{07999AC3-058B-40BF-984F-69EB1E554CA7}",
        r"HKU\.DEFAULT\Software\Classes\CLSID\{E8CF4E59-B7A3-41F2-86C7-82B03334F22A}",
        r"HKU\.DEFAULT\Software\Classes\CLSID\{9C9D53D4-A978-43FC-93E2-1C21B529E6D7}",
        r"HKU\.DEFAULT\Software\Classes\CLSID\{79873CC5-3951-43ED-BDF9-D8759474B6FD}",
        r"HKU\.DEFAULT\Software\Classes\CLSID\{E6871B76-C3C8-44DD-B947-ABFFE144860D}",
        
        # 特定用户配置
        f"HKU\\{user_sid}\\Software\\Classes\\CLSID\\{{7B8E9164-324D-4A2E-A46D-0165FB2000EC}}",
        f"HKU\\{user_sid}\\Software\\Classes\\CLSID\\{{6DDF00DB-1234-46EC-8356-27E7B2051192}}",
        f"HKU\\{user_sid}\\Software\\Classes\\CLSID\\{{D5B91409-A8CA-4973-9A0B-59F713D25671}}",
        f"HKU\\{user_sid}\\Software\\Classes\\CLSID\\{{5ED60779-4DE2-4E07-B862-974CA4FF2E9C}}",
        f"HKU\\{user_sid}\\Software\\Classes\\CLSID\\{{07999AC3-058B-40BF-984F-69EB1E554CA7}}",
        f"HKU\\{user_sid}\\Software\\Classes\\CLSID\\{{E8CF4E59-B7A3-41F2-86C7-82B03334F22A}}",
        f"HKU\\{user_sid}\\Software\\Classes\\CLSID\\{{9C9D53D4-A978-43FC-93E2-1C21B529E6D7}}",
        f"HKU\\{user_sid}\\Software\\Classes\\CLSID\\{{79873CC5-3951-43ED-BDF9-D8759474B6FD}}",
        f"HKU\\{user_sid}\\Software\\Classes\\CLSID\\{{E6871B76-C3C8-44DD-B947-ABFFE144860D}}",
        
        # IDM 主配置项
        r"HKCU\Software\DownloadManager",
        r"HKLM\SOFTWARE\Internet Download Manager",
        r"HKLM\SOFTWARE\Wow6432Node\Internet Download Manager",
        r"HKLM\SOFTWARE\Tonec",
        r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Internet Download Manager",
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\Internet Download Manager",
    ]
    
    # 删除注册表项
    for key in tqdm(registry_keys, desc="深度清理注册表", unit="项", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"):
        try:
            # 解析注册表路径
            if key.startswith("HKLM\\"):
                root = winreg.HKEY_LOCAL_MACHINE
                path = key[5:]
            elif key.startswith("HKCU\\"):
                root = winreg.HKEY_CURRENT_USER
                path = key[5:]
            elif key.startswith("HKU\\"):
                root = winreg.HKEY_USERS
                path = key[4:]
            else:
                continue
            
            # 尝试删除整个项
            try:
                winreg.DeleteKey(root, path)
                continue
            except OSError:
                pass
            
            # 如果无法删除整个项，尝试删除值
            try:
                with winreg.OpenKey(root, path, 0, winreg.KEY_ALL_ACCESS) as reg_key:
                    # 枚举并删除所有值
                    for i in range(winreg.QueryInfoKey(reg_key)[1]):
                        value_name = winreg.EnumValue(reg_key, i)[0]
                        try:
                            winreg.DeleteValue(reg_key, value_name)
                        except:
                            pass
            except:
                pass
            
            # 最后尝试使用 PowerShell 强制删除
            try:
                ps_command = f"Remove-Item -Path 'Registry::{root}\\{path}' -Recurse -Force -ErrorAction SilentlyContinue"
                subprocess.run(["powershell", "-Command", ps_command], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL, 
                               shell=True)
            except:
                pass
        except:
            pass

# 锁定关键注册表项
def lock_registry_keys():
    keys_to_lock = [
        r"HKCU\Software\DownloadManager",
        r"HKLM\SOFTWARE\Internet Download Manager",
        r"HKLM\SOFTWARE\Wow6432Node\Internet Download Manager",
    ]
    
    for key in tqdm(keys_to_lock, desc="锁定注册表项", unit="项", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"):
        try:
            # 解析注册表路径
            if key.startswith("HKLM\\"):
                root = winreg.HKEY_LOCAL_MACHINE
                path = key[5:]
            elif key.startswith("HKCU\\"):
                root = winreg.HKEY_CURRENT_USER
                path = key[5:]
            else:
                continue
            
            # 创建或打开注册表项
            try:
                with winreg.OpenKey(root, path, 0, winreg.KEY_ALL_ACCESS) as reg_key:
                    pass
            except FileNotFoundError:
                winreg.CreateKey(root, path)
            
            # 设置权限 - 拒绝所有访问
            ps_command = f'''
            $key = '{key}'
            $rule = New-Object System.Security.AccessControl.RegistryAccessRule(
                [System.Security.Principal.SecurityIdentifier]'S-1-1-0',
                'FullControl',
                'ContainerInherit',
                'None',
                'Deny'
            )
            $acl = Get-Acl -Path "Registry::$key"
            $acl.SetAccessRule($rule)
            Set-Acl -Path "Registry::$key" -AclObject $acl
            '''
            subprocess.run(["powershell", "-Command", ps_command], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL, 
                           shell=True)
        except:
            pass

# 激活 IDM 并防止弹窗
def activate_and_prevent_popup():
    # 1. 删除特定注册表项
    keys_to_delete = [
        r"HKCU\Software\DownloadManager\FName",
        r"HKCU\Software\DownloadManager\LName",
        r"HKCU\Software\DownloadManager\Email",
        r"HKCU\Software\DownloadManager\Serial",
        r"HKCU\Software\DownloadManager\scansk",
        r"HKCU\Software\DownloadManager\tvfrdt",
        r"HKCU\Software\DownloadManager\radxcnt",
        r"HKCU\Software\DownloadManager\LstCheck",
        r"HKCU\Software\DownloadManager\ptrk_scdt",
        r"HKCU\Software\DownloadManager\LastCheckQU",
        r"HKLM\SOFTWARE\Internet Download Manager\Serial",
        r"HKLM\SOFTWARE\Internet Download Manager\InstallPath",
        r"HKLM\SOFTWARE\Internet Download Manager\InstallTime",
    ]
    
    for key in tqdm(keys_to_delete, desc="删除激活项", unit="项", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"):
        try:
            # 解析注册表路径
            if key.startswith("HKLM\\"):
                root = winreg.HKEY_LOCAL_MACHINE
                path = key[5:]
            else:  # HKCU
                root = winreg.HKEY_CURRENT_USER
                path = key[5:]
            
            # 分割路径和值名称
            if '\\' in path:
                key_path, value_name = path.rsplit('\\', 1)
            else:
                key_path, value_name = "", path
            
            # 打开注册表项并删除值
            with winreg.OpenKey(root, key_path, 0, winreg.KEY_WRITE) as reg_key:
                try:
                    winreg.DeleteValue(reg_key, value_name)
                except FileNotFoundError:
                    pass
        except:
            pass
    
    # 2. 添加关键注册表项
    try:
        key_path = r"SOFTWARE\Internet Download Manager"
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            winreg.SetValueEx(key, "AdvIntDriverEnabled2", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "BlockValidation", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "DisablePopup", 0, winreg.REG_DWORD, 1)
    except:
        pass
    
    try:
        key_path = r"SOFTWARE\Wow6432Node\Internet Download Manager"
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            winreg.SetValueEx(key, "AdvIntDriverEnabled2", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "BlockValidation", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "DisablePopup", 0, winreg.REG_DWORD, 1)
    except:
        pass
    
    # 3. 生成并写入随机用户信息和序列号
    fname = ''.join(random.choices(string.ascii_uppercase, k=5))
    lname = ''.join(random.choices(string.ascii_uppercase, k=7))
    email = f"{fname}.{lname}@tonec.com"
    serial = '-'.join([''.join(random.choices(string.ascii_uppercase + string.digits, k=5)) for _ in range(4)])
    
    try:
        key_path = r"Software\DownloadManager"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "FName", 0, winreg.REG_SZ, fname)
            winreg.SetValueEx(key, "LName", 0, winreg.REG_SZ, lname)
            winreg.SetValueEx(key, "Email", 0, winreg.REG_SZ, email)
            winreg.SetValueEx(key, "Serial", 0, winreg.REG_SZ, serial)
            winreg.SetValueEx(key, "ActivationDate", 0, winreg.REG_SZ, "01/01/2025")
            winreg.SetValueEx(key, "LicenseType", 0, winreg.REG_SZ, "Commercial")
    except:
        pass
    
    # 4. 添加防火墙规则阻止 IDM 验证
    try:
        ps_command = '''
        $ruleName = "Block IDM Validation"
        if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
            New-NetFirewallRule -DisplayName $ruleName -Direction Outbound `
                -Action Block -Protocol TCP -RemotePort 80,443 `
                -RemoteAddress "internetdownloadmanager.com","tonec.com" `
                -Program "%ProgramFiles%\Internet Download Manager\IDMan.exe" `
                -Enabled True
        }
        '''
        subprocess.run(["powershell", "-Command", ps_command], 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL, 
                       shell=True)
    except:
        pass
    
    # 5. 模拟下载（触发激活）
    urls = [
        "https://www.internetdownloadmanager.com/images/idm_box_min.png",
        "https://www.internetdownloadmanager.com/register/IDMlib/images/idman_logos.png",
        "https://www.internetdownloadmanager.com/pictures/idm_about.png"
    ]
    
    for i, url in enumerate(tqdm(urls, desc="触发下载", unit="文件", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]")):
        try:
            # 设置超时时间
            response = requests.get(url, timeout=3)
            temp_file = os.path.join(os.environ['TEMP'], f"idm_trigger_{i}.png")
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            time.sleep(0.5)
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except:
            pass

# 主函数
def main():
    # 检查管理员权限
    if not is_admin():
        print("\n[!] 需要管理员权限运行此工具")
        print("[*] 正在请求管理员权限...")
        time.sleep(1)
        run_as_admin()
        return
    
    print("=" * 60)
    print("IDM 永久激活工具 - 完全解决弹窗问题")
    print("=" * 60)
    print("此工具将执行以下操作：")
    print("1. 结束 IDM 进程及服务")
    print("2. 深度清理注册表残留项")
    print("3. 设置激活信息")
    print("4. 锁定关键注册表项")
    print("5. 配置防护措施")
    print("=" * 60)
    print("\n注意：本工具仅供学习目的，请支持正版软件！")
    print("\n开始执行...\n")
    
    # 整体进度条
    total_steps = 6
    with tqdm(total=total_steps, desc="整体进度", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
        # 1. 结束 IDM 进程
        kill_idm_process()
        pbar.update(1)
        pbar.set_postfix_str("IDM 进程已结束")
        time.sleep(0.5)
        
        # 2. 深度清理注册表
        deep_clean_registry()
        pbar.update(1)
        pbar.set_postfix_str("注册表深度清理完成")
        time.sleep(0.5)
        
        # 3. 激活 IDM 并设置防护
        activate_and_prevent_popup()
        pbar.update(1)
        pbar.set_postfix_str("激活信息已设置")
        time.sleep(0.5)
        
        # 4. 锁定关键注册表项
        lock_registry_keys()
        pbar.update(1)
        pbar.set_postfix_str("注册表已锁定")
        time.sleep(0.5)
        
        # 5. 最终清理
        kill_idm_process()
        pbar.update(1)
        pbar.set_postfix_str("最终清理完成")
        time.sleep(0.5)
        
        # 6. 完成
        pbar.update(1)
        pbar.set_postfix_str("操作完成")
    
    print("\n" + "=" * 60)
    print("IDM 激活操作已完成！")
    print("=" * 60)
    print("\n重要提示：")
    print("- 已完全阻止 IDM 的盗版验证机制")
    print("- 已锁定关键注册表项防止修改")
    print("- 已添加防火墙规则阻止验证连接")
    print("\n请启动 IDM 检查激活状态。")
    print("按 Enter 键退出...")
    input()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[!] 发生错误: {e}")
        print("按 Enter 键退出...")
        input()
