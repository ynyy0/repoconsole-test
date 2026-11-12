# 星河软件源

一个面向 iOS 越狱设备的 APT 插件仓库，托管在 GitHub Pages 上。

- 源地址：<https://ynyy0.github.io/repoconsole-test/>
- 支持架构：`iphoneos-arm` / `iphoneos-arm64` / `iphoneos-arm64e`
- 索引格式：`Packages`、`Packages.bz2`、`Packages.xz`、`Packages.zst`

## 添加源

在 Sileo / Zebra / Cydia 中添加上面的地址，或打开 [首页](https://ynyy0.github.io/repoconsole-test/) 点击「添加到 Sileo」。

## 仓库结构

```
debs/       插件 deb 包，按 <包名>_<版本>_<架构>.deb 命名
icons/      插件图标，文件名与包名一致（<包名>.png）
Packages*   插件索引与压缩版本，由工作流自动生成
Release     源信息与索引校验和，由工作流自动刷新
index.html  源介绍页
.github/    索引重建与 Pages 发布工作流
```

## 上传插件

把编译好的 `.deb` 放进 `debs/`，图标（可选）放进 `icons/`，推送到 `main`。
`Refresh APT package indexes` 工作流会扫描全部 deb、重建四种索引、刷新 `Release`
里的校验和并回写仓库；随后 `Deploy APT repo to GitHub Pages` 发布站点。

deb 的 `control` 里建议写全这些字段：

```
Package: com.example.demo
Name: 示例插件
Version: 1.0.0
Architecture: iphoneos-arm64
Section: Tweaks
Description: 一句话说明插件功能
Maintainer: 作者 <mail@example.com>
Author: 作者
```

未写 `Icon:` 的包会自动使用 `CydiaIcon.png`。
