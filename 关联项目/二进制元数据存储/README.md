# MessagePack 二进制元数据存储样例

无需安装第三方包，使用 Python 3 运行本目录的 `example.py` 即可。

在项目根目录运行：

```powershell
python "关联项目/二进制元数据存储/example.py"
```

脚本会在自身所在目录生成或覆盖两个演示文件：

- `sample.msgpack`：包含中文、数字、布尔值、空值、嵌套字典、混合列表和原始二进制。
- `sample_edited.msgpack`：修改嵌套二进制内容并添加资源后的版本。

示例通过断言验证读写一致性及二进制类型。二进制使用 Python `bytes`，
不需要 Base64；解码得到普通 `dict` / `list` / `bytes` 等对象。
编辑流程是全量加载、修改内存对象、重新编码保存，不是原地修改磁盘字段。
打印出来的 `b'\x00...'` 只是 Python 的显示形式，文件中保存的是原始字节。

## 集成

将 `umsgpack.py` 放在可导入的位置，并保留其中的 MIT 许可声明及附带许可证：

```python
import umsgpack

encoded = umsgpack.packb({"items": [{"data": b"\x00\xff"}]})
decoded = umsgpack.unpackb(encoded)
assert decoded["items"][0]["data"] == b"\x00\xff"
```

这份实现是纯 Python 单文件版；本样例验证功能，不代表加载性能基准。

## 上游记录

- 项目：https://github.com/vsergeev/u-msgpack-python
- 源码：https://raw.githubusercontent.com/vsergeev/u-msgpack-python/master/umsgpack/__init__.py
- 许可证：https://raw.githubusercontent.com/vsergeev/u-msgpack-python/master/LICENSE
- 下载日期：2026-10-20
- 源码自报版本：2.8.0
- 源码大小：43,617 字节
- 下载来源为 master 快照，未经修改；并非通过发布 API 确认的最新发行版。
- `umsgpack.py` SHA-256：`5A3D2E8428309C6142E9FFCDC060A2D21DB480878B33D9401BC4F3762BFEF233`
