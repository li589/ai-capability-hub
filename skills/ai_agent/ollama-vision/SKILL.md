---
name: ollama-vision
version: 1.0.0
description: ใช้ MDES Ollama vision models วิเคราะห์รูปภาพฟรี — qwen3-vl:8b (เร็ว) หรือ qwen3-vl:32b (แม่นยำ)
argument-hint: image_path_or_url [--model qwen3-vl:8b|qwen3-vl:32b] [--prompt 'describe this']
updated: 2026-05-06T00:00:00.000Z
install_source: official
install_method: download
skill_id: official_Qf1azztJ
enabled_at: 1787232395785
name_zh: ollama 视觉
---

# SKILL: ollama-vision v1.0
# บันทึก: สร้างจาก MDES Ollama models list — qwen3-vl รองรับ image input ฟรีไม่จำกัด

## Vision Models ที่มี

| Model | ขนาด | เหมาะกับ |
|-------|------|---------|
| `qwen3-vl:8b` | 8B | เร็ว, screenshot analysis, UI review |
| `qwen3-vl:32b` | 32B | แม่นยำ, complex diagrams, detailed analysis |
| `z-uo/qwen2.5vl_tools:7b` | 7B | tool-calling from image, structured output |

## Use Cases

- วิเคราะห์ screenshot, UI ของ Discord bot อนุ
- อ่าน diagram, architecture chart
- ตรวจ error ใน log screenshot
- วิเคราะห์ heartbeat graph
- organ health visualization

## Implementation

```bash
#!/bin/bash
# ollama-vision: analyze image with MDES Ollama
OLLAMA_TOKEN=$(grep "^OLLAMA_TOKEN=" /workspaces/Jit/.env | cut -d= -f2)
IMAGE="$1"  # path หรือ URL
PROMPT="${2:-อธิบายสิ่งที่เห็นในรูปนี้}"
MODEL="${MODEL:-qwen3-vl:8b}"

# Convert image to base64 if local file
if [ -f "$IMAGE" ]; then
  IMAGE_B64=$(base64 -w 0 "$IMAGE")
  PAYLOAD=$(python3 -c "
import json
payload = {
  'model': '${MODEL}',
  'prompt': '${PROMPT}',
  'images': ['${IMAGE_B64}'],
  'stream': False
}
print(json.dumps(payload))
")
else
  # URL — download first
  curl -s "$IMAGE" -o /tmp/vision_input.jpg
  IMAGE_B64=$(base64 -w 0 /tmp/vision_input.jpg)
  PAYLOAD=$(python3 -c "
import json
payload = {
  'model': '${MODEL}',
  'prompt': '${PROMPT}',
  'images': ['${IMAGE_B64}'],
  'stream': False
}
print(json.dumps(payload))
")
fi

curl -s --location 'https://ollama.mdes-innova.online/api/generate' \
  --header "Authorization: Bearer ${OLLAMA_TOKEN}" \
  --header 'Content-Type: application/json' \
  --data "$PAYLOAD" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','ERROR'))"
```

## Version History
ดู: /workspaces/Jit/ψ/memory/skills/SKILL-VERSIONS.md
