# 安全政策

> 🌐 本文档由 [pytorch/pytorch](https://github.com/pytorch/pytorch) 翻译,英文原版见原项目。

 - [**报告漏洞**](#报告漏洞)
 - [**不属于安全漏洞的问题**](#不属于安全漏洞的问题)
 - [**安全地使用 PyTorch**](#安全地使用-pytorch)
   - [不可信模型](#不可信模型)
   - [TorchScript 模型](#torchscript-模型)
   - [不可信输入](#训练与预测中的不可信输入)
   - [数据隐私](#数据隐私)
   - [使用分布式功能](#使用分布式功能)
 - [**安全修复的向后移植**](#安全修复的向后移植)
 - [**CI/CD 安全原则**](#cicd-安全原则)

## 报告安全问题

请注意,[安全地使用 PyTorch](#安全地使用-pytorch) 项下的所有主题均不被视为 PyTorch 的漏洞。

但如果你认为自己发现了 PyTorch 的安全漏洞,我们鼓励你立即告知我们。我们会调查所有合规的报告,并尽全力尽快修复问题。

请通过 https://github.com/pytorch/pytorch/security/advisories/new 报告安全问题。

所有通过 security advisories 机制提交的报告,**要么在提交后 90 天内被公开,要么被团队驳回**。如果某个 advisory 因"不属于安全问题"被关闭,也请不要犹豫,直接创建一个[新 issue](https://github.com/pytorch/pytorch/issues/new?template=bug-report.yml)——它很可能仍是框架内的有效问题。

## 不属于安全漏洞的问题

PyTorch 是一个执行用户提供的代码的框架,包括模型定义、自定义算子和训练脚本。与许多底层计算库一样,PyTorch 通常不会对每个函数的所有输入做校验——提供有效参数的责任在调用方代码。已经能够在本地执行任意代码或修改系统文件的攻击者,利用 PyTorch 的漏洞并不能获得任何额外能力。以下类别的报告应作为普通 bug 提交,**而不是**安全漏洞:

- **崩溃与越界访问**:传入无效参数(错误的 shape、dtype、设备指定等)可能导致崩溃、段错误或内存越界访问。这通常源于缺少输入校验,值得作为普通 issue 上报,但不属于安全漏洞——调用方本身就在运行原生代码,不用 PyTorch 也能造成同样的效果。

- **数值精度与稳定性**:不同设备(CPU vs. CUDA)、dtype、平台或库版本之间的数值结果差异,是浮点计算中的预期行为。这包括精度损失(CWE-682)、跨运行的不确定性,以及与参考实现不一致的结果。

- **内部或"不安全"函数**:PyTorch 的部分函数刻意设计为低层或无校验(例如以 `_` 为前缀的函数、内部 C++ API,或文档中标注为 unsafe 的 API)。它们的存在是为了性能或灵活性,并不打算抵御恶意调用方。如果攻击者能以任意参数调用这些函数,那他多半已经拥有本地执行权限了。

- **通过资源消耗实现的拒绝服务**:PyTorch 的设计目标就是运行吃满 CPU、GPU 和内存的计算密集型负载。构造导致高资源消耗或长时间运行的输入轻而易举,也属预期之内——这不构成安全漏洞。

- **本地文件系统与缓存信任**:PyTorch 大量使用本地缓存来提升性能(如编译后的 kernel 产物、Triton 缓存)。这些缓存应位于仅限本地用户访问的位置,且在设计上即为可信。如果攻击者拥有本地文件系统写权限,他早已能执行任意代码——污染 PyTorch 缓存不会带来任何额外能力。

- **反序列化产生的畸形对象**:`torch.load` 配合 `weight_only=True` 能确保反序列化过程本身不产生 RCE 或越界访问,但不保证反序列化出来的对象在后续使用中的可用性。与上一条规则类似,此类对象可能导致崩溃和越界访问,属于普通问题,而非安全漏洞。

如果你的安全 advisory 因落入上述类别之一而被关闭,请不要气馁——这些仍然是有价值的报告。我们鼓励你将其重新提交为[普通 issue](https://github.com/pytorch/pytorch/issues/new?template=bug-report.yml),以便作为 bug 被跟踪和修复。

## 安全地使用 PyTorch

**PyTorch 模型就是程序**,所以请认真对待其安全性——运行不可信的模型等同于运行不可信的代码。总体上我们建议将模型权重与模型对应的 Python 代码分开分发。即便如此,也要留意 Python 代码的来源和作者(优先核验出处或校验和,不要随意运行任何 pip 安装的包)。

### 不可信模型

运行不可信模型时要格外小心。此类模型包括由身份不明的开发者创建的模型,或使用了来历不明的数据训练的模型[^data-poisoning-sources]。

**优先在安全、隔离的环境(如沙箱)中执行不可信模型**(例如容器、虚拟机)。这有助于保护你的系统免受潜在恶意代码的侵害。更多细节和操作指引见[此页面](https://developers.google.com/code-sandboxing)。

**警惕高风险的模型格式**。请根据用例选择合适的格式来共享和加载权重。[Safetensors](https://huggingface.co/docs/safetensors/en/index) 安全性最高,但支持的特性也最受限。[`torch.load`](https://pytorch.org/docs/stable/generated/torch.load.html#torch.load) 的攻击面明显更大,但序列化能力更灵活。详见相关文档。

即便是更安全的序列化格式,下游系统若收到意外输入也可能引发多种安全威胁(例如拒绝服务、越界读写),因此我们建议对任何不可信输入做充分校验。

重要提示:模型的可信度并非非黑即白。你必须始终根据具体模型及其与你的用例和风险容忍度的匹配程度,来确定恰当的谨慎级别。

[^data-poisoning-sources]: 要了解使用来历不明数据的风险,请阅读以下康奈尔大学关于数据投毒的论文:
    https://arxiv.org/abs/2312.04748
    https://arxiv.org/abs/2401.05566

### TorchScript 模型

TorchScript 模型应与来自未知来源的本地可执行代码同等对待。只在信任提供方时才运行 TorchScript 模型。请注意,内省 TorchScript 模型的工具(如 `torch.utils.model_dump`)也可能执行模型中存储的部分或全部代码,因此只有在信任待加载二进制的提供方时才应使用这些工具。

PyTorch mobile 模型(`.ptl` 文件)是为移动端部署优化的 TorchScript 模型,应保持同等级别的警惕。只从可信来源加载 PyTorch mobile 模型。

### 训练与预测中的不可信输入

如果你计划让模型接受不可信输入,请注意输入也可能被恶意攻击者当作攻击载体。为了降低风险,请确保只赋予模型严格必需的权限,并保持依赖库已更新至最新安全补丁。

如适用,请针对恶意输入和提示注入(prompt injection)加固你的模型。一些建议:
- 预分析:检查模型在暴露于提示注入时的默认表现(例如使用提示注入模糊测试)。
- 输入净化:在把数据喂给模型之前严格净化输入。具体技术包括:
    - 校验:对允许的字符和数据类型执行严格规则。
    - 过滤:移除潜在恶意的脚本或代码片段。
    - 编码:将特殊字符转换为安全的表示形式。
    - 检测:运行能识别潜在脚本注入的工具(例如[能检测提示注入尝试的模型](https://python.langchain.com/docs/guides/safety/hugging_face_prompt_injection))。

### 数据隐私

**如果使用敏感数据训练模型,请采取特别的安全措施**。优先对模型进行[沙箱隔离](https://developers.google.com/code-sandboxing),并且:
- 不要把敏感数据喂给不可信的模型(即便它运行在沙箱环境中)
- 如果你考虑发布一个部分使用敏感数据训练的模型,请意识到数据有可能从训练后的权重中被还原(模型过拟合时尤其如此)。

### 使用分布式功能

PyTorch 可用于分布式计算,为此提供了 `torch.distributed` 包。PyTorch 的分布式功能仅面向内部通信设计,并不适用于不可信的环境或网络。

出于性能考虑,PyTorch 分布式原语(包括 c10d、RPC 和 TCPStore)均不包含任何授权协议,且以明文发送消息。它们接受来自任何位置的连接,并在不执行任何检查的情况下直接执行收到的负载。因此,如果你在网络上运行 PyTorch 分布式程序,任何能访问该网络的人都可以以运行 PyTorch 的用户身份执行任意代码。

同样的信任假设也适用于分布式 checkpoint。分布式 Checkpoint(`torch.distributed.checkpoint`),包括 `torch.distributed.checkpoint.format_utils` 中的格式转换工具(如 `torch_save_to_dcp` 和 `BroadcastingTorchSaveReader`),用途是在你掌控的存储上保存和恢复可信分布式作业的状态。checkpoint 由你自己的训练作业产出、并从可信存储读回;它们不是你从互联网下载或从不可信第三方接收的产物。由于 checkpoint 总是被假定为来自可信来源,`torch.load` 的 `weights_only` 保护在这里并不适用——加载 checkpoint 和其他任何分布式操作一样,可能以运行 PyTorch 的用户身份执行任意代码。只加载由你自己的基础设施产生并存储的 checkpoint。

## 安全修复的向后移植

安全修复只应用于当前发布版本,不会向后移植到旧版本 PyTorch。适用于既往发布版本的唯一安全问题是已发布二进制本身被篡改(例如 PyPI 上的包或下载索引被未授权修改)。如果你认为某个已发布的二进制已被入侵,请通过[安全 advisory 流程](#报告安全问题)报告。

## CI/CD 安全原则

*目标读者*:贡献者和评审者,尤其是修改 workflow 文件/构建系统的人。

PyTorch 的 CI/CD 安全理念是在保持 CI 流水线开放透明与维持环境高效安全之间寻求平衡。

PyTorch 的测试需求复杂,代码库中很大一部分只能在 GPU 等专用强大硬件上测试,这使其成为资源滥用的高价值目标。为防止滥用,我们要求非成员贡献者的 PR 须经审批才能运行 workflow。为了把审批量控制在较低水平,我们向经常性贡献者开放仓库写权限。

更广泛的仓库写权限在变更评审、代码合入主干和创建发布方面带来了挑战。我们使用[受保护分支](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)把合入主干/发布分支的能力限制在仓库管理员和 merge bot 手中。merge bot 负责机械性地执行合并,并依照 [merge_rules.yml](https://github.com/pytorch/pytorch/blob/main/.github/merge_rules.yaml) 中定义的基于路径的规则校验评审情况。当 PR 获得这些规则中列出的人员评审后,在 PR 下留言 `@pytorchbot merge` 即可启动合并流程。为防止 merge bot 凭据泄露,合并操作只能在临时 runner(定义见下文)上通过专用部署环境执行。

为了加速 CI,workflow 的构建步骤依赖由 [sccache](https://github.com/mozilla/sccache) 支撑的分布式缓存机制,因此易受缓存污染攻击。出于该原因,CI 期间生成的二进制产物不应在能访问任何敏感/非公开信息的环境中执行,也不应发布给公众使用。不要对这些产物的存续时间抱任何预期,尽管实践中它们通常在 PR 关闭后约两周内仍可访问。

为了加速 CI 环境搭建,PyTorch 大量依赖 Docker 预构建和预安装依赖。为防止恶意 PR 篡改过去发布的镜像,ECR 已配置为使用不可变标签。

为了提升 runner 可用性和资源利用效率,部分 CI runner 是非临时性的,即来自毫不相关 PR 的 workflow 步骤可能被调度到同一台 runner 上顺序执行,这使其易受反弹 shell 攻击。因此 PyTorch 不依赖仓库 secrets 机制,因为这类秘密在此类攻击中很容易失守。

### 发布流水线安全

为确保二进制发布安全,PyTorch 发布流水线建立在以下原则之上:
 - 所有二进制构建/上传任务必须在临时 runner 上运行,即从云端分配一台机器执行构建、构建完成后立即释放回云端。这可以保护构建免受外部攻击者干扰——否则攻击者可能通过反弹 shell 进入非临时 runner 并潜伏等待二进制构建。
 - 所有二进制构建均为冷启动构建,即不允许使用分布式缓存/增量构建。这使构建比增量 CI 构建慢得多,但能将其与中间产物缓存系统可能被入侵的风险隔离。
 - 所有上传任务都在限定于受保护分支的[部署环境](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)中执行。
 - 向 PyPI/conda 或稳定索引 `download.pytorch.org/whl` 上传二进制所需的安全凭据,绝不会上传到仓库 secrets 存储或部署环境中。这需要额外的手动发布步骤,但确保这些凭据不会因云端秘密的蓄意或意外泄露而失守。
 - 不得向 GitHub Releases 页面发布任何二进制产物,因为任何拥有仓库写权限的人都可以覆写这些页面。
