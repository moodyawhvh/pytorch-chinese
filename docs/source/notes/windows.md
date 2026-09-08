# Windows 常见问题

> 🌐 本文档由 [pytorch/pytorch](https://github.com/pytorch/pytorch) 翻译,英文原版见原项目。

## 从源码构建

### 包含可选组件

Windows 版 PyTorch 支持两个可选组件:MKL 与 MAGMA。以下是启用它们构建的步骤:

```bat
REM Make sure you have 7z and curl installed.

REM Download MKL files
curl https://s3.amazonaws.com/ossci-windows/mkl_2020.2.254.7z -k -O
7z x -aoa mkl_2020.2.254.7z -omkl

REM Download MAGMA files
REM version available:
REM 2.5.4 (CUDA 10.1 10.2 11.0 11.1) x (Debug Release)
REM 2.5.3 (CUDA 10.1 10.2 11.0) x (Debug Release)
REM 2.5.2 (CUDA 9.2 10.0 10.1 10.2) x (Debug Release)
REM 2.5.1 (CUDA 9.2 10.0 10.1 10.2) x (Debug Release)
set "CUDA_PREFIX=cuda102"
set "CONFIG=release"
set "HOST=https://s3.amazonaws.com/ossci-windows"
curl -k "%HOST%/magma_2.5.4_%CUDA_PREFIX%_%CONFIG%.7z" -o magma.7z
7z x -aoa magma.7z -omagma

REM Setting essential environment variables
set "CMAKE_INCLUDE_PATH=%cd%\mkl\include"
set "LIB=%cd%\mkl\lib;%LIB%"
set "MAGMA_HOME=%cd%\magma"
```

### 加速 Windows 上的 CUDA 构建

Visual Studio 目前不支持并行的自定义任务。作为替代,我们可以用 `Ninja` 来并行化 CUDA 构建任务,只需几行代码即可启用:

```bat
REM Let's install ninja first.
pip install ninja

REM Set it as the cmake generator
set CMAKE_GENERATOR=Ninja
```

### 一键安装脚本

可以看看[这套脚本](https://github.com/peterjc123/pytorch-scripts),它会为你指路。

## 扩展(Extension)

### CFFI Extension

对 CFFI Extension 的支持还非常实验性。必须为 `Extension` 对象指定额外的 `libraries`,才能在 Windows 上构建:

```python
ffi = create_extension(
    '_ext.my_lib',
    headers=headers,
    sources=sources,
    define_macros=defines,
    relative_to=__file__,
    with_cuda=with_cuda,
    extra_compile_args=["-std=c99"],
    libraries=['ATen', '_C'] # Append cuda libraries when necessary, like cudart
)
```

### Cpp Extension

这类扩展相比上一种支持更好,但仍需要一些手动配置。首先,打开 **x86_x64 Cross Tools Command Prompt for VS 2017**,然后就可以开始编译流程了。

## 安装

### 在 win-32 通道中找不到包

```bat
Solving environment: failed

PackagesNotFoundError: The following packages are not available from current channels:

- pytorch

Current channels:
- https://repo.continuum.io/pkgs/main/win-32
- https://repo.continuum.io/pkgs/main/noarch
- https://repo.continuum.io/pkgs/free/win-32
- https://repo.continuum.io/pkgs/free/noarch
- https://repo.continuum.io/pkgs/r/win-32
- https://repo.continuum.io/pkgs/r/noarch
- https://repo.continuum.io/pkgs/pro/win-32
- https://repo.continuum.io/pkgs/pro/noarch
- https://repo.continuum.io/pkgs/msys2/win-32
- https://repo.continuum.io/pkgs/msys2/noarch
```

PyTorch 不支持 32 位系统,请使用 64 位的 Windows 和 Python。

### 导入错误

```python
from torch._C import *

ImportError: DLL load failed: The specified module could not be found.
```

该问题由关键文件缺失导致。对于 wheel 包,由于我们没有打包部分依赖库和 VS2017 运行时文件,请务必手动安装。[VS 2017 运行时安装器](https://aka.ms/vs/15/release/VC_redist.x64.exe)可在此下载。另外还要留意你的 NumPy 安装:确保它使用 MKL 而非 OpenBLAS,可以执行以下命令:

```bat
pip install numpy mkl intel-openmp mkl_fft
```

## 使用(multiprocessing)

### 缺少 if 子句保护导致的多进程错误

```python
RuntimeError:
       An attempt has been made to start a new process before the
       current process has finished its bootstrapping phase.

   This probably means that you are not using fork to start your
   child processes and you have forgotten to use the proper idiom
   in the main module:

       if __name__ == '__main__':
           freeze_support()
           ...

   The "freeze_support()" line can be omitted if the program
   is not going to be frozen to produce an executable.
```

`multiprocessing` 在 Windows 上的实现不同,使用 `spawn` 而非 `fork`。因此必须用 if 子句包裹代码,防止其被重复执行。把你的代码重构成如下结构:

```python
import torch

def main()
    for i, data in enumerate(dataloader):
        # do something here

if __name__ == '__main__':
    main()
```

### 多进程错误 "Broken pipe"

```python
ForkingPickler(file, protocol).dump(obj)

BrokenPipeError: [Errno 32] Broken pipe
```

该问题发生在子进程在父进程完成数据发送之前就结束了。可能是你的代码有问题。可以把 {class}`~torch.utils.data.DataLoader` 的 `num_worker` 降为 0 来调试,看问题是否仍然存在。

### 多进程错误 "driver shut down"

```text
Couldn't open shared file mapping: <torch_14808_1591070686>, error code: <1455> at torch\lib\TH\THAllocator.c:154

[windows] driver shut down
```

请更新显卡驱动。如果问题依旧,可能是显卡太旧,或计算对该卡来说太重。请按照这篇[文章](https://www.pugetsystems.com/labs/hpc/Working-around-TDR-in-Windows-for-a-better-GPU-computing-experience-777/)调整 TDR 设置。

### CUDA IPC 操作

```python
THCudaCheck FAIL file=torch\csrc\generic\StorageSharing.cpp line=252 error=63 : OS call failed or operation not supported on this OS
```

Windows 不支持 CUDA IPC 操作。比如对 CUDA 张量做多进程是无法成功的,有两种替代方案:

1. 不使用 `multiprocessing`。把 {class}`~torch.utils.data.DataLoader` 的 `num_worker` 设为 0。

2. 改为共享 CPU 张量。确保你的自定义 {class}`~torch.utils.data.DataSet` 返回 CPU 张量。
