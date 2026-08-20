#!/bin/bash
# 元宝插件手动安装脚本
# 用于 openclaw plugins install 失败时的兜底方案

set -e

PLUGIN_NAME="openclaw-plugin-yuanbao"
PLUGIN_DIR="$HOME/Library/Application Support/QClaw/openclaw/config/extensions/$PLUGIN_NAME"
TEMP_DIR="$HOME/Downloads/yuanbao-plugin-extract"

echo "🔧 元宝插件手动安装脚本"
echo "========================"

# Step 1: 下载插件 tarball
echo ""
echo "📦 Step 1: 下载插件..."
TARBALL_URL=$(curl -s https://registry.npmjs.org/$PLUGIN_NAME/latest | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['dist']['tarball'])")
echo "   Tarball URL: $TARBALL_URL"

rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"
curl -fsSL "$TARBALL_URL" | tar -xz -C "$TEMP_DIR" --strip-components=1
echo "   ✅ 下载完成"

# Step 2: 复制到 extensions 目录
echo ""
echo "📁 Step 2: 安装插件..."
mkdir -p "$PLUGIN_DIR"
cp -r "$TEMP_DIR"/* "$PLUGIN_DIR/"
echo "   ✅ 插件已安装到: $PLUGIN_DIR"

# Step 3: 安装依赖
echo ""
echo "📚 Step 3: 安装依赖..."
DEPS=("uuid" "ws" "protobufjs" "cos-nodejs-sdk-v5")

for dep in "${DEPS[@]}"; do
    echo "   安装 $dep..."
    url=$(curl -s "https://registry.npmjs.org/$dep/latest" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['dist']['tarball'])")
    mkdir -p "$PLUGIN_DIR/node_modules/$dep"
    curl -fsSL "$url" | tar -xz -C "$PLUGIN_DIR/node_modules/$dep" --strip-components=1
    echo "   ✅ $dep 完成"
done

# Step 4: 提示配置
echo ""
echo "========================"
echo "✅ 插件安装完成！"
echo ""
echo "⚠️  下一步：通过 gateway config.patch 写入配置"
echo ""
echo "请将以下 JSON 中的 <YOUR_APP_KEY> 和 <YOUR_APP_SECRET> 替换为您的实际凭证："
echo ""
echo '{ "action": "config.patch", "raw": { "plugins": { "allow": [..., "openclaw-plugin-yuanbao"], "entries": { "openclaw-plugin-yuanbao": { "enabled": true, "config": {} } } }, "channels": { "yuanbao": { "enabled": true, "appKey": "<YOUR_APP_KEY>", "appSecret": "<YOUR_APP_SECRET>" } } }, "note": "元宝插件配置已写入" }'
echo ""
echo "📌 凭证获取方式：前往 https://yuanbao.tencent.com/ 申请应用凭证"
echo ""
