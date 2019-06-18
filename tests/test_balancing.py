import time

import pytest
import torch
from torch import nn

from torchgpipe_balancing import balance_by_size, balance_by_time, blockpartition


def test_blockpartition():
    assert blockpartition.solve([1, 2, 3, 4, 5, 6], partitions=2) == [[1, 2, 3, 4], [5, 6]]


def test_blockpartition_zeros():
    assert blockpartition.solve([0, 0], partitions=2) == [[0], [0]]


def test_blockpartition_non_positive_partitions():
    with pytest.raises(ValueError):
        blockpartition.solve([42], partitions=0)
    with pytest.raises(ValueError):
        blockpartition.solve([42], partitions=-1)


def test_blockpartition_short_sequence():
    with pytest.raises(ValueError):
        blockpartition.solve([], partitions=1)
    with pytest.raises(ValueError):
        blockpartition.solve([42], partitions=2)


def test_balance_by_time():
    class Delay(nn.Module):
        def __init__(self, seconds):
            super().__init__()
            self.seconds = seconds

        def forward(self, x):
            time.sleep(self.seconds)
            return x

    model = nn.Sequential(*[Delay(i/100) for i in [1, 2, 3, 4, 5, 6]])
    sample = torch.rand(1)
    balance = balance_by_time(model, sample, partitions=2, device='cpu')
    assert balance == [4, 2]


# balance_by_size supports only CUDA device.
@pytest.mark.skipif(not torch.cuda.is_available(), reason='cuda required')
def test_balance_by_size():
    class Expand(nn.Module):
        def __init__(self, times):
            super().__init__()
            self.times = times

        def forward(self, x):
            for i in range(self.times):
                x = x + torch.rand_like(x, requires_grad=True)
            return x

    model = nn.Sequential(*[Expand(i) for i in [1, 2, 3, 4, 5, 6]])
    sample = torch.rand(10, 100, 100)
    balance = balance_by_size(model, sample, partitions=2, device='cuda')
    assert balance == [4, 2]
