# 常见问题解答

> 🌐 本文档由 [pytorch/pytorch](https://github.com/pytorch/pytorch) 翻译,英文原版见原项目。

## 我的模型报错 "cuda runtime error(2): out of memory"

如错误信息所示,GPU 显存已经耗尽。由于 PyTorch 中我们经常处理大量数据,一个小疏忽就可能让程序迅速吃光 GPU 显存;所幸这类问题的修复往往很简单。以下是几个常见检查点:

**不要在训练循环中累积计算历史。**
默认情况下,涉及需要梯度变量的计算会保留历史。这意味着应避免在训练循环之外仍然存活的计算中使用这类变量,例如统计指标跟踪。正确的做法是对变量做 detach,或直接访问其底层数据。

有时可微变量会出现在不明显的地方。看下面这个训练循环(节选自[这里](https://discuss.pytorch.org/t/high-memory-usage-while-training/162)):

```python
total_loss = 0
for i in range(10000):
    optimizer.zero_grad()
    output = model(input)
    loss = criterion(output)
    loss.backward()
    optimizer.step()
    total_loss += loss
```

这里 `total_loss` 在整个训练循环中不断累积历史,因为 `loss` 是一个携带 autograd 历史的可微变量。把 `total_loss += loss` 改写成 `total_loss += float(loss)` 即可修复。

此类问题的其他案例:
[1](https://discuss.pytorch.org/t/resolved-gpu-out-of-memory-error-with-batch-size-1/3719)。

**不要持有不再需要的张量和变量。**
如果你把 Tensor 或 Variable 赋给一个局部变量,Python 在该局部变量离开作用域之前不会释放它。可以用 `del x` 主动释放引用。同理,把 Tensor 或 Variable 赋给对象的成员变量,它在该对象离开作用域之前也不会释放。不持有用不到的临时对象,才能获得最佳的内存占用。

局部变量的作用域可能比你预想的大。例如:

```python
for i in range(5):
    intermediate = f(input[i])
    result += g(intermediate)
output = h(result)
return output
```

这里 `intermediate` 在 `h` 执行期间仍然存活,因为它的作用域延伸到了循环结束之后。想更早释放,用完就 `del intermediate`。

**避免在过长的序列上运行 RNN。**
RNN 反向传播所需的内存随输入长度线性增长;因此,给 RNN 喂过长的序列必然耗尽显存。

这个现象的技术名词是[沿时间反向传播(BPTT)](https://en.wikipedia.org/wiki/Backpropagation_through_time),截断 BPTT 的实现参考资料很多,包括[词语言模型](https://github.com/pytorch/examples/tree/master/word_language_model)示例;截断由 `repackage` 函数处理,详见[这个论坛帖](https://discuss.pytorch.org/t/help-clarifying-repackage-hidden-in-word-language-model/226)。

**不要使用过大的线性层。**
线性层 `nn.Linear(m, n)` 使用 {math}`O(nm)` 内存:也就是说,权重的内存需求随特征数平方增长。这样很容易[撑爆显存](https://github.com/pytorch/pytorch/issues/958)(而且记住至少需要两倍权重大小的空间,因为梯度也要存储)。

**考虑使用 checkpoint。**
可以用 [checkpoint](https://pytorch.org/docs/stable/checkpoint.html) 用计算换内存。

## 我的 GPU 显存没有被正确释放

PyTorch 使用带缓存的内存分配器来加速显存分配。因此 `nvidia-smi` 显示的数值通常不反映真实显存占用。更多 GPU 显存管理细节见 {ref}`cuda-memory-management`。

如果 Python 退出后 GPU 显存仍未释放,很可能还有 Python 子进程存活。可以用 `ps -elf | grep python` 找到它们,再 `kill -9 [pid]` 手动杀掉。

## 我的显存不足异常处理器无法分配内存

你可能写了从显存不足(OOM)错误中恢复的代码:

```python
try:
    run_model(batch_size)
except RuntimeError: # Out of memory
    for _ in range(batch_size):
        run_model(1)
```

但发现真正 OOM 时,恢复代码也无法分配内存。原因在于 Python 异常对象持有对抛出错误的栈帧的引用,导致原始张量对象无法被释放。解决方案是把 OOM 恢复代码移到 `except` 子句之外:

```python
oom = False
try:
    run_model(batch_size)
except RuntimeError: # Out of memory
    oom = True

if oom:
    for _ in range(batch_size):
        run_model(1)
```

(dataloader-workers-random-seed)=

## 我的 data loader worker 返回了相同的随机数

你可能是在数据集中使用其他库生成随机数,而 worker 子进程是通过 `fork` 启动的。关于如何通过 {attr}`worker_init_fn` 选项在 worker 中正确设置随机种子,见 {class}`torch.utils.data.DataLoader` 的文档。

(pack-rnn-unpack-with-data-parallelism)=

## 我的循环网络无法与数据并行配合工作

在配置了 {class}`~torch.nn.DataParallel` 或 {func}`~torch.nn.parallel.data_parallel` 的 {class}`~torch.nn.Module` 中使用 `pack sequence -> recurrent network -> unpack sequence` 模式有个微妙之处:每个设备上 {meth}`forward` 的输入只是整个输入的一部分。由于解包操作 {func}`torch.nn.utils.rnn.pad_packed_sequence` 默认只填充到它所见的最长输入——即该设备上的最长序列——结果汇聚时就会出现尺寸不一致。为此,可以利用 {func}`~torch.nn.utils.rnn.pad_packed_sequence` 的 {attr}`total_length` 参数,确保各 {meth}`forward` 调用返回等长序列。例如:

```python
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

class MyModule(nn.Module):
    # ... __init__, other methods, etc.

    # padded_input is of shape [B x T x *] (batch_first mode) and contains
    # the sequences sorted by lengths
    #   B is the batch size
    #   T is max sequence length
    def forward(self, padded_input, input_lengths):
        total_length = padded_input.size(1)  # get the max sequence length
        packed_input = pack_padded_sequence(padded_input, input_lengths,
                                            batch_first=True)
        packed_output, _ = self.my_lstm(packed_input)
        output, _ = pad_packed_sequence(packed_output, batch_first=True,
                                        total_length=total_length)
        return output


m = MyModule().cuda()
dp_m = nn.DataParallel(m)
```

此外,当 batch 维是第 1 维(即 `batch_first=False`)时,数据并行需要格外小心。此时 `pack_padded_sequence` 的第一个参数 `padding_input` 形状为 `[T x B x *]`,应沿第 1 维散布;而第二个参数 `input_lengths` 形状为 `[B]`,应沿第 0 维散布。需要额外代码来处理张量形状。
