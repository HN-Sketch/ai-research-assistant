import streamlit as st
from openai import OpenAI
import requests
import json
import math
from datetime import datetime

# 初始化OpenRouter客户端
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

# 工具函数定义
class ResearchTools:
    @staticmethod
    def web_search(query: str, max_results: int = 3):
        """
        使用DuckDuckGo进行网页搜索
        注意：这是一个简化的示例，实际使用时可能需要使用正式的搜索API
        """
        try:
            # 这里使用DuckDuckGo的简易搜索
            # 实际项目中可以使用Google Search API、SerpAPI等
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            results = []
            # 获取相关主题
            if 'RelatedTopics' in data:
                for topic in data['RelatedTopics'][:max_results]:
                    if 'Text' in topic:
                        results.append({
                            "title": topic.get('FirstURL', 'No title'),
                            "snippet": topic['Text'],
                            "url": topic.get('FirstURL', '')
                        })
            
            # 如果没有结果，返回模拟数据用于演示
            if not results:
                results = [
                    {
                        "title": f"关于 {query} 的搜索结果1",
                        "snippet": f"这是关于 {query} 的模拟搜索结果。在实际应用中，这里会显示真实的网页摘要信息。",
                        "url": "https://example.com/result1"
                    },
                    {
                        "title": f"关于 {query} 的搜索结果2", 
                        "snippet": f"更多关于 {query} 的信息。这个研究助手可以整合多个来源的信息。",
                        "url": "https://example.com/result2"
                    }
                ]
            
            return json.dumps({"results": results}, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({"error": f"搜索失败: {str(e)}"}, ensure_ascii=False)

    @staticmethod
    def calculator(expression: str):
        """
        计算数学表达式
        """
        try:
            # 安全评估数学表达式
            allowed_chars = set('0123456789+-*/(). ')
            if not all(c in allowed_chars for c in expression):
                return json.dumps({"error": "表达式包含不安全字符"}, ensure_ascii=False)
            
            # 使用eval计算（在生产环境中应该使用更安全的方法）
            result = eval(expression)
            return json.dumps({"expression": expression, "result": result}, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({"error": f"计算错误: {str(e)}"}, ensure_ascii=False)

    @staticmethod
    def get_current_time():
        """获取当前时间"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return json.dumps({"current_time": current_time}, ensure_ascii=False)

# 工具列表供AI选择
AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "搜索网络获取最新信息，用于回答需要实时数据的问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "最大结果数量，默认3",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式，用于解决数学问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '2 + 3 * 4'"
                    }
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
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

# Streamlit应用
def main():
    st.set_page_config(
        page_title="AI研究助手",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 AI研究助手 Agent")
    st.markdown("智能助手可以调用搜索引擎、计算器等工具帮您进行研究")
    
    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    # 侧边栏
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
            st.session_state.messages = []
            st.session_state.conversation_history = []
            st.rerun()
    
    # 显示对话历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "tool_calls" in message:
                for tool_call in message["tool_calls"]:
                    with st.expander(f"🔧 调用了 {tool_call['name']} 工具"):
                        st.json(tool_call)
    
    # 用户输入
    if prompt := st.chat_input("请输入您的研究问题..."):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.conversation_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI思考过程
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # 准备对话历史
                chat_messages = [
                    {
                        "role": "system", 
                        "content": """你是一个专业的研究助手。你可以使用以下工具：
                        - web_search: 搜索最新信息
                        - calculator: 进行数学计算
                        - get_current_time: 获取当前时间
                        
                        使用工具时请仔细思考，确保选择正确的工具和参数。
                        回答要基于事实，引用搜索到的信息。"""
                    }
                ] + st.session_state.conversation_history
                
                # 第一次调用 - 让AI决定是否使用工具
                response = client.chat.completions.create(
                    model="mistralai/mistral-7b-instruct:free",
                    messages=chat_messages,
                    tools=AVAILABLE_TOOLS,
                    tool_choice="auto",
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
                
                # 处理响应
                tool_calls_info = []
                current_tool_call = None
                
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        message_placeholder.markdown(full_response + "▌")
                    
                    # 检查是否有工具调用
                    if chunk.choices[0].delta.tool_calls:
                        tool_call = chunk.choices[0].delta.tool_calls[0]
                        
                        if tool_call.index is not None:
                            if tool_call.index >= len(tool_calls_info):
                                tool_calls_info.append({
                                    "id": tool_call.id,
                                    "name": "",
                                    "arguments": ""
                                })
                            current_tool_call = tool_calls_info[tool_call.index]
                        
                        if tool_call.function.name:
                            current_tool_call["name"] = tool_call.function.name
                            # 显示工具调用
                            st.info(f"🤔 正在思考使用 {tool_call.function.name} 工具...")
                        
                        if tool_call.function.arguments:
                            current_tool_call["arguments"] += tool_call.function.arguments
                
                message_placeholder.markdown(full_response)
                
                # 如果有工具调用，执行工具并再次调用AI
                if tool_calls_info:
                    st.markdown("---")
                    st.subheader("🛠️ 工具执行过程")
                    
                    # 执行每个工具调用
                    for tool_call in tool_calls_info:
                        try:
                            arguments = json.loads(tool_call["arguments"])
                            tool_name = tool_call["name"]
                            
                            st.write(f"**执行 {tool_name}**: {arguments}")
                            
                            # 调用相应的工具
                            if tool_name == "web_search":
                                result = ResearchTools.web_search(**arguments)
                            elif tool_name == "calculator":
                                result = ResearchTools.calculator(**arguments)
                            elif tool_name == "get_current_time":
                                result = ResearchTools.get_current_time()
                            else:
                                result = json.dumps({"error": "未知工具"})
                            
                            # 显示工具结果
                            with st.expander(f"📊 {tool_name} 结果"):
                                st.json(json.loads(result))
                            
                            # 将工具结果添加到对话中
                            tool_call_message = {
                                "role": "tool",
                                "content": result,
                                "tool_call_id": tool_call["id"]
                            }
                            st.session_state.conversation_history.append(tool_call_message)
                            
                        except Exception as e:
                            st.error(f"工具执行错误: {e}")
                    
                    # 使用工具结果再次调用AI
                    st.markdown("---")
                    st.subheader("💭 最终回答")
                    
                    final_response_placeholder = st.empty()
                    final_response = ""
                    
                    # 准备包含工具结果的完整消息
                    final_messages = [
                        {
                            "role": "system", 
                            "content": "基于工具执行结果，给出完整的最终回答。引用具体的数据和信息。"
                        }
                    ] + st.session_state.conversation_history
                    
                    final_response_obj = client.chat.completions.create(
                        model="mistralai/mistral-7b-instruct:free",
                        messages=final_messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True
                    )
                    
                    for chunk in final_response_obj:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            final_response += content
                            final_response_placeholder.markdown(final_response + "▌")
                    
                    final_response_placeholder.markdown(final_response)
                    full_response = final_response
                
                # 保存对话
                assistant_message = {"role": "assistant", "content": full_response}
                if tool_calls_info:
                    assistant_message["tool_calls"] = tool_calls_info
                
                st.session_state.messages.append(assistant_message)
                st.session_state.conversation_history.append(assistant_message)
                
            except Exception as e:
                error_msg = f"❌ 请求失败：{str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()