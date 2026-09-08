# 为 PyTorch 做贡献(Contributing to PyTorch)

> 🌐 本文档由 [pytorch/pytorch](https://github.com/pytorch/pytorch) 翻译,英文原版见原项目。
> 说明:本文件超过 1 万字符,此处仅翻译核心章节(开发环境、代码库结构、单元测试、合入流程等),完整英文原版见 [CONTRIBUTING.en.md](CONTRIBUTING.en.md);未翻译章节含 GreenLight、文档编写、性能分析、C++/CUDA/Windows 开发技巧、ASAN 构建、CI 排错等。

感谢你有兴趣为 PyTorch 做贡献!
如果你是新贡献者,请先阅读我们的[贡献指南](https://github.com/pytorch/pytorch/wiki/The-Ultimate-Guide-to-PyTorch-Contributions),特别是[提交变更](https://github.com/pytorch/pytorch/wiki/The-Ultimate-Guide-to-PyTorch-Contributions#submitting-a-change)一节,它完整介绍了向 PyTorch 贡献变更的流程。

本文档(CONTRIBUTING.md)其余部分涵盖向 PyTorch 贡献时更偏技术的内容。

# 开发 PyTorch

按照[从源码安装 PyTorch](https://github.com/pytorch/pytorch#from-source) 的说明操作。如果在本地开发 PyTorch 时卡住了,请查看下方[技巧与调试](#技巧与调试)一节的常见解决方案。

## 技巧与调试

* 如果你想要快速的 no-op 增量重建,见下方[让 no-op 构建提速](https://github.com/pytorch/pytorch/blob/main/CONTRIBUTING.en.md#make-no-op-build-fast)。

* 使用 `python -m pip install -e . -v --no-build-isolation` 安装时(区别于 `python -m pip install . -v --no-build-isolation`),Python 运行时导入 `torch` 包时会使用当前本地源码树(这是通过在 `site-packages` 中安装一个 import hook 实现的,它把 `torch` 的 Python 模块重定向到源码树;编译产物不会被重定向)。这样修改 Python 文件(`.py`)后无需反复重新安装。但如果你修改了 Python 接口文件(`.pyi`、`.pyi.in`)或非 Python 文件(`.cpp`、`.cc`、`.cu`、`.h` 等),则需要重新安装。

  在 Linux/Mac 上,避免每次修改 C++/CUDA/ObjectiveC 文件都重跑 `python -m pip install -e . -v --no-build-isolation` 的一个办法,是从 `build` 目录到 `torch/lib` 创建符号链接,例如:
  ```bash
  pushd torch/lib; sh -c "ln -sf ../../build/lib/libtorch_cpu.* ."; popd
  ```
  之后重新构建库(例如在 `build` 目录执行 `ninja torch_cpu` 重建 `libtorch_cpu.so`),改动即可在 `torch` 包中生效。

  另外,scikit-build-core 的可编辑安装可以在进程内首次 `import torch` 时自动重建项目。该功能默认关闭(普通可编辑安装不会在 import 时重建);安装时设置 `SKBUILD_EDITABLE_REBUILD` 环境变量即可启用:
  ```bash
  SKBUILD_EDITABLE_REBUILD=true spin develop
  ```
  (等价地,通过原始 pip 安装的 config-settings:
  `python -m pip install -e . -v --no-build-isolation -C editable.rebuild=true`)。
  启用后,编辑源文件并重新导入 `torch` 时会在导入前运行 `cmake --build & --install`,改动无需显式重装即被采纳。设置 `SKBUILD_EDITABLE_VERBOSE=1` 可查看构建输出,`=0` 可静默。


  如需重装,先卸载所有已存在的 PyTorch 安装。可能需要多次运行 `pip uninstall torch`。当你看到 `WARNING: Skipping torch as it is not installed` 时,说明 `torch` 已彻底卸载。

  ```bash
  pip uninstall torch
  ```

  然后运行 `spin clean`。之后即可再次以可编辑模式安装。

* 如果运行 `python -m pip install -e . -v --no-build-isolation` 时出错,可按以下步骤调试:
  1. 运行 `printf '#include <stdio.h>\nint main() { printf("Hello World");}'|clang -x c -; ./a.out`,确认 CMake 正常且能无误编译这个简单的 Hello World 程序。
  2. 清空你的 `build` 目录。构建过程会把二进制编译进 `build` 目录并缓存大量细节,以便下次构建提速。遇到问题时,随时可以在 pytorch 顶层目录 `rm -rf build` 重来。
  3. 如果你改过 PyTorch 仓库,先 commit 想保留的改动,然后用以下命令清理仓库(注意 clean 会*真的*删除所有未跟踪文件和改动):
      ```bash
      git submodule deinit -f .
      git clean -xdf
      spin clean
      git submodule update --init --recursive
      python -m pip install --group dev
      python -m pip install --no-build-isolation -v -e .
      ```
  4. `python -m pip install -e . -v --no-build-isolation` 的核心步骤是在 `build` 目录中执行 CMake 构建(默认为 `ninja`)。如果想试验环境变量,可以直接传入命令(可转发的环境变量见 [`cmake/EnvVarForwarding.cmake`](./cmake/EnvVarForwarding.cmake)):
      ```bash
      ENV_KEY1=ENV_VAL1[, ENV_KEY2=ENV_VAL2]* python -m pip install --no-build-isolation -v -e .
      ```
  5. 尝试在 `pip install` 命令中加 `--no-build-isolation` 以关闭构建隔离,使用当前环境的包而非为构建新建隔离环境。
      ```bash
      python -m pip install --no-build-isolation -v -e .
      ```

* 如果运行 `git submodule update --init --recursive` 出错,请尝试:
  - 如果遇到类似
    ```
    error: Submodule 'third_party/pybind11' could not be updated
    ```
    的错误,检查 Git 本地或全局配置文件里是否有 `submodule.*` 设置。有则删除后重试(更多信息参见[此文档](https://git-scm.com/docs/git-config#Documentation/git-config.txt-submoduleltnamegturl))。

  - 如果遇到类似
    ```
    fatal: unable to access 'https://github.com/pybind/pybind11.git': could not load PEM client certificate ...
    ```
    的错误,很可能是你在使用 HTTP 代理且证书过期。运行 `git config --global --list` 查找 `http.proxysslcert=<cert_file>` 之类的配置,然后用以下命令检查证书有效期:
    ```bash
    openssl x509 -noout -in <cert_file> -dates
    ```

  - 如果遇到某些 third_party 模块未正确检出的错误,例如
    ```
    Could not find .../pytorch/third_party/pybind11/CMakeLists.txt
    ```
    请删除本地 git 配置(pytorch 仓库的 `.git/config`)中的 `submodule.*` 设置后重试。
* 如果你是 Windows 贡献者,请查看[最佳实践](https://github.com/pytorch/pytorch/wiki/Best-Practices-to-Edit-and-Compile-Pytorch-Source-Code-On-Windows)。
* 贡献流程的任何环节需要帮助,欢迎参加我们的 Zoom office hours!详情见[这里](https://github.com/pytorch/pytorch/wiki/Dev-Infra-Office-Hours)。

## Nightly 检出与拉取

`tools/nightly.py` 脚本用于简化 PyTorch 的纯 Python 开发。它使用 `venv` 和 `git` 检出 PyTorch 的 nightly 开发版本,并把预构建二进制安装到当前仓库。类似开发/可编辑安装,但无需编译任何 C++ 代码。

用以下命令检出新的 nightly 分支:

```bash
./tools/nightly.py checkout -b my-nightly-branch
source venv/bin/activate  # Windows 上用 `. .\venv\Scripts\activate`
```

要安装带 CUDA 构建的 nightly 二进制,传入 `--cuda` 标志:

```bash
./tools/nightly.py checkout -b my-nightly-branch --cuda
source venv/bin/activate  # Windows 上用 `. .\venv\Scripts\activate`
```

要安装带 ROCm 构建的 nightly 二进制,传入 `--rocm` 标志:

```bash
./tools/nightly.py checkout -b my-nightly-branch --rocm
source venv/bin/activate  # Windows 上用 `. .\venv\Scripts\activate`
```

也可以用该工具把 nightly 提交拉取到当前分支:

```bash
./tools/nightly.py pull
source venv/bin/activate  # Windows 上用 `. .\venv\Scripts\activate`
```

要指定 Python 解释器创建虚拟环境,传入 `--python` 参数:

```bash
./tools/nightly.py --python /path/to/python3.12
source venv/bin/activate  # Windows 上用 `. .\venv\Scripts\activate`
```

pull 会重建全新的虚拟环境,并把开发依赖和 nightly 二进制重装到仓库目录。

## 代码库结构

* [c10](c10) - 在服务器与移动端通用的核心库文件。我们正把 [ATen/core](aten/src/ATen/core) 中的组件逐步迁移至此。该库只打算包含最基本的功能,适用于在意二进制体积的场景(但直接使用会缺少大量功能)。
* [aten](aten) - PyTorch 的 C++ 张量库(不含 autograd 支持)
  * [src](aten/src) - [README](aten/src/README.md)
    * [ATen](aten/src/ATen)
      * [core](aten/src/ATen/core) - ATen 核心功能,正在向顶层 c10 目录迁移。
      * [native](aten/src/ATen/native) - 算子的现代实现。想写新算子,放这里。多数 CPU 算子放在顶层目录,需要特殊编译的算子除外(见下述 cpu 目录)。
        * [cpu](aten/src/ATen/native/cpu) - 并非算子的 CPU 实现,而是特指使用 AVX 等处理器特定指令编译的实现。详见[README](aten/src/ATen/native/cpu/README.md)。
        * [cuda](aten/src/ATen/native/cuda) - 算子的 CUDA 实现。
        * [mps](aten/src/ATen/native/mps) - 面向 Apple Metal GPU 家族的算子 MPS 实现。
        * [sparse](aten/src/ATen/native/sparse) - COO 稀疏张量运算的 CPU 与 CUDA 实现。
        * [mkl](aten/src/ATen/native/mkl) [mkldnn](aten/src/ATen/native/mkldnn)
          [miopen](aten/src/ATen/native/miopen) [cudnn](aten/src/ATen/native/cudnn)
          - 仅绑定到某个后端库的算子实现。
        * [quantized](aten/src/ATen/native/quantized/) - 量化张量(即 QTensor)运算实现。[README](aten/src/ATen/native/quantized/README.md) 介绍了如何实现原生量化运算等细节。
* [torch](torch) - PyTorch 本体库。[csrc](torch/csrc) 之外的一切都是 Python 模块,遵循 PyTorch Python 前端模块结构。
  * [csrc](torch/csrc) - 构成 PyTorch 库的 C++ 文件。此目录树中既有 Python 绑定代码(惯例以 `python_` 为前缀),也有重量级 C++ 实现。[README](torch/csrc/README.md)
    * [jit](torch/csrc/jit) - TorchScript JIT 前端的编译器与前端。[README](torch/csrc/jit/README.md)
    * [autograd](torch/csrc/autograd) - 反向模式自动微分的实现。[README](torch/csrc/autograd/README.md)
    * [api](torch/csrc/api) - PyTorch C++ 前端。
    * [distributed](torch/csrc/distributed) - PyTorch 的分布式训练支持。
* [tools](tools) - PyTorch 库的代码生成脚本,详见该目录 [README](tools/README.md)。
* [torchgen](torchgen) - 包含从算子定义(通常写在 native_functions.yaml)生成 PyTorch 底层 C++ 与 Python 绑定的逻辑和工具。
* [test](test) - PyTorch Python 前端的单元测试。
  * [test_torch.py](test/test_torch.py) - PyTorch 基础功能测试。
  * [test_autograd.py](test/test_autograd.py) - 非 NN 自动微分支持测试。
  * [test_nn.py](test/test_nn.py) - NN 算子及其自动微分测试。
  * [test_jit.py](test/test_jit.py) - JIT 编译器与 TorchScript 测试。
  * ...
  * [cpp](test/cpp) - PyTorch C++ 前端的 C++ 单元测试。
    * [api](test/cpp/api) - [README](test/cpp/api/README.md)
    * [jit](test/cpp/jit) - [README](test/cpp/jit/README.md)
  * [expect](test/expect) - 自动生成的"expect"文件,用于与期望输出比对。
  * [onnx](test/onnx) - ONNX 导出功能测试,同时覆盖 PyTorch 与 Caffe2。
* [caffe2](caffe2) - Caffe2 库。
  * [core](caffe2/core) - Caffe2 核心文件,如 tensor、workspace、blob 等。
  * ...

## AI 辅助开发

详见 PyTorch 的[AI 使用政策](AI_POLICY.md)。

如何贡献(无论是否借助 AI)的全部细节都在 [PyTorch 贡献终极指南](https://github.com/pytorch/pytorch/wiki/The-Ultimate-Guide-to-PyTorch-Contributions)。这里再提醒几点:

- **你对你发送的内容负个人责任**:如果你发出的评论、issue 或 PR 质量低下,或相比预期持续过度冗长,你的贡献将不再被接受。你有责任审阅并保证你所发送的一切内容的准确性和质量。
- **PR 必须关联一个"actionable"的 Issue**:一般来说,新贡献者绝不应在没有对应 "actionable" 标签 issue 的情况下发送 PR。如果你刚开了这个 issue,必须等维护者评审并将其标记为 actionable 之后,才能为它准备并发送 PR。
- **新特性、工具函数或核心扩展**:针对你遇到的问题创建一个简短扼要的 issue。绝不要在 issue 中附上 AI 生成的解决方案说明(解决方案将在决定实现该特性之后再讨论)。

## Spin

[Spin](https://github.com/scientific-python/spin) 是一个帮助运行常见任务的开发者 CLI 工具。可以用 `pip install spin` 装进开发环境,或用 `uv tool install spin --with=packaging,pyyaml,typing_extensions` 作为全局 uv 工具安装。

运行 `spin --help` 列出可用任务。目前 Spin 支持以下任务:

### 构建

为支持构建与日常开发,提供以下命令。`develop` 和 `install` 在可用时优先使用 `uv pip`,否则回退到普通 pip。构建配置照常来自环境变量,如 `BUILD_CONFIG spin develop`。

|命令|说明|
|-|-|
|`develop` / `editable`|可编辑安装(即 develop 或 `-e` 安装)|
|`install`|非可编辑安装|
|`clean`|清理,即删除 .gitignore 中列出、且位于 NOT-CLEAN-FILES 标记之前的文件和目录|

### Lint

Spin 通过确保 lintrunner 正确安装,并用 uv 将 lintrunner 环境与日常开发环境隔离,来辅助 lint。可在双连字符(`--`)之后向 lintrunner 传递附加参数,例如 `spin quicklint -- --take CLANGTIDY`。

|命令|说明|
|-|-|
|`lint`|执行默认 lint(见下)|
|`quicklint`|对最近一次提交和当前工作目录中所有变更文件执行 lint|
|`quickfix`|自动修复最近一次提交和当前工作目录中所有变更文件的问题|

#### 默认 lint

由于部分 linter 运行耗时较长,我们把所有 linter 分为快、慢两类。默认 lint 只在所有文件上运行快 linter,慢 linter 只对变更文件运行。

### 重新生成

PyTorch 使用了大量代码生成,涵盖从 `torch/version.py` 的版本信息、类型 stub 与其他 linter 支持到 github workflows。通过 Spin,我们为这些任务提供统一接口。

|命令|说明|
|-|-|
|`regenerate-version`|重新生成 `torch/version.py`|
|`regenerate-type-stubs`|重新生成供静态类型检查器使用的类型 stub|
|`regenerate-clangtidy-files`|重新生成 lint 所需的 clang 相关文件|
|`regenerate-github-workflows`|从 jinja 模板重新生成 github workflows|

## 单元测试

### Python 单元测试

**前置条件**:
以下包应通过 `pip` 安装:
- `expecttest` 与 `hypothesis` - 运行测试必需
- `pyrefly` - 推荐用于类型检查。[Pyrefly](https://pyrefly.org/)
- `pytest` - 推荐用于更精细地选择运行测试
运行
```
pip install --group dev
```
即可安装这些依赖。

所有 PyTorch 测试套件都位于 `test` 目录,并以 `test_` 开头。用以下命令运行整个测试套件:

```bash
python test/run_test.py
```

或用命令 `python test/FILENAME.py` 运行单个测试套件,其中 `FILENAME` 为你想运行的测试套件所在文件名。

例如,要运行所有 TorchScript JIT 测试(位于 `test/test_jit.py`):

```bash
python test/test_jit.py
```

可以用 `TESTCLASSNAME.TESTNAME` 进一步缩小测试范围。其中 `TESTNAME` 是要运行的测试名,`TESTCLASSNAME` 是定义它的类名。

接着上例,假设要运行 `test/test_jit.py` 中 `TestJit` 类里的 `test_Sequential`,命令为:

```bash
python test/test_jit.py TestJit.test_Sequential
```

**奇怪的一点**:在我们的 CI(持续集成)任务中,实际上是从 `test` 目录而非仓库根目录运行测试,因为 CI 设置的诸多依赖假定测试从 test 目录运行。因此本地测试与 CI 测试之间可能存在一些不一致——如果你观察到不一致,请[提交 issue](https://github.com/pytorch/pytorch/issues/new/choose)。

### 用 `pytest` 改善本地单元测试

我们不官方支持 `pytest`,但它与我们的 `unittest` 测试配合良好,并为本地开发提供不少有用特性。通过 `pip install pytest` 安装。

如果想只运行名称包含特定子串的测试,可用 `-k` 标志:

```bash
pytest test/test_nn.py -k Loss -v
```

上例是测试所有 Loss 函数变更的方式:该命令会运行 `TestNN.test_BCELoss`、`TestNN.test_MSELoss` 等测试,能省下不少输入。

### 本地 lint

可以在本地通过 `make` 运行与 CI 相同的 lint 步骤:

```bash
make lint
```

在 [lintrunner wiki 页面](https://github.com/pytorch/pytorch/wiki/lintrunner)了解更多关于 linter 的信息。

#### 运行 `pyrefly`

[Pyrefly](https://pyrefly.org/) 是一个高性能 Python 静态类型检查器,提供快速类型检查以及自动补全、即时错误反馈等 IDE 特性。

PyTorch 使用 Pyrefly 对整个代码库做类型检查,配置由仓库根目录的 `pyrefly.toml` 管理。

**Pyrefly 入门:**

对 PyTorch 代码库运行类型检查:
```bash
pyrefly check
```

需要带汇总的更详细错误信息:
```bash
pyrefly check --summarize-errors
```

**了解更多:**
- [Pyrefly 配置](https://pyrefly.org/en/docs/configuration/) - 详细的配置选项
- [Pyrefly IDE 特性](https://pyrefly.org/en/docs/IDE-features/) - 在编辑器中设置 Pyrefly 以获得实时类型检查
- [Python 类型标注教程](https://pyrefly.org/en/docs/typing-for-python-developers/) - 学习 Python 类型标注

关于如何设置 `pyrefly` 并在此代码库中完成类型标注任务的 PyTorch 专属指引,参见[为 PyTorch 添加类型标注指南](https://github.com/pytorch/pytorch/wiki/Guide-for-adding-type-annotations-to-PyTorch)。

### C++ 单元测试

PyTorch 在 `test/cpp` 目录提供了一系列测试。这些测试以 C++ 编写,使用 Google Test 测试框架。从源码编译 PyTorch 后,测试 runner 二进制会写入 `build/bin` 目录。运行命令为 `./build/bin/FILENAME --gtest_filter=TESTSUITE.TESTNAME`,其中 `TESTNAME` 是要运行的测试名,`TESTSUITE` 是该测试所在的套件。

例如,要运行 `test/cpp/jit/test_alias_analysis.cpp` 中 `ContainerAliasingTest` 套件的 `MayContainAlias` 测试:

```bash
./build/bin/test_jit --gtest_filter=ContainerAliasingTest.MayContainAlias
```


### 运行指定 CI 任务

可以用 `tools/testing/explicit_ci_jobs.py` 生成一个让 CI 只运行特定任务的提交:

```bash
# --filter-gha: 只保留匹配此 glob 的 github actions workflow 文件
#               (其余 workflow 文件全部删除)
# --make-commit: 把 CI 变更连同说明信息一起提交到 git
python tools/testing/explicit_ci_jobs.py --filter-gha '*pull*' --make-commit

# 做你的修改

ghstack submit
```

**注意**:除非你同时使用 [`ghstack`](https://github.com/ezyang/ghstack),否则不建议使用该流程。它会产生一个对评审者信号量极低的大提交。

## 合入你的变更(Merging your Change)

如果你认识应当批准你 PR 的合适人选或团队(且你拥有相应权限),把他们加进 Reviewers 列表。

如果不认识,就让 Reviewers 一栏留空。我们的分诊小队会评审你的 PR,打上模块标签,并在几个工作日内指派给合适的评审者。评审者会查看你的 PR 并给出回应。

偶尔也会有力有不逮的时候(抱歉!)。如果你的 PR 要么没被指派评审者,要么评审者连续 4 个工作日没有任何回应,请在 PR 下留言评论(若已指派评审者则 @ 他们)。这能把 PR 重新推回大家的视野。

如果还是没用,就来[我们的 office hours](https://github.com/pytorch/pytorch/wiki/Dev-Infra-Office-Hours) 找我们。

PR 获批后,输入内容为 `@pytorchmergebot merge` 的评论即可合入([这是什么 bot?](https://github.com/pytorch/pytorch/wiki/Bot-commands))

---

# 未翻译章节

以下章节(GreenLight、编写文档、py-spy 性能分析、多构建树管理、C++/CUDA/Windows 开发技巧、提交前 lint、ASAN 构建、Caffe2 说明、CI 失败排查、Dev Infra Office Hours)保留英文,完整内容见 [CONTRIBUTING.en.md](CONTRIBUTING.en.md)。其余目录条目同样以英文原版为准。
