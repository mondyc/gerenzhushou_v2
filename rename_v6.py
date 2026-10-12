# 说明：这个改名脚本，完成了创建文件夹和改名，添加了帮助文档的功能
# 但是改的名字还是有点问题，问题在于需要根据WPS是否存在来判断改的名称中是否需要带WPS版本号
# 新增了对升级包的改名
# 20251230更新：将预置路径改为了相对路径
# 20250102更新：判断pkg文件夹是否存在，如果不存在则提示没有找到pkg文件夹，并退出程序，如果存在则打印
# 20250102更新：检查当前目录下名称包含“灵犀·晓伴_*--*”的文件夹，如果有，则提示“文件夹已存在”，并询问用户是否删除整个文件夹
# 20260331更新：新增了对升级包的改名和文件夹路径
# 20260611更新：新增了对zenity离线安装包的复制
# 20260716更新：新增了对zenity离线安装包(amd64)3.32.zip的复制
# 20261010更新：不再依赖pkg目录和手动压缩，直接识别package目录下的原始安装包，
#               deb/exe自动压缩为zip，mac的zip直接复制改名，产出与之前一致
# 20261012更新：文件搬运完成后自动处理upgrade_package/releases.json，
#               替换版本号、日期，并用md5_tool计算升级包和安装包的md5

import json
import os
import re
import shutil
import zipfile

from md5_tool import compute_md5

# 预置路径
path = './'
helppath = './help_documentation'
uppath = './upgrade_package'
pkgpath = './package'

# 原始安装包与平台的对应关系及文件名匹配模式（版本号用通配）
RAW_PATTERNS = {
    'linux_arm64': r'^suxiaoban_.*_arm64\.deb$',
    'linux_x64':   r'^suxiaoban_.*_amd64\.deb$',
    'mac_arm64':   r'^灵犀·晓伴-.*-arm64\.zip$',
    'mac_x64':     r'^灵犀·晓伴-.*-x64\.zip$',
    'win':         r'^suxiaoban-.*-setup\.exe$',
}

# 扫描package目录根下的文件，按模式为每个平台找到源文件
def get_raw_files(pkgpath):
    raw_files = {}
    for file in os.listdir(pkgpath):
        if not os.path.isfile(os.path.join(pkgpath, file)):
            continue
        for platform, pattern in RAW_PATTERNS.items():
            if platform not in raw_files and re.match(pattern, file):
                raw_files[platform] = file
                break
    return raw_files

raw_files = get_raw_files(pkgpath)
# 如果一个原始安装包都没找到，则提示并退出程序
if not raw_files:
    print("当前package目录中未找到任何原始安装包")
    exit()

# 打印找到的原始安装包及对应平台
for platform in RAW_PATTERNS:
    if platform in raw_files:
        print(platform + " 的原始安装包为：" + raw_files[platform])
    else:
        print("警告：未找到 " + platform + " 的原始安装包，将跳过该平台")

# 将源文件压缩为zip，zip内保留原始文件名，压缩过程中显示进度百分比
def make_zip(src_path, dst_zip, chunk_size=1024*1024):
    total = os.path.getsize(src_path)
    done = 0
    with zipfile.ZipFile(dst_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        info = zipfile.ZipInfo(os.path.basename(src_path))
        info.compress_type = zipfile.ZIP_DEFLATED
        with open(src_path, 'rb') as f:
            with zf.open(info, 'w') as zfile:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    zfile.write(chunk)
                    done += len(chunk)
                    percent = done * 100 // total
                    print("\r压缩进度：" + str(percent) + "% (" + str(done) + "/" + str(total) + " 字节)", end='')
    print("\r压缩进度：100% (" + str(total) + "/" + str(total) + " 字节)")

# 将源文件（deb/exe压缩 或 mac的zip直接复制）生成到两个目标：
# 一个放入发版文件夹，一个放入升级包文件夹
def deliver(src_file, dst1, dst2):
    src_path = os.path.join(pkgpath, src_file)
    if src_file.endswith('.zip'):
        shutil.copy(src_path, dst1)
    else:
        make_zip(src_path, dst1)
    print("生成文件成功：" + dst1)
    shutil.copy(dst1, dst2)

# 检查当前目录下名称包含“灵犀·晓伴_*--*”的文件夹，如果有，则退出程序，并提示“文件夹已存在”
for file in os.listdir('./'):
    if re.match(r'^灵犀·晓伴.*--.*', file):
        print("文件夹已经存在了")
        # 询问用户是否删除整个文件夹
        print("是否删除整个文件夹？ 1. 删除 or 2. 不删除")
        choice = input("请输入你的选择：")
        if choice == "1":
            try:
                # 使用管理员权限删除文件夹
                import subprocess
                subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', file], shell=True)
                print(f"已成功删除文件夹: {file}")
            except PermissionError as e:
                print(f"删除文件夹时发生权限错误: {e}")
                exit(1)
            except Exception as e:
                print(f"删除文件夹时发生错误: {e}")
                exit(1)
        elif choice == "2":
            exit()

# 检查upgrade_package文件夹是否存在，如果不存在则创建，如果存在则提示已存在，则询问用户是否清空这个文件夹的所有内容
if not os.path.exists(uppath):
    os.mkdir(uppath)
    print("upgrade_package文件夹创建成功！")
else:
    print("upgrade_package文件夹已存在！")
    print("是否清空upgrade_package文件夹的所有内容？1. 清空 or 2. 不清空")
    choice = input("请输入你的选择：")
    if choice == "1":
        try:
            # 使用管理员权限清空文件夹内容
            import subprocess
            subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', 'upgrade_package'], shell=True)
            os.mkdir(uppath)
            print(f"已成功清空文件夹: {uppath}")
        except PermissionError as e:
            print(f"删除文件夹时发生权限错误: {e}")
    elif choice == "2":
        exit(1)

# 接收输入灵犀·晓伴的版本号，并打印
version = input("请输入灵犀·晓伴的版本号：")
# 接受输入wps的版本号，并打印
# wps_version = input("请输入wps的版本号：")
# 接收输入日期
date = input("请输入日期（格式：20210101）：")
# 接收输入上个版本的日期
last_version_date = input("请输入上个版本的日期（格式：20210101）：")
# 接收输入强制更新版本
force_update_version = input("请输入强制更新版本：")
# 接收输入旧版本
old_version = input("请输入旧版本：")

# 将日期从20210101格式转换成2026-10-12格式
def format_date(s):
    return s[:4] + "-" + s[4:6] + "-" + s[6:]

# 将两个版本号拼接成新的文件夹名称
new_dir_name = "灵犀·晓伴_"+version
print("新的文件夹名称为："+new_dir_name)

# 使用new_dir_name创建文件夹
os.mkdir(new_dir_name)

# 在new_dir_name的文件夹下创建三个文件夹，首先拼接名称
mac_arm_dir_name = "灵犀·晓伴"+" "+version+" "+"mac-arm"
mac_x64_dir_name = "灵犀·晓伴"+" "+version+" "+"mac-x64"
win_dir_name = "灵犀·晓伴"+" "+version+" "+"win-x64"
linux_arm_dir_name = "灵犀·晓伴"+" "+version+" "+"linux-arm(统信+麒麟)"
linux_x64_dir_name = "灵犀·晓伴"+" "+version+" "+"linux-x64(统信+麒麟)"
# 打印文件夹名称
print("mac文件夹名称为："+mac_arm_dir_name)
print("mac文件夹名称为："+mac_x64_dir_name)
print("win文件夹名称为："+win_dir_name)
print("linux文件夹名称为："+linux_arm_dir_name)
print("linux文件夹名称为："+linux_x64_dir_name)


# 在new_dir_name的文件夹下创建三个名称的文件夹
os.mkdir(os.path.join(new_dir_name, win_dir_name))
os.mkdir(os.path.join(new_dir_name, mac_arm_dir_name))
os.mkdir(os.path.join(new_dir_name, mac_x64_dir_name))
os.mkdir(os.path.join(new_dir_name, linux_arm_dir_name))
os.mkdir(os.path.join(new_dir_name, linux_x64_dir_name))


# 打印创建成功的提示信息
print("mac文件夹创建成功！")
print("win文件夹创建成功！")
print("linux文件夹创建成功！")

# 截取date的后四位
new_date = date[-4:]

# 从package目录下的原始安装包生成发版文件和升级包文件
# linux-arm64：原始安装包为 deb，压缩为zip后改名
if 'linux_arm64' in raw_files:
    new_linux_arm64 = "灵犀·晓伴-" + version + "-标准版-" + new_date + "-linux-arm64.zip"
    new2_linux_arm64 = "gerenzhushou-" + version + "-standard-linux-arm64.zip"
    deliver(raw_files['linux_arm64'],
            os.path.join(new_dir_name, linux_arm_dir_name, new_linux_arm64),
            os.path.join(uppath, new2_linux_arm64))

# linux-x64：原始安装包为 deb，压缩为zip后改名
if 'linux_x64' in raw_files:
    new_linux_x64 = "灵犀·晓伴-" + version + "-标准版-" + new_date + "-linux-x64.zip"
    new2_linux_x64 = "gerenzhushou-" + version + "-standard-linux-x64.zip"
    deliver(raw_files['linux_x64'],
            os.path.join(new_dir_name, linux_x64_dir_name, new_linux_x64),
            os.path.join(uppath, new2_linux_x64))

# mac-arm64：原始安装包已经是zip，直接复制改名
if 'mac_arm64' in raw_files:
    new_mac_arm64 = "灵犀·晓伴-" + version + "-标准版-" + new_date + "-mac-arm64.zip"
    new2_mac_arm64 = "gerenzhushou-" + version + "-standard-darwin-arm64.zip"
    deliver(raw_files['mac_arm64'],
            os.path.join(new_dir_name, mac_arm_dir_name, new_mac_arm64),
            os.path.join(uppath, new2_mac_arm64))

# mac-x64：原始安装包已经是zip，直接复制改名
if 'mac_x64' in raw_files:
    new_mac_x64 = "灵犀·晓伴-" + version + "-标准版-" + new_date + "-mac-x64.zip"
    new2_mac_x64 = "gerenzhushou-" + version + "-standard-darwin-x64.zip"
    deliver(raw_files['mac_x64'],
            os.path.join(new_dir_name, mac_x64_dir_name, new_mac_x64),
            os.path.join(uppath, new2_mac_x64))

# win：原始安装包为 exe，压缩为zip后改名，版本号从文件名中提取
if 'win' in raw_files:
    win_version = re.findall(r'\d+\.\d+\.\d+', raw_files['win'])[0]
    print("win版本号为：" + win_version)
    new_win_x64 = "灵犀·晓伴-" + win_version + "-标准版-" + new_date + "-win-x64.zip"
    new2_win_x64 = "gerenzhushou-" + win_version + "-standard-win32-x64.zip"
    deliver(raw_files['win'],
            os.path.join(new_dir_name, win_dir_name, new_win_x64),
            os.path.join(uppath, new2_win_x64))

# 将help_documentation路径下的帮助说明文档“logo.png”分别复制到win_dir_name和mac_arm_dir_name和mac_x64_dir_name和linux_arm_dir_name和linux_x64_dir_name文件夹下
shutil.copy(os.path.join(helppath, "logo.png"), os.path.join(new_dir_name, win_dir_name, "logo.png"))
shutil.copy(os.path.join(helppath, "logo.png"), os.path.join(new_dir_name, mac_arm_dir_name, "logo.png"))
shutil.copy(os.path.join(helppath, "logo.png"), os.path.join(new_dir_name, mac_x64_dir_name, "logo.png"))
shutil.copy(os.path.join(helppath, "logo.png"), os.path.join(new_dir_name, linux_arm_dir_name, "logo.png"))
shutil.copy(os.path.join(helppath, "logo.png"), os.path.join(new_dir_name, linux_x64_dir_name, "logo.png"))

# 将help_documentation路径下的帮助说明文档“灵犀·晓伴 mac 版安装说明.docx”分别复制到mac_arm_dir_name和mac_x64_dir_name文件夹下
shutil.copy(os.path.join(helppath, "灵犀·晓伴 mac 版安装说明.docx"), os.path.join(new_dir_name, mac_arm_dir_name, "灵犀·晓伴 mac 版安装说明.docx"))
shutil.copy(os.path.join(helppath, "灵犀·晓伴 mac 版安装说明.docx"), os.path.join(new_dir_name, mac_x64_dir_name, "灵犀·晓伴 mac 版安装说明.docx"))

# 将help_documentation路径下的帮助说明文档“华为990+9006c芯片-麒麟2203及更早系统-gpu驱动一键升级-20251106.zip”分别复制到linux_arm_dir_name和linux_x64_dir_name文件夹下
shutil.copy(os.path.join(helppath, "华为990+9006c芯片-麒麟2203及更早系统-gpu驱动一键升级-20251106.zip"), os.path.join(new_dir_name, linux_arm_dir_name, "华为990+9006c芯片-麒麟2203及更早系统-gpu驱动一键升级-20251106.zip"))
shutil.copy(os.path.join(helppath, "华为990+9006c芯片-麒麟2203及更早系统-gpu驱动一键升级-20251106.zip"), os.path.join(new_dir_name, linux_x64_dir_name, "华为990+9006c芯片-麒麟2203及更早系统-gpu驱动一键升级-20251106.zip"))

# 将help_documentation路径下的帮助说明文档“zenity离线安装包.zip”分别复制到linux_arm_dir_name和linux_x64_dir_name文件夹下
shutil.copy(os.path.join(helppath, "zenity离线安装包.zip"), os.path.join(new_dir_name, linux_arm_dir_name, "zenity离线安装包.zip"))
shutil.copy(os.path.join(helppath, "zenity离线安装包(amd64)3.32.zip"), os.path.join(new_dir_name, linux_x64_dir_name, "zenity离线安装包(amd64)3.32.zip"))

# 将help_documentation路径下的帮助说明文档“苏晓伴 mac 版安装说明.docx”复制到mac_dir_name文件夹下
# shutil.copy(os.path.join(helppath, "苏晓伴 mac 版安装说明.docx"), os.path.join(new_dir_name, mac_dir_name, "苏晓伴 mac 版安装说明.docx"))

# 将help_documentation路径下的帮助说明文档“国产电脑使用苏晓伴说明.docx”复制到linux_dir_name文件夹下
# shutil.copy(os.path.join(helppath, "国产电脑使用苏晓伴说明.docx"), os.path.join(new_dir_name, linux_dir_name, "国产电脑使用苏晓伴说明.docx"))

# 将help_documentation路径下“releases.json”文件，复制到uppath路径下
shutil.copy(os.path.join(helppath, "releases.json"), os.path.join(uppath, "releases.json"))

# ============ 处理 upgrade_package/releases.json ============

releases_path = os.path.join(uppath, "releases.json")
content = open(releases_path, encoding="utf-8").read()

# 计数替换：将content中的old全部替换成new，并检查替换数量是否等于expected
def replace_and_check(content, old, new, expected, desc):
    count = content.count(old)
    if count != expected:
        print(f"错误：releases.json中{desc}的替换数量为{count}，预期{expected}，请检查模板文件")
        exit(1)
    return content.replace(old, new)

# 先把forceUpdateVersion的值保护成占位符，避免后续全局替换1.3.51时误伤
content = replace_and_check(content, '"forceUpdateVersion": "1.3.51"', '"forceUpdateVersion": "__FORCE_UPDATE__"', 1, 'forceUpdateVersion字段')

# 全局替换版本号：1.3.51（当前版本）→ version，预期11处（已排除forceUpdateVersion）
content = replace_and_check(content, "1.3.51", version, 11, '"1.3.51"')

# 全局替换版本号：1.3.50（旧版本）→ old_version，预期4处
content = replace_and_check(content, "1.3.50", old_version, 4, '"1.3.50"')

# 替换日期：旧版本发布日期
content = replace_and_check(content, "2026-07-21", format_date(last_version_date), 1, '旧版本日期"2026-07-21"')

# 替换日期：新版本发布日期
content = replace_and_check(content, "2026-07-23", format_date(date), 1, '新版本日期"2026-07-23"')

# 还原forceUpdateVersion的值为用户输入的强制更新版本
content = replace_and_check(content, "__FORCE_UPDATE__", force_update_version, 1, 'forceUpdateVersion占位符')

# 计算md5并按JSON结构更新files和setups的值
data = json.loads(content)

# files下的key就是upgrade_package下升级包文件名去掉.zip，逐个计算md5并更新
for key in data["files"]:
    zip_path = os.path.join(uppath, key + ".zip")
    if not os.path.exists(zip_path):
        print("错误：未找到升级包文件 " + zip_path)
        exit(1)
    data["files"][key] = compute_md5(zip_path)
    print("md5已更新：" + key + ".zip")

# setups的值更新为package下win原始安装包（suxiaoban-*-setup.exe）的md5
for key in data["setups"]:
    if 'win' not in raw_files:
        print("错误：package目录下未找到win安装包，无法更新setups的md5")
        exit(1)
    data["setups"][key] = compute_md5(os.path.join(pkgpath, raw_files['win']))
    print("md5已更新（setups）：" + key)

with open(releases_path, "w", encoding="utf-8") as f:
    f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

print("releases.json处理完成：" + releases_path)
