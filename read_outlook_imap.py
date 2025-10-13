#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 IMAP 读取 Outlook 邮箱
适合使用邮箱密码或应用专用密码的场景
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict
import re


class OutlookIMAPReader:
    """使用 IMAP 读取 Outlook 邮箱"""
    
    # Outlook IMAP 服务器配置
    IMAP_SERVER = "outlook.office365.com"
    IMAP_PORT = 993
    
    def __init__(self, email_address: str, password: str):
        """
        初始化
        
        Args:
            email_address: 邮箱地址
            password: 邮箱密码或应用专用密码
        """
        self.email_address = email_address
        self.password = password
        self.mail = None
    
    def connect(self) -> bool:
        """
        连接到 IMAP 服务器
        
        Returns:
            是否连接成功
        """
        try:
            print(f"🔌 正在连接到 {self.IMAP_SERVER}:{self.IMAP_PORT}...")
            self.mail = imaplib.IMAP4_SSL(self.IMAP_SERVER, self.IMAP_PORT)
            
            print(f"🔐 正在登录 {self.email_address}...")
            self.mail.login(self.email_address, self.password)
            
            print("✅ 连接成功")
            return True
            
        except imaplib.IMAP4.error as e:
            print(f"❌ IMAP 错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.mail:
            try:
                self.mail.logout()
                print("👋 已断开连接")
            except:
                pass
    
    def decode_str(self, s):
        """解码邮件头部信息"""
        if s is None:
            return ""
        
        value, charset = decode_header(s)[0]
        if charset:
            try:
                value = value.decode(charset)
            except:
                value = value.decode('utf-8', errors='ignore')
        elif isinstance(value, bytes):
            value = value.decode('utf-8', errors='ignore')
        return str(value)
    
    def get_latest_emails(self, folder: str = "INBOX", count: int = 10) -> List[Dict]:
        """
        获取最新邮件
        
        Args:
            folder: 文件夹名称，默认 INBOX
            count: 获取数量
            
        Returns:
            邮件列表
        """
        if not self.mail:
            print("❌ 未连接到服务器")
            return []
        
        try:
            # 选择文件夹
            self.mail.select(folder)
            
            # 搜索所有邮件
            status, messages = self.mail.search(None, "ALL")
            
            if status != "OK":
                print("❌ 搜索邮件失败")
                return []
            
            # 获取邮件ID列表
            email_ids = messages[0].split()
            
            # 获取最新的 N 封邮件
            latest_email_ids = email_ids[-count:] if len(email_ids) > count else email_ids
            latest_email_ids = reversed(latest_email_ids)  # 最新的在前
            
            emails = []
            for email_id in latest_email_ids:
                email_data = self.fetch_email(email_id)
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"❌ 获取邮件失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def fetch_email(self, email_id) -> Dict:
        """
        获取单封邮件的详细信息
        
        Args:
            email_id: 邮件ID
            
        Returns:
            邮件信息字典
        """
        try:
            # 获取邮件数据
            status, msg_data = self.mail.fetch(email_id, "(RFC822)")
            
            if status != "OK":
                return None
            
            # 解析邮件
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # 提取基本信息
            subject = self.decode_str(email_message.get("Subject", ""))
            from_addr = self.decode_str(email_message.get("From", ""))
            to_addr = self.decode_str(email_message.get("To", ""))
            date = email_message.get("Date", "")
            
            # 提取正文
            body = self.get_email_body(email_message)
            
            # 检查是否有附件
            has_attachments = False
            for part in email_message.walk():
                if part.get_content_disposition() == "attachment":
                    has_attachments = True
                    break
            
            return {
                "id": email_id.decode() if isinstance(email_id, bytes) else str(email_id),
                "subject": subject,
                "from": from_addr,
                "to": to_addr,
                "date": date,
                "body": body[:500],  # 前500字符
                "has_attachments": has_attachments,
                "raw_message": email_message  # 完整的邮件对象
            }
            
        except Exception as e:
            print(f"❌ 解析邮件失败: {e}")
            return None
    
    def get_email_body(self, email_message) -> str:
        """
        提取邮件正文
        
        Args:
            email_message: 邮件对象
            
        Returns:
            邮件正文文本
        """
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # 跳过附件
                if "attachment" in content_disposition:
                    continue
                
                # 获取文本内容
                if content_type == "text/plain":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        break
                    except:
                        pass
                elif content_type == "text/html" and not body:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        # 简单去除 HTML 标签
                        body = re.sub('<[^<]+?>', '', html_body)
                    except:
                        pass
        else:
            # 非 multipart 邮件
            try:
                charset = email_message.get_content_charset() or 'utf-8'
                body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
            except:
                body = str(email_message.get_payload())
        
        return body.strip()


def main():
    """主函数示例"""
    
    print("=" * 60)
    print("Outlook IMAP 邮箱读取工具")
    print("=" * 60)
    
    # 从格式化字符串解析账号信息
    # 格式：邮箱----密码----id-----令牌
    account_line = "your-email@outlook.com----your-password----client-id----token"
    
    parts = account_line.split("----")
    if len(parts) >= 2:
        email_address = parts[0].strip()
        password = parts[1].strip()
        
        print(f"\n📧 邮箱: {email_address}")
        print(f"🔑 密码: {'*' * len(password)}")
        
        # 创建 IMAP 读取器
        reader = OutlookIMAPReader(email_address, password)
        
        # 连接并读取邮件
        if reader.connect():
            print("\n📬 正在获取最新 5 封邮件...")
            emails = reader.get_latest_emails(count=5)
            
            if emails:
                print(f"\n✅ 成功获取 {len(emails)} 封邮件\n")
                
                for i, email_data in enumerate(emails, 1):
                    print(f"{'='*60}")
                    print(f"📨 邮件 {i}")
                    print(f"{'='*60}")
                    print(f"主题: {email_data['subject']}")
                    print(f"发件人: {email_data['from']}")
                    print(f"收件人: {email_data['to']}")
                    print(f"日期: {email_data['date']}")
                    print(f"有附件: {'是' if email_data['has_attachments'] else '否'}")
                    print(f"正文预览:\n{email_data['body'][:200]}...")
                    print()
            else:
                print("\n⚠️  未获取到邮件")
            
            # 断开连接
            reader.disconnect()
        else:
            print("\n❌ 连接失败，请检查邮箱地址和密码")
    else:
        print("❌ 账号格式错误")


if __name__ == "__main__":
    main()
