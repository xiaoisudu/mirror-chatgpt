#!/usr/bin/env python3
"""
打印全局对象表到文件
"""
import json

# 读取数据
context1 = json.load(open('templates/chatgpt_context_1.json'))
context2 = json.load(open('templates/chatgpt_context_2.json'))

output_file = 'global_table_output.txt'

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 100 + "\n")
    f.write("React Flight Protocol 全局对象表\n")
    f.write("=" * 100 + "\n\n")
    
    f.write(f"📊 数据统计:\n")
    f.write(f"  - chatgpt_context_1.json: {len(context1)} 个元素\n")
    f.write(f"  - chatgpt_context_2.json: {len(context2)} 个元素\n\n")
    
    f.write("=" * 100 + "\n")
    f.write("全局对象表详细内容 (context_1)\n")
    f.write("=" * 100 + "\n\n")
    
    for idx, item in enumerate(context1):
        f.write(f"[{idx:4d}] ")
        
        if isinstance(item, dict):
            # 分离引用和直接属性
            refs = {k: v for k, v in item.items() if k.startswith('_')}
            direct = {k: v for k, v in item.items() if not k.startswith('_')}
            
            if refs:
                f.write(f"(引用对象) {refs}\n")
            if direct:
                f.write(f"       (直接属性) {json.dumps(direct, ensure_ascii=False)}\n")
            
        elif isinstance(item, str):
            display = item if len(item) <= 80 else item[:77] + "..."
            f.write(f"(字符串) '{display}'\n")
        
        elif isinstance(item, list):
            if len(item) <= 5:
                f.write(f"(数组) {item}\n")
            else:
                f.write(f"(数组) 长度={len(item)}, 前5项={item[:5]}\n")
        
        elif isinstance(item, bool):
            f.write(f"(布尔) {item}\n")
        
        elif isinstance(item, int):
            f.write(f"(整数) {item}\n")
        
        elif item is None:
            f.write(f"(null)\n")
        
        else:
            f.write(f"({type(item).__name__}) {str(item)[:80]}\n")
    
    # 特殊索引标记
    f.write("\n" + "=" * 100 + "\n")
    f.write("🔍 关键索引位置\n")
    f.write("=" * 100 + "\n\n")
    
    key_positions = {
        "用户ID": 22,
        "用户邮箱": 24,
        "认证状态": 16,
        "accessToken位置": 43,
        "accessToken值": 44,
    }
    
    for name, idx in key_positions.items():
        if idx < len(context1):
            f.write(f"{name:20s} [{idx:4d}] {context1[idx]}\n")
    
    # 引用统计
    f.write("\n" + "=" * 100 + "\n")
    f.write("📈 引用统计\n")
    f.write("=" * 100 + "\n\n")
    
    all_refs = {}
    for idx, item in enumerate(context1):
        if isinstance(item, dict):
            for key, value in item.items():
                if key.startswith('_') and isinstance(value, int):
                    all_refs[key] = value
    
    f.write(f"总引用数: {len(all_refs)}\n")
    f.write(f"引用键范围: {min(all_refs.keys())} 到 {max(all_refs.keys())}\n")
    f.write(f"引用值范围: {min(all_refs.values())} 到 {max(all_refs.values())}\n\n")
    
    f.write("特殊值计数:\n")
    special_values = {-5: 'null', -7: 'undefined'}
    for special_val, meaning in special_values.items():
        count = sum(1 for v in all_refs.values() if v == special_val)
        f.write(f"  {special_val:3d} ({meaning:10s}): {count} 次\n")
    
    # Context 2
    f.write("\n" + "=" * 100 + "\n")
    f.write("全局对象表详细内容 (context_2)\n")
    f.write("=" * 100 + "\n\n")
    
    for idx, item in enumerate(context2):
        f.write(f"[{idx:4d}] ")
        
        if isinstance(item, dict):
            f.write(f"(对象) {json.dumps(item, ensure_ascii=False)[:100]}\n")
        elif isinstance(item, str):
            f.write(f"(字符串) '{item}'\n")
        elif isinstance(item, list):
            if len(item) <= 10:
                f.write(f"(数组) {item}\n")
            else:
                f.write(f"(数组) 长度={len(item)}\n")
        else:
            f.write(f"({type(item).__name__}) {item}\n")

print(f"✅ 全局对象表已导出到: {output_file}")
print(f"📊 数据统计:")
print(f"  - context_1: {len(context1)} 个元素")
print(f"  - context_2: {len(context2)} 个元素")
print(f"\n💡 查看完整内容:")
print(f"   cat {output_file}")
print(f"   或")
print(f"   head -100 {output_file}")
