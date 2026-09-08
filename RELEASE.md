# 发布 PyTorch(Releasing PyTorch)

> 🌐 本文档由 [pytorch/pytorch](https://github.com/pytorch/pytorch) 翻译,英文原版见原项目。
> 说明:本文件超过 1 万字符,此处翻译核心章节;版本兼容矩阵等表格数据及次要章节保留英文原样,见文末。

## 发布节奏与核心流程(核心章节中文翻译)

### 发布节奏(Release Cadence)

以下是发布节奏。下文所有未来日期均为暂定。发布计划的最新动态请关注 [dev discuss](https://dev-discuss.pytorch.org/c/release-announcements/27)。注意:补丁版本(Patch Release)是可选的。

具体版本日期对照表保留英文原样,见文末表格。

### 总体流程(General Overview)

发布一个新版 PyTorch 一般包含 3 个主要步骤:

0. 切发布分支的准备工作
1. 切发布分支,并做发布分支特有改动
2. 起草 RC(Release Candidate,发布候选版),并合入 cherry-pick
3. 准备并创建最终 RC
4. 将最终 RC 提升为稳定版,并执行发布日任务

### 常见问题(Frequently Asked Questions)

* 问:什么是 release branch cut(发布分支切分)?
  * 答:当大部分受跟踪的特性合入 main 分支后,主发布工程师会基于当前 `main` 开发分支新建一个 git 分支,即"切出发布分支",并启动发布流程。这让 `main` 上的开发流程不受干扰,同时发布工程团队专注于稳定发布分支,以产出一连串发布候选(RC)。发布分支上的活动包括回归与性能测试,以及打磨新特性、修复发布相关 bug。一般来说,发布分支创建之后*不再*向其添加新特性。

* 问:什么是 cherry-pick?
  * 答:cherry-pick 是利用 git 内置的 [cherry-pick 功能](https://git-scm.com/docs/git-cherry-pick),把提交从 main 传播到发布分支的过程。这些提交通常仅限于小修复或文档更新,以确保发布工程团队有足够时间在发布分支上完成一轮完整的测试。要提名某个修复进行 cherry-pick,必须先针对对应发布分支创建单独的 pull request,再按 issue 描述中的模板在 Release Tracker issue 中提及它(示例:https://github.com/pytorch/pytorch/issues/94937)。提名某次 cherry-pick 进入发布的评论应包含:针对 main 的已合入 PR、新建的 cherry-pick PR,以及为什么需要这次 cherry-pick 的验收标准。该流程可在目标 PR 下评论 `@pytorchbot cherry-pick -c [reason]` 来自动化完成。

### 切发布分支前的准备

切发布分支之前需要满足以下条件:

* 必须已创建 Triton 发布分支(如 [release/3.6.x](https://github.com/triton-lang/triton/tree/release/3.6.x)),且 Triton pin 更新 PR(如 [#168096](https://github.com/pytorch/pytorch/pull/168096))至少在分支切分前 1 周合入
* 解决里程碑中所有仍未完成的特性开发类、阻塞发布的问题(例如 [release 2.10 里程碑](https://github.com/pytorch/pytorch/milestone/57))。未完成的 cherry-pick 报告可通过运行 [github-analytics-daily workflow](https://github.com/pytorch/test-infra/blob/main/.github/workflows/github-analytics-daily.yml) 生成
* 验证发布所含的 PyTorch 及各领域库中所有新 workflow 均已创建,并对照发布矩阵的全部维度验证:操作系统(Linux、macOS、Windows)、Python 版本、CPU 架构(x86 与 arm)以及加速器版本(CUDA、ROCm、XPU)
* 所有 [viable/strict](.github/workflows/update-viablestrict.yml) 任务均为绿色,即 `pull`、`trunk`、`lint` 三个任务通过
* pytorch 与各领域库的所有 nightly 任务应为绿色。通过以下 HUD 链接验证:
  * [PyTorch](https://hud.pytorch.org/hud/pytorch/pytorch/nightly)
  * [TorchVision](https://hud.pytorch.org/hud/pytorch/vision/nightly)

### 切发布分支

#### `pytorch/pytorch`

发布分支通常从 [`viable/strict`](https://github.com/pytorch/pytorch/tree/viable/strict) 分支切出,以确保发布分支上测试是通过的。

有便捷脚本可从当前 `viable/strict` 创建发布分支,步骤如下:
* 全新 clone pytorch 仓库:
```bash
git clone git@github.com:pytorch/pytorch.git
```

* 在 PyTorch 仓库根目录执行:
```bash
DRY_RUN=disabled scripts/release/cut-release-branch.sh
```
该脚本会创建 2 个分支:
* `release/{MAJOR}.{MINOR}`
* `orig/release/{MAJOR}.{MINOR}`

#### PyTorch 生态库

*注意*:各生态库的发布分支应在 PyTorch 首个 RC 构建进入 staging 通道后创建(这大约发生在 PyTorch 发布分支创建约一周后)。这是保证每个领域库有足够测试时间的必要条件。生态库的分支切分由 Ecosystem Library POC 负责。Test-Infra 的分支切分应与 PyTorch 核心同步进行。领域库也可使用便捷脚本。

> 注:仅当根目录没有 version.txt 时才需要指定 RELEASE_VERSION

```bash
DRY_RUN=disabled GIT_BRANCH_TO_CUT_FROM=main RELEASE_VERSION=1.11 scripts/release/cut-release-branch.sh
```

#### 为 PyTorch 做发布分支特有改动

分支切出后,通过运行 [`scripts/release/apply-release-changes.sh`](https://github.com/pytorch/pytorch/blob/main/scripts/release/apply-release-changes.sh) 应用发布专属改动(把 workflow 与 composite action 的分支引用从 `@main` 更新为 `@release/[major].[minor]`),该脚本会开启一个包含这些改动的 PR:

```
DRY_RUN=disabled RELEASE_VERSION=2.7 ./scripts/release/apply-release-changes.sh
```

为使 CI/工具链在发布分支上正常工作,pytorch/pytorch 发布分支上还应做以下改动示例:

* 更新向后兼容测试,使其使用 RC 二进制而非 nightly
  * 示例:https://github.com/pytorch/pytorch/pull/186959
* 在 [`pytorch/test-infra`](https://github.com/pytorch/test-infra) 仓库也应创建发布分支,并在 `pytorch/pytorch` 中 pin。test-infra 发布分支通过在 `pytorch/test-infra` 仓库运行 [`release/cut-release-branch.sh`](https://github.com/pytorch/test-infra/blob/main/release/cut-release-branch.sh) 切出。
  * 示例:https://github.com/pytorch/test-infra/commit/9f3fd4d6f311679a8ae6317c0cb33c8ed93a34b5

切出发布分支后,*默认*分支上应做的改动示例:

* 所有版本文件中的 nightly 版本应更新到下一个 MINOR 版本(即 0.9.0 -> 0.10.0):
  * 示例:https://github.com/pytorch/pytorch/pull/77984

#### 为生态库做发布分支特有改动

生态库的分支切分在 `pytorch/pytorch` 切分数天后进行,由 Ecosystem Library POC 执行。切分完成后应通知 PyTorch Dev Infra 成员,且在该领域库起草 RC 之前需要完成领域库专属改动。

参考以下更新版本并设置 RC 上传通道的 PR 示例:
* torchvision:[更新 version.txt](https://github.com/pytorch/vision/pull/8968) 与 [修改 workflow 分支引用](https://github.com/pytorch/vision/pull/8969)

上述 PR 中的 CI workflow 更新部分可通过运行 `python release/apply-release-changes.py [version]` 自动化(版本形如 '2.7')。该脚本位于 pytorch/vision。

### 为 PyTorch 与领域库起草 RC

起草 RC 时,具备相应权限的用户可以向 main `pytorch/pytorch` git 仓库推送一个 git tag。注意:每个领域库使用完全相同的流程。

RC 的 git tag 必须遵循以下格式:
```
v{MAJOR}.{MINOR}.{PATCH}-rc{RC_NUMBER}
```

示例:
```
v1.12.0-rc1
```
在 pytorch 核心仓库(而非 fork)中可用以下命令打 tag:
* 打 tag 前先 checkout 并确认仓库历史
```
git checkout release/1.12
git log --oneline
```
* 打 tag 并推送到 github(这将触发二进制发布构建)
```
git tag -f  v1.12.0-rc2
git push origin  v1.12.0-rc2
```

推送 RC tag 应触发 `binary_build` workflows。该触发机制配置在 [`linux_binary_build_workflow.yml.j2`](https://github.com/pytorch/pytorch/blob/main/.github/templates/linux_binary_build_workflow.yml.j2#L19-L22) 及其他操作系统的对应模板中。

查看发布构建状态请访问 [HUD](https://hud.pytorch.org/hud/pytorch/pytorch/release%2F1.12),并确认所有二进制构建成功。

#### RC 存储

RC 目前存储在以下位置:

* Wheels: https://download.pytorch.org/whl/test/
* Libtorch: https://download.pytorch.org/libtorch/test <!-- @lint-ignore -->

备份存储在非公开 S3 桶 [`s3://pytorch-backup`](https://s3.console.aws.amazon.com/s3/buckets/pytorch-backup?region=us-east-1&tab=objects) 中。

#### RC 健康检查

验证 pytorch 与领域库的发布任务均为绿色,使用以下 HUD 链接:
  * [PyTorch](https://hud.pytorch.org/hud/pytorch/pytorch/release%2F2.13)
  * [TorchVision](https://hud.pytorch.org/hud/pytorch/vision/release%2F0.28)

验证文档构建已完成,并在[文档仓库](https://github.com/pytorch/docs/tree/main/)中生成了与该发布对应的条目。

#### Cherry-picking 修复

通常,一个发布周期内需要对回归、测试修复等进行修复。

对发布分支切出后要进入发布的修复,我们通常使用 cherry-pick 跟踪 issue,示例:
* https://github.com/pytorch/pytorch/issues/128436

另请务必给 PR/issue 打上里程碑目标,尤其当它需要被考虑纳入 dot release 时。

**注意**:cherry-pick 流程不是加新特性的邀请,它主要用于修复回归。

##### 如何执行 cherry-pick

现在可以对已合入 main 的 PyTorch PR 使用 `@pytorchbot cherry-pick` 命令发起 cherry-pick(确保目标发布版对应的 cherry-pick tracker issue 带有 "release tracker" 标签——这便于 bot 找到它并发表评论)。

```
usage: @pytorchbot cherry-pick --onto ONTO [--fixes FIXES] -c
                               {regression,critical,fixnewfeature,docs,release}

将一个 pull request cherry-pick 到发布分支以纳入发布

可选参数:
  --onto ONTO           要 cherry-pick 到的目标分支(示例:release/2.2)
  --fixes FIXES         你的 PR 修复的 issue 链接(即 https://github.com/pytorch/pytorch/issues/110666)
  -c {regression,critical,fixnewfeature,docs,release}
                        cherry-pick 原因的机器友好分类
```

例如,[#120567](https://github.com/pytorch/pytorch/pull/120567#issuecomment-1978964376) 为修复回归,向 `release/2.2` 分支创建了 cherry-pick PR [#121232](https://github.com/pytorch/pytorch/pull/121232)。之后可在 release tracker issue 中引用原 PR 与 cherry-pick PR。注意 cherry-pick PR 仍需 PyTorch RelEng 团队评审才能进入发布分支。该功能依赖 `pytorchbot`,目前仅在 PyTorch 上可用。

#### Cherry-pick 的回退

若被 cherry-pick 进发布分支的 PR 在 main 上被 revert,它的 cherry-pick 也必须回退。

分支切分前已合入 main 的变更,其 revert 也必须传播到发布分支。

### 准备并创建最终 RC

创建最终 RC 前需满足以下条件:

* 解决里程碑中所有未关闭的问题。不应存在未关闭的 issue/PR(例如 [2.1.2](https://github.com/pytorch/pytorch/milestone/39))。每个 issue 要么关闭,要么移出里程碑。

* 验证里程碑中所有已关闭的 PR 都在发布分支上。运行以下命令确认:
``` python github_analyze.py --repo-path ~/local/pytorch --remote upstream --branch release/2.2 --milestone-id 40 --missing-in-branch ```

* issue 跟踪器中没有待评审的 cherry-pick:https://github.com/pytorch/pytorch/issues/115300

* 完成 [RC 健康检查](#rc-健康检查)。CI 应为绿色。

最终 RC 创建后,应执行以下任务:

* 再次完成 [RC 健康检查](#rc-健康检查)。CI 应为绿色。

* 运行并检查 [Validate Binaries](https://github.com/pytorch/test-infra/actions/workflows/validate-binaries.yml) workflow 的输出。

* [里程碑](https://github.com/pytorch/pytorch/milestone/39)中所有已关闭的 issue 都需要验证。通过在该 issue 下评论确认验证结果:https://github.com/pytorch/pytorch/issues/113568#issuecomment-1851031064

* 为该发布创建验证 issue,参考[2.1.2 发布的验证](https://github.com/pytorch/pytorch/issues/114904),并完成所需的验证。

* 在 [benchmark 仓库](https://github.com/pytorch/benchmark)中运行性能测试,确保没有性能回归。

* 准备 PyPI 二进制并暂存以待提升。使用脚本:[`pytorch/test-infra:release/pypi/promote_pypi_to_staging.sh`](https://github.com/pytorch/test-infra/blob/main/release/pypi/promote_pypi_to_staging.sh)

* 验证暂存的 PyPI 二进制。确保生成的包正确,且包大小不超过 PyPI 允许的上限。

### 将 RC 提升为稳定版

RC 提升为稳定版使用脚本:[`pytorch/test-infra:release/promote.sh`](https://github.com/pytorch/test-infra/blob/main/release/promote.sh)

使用者需自行更新待提升包所需的版本号。

提升应分两步:
* 提升 S3 产物(wheels、libtorch)和 Conda 包
* 将 S3 wheels 提升到 PyPI

**注意**:wheels 向 PyPI 的提升只能进行一次,操作时务必小心(关于 PyPI 内可能的 draft release 讨论见 https://github.com/pypi/warehouse/issues/726 )。

### 发布日前的其他准备

发布日应准备好以下事项:

#### 修改发布矩阵

为 get started 页面修改发布矩阵,参考此 [PR](https://github.com/pytorch/test-infra/pull/4611)。

更新 published_versions.json 与 quick-start-module.js 的 PR 是自动生成的,参考此 [PR](https://github.com/pytorch/pytorch.github.io/pull/1467)。

注意:该 PR 必须在发布日合入,因此绝不能有任何失败。测试该 PR 时,可另开一个测试 PR 指向 [RC 存储](#rc-存储)一节所述的 Release Candidate 位置。

#### 提交 Google Colab issue

这通常在发布完成后立即进行。需要创建一个 Google Colab issue,示例见此 [issue](https://github.com/googlecolab/colabtools/issues/2372)。

## 补丁版本(Patch Releases)

补丁版本是 PyTorch 的维护性发布,包含对上一个 minor 版本中发现的回归的修复。补丁版本通常按语义化版本递增 `patch` 位(即 `[major].[minor].[patch]`)。

注意:从 2.1 开始,每个 minor 发布后可预期最多 2 个补丁版本。只为最新的 minor 发布提供补丁版本。

### 补丁版本标准

回归满足以下标准时才考虑发布补丁版本:

1. 该回归是否破坏核心功能(稳定/beta 特性),包括第一方领域库中的功能?
    * 第一方领域库:
        * [pytorch/vision](https://github.com/pytorch/vision)
3. 是否没有可行的规避方案?
    * 该回归能否简单解决,还是无法绕过?

> *注*:只有功能被破坏时才应考虑补丁版本,文档问题通常不属于此类。

### 补丁版本流程

#### 流程说明

> 主要负责人:补丁发布经理、分诊评审员

补丁版本应遵循以下高层阶段。流程在上一次发布完成后立即开始,约需 4-5 周完成。

1. 分诊(Triage):识别 issue、定级、对照补丁版本标准评估,并加入补丁版本里程碑。通常在发布完成后持续 2 周。
2. Go/No Go 会议:PyTorch Releng、PyTorch Core 与项目经理之间召开,评审里程碑中可能触发发布的问题,并作出以下决策:
  * 是否创建新的补丁版本?
  * 补丁版本的时间线执行
3. 决定创建补丁版本后开始 cherry-pick 阶段。此时会新建补丁发布的 release tracker,并在官方渠道发布公告[示例公告](https://dev-discuss.pytorch.org/t/pytorch-release-2-0-1-important-information/1176)。回归修复的作者会被要求自行创建 cherry-pick。通常需要 2 周。
4. 更新发布分支中的 `version.txt` 以匹配预期的补丁版本号,示例见 https://github.com/pytorch/pytorch/commit/f77213d3dae5d103a39cdaf93f21863843571e8d
5. 构建二进制、提升为稳定版并测试。所有 cherry-pick 合入后,发布经理触发新构建并产出新的 RC。此时在官方渠道公告 RC 可用。通常需要 2 周。
6. 正式发布(General Availability)

#### 分诊(Triage)

> 主要负责人:分诊评审员

1. 给潜在的补丁版本候选 issue/pull request 打上 `triage review` 标签
    * (配图略,见英文原版)
2. 分诊评审员随后检查所识别的回归/修复是否符合上述[补丁版本标准](#补丁版本标准)
3. 若符合[补丁版本标准](#补丁版本标准),分诊评审员将该 issue/pull request 加入相应里程碑(如 `1.9.1`)

#### 补丁版本的 issue 跟踪器

补丁发布需要创建 issue 跟踪器。补丁发布要求所有 cherry-pick 变更都附上指向高优先级 GitHub issue 或上一个 RC 的 CI 失败的链接,示例:
* https://github.com/pytorch/pytorch/issues/128436

只接受以下几类 issue:
1. 针对上一个 major 版本回归的修复(如 1.12.0 → 1.13.0 引入的回归可为 1.13.1 所 pick)
2. 针对静默错误、向后兼容、崩溃、死锁、(大量)内存泄漏的低风险关键修复
3. 本发布引入的新特性的修复
4. 文档改进
5. 发布分支特有改动(如阻塞 CI 的修复、版本标识变更)

#### 制定发布计划 / cherry-picking

> 主要负责人:补丁发布经理

1. 回归/修复分诊完成后,补丁发布经理将协作制定并公告补丁发布计划
    * *注*:理想情况下应在识别回归后约 2-3 周发布,以便识别出其他回归
2. 补丁发布经理将与回归/修复作者合作,把其变更 cherry-pick 到相应发布分支(`1.9.1` 对应 `release/1.9`)
    * *注*:补丁发布经理应通知回归作者自行提交 cherry-pick。是否提交取决于作者本人;若未提交,该 issue 不会纳入发布。
3. 若 cherry-pick 作者错过截止时间,补丁发布经理不再接受任何事后请求。

#### 构建二进制 / 提升为稳定版

> 主要负责人:补丁发布经理

1. 补丁发布经理遵循[为 PyTorch 与领域库起草 RC](#为-pytorch-与领域库起草-rc)流程
2. 补丁发布经理遵循[将 RC 提升为稳定版](#将-rc-提升为稳定版)流程

---

# 以下章节保留英文原样(表格数据与次要章节)

## Release Compatibility Matrix

Following is the Release Compatibility Matrix for PyTorch releases:

| PyTorch version | Python | C++ | Stable CUDA | Experimental CUDA | Stable ROCm |
| --- | --- | --- | --- | --- | --- |
| 2.14 | >=3.10, <=(3.15, 3.15t experimental) | C++20 | CUDA 12.6 (CUDNN 9.10.2.21) (NCCL 2.29.3), CUDA 13.0 (CUDNN 9.24.0.43) (NCCL 2.30.7), CUDA 13.2 (CUDNN 9.24.0.43) (NCCL 2.30.7) | -- | ROCm 7.14 |
| 2.13 | >=3.10, <=(3.15, 3.15t experimental) | C++20 | CUDA 12.6 (CUDNN 9.10.2.21) (NCCL 2.29.3), CUDA 13.0 (CUDNN 9.20.0.48) (NCCL 2.29.7) | CUDA 13.2 (CUDNN 9.20.0.48) (NCCL 2.29.7) | ROCm 7.2 |
| 2.12 | >=3.10, <=(3.14, 3.14t experimental) | C++17 | CUDA 12.6 (CUDNN 9.10.2.21) (NCCL 2.29.3), CUDA 13.0 (CUDNN 9.20.0.48) (NCCL 2.29.7) | CUDA 13.2 (CUDNN 9.20.0.48) (NCCL 2.29.7) | ROCm 7.2 |
| 2.11 | >=3.10, <=(3.14, 3.14t experimental) | C++17 | CUDA 12.6 (CUDNN 9.10.2.21) (NCCL 2.28.9), CUDA 12.8 (CUDNN 9.17.1.4) (NCCL 2.28.9), CUDA 13.0 (CUDNN 9.17.1.4) (NCCL 2.28.9) | -- | ROCm 7.2 |
| 2.10 | >=3.10, <=(3.14, 3.14t experimental) | C++17 | CUDA 12.6 (CUDNN 9.10.2.21) (NCCL 2.27.5), CUDA 12.8 (CUDNN 9.10.2.21) (NCCL 2.27.5) | CUDA 13.0 (CUDNN 9.15.1.9) (NCCL 2.28.9) | ROCm 7.1 |
| 2.9 | >=3.10, <=(3.14, 3.14t experimental) | C++17 | CUDA 12.6 (CUDNN 9.10.2.21), CUDA 12.8 (CUDNN 9.10.2.21) | CUDA 13.0 (CUDNN 9.13.0.50) | ROCm 6.4 |
| 2.8 | >=3.9, <=3.13, (3.13t experimental) | C++17 | CUDA 12.6 (CUDNN 9.10.2.21), CUDA 12.8 (CUDNN 9.10.2.21) | CUDA 12.9 (CUDNN 9.10.2.21) | ROCm 6.4 |
| 2.7 | >=3.9, <=3.13, (3.13t experimental) | C++17 | CUDA 11.8 (CUDNN 9.1.0.70), CUDA 12.6 (CUDNN 9.5.1.17) | CUDA 12.8 (CUDNN 9.7.1.26) | ROCm 6.3 |
| 2.6 | >=3.9, <=3.13, (3.13t experimental) | C++17 | CUDA 11.8, CUDA 12.4 (CUDNN 9.1.0.70) | CUDA 12.6 (CUDNN 9.5.1.17) | ROCm 6.2.4 |
| 2.5 | >=3.9, <=3.12, (3.13 experimental) | C++17 | CUDA 11.8, CUDA 12.1, CUDA 12.4, CUDNN 9.1.0.70  | None | ROCm 6.2 |
| 2.4 | >=3.8, <=3.12 | C++17 | CUDA 11.8, CUDA 12.1, CUDNN 9.1.0.70  | CUDA 12.4, CUDNN 9.1.0.70 | ROCm 6.1 |
| 2.3 | >=3.8, <=3.11, (3.12 experimental) | C++17 | CUDA 11.8, CUDNN 8.7.0.84 | CUDA 12.1, CUDNN 8.9.2.26 | ROCm 6.0 |
| 2.2 | >=3.8, <=3.11, (3.12 experimental) | C++17 | CUDA 11.8, CUDNN 8.7.0.84 | CUDA 12.1, CUDNN 8.9.2.26 | ROCm 5.7 |
| 2.1 | >=3.8, <=3.11 | C++17 | CUDA 11.8, CUDNN 8.7.0.84 | CUDA 12.1, CUDNN 8.9.2.26 | ROCm 5.6 |
| 2.0 | >=3.8, <=3.11 | C++14 | CUDA 11.7, CUDNN 8.5.0.96 | CUDA 11.8, CUDNN 8.7.0.84 | ROCm 5.4 |
| 1.13 | >=3.7, <=3.10 | C++14 | CUDA 11.6, CUDNN 8.3.2.44 | CUDA 11.7, CUDNN 8.5.0.96 | ROCm 5.2 |
| 1.12 | >=3.7, <=3.10 | C++14 | CUDA 11.3, CUDNN 8.3.2.44 | CUDA 11.6, CUDNN 8.3.2.44 | ROCm 5.0 |

### PyTorch CUDA Support Matrix

For Release 2.12, 2.13 and 2.14 PyTorch Supports following CUDA Architectures:

| CUDA | architectures supported for Linux x86 and Windows builds | notes |
| --- | --- | --- |
| 12.6.3 | Maxwell(5.0), Pascal(6.0), Volta(7.0), Turing(7.5), Ampere(8.0, 8.6), Hopper(9.0) | |
| 13.0.2 | Turing(7.5), Ampere(8.0, 8.6), Hopper(9.0), Blackwell(10.0, 12.0+PTX) | +PTX available on linux builds only |
| 13.2.1 | Turing(7.5), Ampere(8.0, 8.6), Hopper(9.0), Blackwell(10.0, 12.0+PTX) | +PTX available on linux builds only |

| CUDA | architectures supported for Linux aarch64 builds |
| --- | --- |
| 12.6.3 | Ampere(8.0), Hopper(9.0) |
| 13.0.2 | Ampere(8.0), Hopper(9.0), Blackwell(10.0, 11.0, 12.0+PTX) |
| 13.2.1 | Ampere(8.0), Hopper(9.0), Blackwell(10.0, 11.0, 12.0+PTX) |

### Release cadence table

| Minor Version | Release branch cut | Release date | First patch release date | Second patch release date|
| --- | --- | --- | --- | --- |
| 2.1 | Aug 2023 | Oct 2023 | Nov 2023 | Dec 2023 |
| 2.2 | Dec 2023 | Jan 2024 | Feb 2024 | Mar 2024 |
| 2.3 | Mar 2024 | Apr 2024 | Jun 2024 | Not planned |
| 2.4 | Jun 2024 | Jul 2024 | Sept 2024 | Not planned |
| 2.5 | Sep 2024 | Oct 2024 | Nov 2024 |  Not planned |
| 2.6 | Dec 2024 | Jan 2025 | Not planned | Not planned |
| 2.7 | Mar 2025 | Apr 2025 | Jun 2025 | Not planned |
| 2.8 | Jun 2025 | Jul 2025 | Not planned | Not planned |
| 2.9 | Sept 2025 | Oct 2025 | Nov 2025 | Not planned |
| 2.10 | Dec 2025 | Jan 2026 | Not planned | Not planned |
| 2.11 | 16 Feb 2026 | 18 Mar 2026 | Not planned | Not planned |
| 2.12 | 13 Apr 2026 | 13 May 2026 | Jun 2026 | Not planned |
| 2.13 | 8 Jun 2026 | 8 Jul 2026 | (Aug 2026) | Not planned |
| 2.14 | 10 Aug 2026 | 2 Sept 2026 | (Oct 2026) | Not planned |
| 2.15 | 5 Oct 2026 | 28 Oct 2026 | (Nov 2026) | Not planned |
| 2.16 | 30 Nov 2026 | 22 Dec 2026 | (Jan 2027) | Not planned |

## Running Launch Execution team Core XFN sync

The series of meetings for Core XFN sync should be organized. The goal of these meetings are the following:
1. Establish release POC's from each of the workstreams
2. Cover the tactical phase of releasing minor releases to the market
3. Discuss possible release blockers

Following POC's should be assigned from each of the workstreams:
* Core/Marketing
* Release Eng
* Doc Eng
* Release notes
* Partner

**NOTE**: The meetings should start after the release branch is created and should continue until the week of the release.

# Hardware / Software Support in Binary Build Matrix

PyTorch has a support matrix across a couple of different axis. This section should be used as a decision making framework to drive hardware / software support decisions

## Python

PyTorch supports all minor versions of CPython that are not EOL: https://devguide.python.org/versions/

For each minor release independently, we only support patch releases as follows:
- If the latest patch release is a bugfix release, we only support this one.
- Otherwise, we support all the non-bugfix patch releases.

See https://github.com/pytorch/rfcs/blob/master/RFC-0038-cpython-support.md for details on the rules and process for upgrade and sunset of each version.

## Accelerator Software

For accelerator software like CUDA and ROCm we will typically use the following criteria:
* Support latest 2 minor versions

### Special support cases

In some instances support for a particular version of software will continue if a need is found. For example, our CUDA 11 binaries do not currently meet
the size restrictions for publishing on PyPI so the default version that is published to PyPI is CUDA 10.2.

These special support cases will be handled on a case by case basis and support may be continued if current PyTorch maintainers feel as though there may still be a
need to support these particular versions of software.

## Operating Systems
Supported OS flavors are summarized in the table below:
| Operating System family | Architecture | Notes |
| --- | --- | --- |
| Linux | aarch64, x86_64 | Wheels are manylinux2014 compatible, i.e. they should be runnable on any Linux system with glibc-2.17 or above. |
| macOS | arm64 | Builds should be compatible with macOS 11 (Big Sur) or newer, but are actively tested against macOS 14 (Sonoma). MPS support is enabled on macOS 14 (Sonoma) or later. |
| Windows | x86_64 | Builds are compatible with Windows-10 or newer. |

# Submitting Tutorials

Tutorials in support of a release feature must be submitted to the [pytorch/tutorials](https://github.com/pytorch/tutorials) repo at least two weeks before the release date to allow for editorial and technical review. There is no cherry-pick process for tutorials. All tutorials will be merged around the release day and published at [pytorch.org/tutorials](https://pytorch.org/tutorials/).

# Special Topics

## Updating submodules for a release

In the event a submodule cannot be fast forwarded, and a patch must be applied we can take two different approaches:

* (preferred) Fork the said repository under the pytorch GitHub organization, apply the patches we need there, and then switch our submodule to accept our fork.
* Get the dependencies maintainers to support a release branch for us

Editing submodule remotes can be easily done with: (running from the root of the git repository)
```
git config --file=.gitmodules -e
```

An example of this process can be found here:

* https://github.com/pytorch/pytorch/pull/48312

## Triton dependency for the release

In nightly builds for conda and wheels pytorch depend on Triton build by this workflow: https://hud.pytorch.org/hud/pytorch/pytorch/nightly/1?per_page=50&name_filter=Build%20Triton%20Wheel. The pinned version of triton used by this workflow is specified here:  https://github.com/pytorch/pytorch/blob/main/.ci/docker/ci_commit_pins/triton.txt .

In Nightly builds we have following configuration:
* Wheel builds, depend on : https://download.pytorch.org/whl/nightly/triton/
* ROCm wheel builds, depend on : https://download.pytorch.org/whl/nightly/triton-rocm/
* XPU wheel builds, depend on : https://download.pytorch.org/whl/nightly/triton-xpu/

However for release we have following :
* Wheel builds, depend only triton pypi package: https://pypi.org/project/triton/ for both test and release
* ROCm wheel builds, depend on : https://download.pytorch.org/whl/test/triton-rocm/ for test and https://download.pytorch.org/whl/triton-rocm/ for release
* XPU wheel builds, depend on : https://download.pytorch.org/whl/test/triton-xpu/ for test and https://download.pytorch.org/whl/triton-xpu/ for release

Important: The release of https://pypi.org/project/triton/ needs to be requested from OpenAI once branch cut is completed. Please include the release PIN hash in the request: https://github.com/pytorch/pytorch/blob/release/2.1/.ci/docker/ci_commit_pins/triton.txt .
