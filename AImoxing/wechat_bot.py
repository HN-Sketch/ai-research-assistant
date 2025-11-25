import itchat
import time
import requests
import json
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("=" * 50)
print("🤖 微信AI机器人 - 稳定版")
print("=" * 50)

# 配置
CONFIG = {
    'api_key': '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',
    'api_url': 'https://api.deepseek.com/v1/chat/completions',
    'model': 'deepseek-chat'
}

user_sessions = {}

def get_ai_response(user_input, user_id):
    """调用AI"""
    try:
        if user_id not in user_sessions:
            user_sessions[user_id] = [
                {"role": "system", "content": "你是一个有用的助手。"}
            ]
        
        user_sessions[user_id].append({"role": "user", "content": user_input})
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CONFIG["api_key"]}'
        }
        
        data = {
            'model': CONFIG['model'],
            'messages': user_sessions[user_id],
            'max_tokens': 300,
            'temperature': 0.7
        }
        
        logger.info(f"调用AI API: {user_input[:50]}...")
        response = requests.post(CONFIG['api_url'], headers=headers, json=data, timeout=30)
        result = response.json()
        ai_response = result['choices'][0]['message']['content']
        
        user_sessions[user_id].append({"role": "assistant", "content": ai_response})
        
        # 限制历史长度
        if len(user_sessions[user_id]) > 6:
            user_sessions[user_id] = [user_sessions[user_id][0]] + user_sessions[user_id][-4:]
        
        return ai_response
        
    except Exception as e:
        logger.error(f"AI调用错误: {e}")
        return "抱歉，暂时无法回复，请稍后重试。"

def keep_alive():
    """保持活跃，防止被登出"""
    try:
        # 定期给文件传输助手发送心跳（静默）
        itchat.send("", toUserName='filehelper')
        logger.info("发送心跳包保持连接")
    except:
        logger.warning("心跳发送失败，可能已断开连接")

@itchat.msg_register('Text')
def text_reply(msg):
    """处理文本消息"""
    try:
        text = msg.get('Text', '').strip()
        if not text:
            return
            
        user_id = msg['FromUserName']
        
        # 私聊消息
        if msg['FromUserName'] == msg['ToUserName']:
            logger.info(f"私聊消息: {text}")
            
            if text in ['帮助', 'help']:
                itchat.send("🤖 我是AI助手，直接发消息聊天", user_id)
                return
                
            response = get_ai_response(text, user_id)
            time.sleep(1)  # 避免回复过快
            itchat.send(response, user_id)
            logger.info("回复发送完成")
            
        else:
            # 群聊消息
            self_info = itchat.search_friends()
            self_nickname = self_info.get('NickName', '') if self_info else ''
            
            if self_nickname and f"@{self_nickname}" in text:
                clean_text = text.replace(f"@{self_nickname}", "").strip()
                if clean_text:
                    actual_nickname = msg.get('ActualNickName', '用户')
                    logger.info(f"群聊消息: {clean_text}")
                    
                    response = get_ai_response(clean_text, user_id)
                    time.sleep(1)
                    itchat.send(f"@{actual_nickname} {response}", user_id)
                    
    except Exception as e:
        logger.error(f"消息处理错误: {e}")

def stable_login():
    """稳定登录函数"""
    session_file = 'wx_stable.pkl'
    
    # 登录配置
    login_kwargs = {
        'hotReload': True,
        'statusStorageDir': session_file,
        'enableCmdQR': 2,
    }
    
    try:
        print("🔄 尝试登录...")
        itchat.auto_login(**login_kwargs)
        print("✅ 登录成功！")
        return True
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        # 删除无效的session文件
        if os.path.exists(session_file):
            os.remove(session_file)
        return False

def main():
    """主函数"""
    logger.info("启动稳定版微信机器人")
    
    if not stable_login():
        logger.error("登录失败，程序退出")
        return
    
    print("🎯 机器人运行中...")
    print("💡 使用说明:")
    print("   - 私聊直接发消息")
    print("   - 群聊@机器人")
    print("   - 发送'帮助'查看功能")
    
    # 发送上线通知
    try:
        itchat.send("🤖 AI助手已上线！", toUserName='filehelper')
    except Exception as e:
        logger.warning(f"上线通知发送失败: {e}")
    
    # 设置心跳（可选）
    # import threading
    # heartbeat = threading.Thread(target=heartbeat_worker, daemon=True)
    # heartbeat.start()
    
    try:
        # 运行机器人
        itchat.run()
    except KeyboardInterrupt:
        print("\n👋 用户主动退出")
    except Exception as e:
        logger.error(f"机器人运行错误: {e}")
    finally:
        print("🛑 程序结束")

if __name__ == "__main__":
    main()