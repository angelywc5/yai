"""CUID 唯一标识符生成器。"""

from __future__ import annotations

from cuid2 import cuid_wrapper

# 创建全局 CUID 生成器实例
generate_cuid = cuid_wrapper()


def new_id() -> str:
    """生成新的 CUID。

    Returns:
        25 字符的 CUID 字符串，时间排序友好且碰撞概率极低。
    """
    return generate_cuid()
