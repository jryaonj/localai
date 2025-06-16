from typing import Optional, Callable, Any, Awaitable
from pydantic import Field, BaseModel
import requests
import time
from open_webui.utils.misc import get_last_assistant_message
import json
import os



class Filter:
    class Valves(BaseModel):
        API_ENDPOINT: str = Field(
            default="", description="The base URL for the API endpoint."
        )
        API_KEY: str = Field(default="", description="API key for authentication.")
        priority: int = Field(
            default=5, description="Priority level for the filter operations."
        )

    def __init__(self):
        self.type = "filter"
        self.name = "OpenWebUI Monitor"
        self.valves = self.Valves()
        self.outage = False
        self.start_time = None
        self.inlet_temp = None

    def _prepare_request_body(self, body: dict) -> dict:
        """Convert body and nested objects to JSON-serializable format"""
        body_copy = body.copy()
        
        if 'metadata' in body_copy and 'model' in body_copy['metadata']:
            if hasattr(body_copy['metadata']['model'], 'model_dump'):
                body_copy['metadata']['model'] = body_copy['metadata']['model'].model_dump()
        
        return body_copy

    def _prepare_user_dict(self, __user__: dict) -> dict:
        """将 __user__ 对象转换为可序列化的字典"""
        user_dict = dict(__user__)  # 创建副本以避免修改原始对象

        # 如果存在 valves 且是 BaseModel 的实例，将其转换为字典
        if "valves" in user_dict and hasattr(user_dict["valves"], "model_dump"):
            user_dict["valves"] = user_dict["valves"].model_dump()

        return user_dict

    def _modify_outlet_body(self, body: dict) -> dict:
        body_modify = dict(body)
        last_message = body_modify["messages"][-1]
    
        if "info" not in last_message and self.inlet_temp is not None:
            body_modify["messages"][:-1] = self.inlet_temp["messages"]
        return body_modify

    def inlet(
        self, body: dict, user: Optional[dict] = None, __user__: dict = {}
    ) -> dict:
        self.start_time = time.time()

        try:
            post_url = f"{self.valves.API_ENDPOINT}/api/v1/inlet"
            headers = {"Authorization": f"Bearer {self.valves.API_KEY}"}

            # 使用 _prepare_user_dict 处理 __user__ 对象
            user_dict = self._prepare_user_dict(__user__)
            body_dict = self._prepare_request_body(body)
            self.inlet_temp = body_dict
            request_data = {
                "user": user_dict,
                "body": body_dict
            }
            response = requests.post(post_url, headers=headers, json=request_data)

            if response.status_code == 401:
                return body

            response.raise_for_status()
            response_data = response.json()

            if not response_data.get("success"):
                error_msg = response_data.get("error", "未知错误")
                error_type = response_data.get("error_type", "UNKNOWN_ERROR")
                raise Exception(f"请求失败: [{error_type}] {error_msg}")

            self.outage = response_data.get("balance", 0) <= 0
            if self.outage:
                raise Exception(f"余额不足: 当前余额 `{response_data['balance']:.4f}`")

            return body

        except requests.exceptions.RequestException as e:
            if (
                isinstance(e, requests.exceptions.HTTPError)
                and e.response.status_code == 401
            ):
                return body
            raise Exception(f"网络请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"处理请求时发生错误: {str(e)}")

    async def outlet(
        self,
        body: dict,
        user: Optional[dict] = None,
        __user__: dict = {},
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
    ) -> dict:
        if self.outage:
            return body

        try:
            post_url = f"{self.valves.API_ENDPOINT}/api/v1/outlet"
            headers = {"Authorization": f"Bearer {self.valves.API_KEY}"}

            # 使用 _prepare_user_dict 处理 __user__ 对象
            user_dict = self._prepare_user_dict(__user__)
            body_dict = self._prepare_request_body(body)
            body_modify = self._modify_outlet_body(body_dict)
            request_data = {
                "user": user_dict,
                "body": body_modify
            }
            response = requests.post(post_url, headers=headers, json=request_data)


            if response.status_code == 401:
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "API密钥验证失败",
                                "done": True,
                            },
                        }
                    )
                return body

            response.raise_for_status()
            result = response.json()

            if not result.get("success"):
                error_msg = result.get("error", "未知错误")
                error_type = result.get("error_type", "UNKNOWN_ERROR")
                raise Exception(f"请求失败: [{error_type}] {error_msg}")

            # 获取统计数据
            input_tokens = result["inputTokens"]
            output_tokens = result["outputTokens"]
            total_cost = result["totalCost"]
            new_balance = result["newBalance"]

            print(f"user_dict: {json.dumps(user_dict, indent=4)}")
            print(f"inlet body: {json.dumps(body, indent=4)}")

            # 从 body 中获取消息 ID
            messages = body.get("messages", [])
            message_id = messages[-1].get("id") if messages else None

            if message_id:  # 需要 message_id
                # 构建统计信息字典
                stats_data = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_cost": total_cost,
                    "new_balance": new_balance,
                }

                # 计算耗时（如果有start_time）
                if self.start_time:
                    elapsed_time = time.time() - self.start_time
                    stats_data["elapsed_time"] = elapsed_time

                    # 计算每秒输出速度，使用三元运算符避免除以零
                    stats_data["tokens_per_sec"] = (
                        output_tokens / elapsed_time if elapsed_time > 0 else 0
                    )

                    # 指定目标目录路径
                    directory_path = "/app/backend/data/record"

                    # 确保目录存在
                    os.makedirs(directory_path, exist_ok=True)

                # 构建文件路径
                file_path = os.path.join(directory_path, f"{message_id}.json")

                # 将统计信息写入 JSON 文件
                with open(file_path, "w") as f:
                    json.dump(stats_data, f, indent=4)
            else:
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": f"无法获取消息ID",
                                "done": True,
                            },
                        }
                    )

            return body

        except requests.exceptions.RequestException as e:
            if (
                isinstance(e, requests.exceptions.HTTPError)
                and e.response.status_code == 401
            ):
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "API密钥验证失败",
                                "done": True,
                            },
                        }
                    )
                return body
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"网络请求失败: {str(e)}",
                            "done": True,
                        },
                    }
                )
            raise Exception(f"网络请求失败: {str(e)}")
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"错误: {str(e)}",
                            "done": True,
                        },
                    }
                )
            raise Exception(f"处理请求时发生错误: {str(e)}")
