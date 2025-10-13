#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Outlook 邮箱读取工具
支持使用 Microsoft Graph API 或 IMAP 读取最新邮件
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional


class OutlookEmailReader:
    """Outlook 邮箱读取类"""
    
    def __init__(self, email: str, password: str = None, client_id: str = None, access_token: str = None):
        """
        初始化
        
        Args:
            email: 邮箱地址
            password: 邮箱密码（IMAP 方式）
            client_id: Microsoft 应用 ID
            access_token: 访问令牌（Graph API 方式）
        """
        self.email = email
        self.password = password
        self.client_id = client_id
        self.access_token = access_token
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
    
    def get_latest_emails_with_token(self, count: int = 10) -> List[Dict]:
        """
        使用 access_token 读取最新邮件（Graph API）
        
        Args:
            count: 获取邮件数量，默认10封
            
        Returns:
            邮件列表
        """
        if not self.access_token:
            raise ValueError("需要提供 access_token")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # 获取收件箱邮件，按接收时间降序排列
        url = f"{self.graph_endpoint}/me/messages"
        params = {
            "$top": count,
            "$orderby": "receivedDateTime DESC",
            "$select": "subject,from,receivedDateTime,bodyPreview,isRead,hasAttachments"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            emails = data.get("value", [])
            
            # 格式化输出
            formatted_emails = []
            for email in emails:
                formatted_email = {
                    "id": email.get("id"),
                    "subject": email.get("subject", "无主题"),
                    "from": email.get("from", {}).get("emailAddress", {}).get("address", "未知"),
                    "from_name": email.get("from", {}).get("emailAddress", {}).get("name", "未知"),
                    "received_time": email.get("receivedDateTime"),
                    "preview": email.get("bodyPreview", "")[:200],  # 前200字符
                    "is_read": email.get("isRead", False),
                    "has_attachments": email.get("hasAttachments", False)
                }
                formatted_emails.append(formatted_email)
            
            return formatted_emails
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   状态码: {e.response.status_code}")
                print(f"   响应内容: {e.response.text}")
            return []
    
    def get_email_detail(self, email_id: str) -> Optional[Dict]:
        """
        获取邮件详细内容
        
        Args:
            email_id: 邮件ID
            
        Returns:
            邮件详情
        """
        if not self.access_token:
            raise ValueError("需要提供 access_token")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.graph_endpoint}/me/messages/{email_id}"
        params = {
            "$select": "subject,from,receivedDateTime,body,hasAttachments,attachments"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            email = response.json()
            
            return {
                "id": email.get("id"),
                "subject": email.get("subject", "无主题"),
                "from": email.get("from", {}).get("emailAddress", {}).get("address"),
                "from_name": email.get("from", {}).get("emailAddress", {}).get("name"),
                "received_time": email.get("receivedDateTime"),
                "body_type": email.get("body", {}).get("contentType"),
                "body_content": email.get("body", {}).get("content"),
                "has_attachments": email.get("hasAttachments", False),
                "attachments": email.get("attachments", [])
            }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 获取邮件详情失败: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str, client_secret: str, tenant_id: str = "common") -> Optional[str]:
        """
        使用 refresh_token 获取新的 access_token
        
        Args:
            refresh_token: 刷新令牌
            client_secret: 应用密钥
            tenant_id: 租户ID，默认 "common"
            
        Returns:
            新的 access_token
        """
        if not self.client_id:
            raise ValueError("需要提供 client_id")
        
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": "https://graph.microsoft.com/Mail.Read"
        }
        
        try:
            response = requests.post(token_url, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            new_access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token")
            
            print(f"✅ 成功刷新 access_token")
            if new_refresh_token:
                print(f"   新的 refresh_token: {new_refresh_token[:50]}...")
            
            self.access_token = new_access_token
            return new_access_token
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 刷新令牌失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   响应内容: {e.response.text}")
            return None


def parse_account_info(account_line: str) -> Dict[str, str]:
    """
    解析账号信息
    格式：邮箱----密码----id-----令牌
    
    Args:
        account_line: 账号信息字符串
        
    Returns:
        解析后的字典
    """
    parts = account_line.split("----")
    
    if len(parts) < 4:
        raise ValueError(f"账号格式错误，应为：邮箱----密码----id-----令牌，实际收到 {len(parts)} 个部分")
    
    return {
        "email": parts[0].strip(),
        "password": parts[1].strip(),
        "client_id": parts[2].strip(),
        "token": parts[3].strip()
    }


def main():
    """主函数 - 示例用法"""
    
    print("=" * 60)
    print("Outlook 邮箱读取工具")
    print("=" * 60)
    
    # 方式1：从字符串解析账号信息
    account_info_str = "user@outlook.com----password123----app-id-here----access_token_here"
    
    try:
        # 解析账号信息
        account = parse_account_info(account_info_str)
        print(f"\n📧 邮箱: {account['email']}")
        print(f"🔑 Token: {account['token'][:50]}..." if len(account['token']) > 50 else account['token'])
        
        # 创建读取器（使用 access_token）
        reader = OutlookEmailReader(
            email=account['email'],
            client_id=account['client_id'],
            access_token=account['token']
        )
        
        print("\n📬 正在获取最新邮件...")
        emails = reader.get_latest_emails_with_token(count=5)
        
        if emails:
            print(f"\n✅ 成功获取 {len(emails)} 封邮件\n")
            
            for i, email in enumerate(emails, 1):
                print(f"{'='*60}")
                print(f"📨 邮件 {i}")
                print(f"{'='*60}")
                print(f"主题: {email['subject']}")
                print(f"发件人: {email['from_name']} <{email['from']}>")
                print(f"时间: {email['received_time']}")
                print(f"已读: {'是' if email['is_read'] else '否'}")
                print(f"有附件: {'是' if email['has_attachments'] else '否'}")
                print(f"预览: {email['preview']}")
                print()
        else:
            print("\n⚠️  未获取到邮件或请求失败")
        
    except ValueError as e:
        print(f"\n❌ 错误: {e}")
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()


# 如果需要使用 refresh_token 刷新
def example_with_refresh_token():
    """使用 refresh_token 的示例"""
    
    # 账号信息
    email = "your-email@outlook.com"
    client_id = "your-client-id"
    client_secret = "your-client-secret"  # 需要从 Azure 应用获取
    refresh_token = "your-refresh-token"
    
    # 创建读取器
    reader = OutlookEmailReader(
        email=email,
        client_id=client_id
    )
    
    # 刷新令牌
    print("🔄 正在刷新 access_token...")
    access_token = reader.refresh_access_token(
        refresh_token=refresh_token,
        client_secret=client_secret
    )
    
    if access_token:
        # 读取邮件
        print("\n📬 正在获取最新邮件...")
        emails = reader.get_latest_emails_with_token(count=10)
        
        for i, email in enumerate(emails, 1):
            print(f"\n邮件 {i}: {email['subject']}")
            print(f"  发件人: {email['from']}")
            print(f"  时间: {email['received_time']}")


if __name__ == "__main__":
    main()
    
    # 如果需要查看 refresh_token 示例，取消下面的注释
    # print("\n" + "="*60)
    # print("使用 refresh_token 的示例")
    # print("="*60)
    # example_with_refresh_token()
