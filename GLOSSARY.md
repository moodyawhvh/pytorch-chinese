# PyTorch 术语表

> 🌐 本文档由 [pytorch/pytorch](https://github.com/pytorch/pytorch) 翻译,英文原版见原项目。

<!-- toc -->

- [算子与 Kernel](#算子与-kernel)
  - [ATen](#aten)
  - [算子(Operation)](#算子operation)
  - [原生算子](#原生算子)
  - [自定义算子](#自定义算子)
  - [Kernel](#kernel)
  - [复合算子](#复合算子)
  - [组合算子](#组合算子)
  - [非叶子算子](#非叶子算子)
  - [叶子算子](#叶子算子)
  - [设备 Kernel](#设备-kernel)
  - [复合 Kernel](#复合-kernel)
- [JIT 编译](#jit-编译)
  - [JIT](#jit)
  - [TorchScript](#torchscript)
  - [Tracing(追踪)](#tracing追踪)
  - [Scripting(脚本化)](#scripting脚本化)

<!-- tocstop -->

# 算子与 Kernel

## ATen
"A Tensor Library" 的缩写。基础的张量与数学运算库,其余一切皆构建于其上。

## 算子(Operation)
一个工作单元。例如,矩阵乘法这项工作就是一个名为 aten::matmul 的算子。

## 原生算子
PyTorch ATen 自带的算子,例如 aten::matmul。

## 自定义算子
由用户定义的算子,通常是复合算子。例如,这份[教程](https://pytorch.org/docs/stable/notes/extending.html)详细介绍了如何创建自定义算子。

## Kernel
PyTorch 算子的实现,规定了算子执行时具体要做什么。

## 复合算子
由其他算子组合而成的算子。它的 kernel 通常与设备无关。它一般不定义自己的导数函数,而是由 AutoGrad 基于其使用的算子自动推导导数。

## 组合算子
与复合算子相同。

## 非叶子算子
与复合算子相同。

## 叶子算子
被视为基础运算的算子,与复合算子相对。叶子算子总是定义了 dispatch 函数,通常也定义了导数函数。

## 设备 Kernel
叶子算子面向特定设备的 kernel。

## 复合 Kernel
与设备 Kernel 相对,复合 kernel 通常与设备无关,属于复合算子。

# JIT 编译

## JIT
即时编译(Just-In-Time Compilation)。

## TorchScript
TorchScript JIT 编译器与解释器的接口。

## Tracing(追踪)
对函数使用 `torch.jit.trace`,得到一个可用即时编译优化的可执行体。

## Scripting(脚本化)
对函数使用 `torch.jit.script`,检查其源代码并将其编译为 TorchScript 代码。
