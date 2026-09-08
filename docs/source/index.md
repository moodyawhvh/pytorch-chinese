% PyTorch 文档主文件,创建于
%  sphinx-quickstart on Fri Dec 23 13:31:47 2016.
%  你可以按喜好完全修改本文件,但至少应保留根 `toctree` 指令。

> 🌐 本文档由 [pytorch/pytorch](https://github.com/pytorch/pytorch) 翻译,英文原版见原项目。

% :github_url: https://github.com/pytorch/pytorch

PyTorch 文档
===================================

PyTorch 是一个针对深度学习优化的张量库,同时支持 GPU 与 CPU。

本文档中描述的特性按发布状态分类:

**稳定(Stable,API-Stable):**
这些特性会被长期维护,通常不应存在重大的性能限制或文档缺口。我们也期望保持向后兼容(尽管破坏性变更仍可能发生,并会提前一个版本发出通知)。

**不稳定(Unstable,API-Unstable):**
涵盖所有正在积极开发中的特性,其 API 可能依据用户反馈、必要的性能改进或算子覆盖率尚未完善而变化。这些特性的 API 与性能特征都可能改变。

```{toctree}
:glob:
:maxdepth: 2

Install PyTorch <https://pytorch.org/get-started/locally/>
user_guide/index
pytorch-api
notes
community/index
```

## 索引与表格

* {ref}`genindex`
* {ref}`modindex`
