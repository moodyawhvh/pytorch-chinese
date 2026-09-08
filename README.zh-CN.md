# pytorch 中文文档

[![原项目](https://img.shields.io/badge/原项目-pytorch--pytorch-blue?style=flat-square&logo=github)](https://github.com/pytorch/pytorch)
[![微信联系](https://img.shields.io/badge/微信-uaycar-brightgreen?style=flat-square&logo=wechat)](#)

> 本文档是 [pytorch/pytorch](https://github.com/pytorch/pytorch) 官方 README 的中文翻译版,仅翻译章节标题、导语、使用说明与代表性条目,完整内容以原项目为准。原项目简介:Tensors and Dynamic neural networks in Python with strong GPU acceleration(带强大 GPU 加速的 Python 张量与动态神经网络)。

**代部署 / 定制服务 / 技术咨询 请添加微信:uaycar**

---

## 关于 PyTorch

PyTorch 是一个 Python 包,提供两大高级特性:

- 带强大 GPU 加速的张量计算(类似 NumPy)
- 基于磁带式(tape-based)自动求导系统的深度神经网络

你可以复用 NumPy、SciPy、Cython 等喜爱的 Python 包来扩展 PyTorch。主干健康状态(持续集成信号)见 [hud.pytorch.org](https://hud.pytorch.org/ci/pytorch/pytorch/main)。

从组件粒度看,PyTorch 由以下部分组成:

| 组件 | 说明 |
| ---- | ---- |
| [torch](https://pytorch.org/docs/stable/torch.html) | 类似 NumPy 的张量库,带强大 GPU 支持 |
| [torch.autograd](https://pytorch.org/docs/stable/autograd.html) | 磁带式自动微分库,支持 torch 中所有可微张量运算 |
| [torch.jit](https://pytorch.org/docs/stable/jit.html) | 编译栈(TorchScript),从 PyTorch 代码创建可序列化、可优化的模型 |
| [torch.nn](https://pytorch.org/docs/stable/nn.html) | 与 autograd 深度集成、面向最大灵活性的神经网络库 |
| [torch.multiprocessing](https://pytorch.org/docs/stable/multiprocessing.html) | Python 多进程,支持张量跨进程共享内存,适合数据加载与 Hogwild 训练 |
| [torch.utils](https://pytorch.org/docs/stable/data.html) | DataLoader 等实用工具 |

通常 PyTorch 有两种用法:作为 NumPy 的替代品来借用 GPU 的算力;或作为提供最大灵活性与速度的深度学习研究平台。

## 核心特性

- **GPU 就绪的张量库**:张量可在 CPU 或 GPU 上驻留,提供切片、索引、数学运算、线性代数、归约等大量算子,而且速度飞快。
- **动态神经网络**:多数框架(TensorFlow、Theano、Caffe、CNTK)采用静态图,改网络结构就得从头再来;PyTorch 用反向模式自动微分,零延迟、零开销地任意改变网络行为,且是迄今最快的实现之一。
- **Python 优先**:PyTorch 不是把 Python 绑定到一个庞大的 C++ 框架上,而是与 Python 深度集成,可以像用 NumPy / SciPy / scikit-learn 一样自然,还能配合 Cython、Numba 编写新层。
- **命令式体验**:代码执行即所见,没有异步视图;调试器、报错与堆栈跟踪直接指向代码定义位置,不再为糟糕的堆栈浪费数小时。
- **快速轻量**:框架开销极小,集成 Intel MKL 与 NVIDIA cuDNN、NCCL 加速库;CPU/GPU 后端成熟稳定;为 GPU 编写了自定义内存分配器,能训练比以往更大的模型。
- **无痛扩展**:用 Python 即可编写新网络层;想用 C/C++ 时也有高效、低样板代码的扩展 API,无需手写包装代码。

## 安装

### 二进制安装

通过 Conda 或 pip 安装二进制的命令,见官网:[https://pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/)。

NVIDIA Jetson 平台(Jetson Nano、TX1/TX2、Xavier NX/AGX、AGX Orin)的 Python wheel 由社区维护,需要 JetPack 4.2 及以上。

### 从源码构建

前置要求:

- Python 3.10 或更高版本
- 完整支持 C++20 的编译器(Linux 上需 gcc 11.3.0 或更新)
- Windows 需要 Visual Studio 或 Visual Studio Build Tools
- 至少 10 GB 可用磁盘空间;首次构建约需 30-60 分钟

获取源码:

```bash
git clone https://github.com/pytorch/pytorch
cd pytorch
# 如果是更新已有检出版本
git submodule sync
git submodule update --init --recursive
```

安装依赖(在 PyTorch 目录下执行):

```bash
pip install --group dev
```

可选硬件支持:

- **NVIDIA CUDA**:从官方支持矩阵选择受支持版本,安装 CUDA 与 cuDNN v9.0+;不想启用 CUDA 时导出 `USE_CUDA=0`。
- **AMD ROCm**:安装 ROCm 4.0+(仅支持 Linux),默认安装在 `/opt/rocm`,否则需设置 `ROCM_PATH`;禁用时导出 `USE_ROCM=0`。
- **Intel GPU**:按官方 Intel GPU 前置指引安装,支持 Linux 与 Windows;禁用时导出 `USE_XPU=0`。

编译安装(Linux/macOS):

```bash
python -m pip install --no-build-isolation -v -e .
```

Windows 的 CPU-only 构建同样使用上述 pip 命令;CUDA 构建需要 NVTX(随 CUDA 的 Nsight Compute 组件安装),并注意 MKL、OpenMP 等环境变量配置。更多细节见原仓库安装章节。

### Docker 镜像

拉取预构建镜像并运行(需 docker v23.0+):

```bash
docker run --gpus all --rm -ti --ipc=host pytorch/pytorch:latest
```

注意:PyTorch 通过共享内存在进程间共享数据,使用多进程数据加载时应通过 `--ipc=host` 或 `--shm-size` 增大共享内存。

自行构建镜像(同样要求 Docker >= 23.0,默认支持 CUDA 12.6 与 cuDNN v9):

```bash
make -f docker.Makefile
```

### 构建文档

需要 Sphinx 与 pytorch_sphinx_theme2,本地需先安装 torch:

```bash
cd docs/
pip install -r requirements.txt
make html
make serve
```

执行 `make` 可查看所有可用的输出格式;如遇 numpy 不兼容错误,运行 `pip install 'numpy<2'`。构建 PDF 需要安装 texlive/LaTeX,然后用 `make latexpdf` 生成。

历史版本的安装说明与二进制文件见官网 Previous Versions 页面。

## 入门与资源

快速上手入口:

- [Tutorials:官方教程,带你理解并使用 PyTorch](https://pytorch.org/tutorials/)
- [Examples:覆盖各领域的易懂示例代码](https://github.com/pytorch/examples)
- [API Reference:API 参考文档](https://pytorch.org/docs/)
- [Glossary:术语表](https://github.com/pytorch/pytorch/blob/main/GLOSSARY.md)

更多资源:[PyTorch.org](https://pytorch.org/)、[PyTorch Hub 模型库](https://pytorch.org/hub/)、[官方博客](https://pytorch.org/blog/)、[YouTube 频道](https://www.youtube.com/channel/UCWXI5YeOsh03QvJ59PMaXFw) 等。

## 社区交流

- 论坛:讨论实现与研究,https://discuss.pytorch.org
- GitHub Issues:Bug 报告、功能请求、安装问题、RFC 等
- Slack:[PyTorch Slack](https://pytorch.slack.com/),面向中高级用户与开发者的日常交流与协作
- 品牌规范见官网 [pytorch.org](https://pytorch.org/)

## 发布与贡献

PyTorch 通常每年发布三个次要版本。遇到 Bug 请提交 issue;Bug 修复的 PR 可以直接提交。计划贡献新特性或核心扩展时,请先开 issue 讨论——未经讨论直接发 PR 可能被拒绝。详见原仓库的 [CONTRIBUTING.md](https://github.com/pytorch/pytorch/blob/main/CONTRIBUTING.md) 与 [RELEASE.md](https://github.com/pytorch/pytorch/blob/main/RELEASE.md)。

PyTorch 是社区驱动的项目,由 Soumith Chintala 等核心维护者负责,并汇聚了数百位贡献者的力量。

## 许可证

PyTorch 采用 BSD 风格许可证(详见原仓库 LICENSE 文件)。本中文翻译文档不包含任何源代码,仅用于帮助中文读者理解原项目,版权与商标归原项目作者所有。

---

> 本项目为 [pytorch/pytorch](https://github.com/pytorch/pytorch) 的中文翻译版本,完整源代码请访问原项目:https://github.com/pytorch/pytorch

**代部署 / 定制服务 / 技术咨询 请添加微信:uaycar**

**如果觉得有用,请给原项目点个 Star!** ⭐
