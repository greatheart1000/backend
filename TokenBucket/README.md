#### 令牌桶是一种常见的限流算法，用于控制请求或数据包的速率。它通过一个“桶”来存储令牌，每个令牌代表处理一个单位的数据或请求的权利。系统以固定的速率向桶中添加令牌，而当请求到来时需要消耗相应数量的令牌。
```
uvicorn main:app --reload --host 0.0.0.0
在 WSL 2 中，默认情况下会有一个虚拟的 NAT 网络用于与 Windows 主机通信。要找到 Windows 主机的 IP 地址，你可以使用以下命令
ip route show | grep -i default | awk '{ print $3 }'

curl http://172.27.152.1:8000/hello


