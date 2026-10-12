# RoCE 光模块与物理链路采集

## 已核验的 mlxlink 网卡端口规则

NVIDIA MFT v4.26 官方文档明确：查询 NIC 不使用 label_port 参数 `-p`，以不同物理设备选择端口；交换机端口查询才使用 `-p`。PCI function 或 MST 设备应来自现场映射。

- `ethtool -i "$nic"` 的 `bus-info` 获取当前接口 PCI 地址。
- 双端口设备可以分别暴露 `.0` 和 `.1` function，但必须逐接口核验，不能固定假定所有节点的 eth 编号相同。
- 对普通 PCI 访问：`mlxlink -d "$dev" --show_module`、`mlxlink -d "$dev" --show_counters`，不追加 `-p 2`。
- `Please Provide the Physical Device of Port 2` 可能是错误使用 `-p 2` 引发的参数检查，并不是模块故障。对第二个 function 仍带 `-p 2` 不会修复这个问题。
- MFT 模块未加载的提示并不等于 PCI 查询失败；以实际查询的退出码和输出为准，不把 `mst start`、驱动安装或重启当作读数据的默认前置动作。

参考：[NVIDIA MFT v4.26 手册](https://docs.nvidia.com/nvidia-firmware-tools-mft-documentation-v4-26.pdf)，Tool Usage with NIC vs. Switch (-p Flag)；规则已在 MFT 4.26.1-3 的 BlueField-3 环境经用户真实输出验证。

## 主机内只读查询片段

交付时预填已核对的网口，并在用户真实入口上组织 SSH 批量执行。以下片段假设 `nic` 已赋值：

```bash
dev=$(ethtool -i "$nic" | awk '/^bus-info:/ {print $2}')
if [ -z "$dev" ]; then
    printf 'ERROR: missing PCI address for %s\n' "$nic"
else
    printf 'NIC=%s PCI=%s\n' "$nic" "$dev"
    ethtool -P "$nic"
    date -Ins
    timeout 30s mlxlink -d "$dev" --show_module
    printf 'MODULE_EXIT=%s\n' "$?"
    timeout 30s mlxlink -d "$dev" --show_counters
    printf 'COUNTERS_EXIT=%s\n' "$?"
fi
```

保留接口、PCI、模块型号/序列号、每个通道 Tx/Rx 功率、工具显示范围、温度、电压、LOS/故障标志、时间戳、有效错误、原始 BER 和上次清零时间。只有成功查询的记录可用。

## 判读与下一步

- 网卡 Rx 纠错增长偏高时，首先关注对端 Tx → 本机 Rx 路径；也采集反向和同 bond 的对照口。
- `ethtool -m` 可能只给出原始 EEPROM 数据而没有光功率。没有诊断页时不能猜测各通道功率；可用已安装的厂商工具补查。
- 光功率在工具显示范围内、LOS 为 0，仅说明当前没有这些越限证据，不能排除物理信号质量差、间歇故障或主机电气侧问题。
- Raw BER 不等于纠错后的业务误码；同时核对 Effective Physical Errors、CRC、不可纠正 FEC 和故障时间。`15E-255` 等接近零的工具显示不作为可信的精确 BER 测量。
- 累计计数及 BER 要保留 Time Since Last Clear，不把长时间累计值当作短窗口实时值。纠错计数/秒也不是 BER，不能在没有对应比特分母时换算。
- 本端 Tx 减本端 Rx 不是链路光衰。按确认映射的光通道计算：本端 Tx(dBm) − 对端 Rx(dBm)，以及对端 Tx(dBm) − 本端 Rx(dBm)。考虑诊断读数误差与链路预算；单侧数据不足时明确未闭环。
- 网卡 lane 与模块 channel、交换机分拆子端口不一定同编号；从布线、LLDP、模块资料和对端实际输出核验，不能直接把 lane 1 等同 Channel 1。
- 联合排查至少交付服务器接口/PCI/永久 MAC/模块序列号 → 交换机标识/IP/完整端口名/光通道的映射，以及两端采集时间、Tx/Rx、阈值和错误计数。保持 PPU 计算卡环境与网卡环境的区分。
