from socket import *
import json
import logging
import threading
import os

# 类的定义
# project
# person


class Person:
    islogin = False

    def __init__(self, name):
        self.name = name
        self.password = None  # 密码可以在后续方法中设置
        self.projects = {}  # 参与的项目列表

    def set_password(self, password):
        """设置密码"""
        self.password = password

    def __str__(self):
        return f"Person(name={self.name}, projects={list(self.projects.keys())})"

    def create_project(self, project_name, description):
        """创建新项目"""
        project = Project(project_name, description)
        project.contributions[self] = ["创建项目"]  # 添加创建者的贡献
        project.leader = self  # 设置项目负责人为创建者
        self.projects[project_name] = project
        save_data()


Persons = {}
Persons["None"] = Person(None)


class Project:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.contributions = {}  # person -> list of contributions
        self.leader = None  # 项目负责人
        self.remark = ""  # 新增：项目备注

    def add_contribution(self, person, contribution):
        if person not in self.contributions:
            raise ValueError(f"{person.name} 还不是该项目成员，无法添加贡献")
        self.contributions[person].append(contribution)

    def add_member(self, person):
        """添加项目成员"""
        if person not in self.contributions:
            self.contributions[person] = ["加入项目"]
            person.projects[self.name] = self  # 将项目添加到成员的项目列表中
            save_data()

    def set_leader(self, person):
        if person in self.contributions:
            self.leader = person
            save_data()
        else:
            raise ValueError(f"{person.name} 还不是该项目成员，无法设为负责人")

    def is_leader(self, person):
        return person == self.leader

    def __str__(self):
        leader_name = self.leader.name if self.leader else "无"
        return (
            f"Project(name={self.name}, description={self.description}, "
            f"leader={leader_name}, members={[p.name for p in self.contributions]})"
            f"contributions={{{', '.join([f'{p.name}: {c}' for p, c in self.contributions.items()])}}})"
            f"remark={self.remark}"
        )


IP = "0.0.0.0"
PORT = 25565
BUFLEN = 1024

msg_start = {"type": "start", "size": 0, "code": 200}
msg_over = {"type": "over", "code": 200}
msg_error = {"type": "error", "code": 404}
msg_success = {"type": "success", "code": 200, "message": "success"}
msg_connected = {"type": "connected", "code": 200}
msg_data = {"type": "data", "data": []}
msg_nouser = {"type": "nouser", "code": 200}

DATA_FILE = "design_manager_data.json"

logging.basicConfig(
    filename="log.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def log_message(message, level="info"):
    """记录日志信息并打印到控制台"""
    print(message)
    if level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)
    else:
        logging.info(message)


def save_data():
    """将数据保存到文件"""
    data_to_save = {}
    for name, person in Persons.items():
        data_to_save[name] = {
            "name": person.name,
            "password": person.password,
            "projects": list(person.projects.keys()),
            "islogin": person.islogin,
        }
    for person in Persons.values():
        for project in person.projects.values():
            data_to_save[project.name] = {
                "name": project.name,
                "description": project.description,
                "contributions": {
                    person.name: contributions
                    for person, contributions in project.contributions.items()
                },
                "leader": project.leader.name if project.leader else None,
                "remark": getattr(project, "remark", ""),  # 新增
            }
    with open(DATA_FILE, "w") as f:
        json.dump(data_to_save, f)
    log_message("数据已保存到文件")


def load_data():
    """从文件加载数据"""
    global Persons
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                loaded_data = json.load(f)
                for name, person_data in loaded_data.items():
                    if "password" not in person_data:
                        break
                    person = Person(person_data["name"])
                    person.password = person_data["password"]
                    person.islogin = False
                    Persons[name] = person
                for name, project_data in loaded_data.items():
                    if "projects" not in project_data:
                        project = Project(
                            project_data["name"], project_data["description"]
                        )
                        project.leader = Persons.get(project_data["leader"])
                        project.remark = project_data.get("remark", "")  # 新增
                        for person_name, contributions in project_data[
                            "contributions"
                        ].items():
                            person = Persons.get(person_name)
                            if person:
                                project.contributions[person] = contributions
                                person.projects[project.name] = project

                log_message("数据已从文件加载")
            except json.JSONDecodeError:
                log_message("数据文件格式错误，无法加载", level="error")
                Persons = {"None": Person(None)}
            except KeyError as e:
                log_message(f"数据文件缺少必要字段: {e}", level="error")
    else:
        log_message("未找到数据文件，使用默认设置")


def handle_client(datasocket, addr, shutdown_event, listenSocket):
    """处理客户端连接"""
    current_user = Persons["None"]
    log_message(f"处理客户端{addr}的请求")
    while True:
        try:
            data = datasocket.recv(BUFLEN)  # 接收客户端数据
            if not data:
                log_message(f"客户端{addr}已断开连接")
                break
            message = json.loads(data.decode())
            msg_type = message.get("type")

            if msg_type == "login":
                # 处理登录请求
                username = message.get("name")
                if username in Persons:
                    current_user = Persons[username]
                    if current_user.password is not None:
                        # 如果用户已存在且有密码，检查密码
                        password = message.get("password")
                        if password == current_user.password:
                            current_user.islogin = True
                            log_message(f"用户 {username} 登录成功")
                        else:
                            log_message(f"用户 {username} 密码错误", level="error")
                            datasocket.send(json.dumps(msg_error).encode())
                            continue
                    log_message(f"用户 {username} 登录成功")
                    current_user.islogin = True
                    msg_success["message"] = f"用户 {username} 登录成功"
                    datasocket.send(json.dumps(msg_success).encode())
                    msg_success["message"] = "success"  # 恢复message
                else:
                    # 如果用户不存在，创建新用户
                    current_user = Person(username)
                    Persons[username] = current_user
                    current_user.islogin = True
                    log_message(f"新用户 {username} 注册成功")
                    msg_success["message"] = f"用户 {username} 注册成功"
                    datasocket.send(json.dumps(msg_success).encode())
                    msg_success["message"] = "success"  # 恢复message
                save_data()
            elif msg_type == "set_password":
                # 处理设置密码请求
                if current_user.islogin:
                    password = message.get("password")
                    if password:
                        current_user.set_password(password)
                        log_message(f"用户 {current_user.name} 设置密码成功")
                        datasocket.send(json.dumps(msg_success).encode())
                    else:
                        log_message(
                            f"用户 {current_user.name} 设置密码失败，密码不能为空",
                            level="error",
                        )
                        datasocket.send(json.dumps(msg_error).encode())
                else:
                    log_message(f"用户 {current_user.name} 未登录", level="warning")
                    datasocket.send(json.dumps(msg_error).encode())
                save_data()

            elif msg_type == "logout":
                # 处理登出请求
                if current_user.islogin:
                    log_message(f"用户 {current_user.name} 登出成功")
                    current_user.islogin = False
                    datasocket.send(json.dumps(msg_success).encode())
                    current_user = Persons["None"]  # 重置当前用户
                else:
                    log_message(f"用户 {current_user.name} 未登录", level="warning")
                    datasocket.send(json.dumps(msg_error).encode())
                save_data()

            elif msg_type == "request_personal_data":
                # 发送start消息
                msg_data["data"] = current_user.__str__()
                msg_start["size"] = len(json.dumps(msg_data).encode())
                datasocket.send(json.dumps(msg_start).encode())
                # 等待客户端确认
                ack = datasocket.recv(BUFLEN)
                if json.loads(ack.decode()).get("type") == "ok":
                    # 发送数据
                    if current_user.islogin == False:
                        senddata = json.dumps(msg_nouser).encode()
                        datasocket.send(senddata)
                    else:
                        senddata = json.dumps(msg_data).encode()
                        datasocket.send(senddata)
                # 发送over消息
                datasocket.send(json.dumps(msg_over).encode())
                # 等待客户端确认
                final_ack = datasocket.recv(BUFLEN)
                if json.loads(final_ack.decode()).get("type") == "success":
                    log_message(f"客户端{addr}接收数据成功")
                    datasocket.send(json.dumps(msg_success).encode())
                else:
                    log_message(f"客户端{addr}接收数据异常", level="error")
                    datasocket.send(json.dumps(msg_error).encode())
            
            elif msg_type == "set_remark":
                project_name = message.get("project_name")
                remark = message.get("remark", "")
                if project_name not in current_user.projects:
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                project = current_user.projects[project_name]
                # 只有负责人可以设置备注
                if project.leader != current_user:
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                project.remark = remark
                save_data()
                datasocket.send(json.dumps(msg_success).encode())

            elif msg_type == "get_remark":
                project_name = message.get("project_name")
                if project_name not in current_user.projects:
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                project = current_user.projects[project_name]
                datasocket.send(json.dumps({"type": "remark", "remark": project.remark}).encode())


            elif msg_type == "request_project_data":
                projectname = message.get("name")
                log_message(f"客户端{addr}请求项目数据，项目名称{projectname}")
                if projectname not in current_user.projects:
                    log_message(f"客户{addr}不存在项目{projectname}")
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                project = current_user.projects[projectname]
                # 动态获取所有参与人
                members = [
                    person.name
                    for person in Persons.values()
                    if person.name and projectname in person.projects
                ]
                leader_name = project.leader.name if project.leader else "无"
                # 构造项目详情字符串
                project_info = (
                    f"Project(name={project.name}, description={project.description}, "
                    f"leader={leader_name}, members={members})"
                    f"contributions={{{', '.join([f'{p.name}: {c}' for p, c in project.contributions.items()])}}})"
                )
                # 发送start消息
                msg_data["data"] = project_info
                msg_start["size"] = len(json.dumps(msg_data).encode())
                datasocket.send(json.dumps(msg_start).encode())
                # 等待客户端确认
                ack = datasocket.recv(BUFLEN)
                if json.loads(ack.decode()).get("type") == "ok":
                    # 发送数据
                    senddata = json.dumps(msg_data).encode()
                    datasocket.send(senddata)
                # 发送over消息
                datasocket.send(json.dumps(msg_over).encode())
                # 等待客户端确认
                final_ack = datasocket.recv(BUFLEN)
                if json.loads(final_ack.decode()).get("type") == "success":
                    log_message(f"客户端{addr}接收数据成功")
                    datasocket.send(json.dumps(msg_success).encode())
                else:
                    log_message(f"客户端{addr}接收数据异常", level="error")
                    datasocket.send(json.dumps(msg_error).encode())

            elif msg_type == "create_project":
                # 处理创建项目请求
                project_name = message.get("name")
                description = message.get("description")
                if not project_name or not description:
                    log_message(
                        f"客户端{addr}创建项目失败，缺少名称或描述", level="error"
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                current_user.create_project(project_name, description)
                log_message(f"用户 {current_user.name} 创建项目 {project_name} 成功")
                datasocket.send(json.dumps(msg_success).encode())
                save_data()
            elif msg_type == "add_member":
                # 处理添加项目成员请求
                project_name = message.get("project_name")
                member_name = message.get("member_name")
                if project_name not in current_user.projects:
                    log_message(
                        f"用户 {current_user.name} 尝试添加成员到不存在的项目 {project_name}",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                if member_name not in Persons:
                    log_message(
                        f"用户 {current_user.name} 尝试添加不存在的成员 {member_name}",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                member = Persons[member_name]
                current_user.projects[project_name].add_member(member)
                log_message(
                    f"用户 {current_user.name} 成功将 {member_name} 添加到项目 {project_name}"
                )
                datasocket.send(json.dumps(msg_success).encode())
                save_data()
            elif msg_type == "set_leader":
                # 处理设置项目负责人请求
                project_name = message.get("project_name")
                leader_name = message.get("leader_name")
                if project_name not in current_user.projects:
                    log_message(
                        f"用户 {current_user.name} 尝试设置负责人到不存在的项目 {project_name}",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                if leader_name not in Persons:
                    log_message(
                        f"用户 {current_user.name} 尝试设置不存在的负责人 {leader_name}",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                leader = Persons[leader_name]
                current_user.projects[project_name].set_leader(leader)
                log_message(
                    f"用户 {current_user.name} 成功将 {leader_name} 设置为项目 {project_name} 的负责人"
                )
                datasocket.send(json.dumps(msg_success).encode())
                save_data()
            elif msg_type == "is_leader":
                # 处理检查是否为项目负责人的请求
                project_name = message.get("project_name")
                if project_name not in current_user.projects:
                    log_message(
                        f"用户 {current_user.name} 尝试检查不存在的项目 {project_name}",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                is_leader = current_user.projects[project_name].is_leader(current_user)
                response = {"type": "is_leader", "is_leader": is_leader}
                datasocket.send(json.dumps(response).encode())
            elif msg_type == "get_all_projects":
                # 处理获取所有项目请求
                projects_data = [
                    str(project) for project in current_user.projects.values()
                ]
                msg_data["data"] = projects_data
                msg_start["size"] = len(json.dumps(msg_data).encode())
                datasocket.send(json.dumps(msg_start).encode())
                ack = datasocket.recv(BUFLEN)
                if json.loads(ack.decode()).get("type") == "ok":
                    senddata = json.dumps(msg_data).encode()
                    datasocket.send(senddata)
                datasocket.send(json.dumps(msg_over).encode())
                final_ack = datasocket.recv(BUFLEN)
                if json.loads(final_ack.decode()).get("type") == "success":
                    log_message(f"客户端{addr}接收数据成功")
                    datasocket.send(json.dumps(msg_success).encode())
                else:
                    log_message(f"客户端{addr}接收数据异常", level="error")
                    datasocket.send(json.dumps(msg_error).encode())
            elif msg_type == "get_all_users":
                # 处理获取所有用户请求
                users_data = [
                    str(person)
                    for person in Persons.values()
                    if person.name is not None
                ]
                msg_data["data"] = users_data
                msg_start["size"] = len(json.dumps(msg_data).encode())
                datasocket.send(json.dumps(msg_start).encode())
                ack = datasocket.recv(BUFLEN)
                if json.loads(ack.decode()).get("type") == "ok":
                    senddata = json.dumps(msg_data).encode()
                    datasocket.send(senddata)
                datasocket.send(json.dumps(msg_over).encode())
                final_ack = datasocket.recv(BUFLEN)
                if json.loads(final_ack.decode()).get("type") == "success":
                    log_message(f"客户端{addr}接收数据成功")
                    datasocket.send(json.dumps(msg_success).encode())
                else:
                    log_message(f"客户端{addr}接收数据异常", level="error")
                    datasocket.send(json.dumps(msg_error).encode())

            elif msg_type == "change_contribution":
                # 处理修改贡献请求
                project_name = message.get("project_name")
                contribution = message.get("contribution")
                if project_name not in current_user.projects:
                    log_message(
                        f"用户 {current_user.name} 尝试修改不存在的项目 {project_name} 的贡献",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                if not contribution:
                    log_message(
                        f"用户 {current_user.name} 修改贡献失败，贡献不能为空",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                try:
                    current_user.projects[project_name].add_contribution(
                        current_user, contribution
                    )
                    log_message(
                        f"用户 {current_user.name} 成功修改项目 {project_name} 的贡献"
                    )
                    datasocket.send(json.dumps(msg_success).encode())
                except ValueError as e:
                    log_message(str(e), level="error")
                    datasocket.send(json.dumps(msg_error).encode())
                save_data()

            elif msg_type == "remove_member":
                # 处理删除项目成员请求
                project_name = message.get("project_name")
                member_name = message.get("member_name", "").strip().strip("'\"")
                if project_name not in current_user.projects:
                    log_message(
                        f"用户 {current_user.name} 尝试从不存在的项目 {project_name} 删除成员",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                if member_name not in Persons.keys():
                    log_message(
                        f"用户 {current_user.name} 尝试删除不存在的成员 {member_name}",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                member = Persons[member_name]
                project = current_user.projects[project_name]
                if member not in project.contributions.keys():
                    log_message(
                        f"用户 {current_user.name} 尝试删除非项目成员 {member_name}",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                # 不能删除项目负责人
                if project.leader == member:
                    log_message(
                        f"用户 {current_user.name} 尝试删除项目负责人 {member_name}",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                # 只有leader才能删除成员，且不能删除自己
                if project.leader != current_user:
                    log_message(
                        f"用户 {current_user.name} 不是项目 {project_name} 的负责人，无权删除成员",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                if member == current_user:
                    log_message(
                        f"用户 {current_user.name} 不能通过此接口删除自己",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                # 删除成员
                del project.contributions[member]
                if project_name in member.projects:
                    del member.projects[project_name]
                log_message(
                    f"用户 {current_user.name} 成功将 {member_name} 从项目 {project_name} 移除"
                )
                datasocket.send(json.dumps(msg_success).encode())
                save_data()

            elif msg_type == "delete_contribution_object":
                # 处理删除贡献对象请求
                project_name = message.get("project_name")
                contribution_object = message.get("contribution_object")
                if project_name not in current_user.projects:
                    log_message(
                        f"用户 {current_user.name} 尝试删除不存在的项目 {project_name} 的贡献对象",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                if (
                    contribution_object
                    not in current_user.projects[project_name].contributions
                ):
                    log_message(
                        f"用户 {current_user.name} 尝试删除不存在的贡献对象 {contribution_object}",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                del current_user.projects[project_name].contributions[
                    contribution_object
                ]
                log_message(
                    f"用户 {current_user.name} 成功删除项目 {project_name} 的贡献对象 {contribution_object}"
                )
                datasocket.send(json.dumps(msg_success).encode())
                save_data()
            elif msg_type == "delete_project":
                # 处理删除项目请求
                project_name = message.get("project_name")
                if not project_name:
                    log_message(
                        f"客户端{addr}删除项目失败，缺少项目名称", level="error"
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                if project_name not in current_user.projects:
                    log_message(
                        f"用户 {current_user.name} 尝试删除不存在的项目 {project_name}",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                project = current_user.projects[project_name]
                # 只有负责人才能删除项目
                if project.leader != current_user:
                    log_message(
                        f"用户 {current_user.name} 尝试删除项目 {project_name} 但不是负责人",
                        level="error",
                    )
                    datasocket.send(json.dumps(msg_error).encode())
                    continue
                # 删除项目
                # 从所有成员的projects中移除该项目
                for member in list(project.contributions.keys()):
                    if project_name in member.projects:
                        del member.projects[project_name]
                log_message(f"用户 {current_user.name} 删除项目 {project_name} 成功")
                datasocket.send(json.dumps(msg_success).encode())
                save_data()
            elif msg_type == "request_help":
                # 处理请求帮助消息
                help_message = (
                    "可用命令:\n"
                    "1. login: 登录或注册用户\n"
                    "2. set_password: 设置用户密码\n"
                    "3. logout: 登出当前用户\n"
                    "4. request_personal_data: 请求个人数据\n"
                    "5. request_project_data: 请求项目数据\n"
                    "6. create_project: 创建新项目\n"
                    "7. add_member: 添加项目成员\n"
                    "8. set_leader: 设置项目负责人\n"
                    "9. is_leader: 检查是否为项目负责人\n"
                    "10. get_all_projects: 获取所有参与的项目\n"
                    "11. get_all_users: 获取所有用户信息\n"
                    "12. request_help: 请求帮助信息\n"
                    "13. exit: 退出客户端\n"
                    "14. close: 关闭服务器"
                    "15. change_contribution: 修改项目贡献\n"
                    "16. delete_contribution_object: 删除项目贡献对象\n"
                    "请确保在发送命令时使用正确的格式和参数。"
                )
                datasocket.send(
                    json.dumps({"type": "help", "message": help_message}).encode()
                )

            elif message.get("command") == "exit":
                log_message(f"客户端{addr}发送退出命令")
                current_user.islogin = False
                break
            elif message.get("command") == "close":
                log_message(f"服务器关闭指令接收自{addr}")
                datasocket.send(json.dumps(msg_success).encode())
                # 设置关闭事件
                shutdown_event.set()
                # 关闭监听套接字以打断主循环的 accept()
                listenSocket.close()
                break
            else:
                log_message(f"未知消息类型来自{addr}: {msg_type}", level="warning")

        except ConnectionResetError:
            log_message(f"客户端{addr}异常关闭", level="warning")
            break
        except Exception as e:
            log_message(f"处理客户端{addr}时出错: {e}", level="error")
            break
    datasocket.close()
    log_message(f"与客户端{addr}的连接已关闭")


def main():
    """main function"""
    global listenSocket
    listenSocket = socket(AF_INET, SOCK_STREAM)
    listenSocket.bind((IP, PORT))  # 监听端口
    listenSocket.listen(5)  # 最大连接数

    shutdown_event = threading.Event()

    load_data()

    log_message(f"{IP}:{PORT} 服务器启动成功")

    while not shutdown_event.is_set():
        try:
            log_message(f"等待客户端连接...")
            datasocket, addr = listenSocket.accept()  # 接收客户端连接
            log_message(f"客户端{addr}已连接")
            datasocket.send(json.dumps(msg_connected).encode())
            client_thread = threading.Thread(
                target=handle_client,
                args=(datasocket, addr, shutdown_event, listenSocket),
            )
            client_thread.start()
        except OSError:
            # 当 listenSocket 被关闭时，会抛出 OSError，表示需要退出主循环
            if shutdown_event.is_set():
                log_message("服务器关闭中...")
            else:
                logging.error("监听套接字发生错误")
            break
        except Exception as e:
            logging.error(f"主循环中发生错误: {e}")
            break

    listenSocket.close()
    shutdown_event.set()
    log_message("服务器已关闭")


if __name__ == "__main__":
    main()
