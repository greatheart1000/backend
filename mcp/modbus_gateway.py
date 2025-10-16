# modbus_gateway.py
import asyncio
from pymodbus.server.async_io import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification
from orchestrator import orchestrate

# 寄存器映射（示例）
# Holding Register 100: 功能码 (1=text,2=image,3=video,4=tts)
# Holding Register 101-200: ASCII码存放 prompt/文本
# 其他寄存器：状态/结果指针

store = ModbusSlaveContext(
    hr={i:0 for i in range(0, 1000)},
    zero_mode=True
)
context = ModbusServerContext(slaves=store, single=True)

identity = ModbusDeviceIdentification()
identity.VendorName  = 'MyCompany'
identity.ProductCode = 'MCP-GW'

async def handle_requests():
    while True:
        # 读寄存器 100-200：检查是否有新任务（非 0）
        regs = context[0].getValues(3, 100, count=100)
        func_code = regs[0]
        if func_code != 0:
            # 把 prompt 从 regs[1:] 解成字符串
            prompt = "".join(chr(c) for c in regs[1:] if c!=0)
            print("新任务：", func_code, prompt)

            # 分发到 orchestrator
            task_map = {1:"text_reasoning",2:"image_generation",3:"video_generation",4:"tts"}
            func = task_map.get(func_code)
            out = orchestrate(prompt)

            # 把结果（比如 URL 或文字）写回 300 起的寄存器（ASCII）
            res_str = out["result"].get("result") or out["result"].get("url") or ""
            for i, ch in enumerate(res_str[:100]):
                context[0].setValues(3, 300+i, [ord(ch)])
            # 清空任务寄存器
            context[0].setValues(3, 100, [0]*100)

        await asyncio.sleep(1)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # 启动 Modbus TCP Server
    loop.create_task(StartTcpServer(context, identity=identity, address=("0.0.0.0", 5020), defer_start=True))
    # 启动任务监控
    loop.create_task(handle_requests())
    loop.run_forever()