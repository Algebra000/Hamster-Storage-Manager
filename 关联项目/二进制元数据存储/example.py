"""运行：python example.py；无需 pip 安装，输出文件放在本脚本旁。"""

from pathlib import Path
from pprint import pprint

import umsgpack


ROOT = Path(__file__).resolve().parent


def save(path: Path, data: dict) -> None:
    """先写临时文件再替换；适用于本样例的单进程写入。"""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(umsgpack.packb(data))
    temporary.replace(path)


def load(path: Path) -> dict:
    return umsgpack.unpackb(path.read_bytes())


def main() -> None:
    original = {
        "名称": "仓鼠资源包",
        "版本": 1,
        "启用": True,
        "备注": None,
        "比例": 1.25,
        "封面": b"\x00\xff\x80\x01",
        "资源": [
            {
                "名称": "原始字节",
                "内容": bytes(range(256)),  # 包含全部可能的单字节值
                "属性": {"标签": ["测试", "二进制"], "尺寸": [16, 16]},
            },
            {"名称": "空资源", "内容": b""},
        ],
        "混合列表": [1, "文本", False, None, b"\x00\xff", [b"nested", {}]],
        "空值集合": {"对象": {}, "列表": [], "文本": "", "二进制": b""},
    }

    # 1. 创建文件，再一次性加载成 dict。
    original_path = ROOT / "sample.msgpack"
    save(original_path, original)
    restored = load(original_path)
    assert restored == original, "往返读写后数据发生变化"
    assert isinstance(restored, dict)
    assert isinstance(restored["资源"], list)
    assert isinstance(restored["资源"][0]["内容"], bytes)
    assert isinstance(restored["混合列表"][5][0], bytes)
    assert restored["空值集合"]["二进制"] == b""
    assert isinstance(restored["空值集合"]["二进制"], bytes)

    # 2. 修改嵌套二进制值、添加列表元素，另存为文件。
    restored["版本"] = 2
    restored["资源"][0]["内容"] = b"\x10\x20\x30\x00\xff"
    restored["资源"].append({"名称": "新增资源", "内容": b"new payload"})
    edited_path = ROOT / "sample_edited.msgpack"
    save(edited_path, restored)
    edited = load(edited_path)
    assert edited == restored, "编辑保存后数据发生变化"
    assert load(original_path) == original, "原始样例不应被编辑操作覆盖"

    print(f"u-msgpack-python {umsgpack.__version__}")
    print("PASS: nested maps/lists, mixed lists, all 256 byte values, empty values")
    print("PASS: edit, save and reload")
    for path in (original_path, edited_path):
        print(f"{path.name}: {path.stat().st_size} bytes")
    pprint(edited, sort_dicts=False)


if __name__ == "__main__":
    main()
