# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     cleanupHandler.py
   Description :   代理自动清理处理
   Author :        ProxyPool
   date：          2024/12/20
-------------------------------------------------
"""
import time
from datetime import datetime, timedelta
from threading import Thread
from handler.logHandler import LogHandler
from handler.configHandler import ConfigHandler
from handler.proxyHandler import ProxyHandler

log = LogHandler('cleanup')


class CleanupHandler:
    """代理自动清理管理"""
    
    def __init__(self):
        self.conf = ConfigHandler()
        self.proxy_handler = ProxyHandler()
        self.is_running = False
        
    def start_cleanup_scheduler(self, interval_hours: int = 6):
        """
        启动定时清理调度器
        :param interval_hours: 清理间隔（小时）
        """
        if self.is_running:
            log.warning("Cleanup scheduler already running")
            return
            
        self.is_running = True
        Thread(target=self._cleanup_loop, args=(interval_hours,), daemon=True).start()
        log.info(f"Cleanup scheduler started, interval: {interval_hours} hours")
    
    def _cleanup_loop(self, interval_hours: int):
        """清理循环"""
        while self.is_running:
            try:
                self.cleanup_stale_proxies()
                self.cleanup_low_score_proxies()
            except Exception as e:
                log.error(f"Cleanup error: {e}")
            
            # 等待下次执行
            time.sleep(interval_hours * 3600)
    
    def cleanup_stale_proxies(self, max_age_hours: int = 72) -> int:
        """
        清理长时间未更新的代理
        :param max_age_hours: 最大存活时间（小时）
        :return: 删除的代理数量
        """
        deleted_count = 0
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        try:
            proxies = self.proxy_handler.getAll()
            
            for proxy in proxies:
                if not proxy.last_time:
                    continue
                    
                try:
                    # 解析最后检测时间
                    last_check = datetime.strptime(proxy.last_time, "%Y-%m-%d %H:%M:%S")
                    
                    if last_check < cutoff_time:
                        self.proxy_handler.delete(proxy.proxy)
                        deleted_count += 1
                except ValueError:
                    # 时间格式解析失败，跳过
                    continue
            
            if deleted_count > 0:
                log.info(f"Cleaned up {deleted_count} stale proxies (older than {max_age_hours} hours)")
                
        except Exception as e:
            log.error(f"Failed to cleanup stale proxies: {e}")
            
        return deleted_count
    
    def cleanup_low_score_proxies(self, min_score: int = 30, min_checks: int = 3) -> int:
        """
        清理低评分代理
        :param min_score: 最低评分阈值
        :param min_checks: 最少检测次数（避免误删新代理）
        :return: 删除的代理数量
        """
        deleted_count = 0
        
        try:
            proxies = self.proxy_handler.getAll()
            
            for proxy in proxies:
                # 只处理检测次数足够的代理
                if proxy.check_count >= min_checks and proxy.score < min_score:
                    self.proxy_handler.delete(proxy.proxy)
                    deleted_count += 1
            
            if deleted_count > 0:
                log.info(f"Cleaned up {deleted_count} low-score proxies (score < {min_score})")
                
        except Exception as e:
            log.error(f"Failed to cleanup low-score proxies: {e}")
            
        return deleted_count
    
    def cleanup_failed_proxies(self, max_fail_count: int = 5) -> int:
        """
        清理失败次数过多的代理
        :param max_fail_count: 最大失败次数
        :return: 删除的代理数量
        """
        deleted_count = 0
        
        try:
            proxies = self.proxy_handler.getAll()
            
            for proxy in proxies:
                if proxy.fail_count >= max_fail_count:
                    self.proxy_handler.delete(proxy.proxy)
                    deleted_count += 1
            
            if deleted_count > 0:
                log.info(f"Cleaned up {deleted_count} failed proxies (fail_count >= {max_fail_count})")
                
        except Exception as e:
            log.error(f"Failed to cleanup failed proxies: {e}")
            
        return deleted_count
    
    def get_cleanup_stats(self) -> dict:
        """获取清理统计信息"""
        try:
            proxies = self.proxy_handler.getAll()
            now = datetime.now()
            
            stale_24h = 0
            stale_48h = 0
            stale_72h = 0
            low_score = 0
            high_fail = 0
            
            for proxy in proxies:
                # 检查过期时间
                if proxy.last_time:
                    try:
                        last_check = datetime.strptime(proxy.last_time, "%Y-%m-%d %H:%M:%S")
                        age_hours = (now - last_check).total_seconds() / 3600
                        
                        if age_hours > 72:
                            stale_72h += 1
                        elif age_hours > 48:
                            stale_48h += 1
                        elif age_hours > 24:
                            stale_24h += 1
                    except ValueError:
                        pass
                
                # 检查评分
                if proxy.check_count >= 3 and proxy.score < 30:
                    low_score += 1
                
                # 检查失败次数
                if proxy.fail_count >= 5:
                    high_fail += 1
            
            return {
                "total": len(proxies),
                "stale_24h": stale_24h,
                "stale_48h": stale_48h,
                "stale_72h": stale_72h,
                "low_score": low_score,
                "high_fail": high_fail,
                "is_running": self.is_running
            }
            
        except Exception as e:
            log.error(f"Failed to get cleanup stats: {e}")
            return {"error": str(e)}
    
    def run_full_cleanup(self) -> dict:
        """执行完整清理"""
        results = {
            "stale": self.cleanup_stale_proxies(),
            "low_score": self.cleanup_low_score_proxies(),
            "failed": self.cleanup_failed_proxies()
        }
        results["total"] = sum(results.values())
        return results


# 创建单例
cleanup_handler = CleanupHandler()
