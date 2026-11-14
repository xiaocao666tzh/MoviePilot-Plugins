"""提供仅获取种子内容的 MoviePilot 接口。"""

from typing import Optional

from fastapi import HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from app.chain.download import DownloadChain
from app.core.context import TorrentInfo
from app.db.site_oper import SiteOper
from app.plugins import _PluginBase


MAX_TORRENT_BYTES = 16 * 1024 * 1024


class _TorrentRequest(BaseModel):
    """只接受资源定位信息，站点凭据始终由 MoviePilot 自己读取。"""

    model_config = ConfigDict(extra="forbid")
    site_id: Optional[int] = None
    enclosure: str = Field(min_length=1, max_length=65536)
    title: str = Field(min_length=1, max_length=4096)


class TorrentBridge(_PluginBase):
    plugin_name = "Torrent Bridge"
    plugin_desc = "返回种子文件"
    plugin_version = "1.0.0"
    plugin_author = "xcao"
    plugin_order = 99
    auth_level = 1
    _enabled = False

    def init_plugin(self, config: dict = None):
        self._enabled = bool((config or {}).get("enabled", False))

    def get_state(self) -> bool:
        return self._enabled

    def get_api(self):
        return [{
            "path": "/torrent",
            "endpoint": self.torrent,
            "methods": ["POST"],
            "auth": "apikey",
            "summary": "仅获取种子文件，不创建下载任务",
        }]

    def get_form(self):
        return [{
            "component": "VSwitch",
            "props": {"model": "enabled", "label": "启用种子文件接口"},
        }], {"enabled": False}

    def get_page(self):
        return None

    def stop_service(self):
        pass

    def torrent(self, body: _TorrentRequest) -> Response:
        if not self._enabled:
            raise HTTPException(status_code=503, detail="种子文件桥接插件尚未启用")
        # 不接受下载器、目录、Cookie 或 UA；这些字段不能由调用者覆盖。
        torrent = TorrentInfo(
            site=body.site_id, title=body.title, enclosure=body.enclosure,
        )
        if body.site_id is not None:
            site = SiteOper().get(body.site_id)
            if not site:
                raise HTTPException(status_code=404, detail="MoviePilot 站点不存在")
            torrent.site_cookie = site.cookie
            torrent.site_ua = site.ua
            torrent.site_proxy = bool(site.proxy)
            torrent.site_name = site.name
        try:
            # 只调用种子解析与取文件方法，不调用 download_single 或下载器方法。
            content, _, _ = DownloadChain().download_torrent(torrent)
        except Exception:
            raise HTTPException(status_code=502, detail="MoviePilot 获取种子失败，请检查其日志") from None
        if isinstance(content, str) and content.startswith(("magnet:?xt=urn:btih:", "magnet:?xt=urn:btmh:")):
            return Response(content=content, media_type="text/plain")
        if not isinstance(content, bytes) or not content.startswith(b"d") or not content.endswith(b"e"):
            raise HTTPException(status_code=502, detail="MoviePilot 未取得有效种子文件")
        if len(content) > MAX_TORRENT_BYTES:
            raise HTTPException(status_code=413, detail="种子文件超过 16 MiB")
        return Response(
            content=content,
            media_type="application/x-bittorrent",
            headers={
                "Content-Disposition": 'attachment; filename="download.torrent"',
                "Cache-Control": "no-store",
            },
        )
