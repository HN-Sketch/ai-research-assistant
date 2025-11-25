import streamlit as st
from openai import OpenAI

# 设置页面配置
st.set_page_config(
    page_title="Mistral 7B 聊天机器人",
    page_icon="🤖",
    layout="wide"
)

# 直接硬编码 API 密钥（避免 secrets 问题）
API_KEY = "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"

# 初始化客户端（不使用缓存装饰器避免问题）
def init_client():
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
    )

client = init_client()

# 设置模型
MODEL_NAME = "mistralai/mistral-7b-instruct:free"
MODEL_DISPLAY = "Mistral 7B"

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 侧边栏
with st.sidebar:
    st.title("🎯 Mistral 7B 聊天机器人")
    st.markdown("---")
    
    st.subheader("ℹ️ 关于")
    st.markdown(f"""
    - **模型**: {MODEL_DISPLAY}
    - **状态**: ✅ 可用
    - **特点**: 免费使用，支持中文
    """)
    
    st.markdown("---")
    st.subheader("⚙️ 设置")
    
    # 参数设置
    temperature = st.slider("创造性", 0.0, 1.0, 0.7, 0.1)
    max_tokens = st.slider("最大回复长度", 100, 1000, 500, 50)
    
    st.markdown("---")
    
    # 清空聊天记录按钮
    if st.button("🗑️ 清空聊天记录", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()
    
    st.markdown("---")
    st.caption("💡 提示：免费模型可能有速率限制")

# 主界面
st.title(f"💬 {MODEL_DISPLAY} 聊天机器人")
st.markdown("---")

# 显示聊天记录
for message in st.session_state.chat_history:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(message["content"])

# 聊天输入
if prompt := st.chat_input("请输入您的问题..."):
    # 添加用户消息到会话
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)
    st.session_state.chat_history.append(user_message)
    
    # 立即显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 生成AI回复
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # 准备消息（包含系统消息）
            chat_messages = [
                {"role": "system", "content": "你是一个乐于助人的AI助手。请用中文回答用户的问题，回答要友好、详细。"}
            ] + st.session_state.messages
            
            # 调用 OpenRouter API
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=chat_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            # 流式显示回复
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # 添加AI回复到会话
            assistant_message = {"role": "assistant", "content": full_response}
            st.session_state.messages.append(assistant_message)
            st.session_state.chat_history.append(assistant_message)
            
        except Exception as e:
            error_msg = f"❌ 请求失败：{str(e)}"
            message_placeholder.markdown(error_msg)
            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

# 底部信息
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"📊 当前模型: {MODEL_DISPLAY}")
with col2:
    st.caption("🎯 免费使用")
with col3:
    st.caption("⚡ 实时流式响应")