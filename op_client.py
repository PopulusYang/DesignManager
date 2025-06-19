import socket
import json

BUFLEN = 2048

msg_login = {"type" : "login", "name" : "", "password" : ""}

def connect_to_server(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        print(f"已连接到服务器 {ip}:{port}")

        # 接收服务器欢迎消息
        data = sock.recv(BUFLEN)
        print("服务器:", data.decode())

        return sock
    except Exception as e:
        print(f"连接失败: {e}")
        return None


def send_json_command(sock, command):
    msg = {}
    if command in ["exit", "close"]:
        msg["command"] = command
    elif command in ["login"]:
        msg_login["name"]=input("请输入您的姓名")
        if not msg_login["name"]:
            print("姓名不能为空")
            return
        password = input("请输入您的密码(无密码空置即可): ")
        if not password:
            msg_login["password"] = ""
        else:
            msg_login["password"] = password
        msg = msg_login

    elif command in ["request_project_data"]:
        project_name = input("请输入项目名称: ")
        if not project_name:
            print("项目名称不能为空")
            return
        msg = {"type": "request_project_data", "name": project_name}

    elif command in ["create_project"]:
        project_name = input("请输入项目名称: ")
        if not project_name:
            print("项目名称不能为空")
            return
        project_discription = input("请输入项目描述: ")
        msg = {"type": "create_project", "name": project_name, "description": project_discription}
    elif command in ["add_member"]:
        project_name = input("请输入项目名称: ")
        if not project_name:
            print("项目名称不能为空")
            return
        member_name = input("请输入成员姓名: ")
        if not member_name:
            print("成员姓名不能为空")
            return
        msg = {"type": "add_member", "project_name": project_name, "member_name": member_name}
    elif command in ["set_leader"]:
        project_name = input("请输入项目名称: ")
        if not project_name:
            print("项目名称不能为空")
            return
        leader_name = input("请输入新负责人姓名: ")
        if not leader_name:
            print("负责人姓名不能为空")
            return
        msg = {"type": "set_leader", "project_name": project_name, "leader_name": leader_name}
    elif command in ["is_leader"] :
        project_name = input("请输入项目名称: ")
        if not project_name:
            print("项目名称不能为空")
            return
        msg = {"type": "is_leader", "project_name": project_name}
    elif command in ["change_contribution"]:
        project_name = input("请输入项目名称: ")
        if not project_name:
            print("项目名称不能为空")
            return
        contribution = input("请输入贡献: ")
        if not contribution:
            print("贡献不能为空")
            return
        msg = {"type": "change_contribution", "project_name": project_name, "contribution": contribution}
    elif command in ["delete_contribution"]:
        project_name = input("请输入项目名称: ")
        if not project_name:
            print("项目名称不能为空")
            return
        contribution = input("请输入贡献序号: ")
        if not contribution:
            print("贡献不能为空")
            return
        msg = {"type": "delete_contribution_object", "project_name": project_name, "contribution_object": int(contribution)}
    elif command in ["set_password"]:
        password = input("请输入新密码: ")
        if not password:
            print("密码不能为空")
            return
        msg = {"type": "set_password","password": password}
    else:
        msg["type"] = command
    try:
        sock.send(json.dumps(msg).encode())
    except Exception as e:
        print(f"发送失败: {e}")


def receive_json(sock):
    try:
        data = sock.recv(BUFLEN)
        if not data:
            print("连接已关闭")
            return False
        try:
            message = json.loads(data.decode())
            print("收到:", message)
            msg = message.get("message", "")
            if not msg:
                msg = message.get("data", "")
            if isinstance(msg, list):
                print("数据列表:")
                for item in msg:
                    print(item)
            elif isinstance(msg, dict):
                print("数据字典:")
                for key, value in msg.items():
                    print(f"{key}: {value}")
            else:
                print("数据:", msg)
        except json.JSONDecodeError:
            print("收到非 JSON 消息:", data.decode())
        return True
    except:
        return False


def main():
    ip = input("请输入服务器地址（例如 127.0.0.1）: ").strip()
    port = input("请输入端口号（例如 25565）: ").strip()
    if not port.isdigit():
        print("端口号必须是数字")
        return

    sock = connect_to_server(ip, int(port))
    if not sock:
        return

    try:
        while True:
            command = input("输入命令(request / exit / close)：").strip()
            if not command:
                continue
            send_json_command(sock, command)
            if command == "exit":
                break
            if not receive_json(sock):
                break
    finally:
        sock.close()
        print("客户端已关闭")


if __name__ == "__main__":
    main()
