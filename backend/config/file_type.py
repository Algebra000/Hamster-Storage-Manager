
#定义常见文件类型的后缀名

image_type_list = [
    'jpg', 'jpeg', 'png', 'apng', 'webp', 'gif', 'bmp', 'tiff', 'tif',
    'ico', 'svg', 'heic', 'heif', 'raw', 'psd', 'ai', 'eps',
    'nef', 'cr3', 'cr2',
    'arw', 'srf', 'sr2', 'arq',  # 索尼
    'raf',  # 富士
    'orf',  # 奥林巴斯
    'rw2',  # 松下
    'dng',  # Adobe 数字负片（通用 RAW）
    '3fr', 'fff',  # 哈苏
    'mef',  # 玛米亚
    'mrw',  # 美能达
    'pef',  # 宾得
    'pbm', 'pgm', 'ppm',  # Netpbm 格式（最简单）
    'pam' # Netpbm 任意深度扩展
]

video_type_list = [
    'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', 'm4v', 'mpg', 'mpeg',
    '3gp', 'ogv', 'ts', 'mts', 'vob', 'rm', 'rmvb', 'asf', 'f4v'
]

document_type_list = [
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'rtf',
    'odt', 'ods', 'odp', 'pages', 'numbers', 'key', 'epub', 'mobi',
     'md', 'csv', 'html'
]

sourcecode_type_list = [
    'c', 'cpp', 'h', 'hpp', 'java', 'js', 'php',
    'rb', 'go', 'rs', 'swift', 'kt', 'tsx', 'jsx', 'cs', 'vb',
    'pl', 'pm', 'scala', 'groovy', 'lua', 'dart', 'tex'
]

script_type_list = [
    'sh', 'bash', 'zsh', 'ps1', 'bat', 'cmd', 'vbs', 'ahk', 'py', 'rb',
    'pl', 'js', 'php', 'lua', 'tcl', 'css', 'r', 'm',
]

database_type_list = [
    'db', 'sqlite', 'sqlite3', 'mdb', 'accdb', 'frm', 'myd', 'myi',
    'dbf', 'mdf', 'ldf', 'sql', 'backup', 'dump'
]

config_type_list = [
    'json', 'xml', 'yaml', 'yml', 'toml', 'ini',
    'config', 'properties', 'env',
    'cfg', 'conf',
    'env', 'editorconfig', 'gitignore'
]

dataseg_type_list = [
    '','dat'
]

tempfile_type_list = [
    'tmp', 'temp', 'swp', 'swo', 'swn', 'bak', 'old', 'backup',
    '~', 'part', 'crdownload', 'download'
]

executable_type_list = [
    'exe', 'msi', 'app', 'dmg', 'pkg', 'deb', 'rpm', 'apk',
    'jar', 'com', 'scr', 'elf', 'bin'
]

shortcut_type_list = [
    'lnk', 'url', 'desktop', 'alias', 'appref-ms', 'pif'
]

zip_type_list = [
    'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'lz', 'lzma',
    'z', 'lz4', 'lzh', 'arc', 'arj', 'cab', 'dmg', 'iso',
    'img', 'vhd', 'vhdx', 'tgz', 'tbz2', 'txz'
]

fonts_type_list = [
    'ttf', 'otf', 'woff', 'woff2', 'eot', 'fon', 'fnt'
]

# 附加类别：音频文件
audio_type_list = [
    'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'aiff',
    'ape', 'opus', 'mid', 'midi', 'amr', 'ra', 'rm'
]

# 附加类别：系统文件
system_type_list = [
    'dll', 'sys', 'drv', 'vxd', 'ocx', 'cpl', '386', 'so', 'dylib',
    'ko', 'o', 'obj', 'lib', 'a', 'exp'
]

# 附加类别：虚拟机和容器
vm_type_list = [
    'vdi', 'vmdk', 'vhd', 'vhdx', 'ova', 'ovf', 'qcow2', 'vbox'
]



