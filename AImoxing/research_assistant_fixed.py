import streamlit as st
from openai import OpenAI
import json
from datetime import datetime

# 设置页面配置
st.set_page_config(
    page_title="AI研究助手",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 初始化Groq客户端（免费替代方案）
@st.cache_resource
def init_client():
    return OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=st.secrets.get("GROQ_API_KEY", "gsk_你的密钥这里")  # 从Secrets获取或直接填写
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
    st.title("🔍 AI研究助手")
    st.markdown("智能助手可以调用搜索引擎、计算器等工具帮您进行研究")
    
    # 初始化会话状态
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # 显示对话历史
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 用户输入
    user_input = st.chat_input("请输入您的研究问题...")
    
    if user_input:
        process_user_input(user_input)

def process_user_input(user_input):
    """处理用户输入"""
    # 添加用户消息
    user_message = {"role": "user", "content": user_input}
    st.session_state.chat_history.append(user_message)
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    with st.chat_message("assistant"):
        try:
            # 使用Groq的模型
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Groq的免费快速模型
                messages=[
                    {
                        "role": "system", 
                        "content": """你是一个专业的研究助手。你可以使用以下工具：
                        - web_search: 搜索最新信息
                        - calculator: 进行数学计算
                        - get_current_time: 获取当前时间
                        
                        根据问题需要选择合适的工具。"""
                    },
                    {"role": "user", "content": user_input}
                ],
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=800
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            if tool_calls:
                process_tool_calls(response_message, tool_calls)
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

def process_tool_calls(response_message, tool_calls):
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
            "name": function_name,
            "arguments": function_args
        })
    
    # 生成最终回答
    final_messages = [
        {
            "role": "system", 
            "content": "基于工具执行结果，给出完整的最终回答。"
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
            model="llama-3.1-8b-instant",
            messages=final_messages,
            temperature=0.3,
            max_tokens=800
        )
        
        final_content = final_response.choices[0].message.content
        st.markdown(final_content)
        
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": final_content,
            "tool_calls": tool_calls_info
        })
        
    except Exception as e:
        error_msg = f"❌ 生成最终回答失败：{str(e)}"
        st.error(error_msg)

if __name__ == "__main__":
    main()