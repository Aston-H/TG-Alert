from AppKit import NSRunningApplication, NSWorkspace
import time

class NSRunningApplicationDemo:
    def __init__(self, bundle_id='com.apple.Safari'):
        self.bundle_id = bundle_id
        self.app = self.find_app()
    
    def find_app(self):
        """查找应用"""
        apps = NSRunningApplication.runningApplicationsWithBundleIdentifier_(self.bundle_id)
        return apps[0] if apps else None
    
    # ==================== 信息获取 ====================
    
    def get_basic_info(self):
        """获取基本信息"""
        if not self.app:
            return None
        
        return {
            # 基本信息
            'localizedName': self.app.localizedName(),
            'bundleIdentifier': self.app.bundleIdentifier(),
            'processIdentifier': self.app.processIdentifier(),
            'executableURL': str(self.app.executableURL()) if self.app.executableURL() else None,
            'bundleURL': str(self.app.bundleURL()) if self.app.bundleURL() else None,
            'launchDate': str(self.app.launchDate()) if self.app.launchDate() else None,
            'executableArchitecture': self.app.executableArchitecture(),
        }
    
    def get_state_info(self):
        """获取状态信息"""
        if not self.app:
            return None
        
        return {
            # 状态信息
            'isActive': self.app.isActive(),
            'isHidden': self.app.isHidden(),
            'isTerminated': self.app.isTerminated(),
            'isFinishedLaunching': self.app.isFinishedLaunching(),
            'ownsMenuBar': self.app.ownsMenuBar(),
        }
    
    # ==================== 窗口操作 ====================
    
    def activate_app(self, ignore_other_apps=True):
        """
        激活应用（带到前台）
        ignore_other_apps: 是否忽略其他应用，强制激活
        """
        if not self.app:
            print("激活应用: 失败 (应用不存在)")
            return False
        
        # 使用数值常量而不是枚举
        # NSApplicationActivateIgnoringOtherApps = 2
        options = 2 if ignore_other_apps else 0
        
        try:
            success = self.app.activateWithOptions_(options)
            
            # 如果应用被隐藏，先取消隐藏
            if success and self.app.isHidden():
                self.app.unhide()
            
            print(f"激活应用: {'成功' if success else '失败'}")
            return success
        except Exception as e:
            print(f"激活应用: 失败 ({e})")
            return False
    
    def hide_app(self):
        """隐藏应用"""
        if not self.app:
            print("隐藏应用: 失败 (应用不存在)")
            return False
        
        try:
            # 某些应用（尤其是 Citrix）可能不支持 hide() 方法
            # 可以尝试使用 AppleScript 代替
            success = self.app.hide()
            print(f"隐藏应用: {'成功' if success else '失败'}")
            
            if not success:
                # 尝试使用 AppleScript
                print("尝试使用 AppleScript 隐藏...")
                success = self.hide_with_applescript()
            
            return success
        except Exception as e:
            print(f"隐藏应用: 失败 ({e})")
            return False
    
    def unhide_app(self):
        """显示应用（取消隐藏）"""
        if not self.app:
            print("显示应用: 失败 (应用不存在)")
            return False
        
        try:
            success = self.app.unhide()
            print(f"显示应用: {'成功' if success else '失败'}")
            
            if not success:
                # 尝试使用 AppleScript
                print("尝试使用 AppleScript 显示...")
                success = self.unhide_with_applescript()
            
            return success
        except Exception as e:
            print(f"显示应用: 失败 ({e})")
            return False
    
    # ==================== AppleScript 备用方法 ====================
    
    def hide_with_applescript(self):
        """使用 AppleScript 隐藏应用"""
        import subprocess
        
        app_name = self.app.localizedName()
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                set visible to false
            end tell
        end tell
        '''
        
        try:
            subprocess.run(['osascript', '-e', script], 
                         check=True, 
                         capture_output=True, 
                         timeout=5)
            return True
        except Exception as e:
            print(f"AppleScript 隐藏失败: {e}")
            return False
    
    def unhide_with_applescript(self):
        """使用 AppleScript 显示应用"""
        import subprocess
        
        app_name = self.app.localizedName()
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                set visible to true
            end tell
        end tell
        '''
        
        try:
            subprocess.run(['osascript', '-e', script], 
                         check=True, 
                         capture_output=True, 
                         timeout=5)
            return True
        except Exception as e:
            print(f"AppleScript 显示失败: {e}")
            return False
    
    def activate_with_applescript(self):
        """使用 AppleScript 激活应用"""
        import subprocess
        
        app_name = self.app.localizedName()
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        '''
        
        try:
            subprocess.run(['osascript', '-e', script], 
                         check=True, 
                         capture_output=True, 
                         timeout=5)
            print("激活应用 (AppleScript): 成功")
            return True
        except Exception as e:
            print(f"激活应用 (AppleScript): 失败 ({e})")
            return False
    
    # ==================== 进程控制 ====================
    
    def terminate_app(self):
        """正常终止应用"""
        if not self.app:
            print("终止应用: 失败 (应用不存在)")
            return False
        
        try:
            success = self.app.terminate()
            print(f"终止应用: {'成功' if success else '失败'}")
            return success
        except Exception as e:
            print(f"终止应用: 失败 ({e})")
            return False
    
    def force_terminate_app(self):
        """强制终止应用"""
        if not self.app:
            print("强制终止应用: 失败 (应用不存在)")
            return False
        
        try:
            success = self.app.forceTerminate()
            print(f"强制终止应用: {'成功' if success else '失败'}")
            return success
        except Exception as e:
            print(f"强制终止应用: 失败 ({e})")
            return False

# ==================== 使用示例 ====================

def demo_all_features(bundle_id='com.apple.Safari'):
    """演示所有功能"""
    
    print("=" * 60)
    print(f"应用操作演示 - Bundle ID: {bundle_id}")
    print("=" * 60)
    
    demo = NSRunningApplicationDemo(bundle_id)
    
    if not demo.app:
        print("❌ 应用未运行")
        return
    
    # 1. 获取基本信息
    print("\n" + "=" * 60)
    print("1. 基本信息")
    print("=" * 60)
    basic_info = demo.get_basic_info()
    for key, value in basic_info.items():
        print(f"{key}: {value}")
    
    # 2. 获取状态信息
    print("\n" + "=" * 60)
    print("2. 状态信息")
    print("=" * 60)
    state_info = demo.get_state_info()
    for key, value in state_info.items():
        print(f"{key}: {value}")
    
    # 3. 窗口操作
    print("\n" + "=" * 60)
    print("3. 窗口操作")
    print("=" * 60)
    
    print("\n激活应用...")
    demo.activate_app()
    time.sleep(2)
    
    # 注意：某些应用（如 Citrix）可能不支持 hide/unhide
    print("\n隐藏应用...")
    demo.hide_app()
    time.sleep(2)
    
    print("\n显示应用...")
    demo.unhide_app()
    time.sleep(2)



if __name__ == "__main__":
    # 测试 Safari
    demo_all_features('com.apple.Safari')
    
    # 测试 Citrix
    # demo_citrix()
    # 应用名: Citrix Viewer
    # Bundle ID: com.citrix.receiver.icaviewer.mac

    # print(f"查询应用:{find_app_by_bundle_id("com.apple.Safari")}")