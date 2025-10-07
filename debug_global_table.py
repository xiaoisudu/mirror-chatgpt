#!/usr/bin/env python3
"""
全局对象表调试工具
展示 React Flight Protocol 如何使用全局对象表
"""

import json
from typing import Any, Dict

class ReactFlightDebugger:
    def __init__(self, data_array):
        self.data = data_array
        self.global_table = {}
        self.build_global_table()
    
    def build_global_table(self):
        """构建全局对象表（实际上就是数组本身）"""
        for idx, item in enumerate(self.data):
            self.global_table[idx] = item
        print(f"✅ 全局对象表已构建：{len(self.global_table)} 个条目")
    
    def resolve_reference(self, ref_id: int) -> Any:
        """解析引用"""
        if ref_id == -5:
            return None
        if ref_id == -7:
            return "<undefined>"  # 用特殊标记表示
        if ref_id in self.global_table:
            return self.global_table[ref_id]
        return f"<未找到: {ref_id}>"
    
    def resolve_object(self, obj: Any, depth=0, max_depth=3) -> Any:
        """递归解析对象中的所有引用"""
        if depth > max_depth:
            return "<max depth reached>"
        
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if key.startswith('_'):
                    # 这是一个引用
                    ref_id = value
                    resolved_value = self.resolve_reference(ref_id)
                    # 递归解析
                    resolved_value = self.resolve_object(resolved_value, depth + 1, max_depth)
                    # 去掉下划线前缀作为真实属性名
                    real_key = key[1:]
                    result[real_key] = resolved_value
                else:
                    # 直接属性
                    result[key] = self.resolve_object(value, depth + 1, max_depth)
            return result
        
        elif isinstance(obj, list):
            return [self.resolve_object(item, depth + 1, max_depth) for item in obj]
        
        else:
            return obj
    
    def print_table_range(self, start: int, end: int):
        """打印全局表的某个范围"""
        print(f"\n{'='*80}")
        print(f"全局对象表 [{start}..{end}]")
        print(f"{'='*80}")
        for i in range(start, min(end + 1, len(self.data))):
            item = self.global_table[i]
            type_name = type(item).__name__
            
            if isinstance(item, dict):
                refs = {k: v for k, v in item.items() if k.startswith('_')}
                direct = {k: v for k, v in item.items() if not k.startswith('_')}
                
                if refs:
                    print(f"[{i:4d}] {type_name:10s} 引用: {refs}")
                if direct:
                    print(f"       {'':10s} 直接: {direct}")
            
            elif isinstance(item, str):
                display = item if len(item) <= 50 else item[:47] + "..."
                print(f"[{i:4d}] {type_name:10s} '{display}'")
            
            elif isinstance(item, list):
                print(f"[{i:4d}] {type_name:10s} 长度={len(item)} {item[:3]}...")
            
            else:
                print(f"[{i:4d}] {type_name:10s} {item}")
    
    def demonstrate_resolution(self, start_index: int):
        """演示从某个索引开始的解析过程"""
        print(f"\n{'='*80}")
        print(f"🔍 演示：从索引 {start_index} 开始解析")
        print(f"{'='*80}")
        
        item = self.global_table[start_index]
        print(f"\n原始数据 [{start_index}]:")
        print(json.dumps(item, indent=2, ensure_ascii=False))
        
        print(f"\n解析后的对象:")
        resolved = self.resolve_object(item, max_depth=2)
        print(json.dumps(resolved, indent=2, ensure_ascii=False, default=str))
    
    def find_by_value(self, search_value: str, limit=10):
        """在全局表中搜索包含特定值的条目"""
        print(f"\n{'='*80}")
        print(f"🔎 搜索包含 '{search_value}' 的条目")
        print(f"{'='*80}")
        
        found = 0
        for idx, item in self.global_table.items():
            if isinstance(item, str) and search_value in item:
                print(f"[{idx:4d}] '{item}'")
                found += 1
                if found >= limit:
                    break
        
        if found == 0:
            print("未找到匹配项")
        else:
            print(f"\n找到 {found} 个匹配项")


# 使用示例
if __name__ == "__main__":
    print("🚀 React Flight Protocol 全局对象表调试器")
    print("="*80)
    
    # 加载数据
    with open('templates/chatgpt_context_1.json', 'r', encoding='utf-8') as f:
        context1 = json.load(f)
    
    with open('templates/chatgpt_context_2.json', 'r', encoding='utf-8') as f:
        context2 = json.load(f)
    
    print(f"\n📦 加载的数据:")
    print(f"  context_1: {len(context1)} 个元素")
    print(f"  context_2: {len(context2)} 个元素")
    
    # 创建调试器
    debugger = ReactFlightDebugger(context1)
    
    # 1. 显示表的开始部分
    debugger.print_table_range(0, 30)
    
    # 2. 演示解析过程
    debugger.demonstrate_resolution(0)
    debugger.demonstrate_resolution(4)
    debugger.demonstrate_resolution(14)
    
    # 3. 搜索特定值
    debugger.find_by_value("GPT", limit=5)
    debugger.find_by_value("accessToken")
    
    # 4. 显示重要的索引区域
    print("\n" + "="*80)
    print("📍 重要数据区域")
    print("="*80)
    
    # 用户信息区域
    print("\n👤 用户信息 (索引 19-50):")
    debugger.print_table_range(19, 50)
    
    # 查找模型相关数据
    print("\n" + "="*80)
    print("🤖 查找模型相关数据")
    print("="*80)
    
    for idx in range(len(context1)):
        item = context1[idx]
        if isinstance(item, str) and 'gpt' in item.lower():
            print(f"[{idx:4d}] {item}")
    
    print("\n" + "="*80)
    print("✅ 调试完成")
    print("="*80)
