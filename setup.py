# PyTorch is built with scikit-build-core through the PEP 517 interface
# declared in pyproject.toml; pip and `python -m build` never run this
# file. It exists only for direct `python setup.py <command>` calls:
# install and develop are forwarded to pip, everything else fails with
# instructions (#180248).
#
# 【中文注释】PyTorch 通过 pyproject.toml 中声明的 PEP 517 接口使用
# scikit-build-core 构建;pip 与 `python -m build` 不会执行本文件。
# 本文件仅服务于直接调用 `python setup.py <命令>` 的场景:
# install 和 develop 会被转发给 pip,其余命令则报错并给出指引(#180248)。
#
# Deprecation schedule:
#   PyTorch 2.14-2.15: install and develop forward to pip
#   PyTorch 2.16-2.17: all commands fail with instructions
#   PyTorch 2.18:      this file is removed
# 【中文注释】废弃时间表:
#   PyTorch 2.14-2.15:install 与 develop 转发给 pip(当前行为)
#   PyTorch 2.16-2.17:所有命令报错并给出指引
#   PyTorch 2.18:     移除本文件
#
# See https://github.com/pytorch/pytorch/issues/152276 for background.

import shlex
import subprocess
import sys
import warnings


# pip install 基础命令:使用当前解释器,关闭构建隔离,输出详细信息
PIP_INSTALL = [sys.executable, "-m", "pip", "install", "-v", "--no-build-isolation"]
# 允许转发的命令映射:install -> 普通安装;develop -> 可编辑(-e)安装
FORWARDS = {
    "install": [*PIP_INSTALL, "."],
    "develop": [*PIP_INSTALL, "-e", "."],
}

# 废弃提示模板:说明 setup.py 已退出构建流程,并给出替代命令
DEPRECATION_NOTICE = """\
`python setup.py {command}` is deprecated: PyTorch is built with
scikit-build-core via the standard PEP 517 interface (pyproject.toml),
and setup.py is no longer part of the build.

Deprecation schedule:
  PyTorch 2.14-2.15: install and develop forward to pip
                     (current behavior); other commands fail
  PyTorch 2.16-2.17: all commands fail with instructions
  PyTorch 2.18:      setup.py is removed

Replacement commands:
  install:           spin install  (or: pip install --no-build-isolation -v .)
  editable install:  spin develop  (or: pip install --no-build-isolation -v -e .)
  wheel:             python -m build --wheel --no-isolation
  sdist:             python -m build --sdist

Build customization through environment variables (DEBUG=1, USE_CUDA=0,
MAX_JOBS=..., etc.) works unchanged with the replacement commands. See
the "From Source" section of README.md for details and
https://github.com/pytorch/pytorch/issues/152276 for background.
"""


def main() -> int:
    # 取第一个命令行参数作为子命令;缺省时用占位符生成报错信息
    command = sys.argv[1] if len(sys.argv) > 1 else "<command>"
    notice = DEPRECATION_NOTICE.format(command=command)
    # 查询该命令是否允许转发给 pip
    replacement = FORWARDS.get(command)
    if replacement is None:
        # 不在白名单内的命令直接失败,打印废弃提示
        raise SystemExit(f"error: {notice}")
    # install/develop:先发出废弃警告,再转发给 pip 执行
    warnings.warn(notice, DeprecationWarning)
    if len(sys.argv) > 2:
        # setup.py 时代的附加参数一概忽略
        warnings.warn(f"ignoring extra arguments: {shlex.join(sys.argv[2:])}")
    print(f"Forwarding to `{shlex.join(replacement)}`.", file=sys.stderr)
    # 透传 pip 的退出码,保持与原安装命令一致的语义
    return subprocess.run(replacement).returncode


if __name__ == "__main__":
    sys.exit(main())
