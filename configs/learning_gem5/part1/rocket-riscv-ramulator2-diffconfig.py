# Copyright (c) 2015 Jason Power
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
This is the RISCV equivalent to `simple.py` (which is designed to run using the
X86 ISA). More detailed documentation can be found in `simple.py`.
"""

import argparse

from caches import *

import m5
from m5.objects import *

parser = argparse.ArgumentParser()
parser.add_argument(
    "--wkload",
    type=str,
    default="/home/tongxian/myProjects/workloads/openblas-related/app-of-open\
        blas-as-wkload/wkloadUsingOpenBLAS-riscv64-linux",
)

args = parser.parse_args()

system = System()

system.clk_domain = SrcClockDomain()  # 设置cpu时钟域
system.clk_domain.clock = "1GHz"  # 设置cpu主频
system.clk_domain.voltage_domain = (
    VoltageDomain()
)  # 设置电压域，这是gem5模拟cpu功耗时需要的参数

system.mem_mode = "timing"  # 设置模拟时mem的类型，需要设定为timing类型才能调动外部集成的ramulator2模拟器
system.mem_ranges = [AddrRange("1GiB")]  # 设置内存地址空间大小
system.cpu = (
    RiscvTimingSimpleCPU()
)  # 设置模拟是cpu的类型，TimingSimpleCPU模拟最接近现实的，但是耗费时间也最长

system.cpu.icache = L1ICache()
system.cpu.dcache = L1DCache()  # 创建L1缓存,并且初始化容量

system.cpu.icache.cpu_side = system.cpu.icache_port
system.cpu.dcache.cpu_side = system.cpu.dcache_port  # L1缓存直连cpu

system.l2bus = (
    SystemXBar()
)  # 设置模拟时候连接l2 cache的总线的类型，在gem5中，总线名字为l2bus，设置类型为systemxbar即可。

system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
system.cpu.dcache.mem_side = (
    system.l2bus.cpu_side_ports
)  # l1 cache与SystemXBar相连

system.l2cache = L2Cache()  # 创建L2缓存，并初始化容量

system.membus = SystemXBar()  # 创建membus并且设置模拟时的类型

system.l2cache.cpu_side = system.l2bus.mem_side_ports
system.l2cache.mem_side = system.membus.cpu_side_ports  # 连接L2 cache

system.mem_ctrl = (
    Ramulator2()
)  # 创建gem5内存控制器，并且选择类型。Ramulator2即为集成的ramulator2外部模拟器。
system.mem_ctrl.config_path = (
    "diff2-trace_and_timing_config.yaml"  # 集成的ramulator2内存配置文件。
)
system.mem_ctrl.port = system.membus.mem_side_ports  # 内存控制器连接至总线


system.cpu.createInterruptController()

thispath = os.path.dirname(os.path.realpath(__file__))
# binary = os.path.join(
#    thispath,
#    "../../../",
#    "tests/test-progs/hello/bin/riscv/linux/hello",
# )
# binary = "/home/tongxian/myProjects/workloads/matrix-mul/mat-mul-riscv-linux"
binary = args.wkload

system.workload = SEWorkload.init_compatible(binary)

process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print(f"Beginning simulation!")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
