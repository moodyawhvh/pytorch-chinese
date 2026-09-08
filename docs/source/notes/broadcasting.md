(broadcasting-semantics)=

# 广播语义(Broadcasting semantics)

> 🌐 本文档由 [pytorch/pytorch](https://github.com/pytorch/pytorch) 翻译,英文原版见原项目。

许多 PyTorch 运算支持 NumPy 的广播语义。细节参见 [NumPy 文档](https://numpy.org/doc/stable/user/basics.broadcasting.html)。

简而言之,如果一个 PyTorch 运算支持广播,那么它的 Tensor 参数可以被自动扩展为相同尺寸(且不复制数据)。

## 一般语义

两个张量满足以下规则即为"可广播(broadcastable)":

- 从末尾维度开始逐个对比维度大小,每一处要么相等,要么其中一方为 1,要么其中一方该维度不存在。

例如:

```python
>>> x=torch.empty(5,7,3)
>>> y=torch.empty(5,7,3)
# same shapes are always broadcastable (i.e. the above rules always hold)

>>> x=torch.empty((0,))
>>> y=torch.empty(2,2)
# x and y are not broadcastable, because the 0-sized dimension of x
# does not match the 2-sized dimension of y.

# can line up trailing dimensions
>>> x=torch.empty(5,3,4,1)
>>> y=torch.empty(  3,1,1)
# x and y are broadcastable.
# 1st trailing dimension: both have size 1
# 2nd trailing dimension: y has size 1
# 3rd trailing dimension: x size == y size
# 4th trailing dimension: y dimension doesn't exist

# but:
>>> x=torch.empty(5,2,4,1)
>>> y=torch.empty(  3,1,1)
# x and y are not broadcastable, because in the 3rd trailing dimension 2 != 3
```

若两个张量 `x`、`y` "可广播",结果张量的尺寸按以下方式计算:

- 如果 `x` 与 `y` 的维数不同,则在维数较少的张量的维度前面补 1,使两者维数一致。
- 然后,对每个维度,结果维度大小取 `x` 与 `y` 在该维度上的最大值。

例如:

```python
# can line up trailing dimensions to make reading easier
>>> x=torch.empty(5,1,4,1)
>>> y=torch.empty(  3,1,1)
>>> (x+y).size()
torch.Size([5, 3, 4, 1])

# but not necessary:
>>> x=torch.empty(1)
>>> y=torch.empty(3,1,7)
>>> (x+y).size()
torch.Size([3, 1, 7])

>>> x=torch.empty(5,2,4,1)
>>> y=torch.empty(3,1,1)
>>> (x+y).size()
RuntimeError: The size of tensor a (2) must match the size of tensor b (3) at non-singleton dimension 1
```

## 原地(in-place)语义

一个复杂之处在于:原地操作不允许作为操作目标的张量因广播而改变形状。

例如:

```python
>>> x=torch.empty(5,3,4,1)
>>> y=torch.empty(3,1,1)
>>> (x.add_(y)).size()
torch.Size([5, 3, 4, 1])

# but:
>>> x=torch.empty(1,3,1)
>>> y=torch.empty(3,1,7)
>>> (x.add_(y)).size()
RuntimeError: The expanded size of the tensor (1) must match the existing size (7) at non-singleton dimension 2.
```

## 向后兼容性

旧版 PyTorch 允许某些逐点(pointwise)函数在形状不同、但元素数量相等的张量上执行:逐点运算会把每个张量都当作一维张量来处理。PyTorch 现已支持广播,"一维"逐点行为被视为已废弃:当张量不可广播但元素数量相同时,会产生 Python 警告。

注意,当两个张量形状不同但可广播且元素数量相等时,广播的引入可能造成向后不兼容的变化。例如:

```python
>>> torch.add(torch.ones(4,1), torch.randn(4))
```

过去会产生尺寸为 torch.Size([4,1]) 的张量,现在则产生尺寸为 torch.Size([4,4]) 的张量。为帮助识别代码中可能存在广播引入的向后不兼容的场景,可以把 `torch.utils.backcompat.broadcast_warning.enabled` 设为 `True`,上述情形将产生 Python 警告。

例如:

```python
>>> torch.utils.backcompat.broadcast_warning.enabled=True
>>> torch.add(torch.ones(4,1), torch.ones(4))
__main__:1: UserWarning: self and other do not have the same shape, but are broadcastable, and have the same number of elements.
Changing behavior in a backwards incompatible manner to broadcasting rather than viewing as 1-dimensional.
```
