#!/bin/bash
# keep_citrix_alive.sh

set AppStr to "Citrix Viewer"

repeat
	try
		tell application "System Events"
			if exists process AppStr then
				tell process AppStr
					if (count of windows) > 0 then
						-- 记录原始状态
						set wasInFront to frontmost
						
						-- 激活并发送按键
						set frontmost to true
						delay 0.5
						key code 126
						
						-- 成功通知
						set timeStamp to time string of (current date)
						display notification "原始状态：" & wasInFront & return & "保活信号已发送时间: " & timeStamp with title "✅ Citrix 保活"
						
						-- 恢复原始状态
						if not wasInFront then
							set visible to false
							delay 0.2
						end if
					else
						-- 警告：无窗口
						display notification "Citrix 没有打开的窗口" with title "⚠️ 警告" sound name "Basso"
					end if
				end tell
			else
				-- 错误：应用未运行
				display notification "请先启动 Citrix Viewer" with title "❌ 应用未运行" sound name "Funk"
			end if
		end tell
	on error errMsg
		-- 脚本错误
		display notification errMsg with title "❌ 脚本错误" sound name "Basso"
	end try
	
	delay 600 -- 等待 10 分钟
end repeat