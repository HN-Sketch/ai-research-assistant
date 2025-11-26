import streamlit as st
import google.generativeai as genai
import requests
import json
import math
from datetime import datetime
from google.generativeai.types import HarmCategory, HarmBlockThreshold

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

# 初始化Gemini客户端
@st.cache_resource
def init_client():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # 添加详细的调试信息
        st.sidebar.write(f"🔑 Gemini API密钥格式: {api_key[:10]}...")
        
        # 配置Gemini
        genai.configure(api_key=api_key)
        
        # 创建模型实例 - 使用Gemini 2.5 Flash
        model = genai.GenerativeModel('gemini-2.0-flash-exp')  # 当前可用的最新版本
        
        st.sidebar.success("✅ Gemini客户端初始化成功")
        return model
    except Exception as e:
        st.sidebar.error(f"❌ Gemini客户端初始化失败: {e}")
        return None

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

def parse_gemini_response_for_tools(response_text):
    """解析Gemini的响应，识别工具调用"""
    tool_calls = []
    
    # 简单的关键词匹配来识别工具调用意图
    if "搜索" in response_text or "查询" in response_text or "查找" in response_text:
        # 提取搜索关键词
        import re
        search_patterns = [
            r'搜索["“”]([^"“”]+)["“”]',
            r'查询["“”]([^"“”]+)["“”]',
            r'查找["“”]([^"“”]+)["“”]'
        ]
        
        for pattern in search_patterns:
            matches = re.findall(pattern, response_text)
            if matches:
                tool_calls.append({
                    "name": "web_search",
                    "arguments": {"query": matches[0], "max_results": 3}
                })
                break
    
    # 识别数学计算
    elif "计算" in response_text or "算一下" in response_text:
        calc_patterns = [
            r'计算["“”]([^"“”]+)["“”]',
            r'算一下["“”]([^"“”]+)["“”]',
            r'([0-9+\-*/(). ]+)[的]?结果'
        ]
        
        for pattern in calc_patterns:
            matches = re.findall(pattern, response_text)
            if matches:
                expression = matches[0].strip()
                # 验证是否是合法的数学表达式
                if any(op in expression for op in ['+', '-', '*', '/', '(', ')']):
                    tool_calls.append({
                        "name": "calculator",
                        "arguments": {"expression": expression}
                    })
                break
    
    # 识别时间查询
    elif "时间" in response_text or "现在几点" in response_text or "日期" in response_text:
        tool_calls.append({
            "name": "get_current_time",
            "arguments": {}
        })
    
    return tool_calls

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

def process_user_input(user_input, temperature, max_tokens):
    """处理用户输入 - 适配Gemini API"""
    user_message = {"role": "user", "content": user_input}
    st.session_state.chat_history.append(user_message)
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    with st.chat_message("assistant"):
        try:
            if client is None:
                raise Exception("Gemini客户端未正确初始化")
            
            # 构建对话历史
            conversation_history = []
            for msg in st.session_state.chat_history[-6:]:  # 只保留最近6条消息
                conversation_history.append(f"{msg['role']}: {msg['content']}")
            
            # 构建系统提示和工具描述
            system_prompt = f"""你是一个专业的研究助手。你可以使用以下工具：

工具列表：
1. web_search - 搜索网络获取最新信息，参数：query(搜索关键词), max_results(最大结果数)
2. calculator - 计算数学表达式，参数：expression(数学表达式)
3. get_current_time - 获取当前日期和时间，无参数

使用规则：
- 如果用户的问题需要实时信息，请使用web_search工具
- 如果涉及数学计算，请使用calculator工具  
- 如果需要当前时间，请使用get_current_time工具
- 在回复中明确说明你要使用哪个工具以及参数

对话历史：
{chr(10).join(conversation_history)}

用户问题：{user_input}

请分析用户问题并决定是否需要使用工具："""
            
            # 调用Gemini API
            response = client.generate_content(
                system_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            response_text = response.text if response.text else "我没有找到合适的工具来回答这个问题。"
            
            # 解析响应，识别工具调用
            tool_calls = parse_gemini_response_for_tools(response_text)
            
            if tool_calls:
                # 模拟OpenAI格式的tool_calls
                mock_tool_calls = []
                for i, tool_call in enumerate(tool_calls):
                    mock_tool_calls.append(type('MockToolCall', (), {
                        'function': type('MockFunction', (), {
                            'name': tool_call["name"],
                            'arguments': json.dumps(tool_call["arguments"], ensure_ascii=False)
                        })()
                    })())
                
                process_tool_calls(
                    type('MockResponse', (), {'content': response_text})(),
                    mock_tool_calls,
                    temperature,
                    max_tokens
                )
            else:
                # 没有工具调用，直接显示回复
                st.markdown(response_text)
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": response_text
                })
                
        except Exception as e:
            # 显示更详细的错误信息
            st.error(f"❌ 详细错误信息：{str(e)}")
            
            # 检查API密钥是否存在
            if "GEMINI_API_KEY" not in st.secrets:
                st.error("❌ 在Streamlit Secrets中未找到 GEMINI_API_KEY")
            else:
                st.info(f"✅ API密钥已配置，长度: {len(st.secrets['GEMINI_API_KEY'])} 字符")
            
            # 显示完整的错误信息
            import traceback
            st.code(traceback.format_exc())
            
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": f"请求失败：{str(e)}"
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
            "tool_call_id": f"mock_{len(tool_results)}",
            "name": function_name,
            "result": result
        })
        
        tool_calls_info.append({
            "id": f"mock_{len(tool_calls_info)}",
            "name": function_name,
            "arguments": function_args
        })
    
    st.markdown("---")
    st.subheader("📝 最终回答")
    
    # 构建包含工具结果的提示
    tool_results_text = "工具执行结果：\n"
    for tool_result in tool_results:
        result_data = json.loads(tool_result["result"])
        if "error" not in result_data:
            tool_results_text += f"- {tool_result['name']}: {result_data}\n"
    
    final_prompt = f"""基于以下工具执行结果，给出完整的最终回答。引用具体的数据和信息。

{response_message.content}

{tool_results_text}

请基于以上信息给出完整的回答："""
    
    try:
        if client is None:
            raise Exception("Gemini客户端未正确初始化")
            
        final_response = client.generate_content(
            final_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
        
        final_content = final_response.text if final_response.text else "无法生成最终回答"
        
        # 模拟流式输出
        final_placeholder = st.empty()
        display_text = ""
        for char in final_content:
            display_text += char
            final_placeholder.markdown(display_text + "▌")
            # 添加微小延迟以模拟流式效果
        
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