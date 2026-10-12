# 小米 14 / Jev v1.3 实测交接

截至 2026-09-27。后续会话先重新核对，不把这里的连接地址、权限和应用状态当作实时值。

- 设备：小米 14（`23127PN0CC`），HyperOS 3.0 / Android 16。无线 ADB 的 IP、端口和 transport ID 多次变化；先用 `adb devices -l` 与 `adb mdns services`，必要时向用户要“无线调试”主页的当前地址。
- 原版：`com.jev.probe`，Jev v1.3。用户选择保留它，因为 v1.4 去掉了微信支持。原版已配置判断和回复接口；应用内两项测试成功。不要读取或导出其密钥。原版无障碍与悬浮窗曾启用。
- 飞书的具体聊天窗口实测出现 Jev 悬浮窗；微信具体聊天窗口没有。微信 `uiautomator dump` 只返回空根节点；注意这不直接证明 Jev 伪装服务看到的树相同，但与未触发行为一致。
- [v1.3 ChatCaptureService.kt](https://github.com/jev-chat/jev-chat-jarvis/blob/v1.3/app/src/main/java/com/jev/probe/capture/ChatCaptureService.kt) 在 `adapter.extract(root, resources)` 返回 `null` 时直接退出，悬浮球和 OCR 均不触发。[v1.3 WeChatAdapter](https://github.com/jev-chat/jev-chat-jarvis/blob/v1.3/app/src/main/java/com/jev/probe/capture/ChatAppAdapter.kt) 只在找到 `com.tencent.mm:id/bkl` 时认定聊天页。[v1.4](https://github.com/jev-chat/jev-chat-jarvis/blob/v1.4/app/src/main/java/com/jev/probe/capture/ChatCaptureService.kt) 已把 `null` 分支改为显示闲置悬浮球，但它禁用了微信。
- 本地回移补丁在 `C:\Users\admin\Documents\Codex\2026-09-23\r\work\jev-v1.3-fix`。`app/src/main/java/com/jev/probe/capture/ChatCaptureService.kt` 回移 v1.4 的闲置悬浮球分支；调试构建另用包名 `com.jev.probe.test`、名称“Jev修复测试版”，避免覆盖原版。`assembleDebug` 成功，APK 在 `app/build/outputs/apk/debug/app-debug.apk`。调试签名与原版发布签名不同，不能就地覆盖并保留原版数据。
- 测试版已并列安装，但在用户要求暂停后，已通过系统设置关闭测试版无障碍服务；原版服务仍在启用列表。测试版尚未完成微信悬浮球实测。恢复时先检查这两项当前状态，再给测试版授权并测试。若暂停，关闭测试服务和待确认的系统弹窗。
- 此补丁的预期仅是让微信控件树不可读时仍可手动进入“截屏识别一次”。它没有证明自动新消息分析可用；手动 OCR 会读取屏幕可见文字，测试时使用非敏感会话，勿在支付或隐私界面触发。

## 2026-09-28 续测

- 无线 ADB 重连后，两版并存。测试版无障碍、悬浮窗在系统页面启用；`dumpsys accessibility` 确认服务已绑定。微信聊天页能看到测试版悬浮球，长按约半秒才会出现“截屏识别一次”菜单；轻点只展开分析面板。
- 微信聊天页 `uiautomator dump` 只有一个根节点、没有消息气泡。测试版手动截屏的窗口 API 返回错误码 6。加入全屏截屏回退后 API 可成功，但 1200×2670 画面是纯黑，OCR 为 0；ADB `screencap` 也基本全黑。`dumpsys window` 显示微信前台 `LauncherUI` 带 `SECURE` 标志。故障发生在读取画面阶段，与判断接口密钥无关；不应把改 OCR 或填密钥当成解决此保护的办法。
- 本地 fork 继续保留 v1.3 与并列包名 `com.jev.probe.test`；增加受保护黑屏的明确提示，以及“手动粘贴消息”页面（主界面与长按悬浮球菜单均可进入）。用户可在微信手动复制非敏感消息，粘贴后调用 Jev 判断并手动复制候选回复；不会自动读取或发送。APK 已构建并安装。用户在测试版设置中亲自填入密钥后，以虚构消息 `hello` 实机验证：约 1 秒返回判断与 3 条候选回复。测试版是独立数据区，不要尝试读取或迁移原版密钥。
- 原版 `com.jev.probe` 保留。后续恢复时，先核对当时的无障碍、悬浮窗、测试版密钥和用户所处页面；无线 ADB 地址只是临时连接信息。
