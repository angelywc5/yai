"""异步邮件发送服务。"""

from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
import httpx

from src.config.settings import Settings

logger = logging.getLogger(__name__)


class EmailService:
    """异步邮件发送（支持 SMTP 和 Resend API）。"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.mode = settings.smtp_provider  # "smtp" | "resend"

    async def send_verification_email(self, email: str, token: str) -> None:
        """发送邮箱验证邮件。"""
        verification_url = f"{self.settings.frontend_url}/verify-email?token={token}"
        subject = f"【{self.settings.app_name}】邮箱验证"
        html_body = f"""
        <html>
        <body>
            <h2>欢迎注册 {self.settings.app_name}！</h2>
            <p>请点击下方链接完成邮箱验证（24 小时内有效）：</p>
            <p><a href="{verification_url}" style="color: #007bff; font-size: 16px;">{verification_url}</a></p>
            <p>如果您没有注册此账号，请忽略此邮件。</p>
        </body>
        </html>
        """
        text_body = f"""
        欢迎注册 {self.settings.app_name}！

        请访问以下链接完成邮箱验证（24 小时内有效）：
        {verification_url}

        如果您没有注册此账号，请忽略此邮件。
        """

        if self.mode == "resend":
            await self._send_via_resend(email, subject, html_body, text_body)
        else:
            await self._send_via_smtp(email, subject, html_body, text_body)

    async def _send_via_smtp(
        self, to: str, subject: str, html_body: str, text_body: str
    ) -> None:
        """通过 SMTP 发送邮件。"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.settings.smtp_from_email
            message["To"] = to

            part1 = MIMEText(text_body, "plain", "utf-8")
            part2 = MIMEText(html_body, "html", "utf-8")
            message.attach(part1)
            message.attach(part2)

            await aiosmtplib.send(
                message,
                hostname=self.settings.smtp_host,
                port=self.settings.smtp_port,
                username=self.settings.smtp_username,
                password=self.settings.smtp_password,
                use_tls=self.settings.smtp_use_tls,
            )
            logger.info(f"验证邮件已发送至 {to} (SMTP)")
        except Exception as e:
            logger.error(f"SMTP 邮件发送失败 ({to}): {e}")
            raise

    async def _send_via_resend(
        self, to: str, subject: str, html_body: str, text_body: str
    ) -> None:
        """通过 Resend API 发送邮件。"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.settings.resend_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": self.settings.smtp_from_email,
                        "to": [to],
                        "subject": subject,
                        "html": html_body,
                        "text": text_body,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
            logger.info(f"验证邮件已发送至 {to} (Resend)")
        except Exception as e:
            logger.error(f"Resend API 邮件发送失败 ({to}): {e}")
            raise
