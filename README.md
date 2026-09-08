<div align="center">

# pytorch 中文翻译版

**[中文版] pytorch — 基于 Python 的张量计算与动态神经网络深度学习框架,提供强大的 GPU 加速**

[![原项目](https://img.shields.io/badge/原项目-pytorch--pytorch-blue?style=flat-square&logo=github)](https://github.com/pytorch/pytorch)
[![中文文档](https://img.shields.io/badge/中文文档-README.zh--CN.md-orange?style=flat-square)](README.zh-CN.md)
[![GitHub Stars](https://img.shields.io/github/stars/pytorch/pytorch?style=flat-square&label=原项目Stars)](https://github.com/pytorch/pytorch/stargazers)
[![微信联系](https://img.shields.io/badge/微信-uaycar-brightgreen?style=flat-square&logo=wechat)](#)

</div>

---

> 这是 [pytorch/pytorch](https://github.com/pytorch/pytorch) 的中文翻译版本。
> 完整源代码请访问原项目:https://github.com/pytorch/pytorch

**代部署 / 定制服务 / 技术咨询 请添加微信:uaycar**

---

## 📖 项目简介

PyTorch 是目前最主流的开源深度学习框架之一,由 Python 包提供两大核心能力:类似 NumPy 的张量计算(带强大 GPU 加速),以及基于"磁带式"自动求导系统的动态神经网络。它对 Python 生态深度友好,可以像使用 NumPy / SciPy 一样自然地使用它,并随时复用 NumPy、SciPy、Cython 等你喜爱的 Python 库进行扩展。无论是科研原型还是生产部署,PyTorch 都是灵活性与速度兼顾的首选。

## ✨ 主要特性

- **GPU 就绪的张量库**:张量可驻留在 CPU 或 GPU 上,提供切片、索引、数学运算、线性代数、归约等丰富的算子,计算速度极快。
- **动态神经网络(磁带式 Autograd)**:采用反向模式自动微分,可零延迟地任意改变网络行为,完美支持各种"疯狂"的研究想法。
- **Python 优先**:不是 C++ 框架的 Python 绑定,而是与 Python 深度集成,可直接用 Python 编写新的网络层。
- **命令式体验**:代码即执行,没有异步黑盒;调试器和堆栈信息直观指向你的代码定义处。
- **快速且轻量**:集成 Intel MKL、NVIDIA cuDNN、NCCL 等加速库,自定义 GPU 内存分配器,内存效率极高。
- **无痛扩展**:新模块可用 Python 直接编写,也提供简洁的 C/C++ 扩展 API,几乎无需样板代码。
- **完整的生态**:torch、torch.autograd、torch.jit(TorchScript)、torch.nn、torch.multiprocessing、torch.utils 等组件一应俱全。

## 📁 文件说明

| 文件 | 说明 |
|:-----|:-----|
| README.md | 本文件(中文简介) |
| README.zh-CN.md | 详细中文文档(完整汉化) |

## 🚀 快速开始

1. 用 pip 或 conda 安装最新稳定版(推荐访问官网选择你的平台):

```bash
pip install torch
```

2. 或从 Docker Hub 拉取预构建镜像直接运行:

```bash
docker run --gpus all --rm -ti --ipc=host pytorch/pytorch:latest
```

3. 验证安装,跑一个最简单的张量运算:

```python
import torch
x = torch.rand(5, 3)
print(x)
```

4. 想从源码构建,先克隆仓库并初始化子模块:

```bash
git clone https://github.com/pytorch/pytorch
cd pytorch
git submodule sync
git submodule update --init --recursive
```

5. 安装依赖后本地安装(以 Linux/macOS 为例):

```bash
python -m pip install --no-build-isolation -v -e .
```

6. 跟着官方教程入门:https://pytorch.org/tutorials/

完整源代码与最新版本请访问原项目:https://github.com/pytorch/pytorch

## 📞 联系方式

**代部署 / 定制服务 / 技术咨询 请添加微信:uaycar**

---

本项目为 [pytorch/pytorch](https://github.com/pytorch/pytorch) 的中文翻译版本,所有代码版权归原项目作者所有,遵循其原始许可证。

**如果觉得有用,请给原项目点个 Star!** ⭐
