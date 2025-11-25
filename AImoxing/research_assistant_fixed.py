import streamlit as st
from openai import OpenAI
import requests
import json
import math
from datetime import datetime

# 设置页面配置（移动端优化）
st.set_page_config(
    page_title="AI研究助手",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"  # 移动端默认收起侧边栏
)

# 移动端CSS优化
st.markdown("""
<style>
    /* 移动端响应式设计 */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* 聊天输入框固定在底部 */
        .stChatInput {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            padding: 1rem;
            z-index: 999;
            border-top: 1px solid #e6e6e6;
        }
        
        /* 调整聊天消息间距 */
        .stChatMessage {
            margin-bottom: 0.5rem;
        }
        
        /* 侧边栏移动端适配 */
        .css-1d391kg {
            width: 100%;
        }
    }
    
    /* 通用移动端优化 */
    .stButton button {
        width: 100%;
    }
    
    /* 隐藏桌面端不必要的元素 */
    @media (max-width: 768px) {
        .desktop-only {
            display: none;
        }
    }
</style>
""", unsafe_allow_html=True)

# 检测移动设备函数
def is_mobile():
    """检测是否为移动设备"""
    try:
        # 通过用户代理字符串检测
        user_agent = st.query_params.get("user_agent", "")
        if not user_agent:
            return False
            
        mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'webos', 'blackberry']
        return any(keyword in user_agent.lower() for keyword in mobile_keywords)
    except:
        return False

# 初始化OpenRouter客户端
@st.cache_resource
def init_client():
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="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",
    )

client = init_client()

# 工具函数定义（保持不变）
class ResearchTools:
    @staticmethod
    def web_search(query: str, max_results: int = 3):
        """网页搜索工具"""
        try:
            results = [
                {
                    "title": f"关于 '{query}' 的研究资料",
                    "snippet": f"根据现有知识，{query} 是一个重要研究领域，涉及多个学科交叉。",
                    "url": "https://research-database.com/query"
                },
                {
                    "title": f"'{query}' 的相关分析",
                    "snippet": "多角度分析显示该主题具有深入研究价值，特别是在当前技术发展背景下。",
                    "url": "https://analysis-portal.org/topic"
                }
            ]
            
            return json.dumps({
                "query": query,
                "results": results[:max_results],
                "search_time": datetime.now().strftime("%H:%M:%S")
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({"error": f"搜索失败: {str(e)}"}, ensure_ascii=False)

    @staticmethod
    def calculator(expression: str):
        """计算器工具"""
        try:
            allowed_chars = set('0123456789+-*/(). ')
            if not all(c in allowed_chars for c in expression):
                return json.dumps({"error": "表达式包含不安全字符"}, ensure_ascii=False)
            
            result = eval(expression)
            return json.dumps({
                "expression": expression, 
                "result": result,
                "calculated_at": datetime.now().strftime("%H:%M:%S")
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({"error": f"计算错误: {str(e)}"}, ensure_ascii=False)

    @staticmethod
    def get_current_time():
        """获取当前时间"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return json.dumps({"current_time": current_time}, ensure_ascii=False)

# 工具列表（保持不变）
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索网络获取最新信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "max_results": {"type": "number", "description": "最大结果数量", "default": 3}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def main():
    # 移动端适配的标题
    if is_mobile():
        st.markdown("# 📱 AI研究助手")
        st.markdown("智能助手帮您进行研究")
    else:
        st.title("🔍 AI研究助手 Agent")
        st.markdown("智能助手可以调用搜索引擎、计算器等工具帮您进行研究")
    
    # 初始化会话状态
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # 移动端简化的侧边栏
    if not is_mobile():
        with st.sidebar:
            st.header("⚙️ 设置")
            temperature = st.slider("创造性", 0.0, 1.0, 0.3, 0.1)
            max_tokens = st.slider("回复长度", 100, 2000, 800, 50)
            
            st.header("🛠️ 可用工具")
            st.markdown("""
            - 🔍 网页搜索
            - 🧮 数学计算  
            - ⏰ 时间查询
            """)
            
            if st.button("🗑️ 清空对话"):
                st.session_state.chat_history = []
                st.rerun()
    else:
        # 移动端设置放在主界面
        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider("创造性", 0.0, 1.0, 0.3, 0.1, key="mobile_temp")
        with col2:
            max_tokens = st.slider("回复长度", 100, 2000, 800, 50, key="mobile_tokens")
        
        if st.button("🗑️ 清空对话", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    # 显示对话历史
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            role = message["role"]
            content = message["content"]
            
            with st.chat_message(role):
                st.markdown(content)
                
                if "tool_calls" in message:
                    for tool_call in message["tool_calls"]:
                        with st.expander(f"🔧 使用了 {tool_call['name']} 工具", key=f"tool_{i}"):
                            st.json(tool_call)
    
    # 用户输入 - 移动端优化
    user_input = st.chat_input("请输入您的研究问题...")
    
    if user_input:
        process_user_input(user_input, temperature, max_tokens)

# 以下 process_user_input 和 process_tool_calls 函数保持不变
def process_user_input(user_input, temperature, max_tokens):
    """处理用户输入"""
    user_message = {"role": "user", "content": user_input}
    st.session_state.chat_history.append(user_message)
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    with st.chat_message("assistant"):
        try:
            conversation_messages = [
                {
                    "role": "system", 
                    "content": """你是一个专业的研究助手。你可以使用以下工具：
                    - web_search: 搜索最新信息
                    - calculator: 进行数学计算
                    - get_current_time: 获取当前时间
                    
                    根据问题需要选择合适的工具。"""
                }
            ]
            
            recent_history = st.session_state.chat_history[-10:]
            for msg in recent_history:
                if "tool_calls" not in msg:
                    conversation_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            response = client.chat.completions.create(
                model="mistralai/mistral-7b-instruct:free",
                messages=conversation_messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            if tool_calls:
                process_tool_calls(response_message, tool_calls, temperature, max_tokens)
            else:
                ai_content = response_message.content or "我没有找到合适的工具来回答这个问题。"
                st.markdown(ai_content)
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": ai_content
                })
                
        except Exception as e:
            error_msg = f"❌ 请求失败：{str(e)}"
            st.error(error_msg)
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": error_msg
            })

def process_tool_calls(response_message, tool_calls, temperature, max_tokens):
    """处理工具调用"""
    st.info("🤔 AI正在使用工具分析问题...")
    
    tool_results = []
    tool_calls_info = []
    
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        with st.expander(f"🔧 执行 {function_name}"):
            st.write("参数:")
            st.json(function_args)
            
            if function_name == "web_search":
                result = ResearchTools.web_search(**function_args)
            elif function_name == "calculator":
                result = ResearchTools.calculator(**function_args)
            elif function_name == "get_current_time":
                result = ResearchTools.get_current_time()
            else:
                result = json.dumps({"error": "未知工具"})
            
            st.write("结果:")
            st.json(json.loads(result))
        
        tool_results.append({
            "tool_call_id": tool_call.id,
            "name": function_name,
            "result": result
        })
        
        tool_calls_info.append({
            "id": tool_call.id,
            "name": function_name,
            "arguments": function_args
        })
    
    st.markdown("---")
    st.subheader("📝 最终回答")
    
    final_messages = [
        {
            "role": "system", 
            "content": "基于工具执行结果，给出完整的最终回答。引用具体的数据和信息。"
        }
    ]
    
    if response_message.content:
        final_messages.append({
            "role": "assistant",
            "content": response_message.content
        })
    
    for tool_result in tool_results:
        final_messages.append({
            "role": "tool",
            "tool_call_id": tool_result["tool_call_id"],
            "content": tool_result["result"]
        })
    
    final_messages.append({
        "role": "user",
        "content": "请基于以上工具执行结果，给出完整的回答"
    })
    
    try:
        final_response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",
            messages=final_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        final_placeholder = st.empty()
        final_content = ""
        
        for chunk in final_response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                final_content += content
                final_placeholder.markdown(final_content + "▌")
        
        final_placeholder.markdown(final_content)
        
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": final_content,
            "tool_calls": tool_calls_info
        })
        
    except Exception as e:
        error_msg = f"❌ 生成最终回答失败：{str(e)}"
        st.error(error_msg)
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": error_msg
        })

if __name__ == "__main__":
    main()