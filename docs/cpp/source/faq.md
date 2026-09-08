---
myst:
  html_meta:
    description: PyTorch C++ API 与 libtorch 常见问题解答。
    keywords: PyTorch, C++, FAQ, libtorch, troubleshooting
---

# 常见问题解答

> 🌐 本文档由 [pytorch/pytorch](https://github.com/pytorch/pytorch) 翻译,英文原版见原项目。

下面列出了用户在使用 C++ API 各部分时经常遇到的问题。

## C++ 扩展

### PyTorch/ATen 的未定义符号错误

**问题**:导入扩展时收到 `ImportError`,提示 PyTorch 或 ATen 的某个 C++ 符号未定义。例如:

```cpp
>>> import extension
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ImportError: /home/user/.pyenv/versions/3.7.1/lib/python3.7/site-packages/extension.cpython-37m-x86_64-linux-gnu.so: undefined symbol: _ZN2at19UndefinedTensorImpl10_singletonE
```

**修复**:在导入你的扩展之前先 `import torch`。这样扩展所依赖的 PyTorch 动态(共享)库中的符号就可用了,导入扩展时即可完成符号解析。

### 我用 `at::` 命名空间的函数创建了张量,然后报错

**问题**:你用 `at::ones`、`at::randn` 或 `at::` 命名空间中的其他张量工厂函数创建了张量,然后报错。

**修复**:把工厂函数调用中的 `at::` 替换为 `torch::`。永远不要使用 `at::` 命名空间的工厂函数,它们创建的是张量(tensor);对应的 `torch::` 函数创建的是变量(variable),你的代码里应该始终只使用变量。

## LibTorch

### 如何把模型移到 GPU 上?

**问题**:你想在 GPU 上运行模型,但不确定如何把模型和张量都移到正确的设备上。

**修复**:使用 `to()` 方法把模型和张量移到 CUDA 设备:

```cpp
torch::Device device(torch::kCUDA);
model->to(device);
auto input = torch::randn({1, 3, 224, 224}).to(device);
auto output = model->forward(input);
```

移动之前也可以先检查 CUDA 是否可用:

```cpp
torch::Device device(torch::cuda::is_available() ? torch::kCUDA : torch::kCPU);
```

确保包含 `<torch/script.h>` 以便编译时带有 TorchScript 头文件。

### 我的模型在 C++ 里比在 Python 里慢

**问题**:同样的模型推理,C++ 里比 Python 里慢。

**修复**:常见原因有以下几个:

1. **启用推理模式**:用 `torch::NoGradGuard` 包裹推理代码,禁用梯度计算:

```cpp
torch::NoGradGuard no_grad;
auto output = model->forward(input);
```

2. **启用优化**:对 TorchScript 模型,使用 `optimize_for_inference`:

```cpp
module = torch::jit::optimize_for_inference(module);
```

3. **预热模型**:正式跑分前先执行几次推理,让 JIT 编译与内存分配完成。

4. **检查线程设置**:确保线程配置合理:

```cpp
at::set_num_threads(4);  // 根据硬件调整
```

## 神经网络模块

### 如何在自定义模块中注册子模块?

**问题**:你写了自定义模块,但子模块在 `forward()` 执行期间或模型保存/加载时没有被识别。

**修复**:必须在构造函数中用 `register_module()` 注册子模块:

```cpp
struct MyModel : torch::nn::Module {
  MyModel() {
    fc1 = register_module("fc1", torch::nn::Linear(784, 128));
    fc2 = register_module("fc2", torch::nn::Linear(128, 10));
  }

  torch::Tensor forward(torch::Tensor x) {
    x = torch::relu(fc1->forward(x));
    return fc2->forward(x);
  }

  torch::nn::Linear fc1{nullptr}, fc2{nullptr};
};
```

### 如何把模块切换到评估模式?

**问题**:Dropout、BatchNorm 等层在训练与评估时行为不同,你需要在这两种模式之间切换。

**修复**:使用 `eval()` 和 `train()` 方法:

```cpp
model->eval();  // 切换到评估模式
// ... 执行推理 ...
model->train(); // 切回训练模式
```

## 数据加载

### 如何创建自定义数据集?

**问题**:你想加载自己的数据,而不是使用内置数据集。

**修复**:创建一个继承自 `torch::data::datasets::Dataset` 的类,并实现 `get()` 和 `size()` 方法:

```cpp
class CustomDataset : public torch::data::datasets::Dataset<CustomDataset> {
 public:
  explicit CustomDataset(const std::string& data_path) {
    // Load your data here
  }

  torch::data::Example<> get(size_t index) override {
    // Return a single data sample
    torch::Tensor data = /* load data at index */;
    torch::Tensor label = /* load label at index */;
    return {data, label};
  }

  torch::optional<size_t> size() const override {
    return dataset_size_;
  }

 private:
  size_t dataset_size_;
};
```

然后配合 DataLoader 使用:

```cpp
auto dataset = CustomDataset("path/to/data")
  .map(torch::data::transforms::Stack<>());
auto dataloader = torch::data::make_data_loader(
  std::move(dataset),
  torch::data::DataLoaderOptions().batch_size(32).workers(4));
```

## 序列化

### 如何保存和加载模型权重?

**问题**:你想保存训练好的模型权重,以便之后加载。

**修复**:使用 `torch::save()` 和 `torch::load()`:

```cpp
// Saving
torch::save(model, "model.pt");

// Loading
torch::load(model, "model.pt");
```

如果只保存特定的张量或状态:

```cpp
torch::serialize::OutputArchive archive;
model->save(archive);
archive.save_to("model_weights.pt");

// Loading
torch::serialize::InputArchive archive;
archive.load_from("model_weights.pt");
model->load(archive);
```

## 构建与编译

### CMake 找不到 Torch

**问题**:用 CMake 构建项目时报错,说找不到 `Torch` 包。

**修复**:需要通过 `CMAKE_PREFIX_PATH` 指定 LibTorch 的安装路径:

```cpp
cmake -DCMAKE_PREFIX_PATH=/path/to/libtorch ..
```

或者,把 `Torch_DIR` 指向包含 `TorchConfig.cmake` 的目录:

```cpp
cmake -DTorch_DIR=/path/to/libtorch/share/cmake/Torch ..
```

### 链接错误:未定义的引用

**问题**:项目可以编译,但链接时报 PyTorch 符号未定义的引用错误。

**修复**:确保在 `CMakeLists.txt` 中链接了所有必需的库:

```cpp
find_package(Torch REQUIRED)
add_executable(my_app main.cpp)
target_link_libraries(my_app "${TORCH_LIBRARIES}")
```

同时确保编译器标志设置正确:

```cpp
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${TORCH_CXX_FLAGS}")
```
