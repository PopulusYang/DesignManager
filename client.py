import tkinter as tk
from tkinter import messagebox
import socket
import json
import os

BUFLEN = 1024
CONFIG_FILE = "client_config.json"


class ClientApp:
    def __init__(self, master):
        self.master = master
        master.title("客户端")
        master.geometry("640x480")

        self.server_frame = tk.Frame(master)
        self.login_frame = tk.Frame(master)
        self.main_frame = None  # 主界面

        self.create_server_frame()
        self.create_login_frame()  # 提前创建登录界面

        self.server_frame.pack()

        self.sock = None
        self.current_user = None  # 保存当前登录用户
        self.projects = []  # 保存项目列表

        self.load_config()  # 加载配置

    def create_server_frame(self):
        # 使用教程
        tutorial = (
            "使用教程：\n"
            "1. 输入服务器地址和端口号，点击“连接服务器”。\n"
            "2. 连接成功后，输入姓名和密码登录或注册。\n"
            "3. 登录后可管理和参与项目。\n"
            "4. 若没有注册，将自动注册。\n（密码输入框需要输入任意字符，但该密码不会被保存）\n"
            "5. 如果需要密码，则登录后再修改密码。\n"
            "如有疑问请联系管理员。"
        )
        tk.Label(self.server_frame, text=tutorial, justify="left", fg="#1565c0").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0)
        )

        tk.Label(self.server_frame, text="服务器地址:").grid(
            row=1, column=0, padx=10, pady=10, sticky="e"
        )
        self.ip_entry = tk.Entry(self.server_frame)
        self.ip_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(self.server_frame, text="端口号:").grid(
            row=2, column=0, padx=10, pady=10, sticky="e"
        )
        self.port_entry = tk.Entry(self.server_frame)
        self.port_entry.grid(row=2, column=1, padx=10, pady=10)

        self.connect_btn = tk.Button(
            self.server_frame, text="连接服务器", command=self.connect_to_server
        )
        self.connect_btn.grid(row=3, column=0, columnspan=2, pady=20)

    def create_login_frame(self):
        tk.Label(self.login_frame, text="姓名:").grid(
            row=0, column=0, padx=10, pady=10, sticky="e"
        )
        self.name_entry = tk.Entry(self.login_frame)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.login_frame, text="密码:").grid(
            row=1, column=0, padx=10, pady=10, sticky="e"
        )
        self.password_entry = tk.Entry(self.login_frame, show="*")  # 密码显示为星号
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        self.login_btn = tk.Button(
            self.login_frame, text="登录 / 注册", command=self.login
        )
        self.login_btn.grid(row=2, column=0, columnspan=2, pady=20)

        self.back_btn = tk.Button(
            self.login_frame, text="返回", command=self.back_to_server_frame
        )
        self.back_btn.grid(row=3, column=0, columnspan=2, pady=20)

    def create_main_frame(self):
        # 创建主界面
        self.main_frame = tk.Frame(self.master)

        # 左侧：项目列表
        left_frame = tk.Frame(self.main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.project_list_label = tk.Label(left_frame, text="项目列表:")
        self.project_list_label.pack(anchor="w")

        self.project_list = tk.Listbox(left_frame, height=15, width=30)
        for project in self.projects:
            self.project_list.insert(tk.END, project)
        self.project_list.pack(fill=tk.BOTH, expand=True, pady=5)

        # 右侧：按钮区
        right_frame = tk.Frame(self.main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=20)

        self.welcome_label = tk.Label(right_frame, text=f"欢迎, {self.current_user}!")
        self.welcome_label.pack(pady=10)

        self.change_password_btn = tk.Button(
            right_frame, text="修改密码", command=self.show_change_password_dialog
        )
        self.change_password_btn.pack(fill=tk.X, pady=10)

        self.add_project_btn = tk.Button(
            right_frame, text="添加项目", command=self.show_add_project_dialog
        )
        self.add_project_btn.pack(fill=tk.X, pady=10)

        self.delete_project_btn = tk.Button(
            right_frame, text="删除选中项目", command=self.delete_selected_project
        )
        self.delete_project_btn.pack(fill=tk.X, pady=10)

        # 新增“进入项目”按钮
        self.enter_project_btn = tk.Button(
            right_frame, text="进入项目", command=self.enter_selected_project
        )
        self.enter_project_btn.pack(fill=tk.X, pady=10)

        self.logout_btn = tk.Button(right_frame, text="退出登录", command=self.logout)
        self.logout_btn.pack(fill=tk.X, pady=10)

        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def show_change_password_dialog(self):
        # 创建修改密码对话框
        dialog = tk.Toplevel(self.master)
        dialog.title("修改密码")

        tk.Label(dialog, text="新密码:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        new_password_entry = tk.Entry(dialog, show="*")
        new_password_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(dialog, text="确认密码:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        confirm_password_entry = tk.Entry(dialog, show="*")
        confirm_password_entry.grid(row=1, column=1, padx=5, pady=5)

        def change_password():
            new_password = new_password_entry.get().strip()
            confirm_password = confirm_password_entry.get().strip()

            if not new_password or not confirm_password:
                messagebox.showwarning("输入为空", "请输入新密码和确认密码")
                return

            if new_password != confirm_password:
                messagebox.showerror("密码不匹配", "两次输入的密码不一致")
                return

            # 发送修改密码请求
            try:
                if self.sock:
                    change_password_data = {
                        "type": "set_password",
                        "password": new_password,
                    }
                    self.sock.send(json.dumps(change_password_data).encode())

                    # 接收服务器响应
                    response = self.sock.recv(BUFLEN).decode()
                    response_data = json.loads(response)

                    if response_data.get("code") == 200:
                        messagebox.showinfo(
                            "修改成功", response_data.get("message", "密码修改成功")
                        )
                        dialog.destroy()  # 关闭对话框
                    else:
                        messagebox.showerror(
                            "修改失败", response_data.get("message", "密码修改失败")
                        )

            except Exception as e:
                messagebox.showerror("修改失败", f"与服务器通信失败: {e}")

        change_btn = tk.Button(dialog, text="确认修改", command=change_password)
        change_btn.grid(row=2, column=0, columnspan=2, pady=10)

    def connect_to_server(self):
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()

        if not port.isdigit():
            messagebox.showerror("错误", "端口号必须为数字")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, int(port)))
            data = self.sock.recv(BUFLEN).decode()
            print("服务器响应:", data)
            # 隐藏当前连接界面，显示登录界面
            self.server_frame.pack_forget()
            self.login_frame.pack()
        except Exception as e:
            messagebox.showerror("连接失败", f"无法连接服务器: {e}")
            if self.sock:
                self.sock.close()
                self.sock = None

    def login(self):
        name = self.name_entry.get().strip()
        password = self.password_entry.get().strip()
        if not name or not password:
            messagebox.showwarning("输入为空", "请输入姓名和密码")
            return
        print(f"登录用户: {name}, 密码: {password}")

        # 构建登录请求
        login_data = {"type": "login", "name": name, "password": password}
        try:
            # 发送登录请求到服务器
            self.sock.send(json.dumps(login_data).encode())

            # 接收服务器响应
            response = self.sock.recv(BUFLEN).decode()
            response_data = json.loads(response)

            if response_data.get("code") == 200:
                messagebox.showinfo(
                    "登录成功", response_data.get("message", "登录成功")
                )
                self.current_user = name  # 保存当前登录用户
                # 保存配置
                self.save_config()
                # 获取项目列表
                self.get_projects()
                # 隐藏登录界面，显示主界面
                self.login_frame.pack_forget()
                self.create_main_frame()
                self.main_frame.pack()
            else:
                messagebox.showerror(
                    "登录失败", response_data.get("message", "登录失败")
                )

        except Exception as e:
            messagebox.showerror("登录失败", f"与服务器通信失败: {e}")

    def logout(self):
        # 发送退出登录命令
        try:
            if self.sock:
                self.sock.send(json.dumps({"type": "logout"}).encode())
                # 接收服务器响应
                response = self.sock.recv(BUFLEN).decode()
                response_data = json.loads(response)
                if response_data.get("code") == 200:
                    messagebox.showinfo(
                        "退出成功", response_data.get("message", "退出成功")
                    )
                    self.current_user = None  # 清空当前用户
                    self.projects = []  # 清空项目列表

                    # 销毁主界面
                    if self.main_frame:
                        self.main_frame.destroy()
                        self.main_frame = None

                    # 显示服务器连接界面
                    self.server_frame.pack()
                else:
                    messagebox.showerror(
                        "退出失败", response_data.get("message", "退出失败")
                    )

        except Exception as e:
            messagebox.showerror("退出失败", f"与服务器通信失败: {e}")

    def back_to_server_frame(self):
        # 发送退出命令
        try:
            if self.sock:
                self.sock.send(json.dumps({"command": "exit"}).encode())
        except Exception as e:
            print(f"发送退出命令失败: {e}")

        # 销毁登录界面
        self.login_frame.pack_forget()
        # 显示服务器连接界面
        self.server_frame.pack()

    def load_config(self):
        """加载配置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.ip_entry.insert(0, config.get("server_ip", "127.0.0.1"))
                    self.port_entry.insert(0, config.get("server_port", "25565"))
                    self.name_entry.insert(0, config.get("username", ""))
                    self.password_entry.insert(0, config.get("password", ""))
            except Exception as e:
                print(f"加载配置失败: {e}")
        # 加载配置后隐藏登录界面
        self.login_frame.pack_forget()

    def save_config(self):
        """保存配置"""
        config = {
            "server_ip": self.ip_entry.get().strip(),
            "server_port": self.port_entry.get().strip(),
            "username": self.name_entry.get().strip(),
            "password": self.password_entry.get().strip(),
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def get_projects(self):
        """获取项目列表，只保留项目名称"""
        try:
            if self.sock:
                self.sock.send(json.dumps({"type": "get_all_projects"}).encode())

                # 接收start消息
                start_data = self.sock.recv(BUFLEN).decode()
                start_json = json.loads(start_data)
                if start_json.get("type") == "error":
                    # 服务端返回错误，说明没有项目
                    self.projects = []
                    self.refresh_project_list()
                    return
                if start_json.get("type") == "start":
                    total_size = start_json.get("size", 0)
                    self.sock.send(json.dumps({"type": "ok"}).encode())

                    # 循环接收数据
                    received = b""
                    while len(received) < total_size:
                        chunk = self.sock.recv(BUFLEN)
                        if not chunk:
                            break
                        received += chunk

                    # 只取前total_size字节，防止多收
                    try:
                        text = received[:total_size].decode()
                        data_json = json.loads(text)
                    except Exception as e:
                        messagebox.showerror(
                            "解析项目列表失败",
                            f"数据内容：{repr(received[:total_size])}\n错误：{e}",
                        )
                        return

                    # 只保留项目名称
                    self.projects = []
                    for item in data_json.get("data", []):
                        if "Project(name=" in item:
                            name_part = item.split("Project(name=")[1]
                            project_name = name_part.split(",")[0].strip()
                            self.projects.append(project_name)
                        else:
                            self.projects.append(item)

                    # 接收over消息
                    over_data = self.sock.recv(BUFLEN).decode()
                    if json.loads(over_data).get("type") == "over":
                        self.sock.send(json.dumps({"type": "success"}).encode())
                        # 这里再接收一次success消息并丢弃
                        try:
                            final_msg = self.sock.recv(BUFLEN).decode()
                            if final_msg:
                                final_json = json.loads(final_msg)
                                if final_json.get("type") == "success":
                                    pass
                        except Exception:
                            pass
                else:
                    messagebox.showerror(
                        "获取项目列表失败",
                        start_json.get("message", "获取项目列表失败"),
                    )
        except Exception as e:
            messagebox.showerror("获取项目列表失败", f"与服务器通信失败: {e}")

    def refresh_project_list(self):
        """刷新项目列表控件"""
        if hasattr(self, "project_list"):
            self.project_list.delete(0, tk.END)
            for project in self.projects:
                self.project_list.insert(tk.END, project)

    def show_add_project_dialog(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("添加项目")

        tk.Label(dialog, text="项目名称:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        name_entry = tk.Entry(dialog)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(dialog, text="项目描述:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        desc_entry = tk.Entry(dialog)
        desc_entry.grid(row=1, column=1, padx=5, pady=5)

        def add_project():
            name = name_entry.get().strip()
            desc = desc_entry.get().strip()
            if not name or not desc:
                messagebox.showwarning("输入为空", "请输入项目名称和描述")
                return
            try:
                if self.sock:
                    req = {"type": "create_project", "name": name, "description": desc}
                    self.sock.send(json.dumps(req).encode())
                    resp = self.sock.recv(BUFLEN).decode()
                    resp_data = json.loads(resp)
                    if resp_data.get("code") == 200:
                        messagebox.showinfo("添加成功", "项目添加成功")
                        dialog.destroy()
                        # 重新获取项目列表并刷新
                        self.get_projects()
                        self.refresh_project_list()
                    else:
                        messagebox.showerror(
                            "添加失败", resp_data.get("message", "添加项目失败")
                        )
            except Exception as e:
                messagebox.showerror("添加失败", f"与服务器通信失败: {e}")

        tk.Button(dialog, text="确认添加", command=add_project).grid(
            row=2, column=0, columnspan=2, pady=10
        )

    def delete_selected_project(self):
        selection = self.project_list.curselection()
        if not selection:
            messagebox.showwarning("未选择", "请先选择要删除的项目")
            return
        project_name = self.project_list.get(selection[0])
        # 确认对话框
        confirm = messagebox.askyesno("确认删除", f"确定要删除项目“{project_name}”吗？")
        if not confirm:
            return
        try:
            if self.sock:
                req = {"type": "delete_project", "project_name": project_name}
                self.sock.send(json.dumps(req).encode())
                resp = self.sock.recv(BUFLEN).decode()
                resp_data = json.loads(resp)
                if resp_data.get("code") == 200:
                    messagebox.showinfo("删除成功", "项目已删除")
                    # 重新获取项目列表并刷新
                    self.get_projects()
                    self.refresh_project_list()
                else:
                    messagebox.showerror(
                        "删除失败", resp_data.get("message", "删除项目失败")
                    )
        except Exception as e:
            messagebox.showerror("删除失败", f"与服务器通信失败: {e}")

    def enter_selected_project(self, project_name=None):
        if project_name is None:
            selection = self.project_list.curselection()
            if not selection:
                messagebox.showwarning("未选择", "请先选择要进入的项目")
                return
            project_name = self.project_list.get(selection[0])
        try:
            if self.sock:
                req = {"type": "request_project_data", "name": project_name}
                self.sock.send(json.dumps(req).encode())

                # 接收start消息
                start_data = self.sock.recv(BUFLEN).decode()
                start_json = json.loads(start_data)
                if start_json.get("type") == "start":
                    total_size = start_json.get("size", 0)
                    self.sock.send(json.dumps({"type": "ok"}).encode())

                    # 循环接收数据
                    received = b""
                    while len(received) < total_size:
                        chunk = self.sock.recv(BUFLEN)
                        if not chunk:
                            break
                        received += chunk

                    try:
                        text = received[:total_size].decode()
                        data_json = json.loads(text)
                    except Exception as e:
                        messagebox.showerror(
                            "解析项目详情失败",
                            f"数据内容：{repr(received[:total_size])}\n错误：{e}",
                        )
                        return

                    # 解析项目详情字符串
                    project_str = data_json.get("data", "")
                    desc = ""
                    leader = ""
                    members = ""
                    contributions = ""
                    try:
                        # 提取描述
                        if "description=" in project_str:
                            desc = (
                                project_str.split("description=")[1]
                                .split(", leader=")[0]
                                .strip()
                            )
                        # 提取负责人
                        if "leader=" in project_str:
                            leader = (
                                project_str.split("leader=")[1]
                                .split(", members=")[0]
                                .strip()
                            )
                        # 提取成员
                        if "members=[" in project_str:
                            members = (
                                project_str.split("members=[")[1].split("]")[0].strip()
                            )
                        # 提取贡献
                        if "contributions={" in project_str:
                            contributions = (
                                project_str.split("contributions={")[1]
                                .split("})")[0]
                                .strip()
                            )
                    except Exception:
                        pass

                    # 弹出详情窗口
                    detail = tk.Toplevel(self.master)
                    detail.title(f"项目详情 - {project_name}")
                    detail.geometry("640x480")

                    # 主体区域
                    main_frame = tk.Frame(detail)
                    main_frame.pack(fill=tk.BOTH, expand=True)

                    # 左侧：项目信息
                    left_frame = tk.Frame(main_frame)
                    left_frame.pack(
                        side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10
                    )
                    # 下方：按钮区
                    button_frame = tk.Frame(detail)
                    button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

                    tk.Label(left_frame, text=f"项目名称：{project_name}").pack(
                        anchor="w", pady=5
                    )
                    tk.Label(left_frame, text=f"项目描述：{desc}").pack(
                        anchor="w", pady=5
                    )
                    tk.Label(left_frame, text=f"项目负责人：{leader}").pack(
                        anchor="w", pady=5
                    )
                    tk.Label(left_frame, text=f"项目参与人：{members}").pack(
                        anchor="w", pady=5
                    )

                    # 查看贡献按钮
                    def show_contributions():
                        contrib_win = tk.Toplevel(detail)
                        contrib_win.title("项目贡献")
                        contrib_win.geometry("400x300")
                        if not contributions:
                            tk.Label(contrib_win, text="暂无贡献信息").pack(
                                padx=10, pady=10
                            )
                            return
                        # contributions字符串格式：成员1: [...], 成员2: [...]
                        for line in contributions.split("],"):
                            line = line.strip().rstrip(",")
                            if not line:
                                continue
                            if ":" in line:
                                member, contribs = line.split(":", 1)
                                member = member.strip()
                                contribs = contribs.strip().lstrip("[")
                                contribs_list = [
                                    c.strip().strip("'\"")
                                    for c in contribs.strip("[]").split(",")
                                    if c.strip()
                                ]
                                frame = tk.Frame(contrib_win)
                                frame.pack(anchor="w", fill=tk.X, padx=10, pady=2)
                                tk.Label(
                                    frame, text=f"{member}:", width=12, anchor="w"
                                ).pack(side=tk.LEFT)
                                lb = tk.Listbox(
                                    frame, height=len(contribs_list) or 1, width=30
                                )
                                for c in contribs_list:
                                    lb.insert(tk.END, c)
                                lb.pack(side=tk.LEFT, padx=5)

                    tk.Button(
                        button_frame, text="查看贡献", command=show_contributions
                    ).pack(side=tk.LEFT, padx=10)

                    # 增加成员按钮
                    def add_member_to_project():
                        # 获取所有用户（除自己和已在项目中的成员外）
                        try:
                            self.sock.send(
                                json.dumps({"type": "get_all_users"}).encode()
                            )
                            # 接收start消息
                            start_data = self.sock.recv(BUFLEN).decode()
                            start_json = json.loads(start_data)
                            if start_json.get("type") == "start":
                                total_size = start_json.get("size", 0)
                                self.sock.send(json.dumps({"type": "ok"}).encode())
                                received = b""
                                while len(received) < total_size:
                                    chunk = self.sock.recv(BUFLEN)
                                    if not chunk:
                                        break
                                    received += chunk
                                try:
                                    text = received[:total_size].decode()
                                    data_json = json.loads(text)
                                except Exception as e:
                                    messagebox.showerror(
                                        "解析用户列表失败",
                                        f"数据内容：{repr(received[:total_size])}\n错误：{e}",
                                    )
                                    return
                                # 提取所有用户名
                                all_users = []
                                for item in data_json.get("data", []):
                                    if "Person(name=" in item:
                                        name_part = item.split("Person(name=")[1]
                                        user_name = name_part.split(",")[0].strip()
                                        if user_name and user_name != self.current_user:
                                            all_users.append(user_name)
                                # 去除已在项目中的成员
                                current_members = [
                                    m.strip() for m in members.split(",") if m.strip()
                                ]
                                selectable_users = [
                                    u for u in all_users if u not in current_members
                                ]
                                # 弹出选择窗口
                                select_win = tk.Toplevel(detail)
                                select_win.title("选择要添加的成员")
                                tk.Label(select_win, text="请选择要添加的成员：").pack(
                                    anchor="w", padx=10, pady=5
                                )
                                lb = tk.Listbox(
                                    select_win,
                                    selectmode=tk.MULTIPLE,
                                    width=30,
                                    height=10,
                                )
                                for u in selectable_users:
                                    lb.insert(tk.END, u)
                                lb.pack(padx=10, pady=5)

                                def do_add():
                                    selected = lb.curselection()
                                    if not selected:
                                        messagebox.showwarning(
                                            "未选择", "请先选择要添加的成员"
                                        )
                                        return
                                    for idx in selected:
                                        member_name = lb.get(idx)
                                        try:
                                            req = {
                                                "type": "add_member",
                                                "project_name": project_name,
                                                "member_name": member_name,
                                            }
                                            self.sock.send(json.dumps(req).encode())
                                            resp = self.sock.recv(BUFLEN).decode()
                                            resp_data = json.loads(resp)
                                            if resp_data.get("code") == 200:
                                                pass
                                            else:
                                                messagebox.showerror(
                                                    "添加失败",
                                                    f"{member_name} 添加失败",
                                                )
                                        except Exception as e:
                                            messagebox.showerror(
                                                "添加失败",
                                                f"{member_name} 添加失败: {e}",
                                            )
                                    messagebox.showinfo(
                                        "添加完成", "成员添加操作已完成"
                                    )
                                    select_win.destroy()
                                    detail.destroy()  # 关闭原详情窗口
                                    self.enter_selected_project(
                                        project_name
                                    )  # 传递项目名，刷新详情

                                tk.Button(select_win, text="添加", command=do_add).pack(
                                    pady=10
                                )
                                # 接收over消息
                                over_data = self.sock.recv(BUFLEN).decode()
                                if json.loads(over_data).get("type") == "over":
                                    self.sock.send(
                                        json.dumps({"type": "success"}).encode()
                                    )
                                    try:
                                        final_msg = self.sock.recv(BUFLEN).decode()
                                        if final_msg:
                                            final_json = json.loads(final_msg)
                                            if final_json.get("type") == "success":
                                                pass
                                    except Exception:
                                        pass
                        except Exception as e:
                            messagebox.showerror(
                                "获取用户失败", f"与服务器通信失败: {e}"
                            )

                    tk.Button(
                        button_frame, text="增加成员", command=add_member_to_project
                    ).pack(side=tk.LEFT, padx=10)

                    # 删除成员按钮（仅leader可见）
                    if leader == self.current_user:

                        def delete_member_from_project():
                            # 获取可删除成员（不含负责人自己）
                            current_members = [
                                m.strip().strip("'\"")
                                for m in members.split(",")
                                if m.strip() and m.strip().strip("'\"") != leader
                            ]
                            if not current_members:
                                messagebox.showinfo(
                                    "无可删除成员", "没有可删除的成员。"
                                )
                                return
                            select_win = tk.Toplevel(detail)
                            select_win.title("选择要删除的成员")
                            tk.Label(select_win, text="请选择要删除的成员：").pack(
                                anchor="w", padx=10, pady=5
                            )
                            lb = tk.Listbox(
                                select_win,
                                selectmode=tk.SINGLE,
                                width=30,
                                height=10,
                            )
                            for u in current_members:
                                lb.insert(tk.END, u)
                            lb.pack(padx=10, pady=5)

                            def do_delete():
                                selected = lb.curselection()
                                if not selected:
                                    messagebox.showwarning(
                                        "未选择", "请先选择要删除的成员"
                                    )
                                    return
                                member_name = lb.get(selected[0]).strip().strip("'\"")
                                confirm = messagebox.askyesno(
                                    "确认删除",
                                    f"确定要将成员“{member_name}”移出项目吗？",
                                )
                                if not confirm:
                                    return
                                try:
                                    req = {
                                        "type": "remove_member",
                                        "project_name": project_name,
                                        "member_name": member_name,
                                    }
                                    self.sock.send(json.dumps(req).encode())
                                    resp = self.sock.recv(BUFLEN).decode()
                                    resp_data = json.loads(resp)
                                    if resp_data.get("code") == 200:
                                        messagebox.showinfo(
                                            "删除成功", f"{member_name} 已被移出项目"
                                        )
                                        select_win.destroy()
                                        detail.destroy()
                                        self.enter_selected_project(project_name)
                                    else:
                                        messagebox.showerror(
                                            "删除失败",
                                            resp_data.get("message", "删除成员失败"),
                                        )
                                except Exception as e:
                                    messagebox.showerror(
                                        "删除失败", f"{member_name} 删除失败: {e}"
                                    )

                            tk.Button(select_win, text="删除", command=do_delete).pack(
                                pady=10
                            )

                        tk.Button(
                            button_frame,
                            text="删除成员",
                            command=delete_member_from_project,
                        ).pack(side=tk.LEFT, padx=10)

                    # 更改负责人按钮（仅leader可见）
                    if leader == self.current_user:

                        def change_leader():
                            # 获取可选成员（不含当前负责人）
                            candidate_members = [
                                m.strip().strip("'\"")
                                for m in members.split(",")
                                if m.strip() and m.strip().strip("'\"") != leader
                            ]
                            if not candidate_members:
                                messagebox.showinfo(
                                    "无可选成员", "没有可设置为负责人的成员。"
                                )
                                return
                            select_win = tk.Toplevel(detail)
                            select_win.title("选择新负责人")
                            tk.Label(select_win, text="请选择新负责人：").pack(
                                anchor="w", padx=10, pady=5
                            )
                            lb = tk.Listbox(
                                select_win,
                                selectmode=tk.SINGLE,
                                width=30,
                                height=10,
                            )
                            for u in candidate_members:
                                lb.insert(tk.END, u)
                            lb.pack(padx=10, pady=5)

                            def do_set_leader():
                                selected = lb.curselection()
                                if not selected:
                                    messagebox.showwarning("未选择", "请先选择新负责人")
                                    return
                                new_leader = lb.get(selected[0]).strip().strip("'\"")
                                confirm = messagebox.askyesno(
                                    "确认更改",
                                    f"确定要将“{new_leader}”设为新负责人吗？",
                                )
                                if not confirm:
                                    return
                                try:
                                    req = {
                                        "type": "set_leader",
                                        "project_name": project_name,
                                        "leader_name": new_leader,
                                    }
                                    self.sock.send(json.dumps(req).encode())
                                    resp = self.sock.recv(BUFLEN).decode()
                                    resp_data = json.loads(resp)
                                    if resp_data.get("code") == 200:
                                        messagebox.showinfo(
                                            "更改成功", f"{new_leader} 已成为新负责人"
                                        )
                                        select_win.destroy()
                                        detail.destroy()
                                        self.enter_selected_project(project_name)
                                    else:
                                        messagebox.showerror(
                                            "更改失败",
                                            resp_data.get("message", "更改负责人失败"),
                                        )
                                except Exception as e:
                                    messagebox.showerror(
                                        "更改失败", f"{new_leader} 更改失败: {e}"
                                    )

                            tk.Button(
                                select_win, text="更改", command=do_set_leader
                            ).pack(pady=10)

                        tk.Button(
                            button_frame, text="更改负责人", command=change_leader
                        ).pack(side=tk.LEFT, padx=10)

                    # 增加贡献按钮（只能为自己添加）
                    def add_contribution():
                        # 只允许为自己添加
                        if self.current_user not in [
                            m.strip().strip("'\"") for m in members.split(",")
                        ]:
                            messagebox.showinfo(
                                "提示", "你不是该项目成员，无法添加贡献。"
                            )
                            return
                        win = tk.Toplevel(detail)
                        win.title("增加贡献")
                        tk.Label(win, text=f"贡献成员：{self.current_user}").grid(
                            row=0, column=0, padx=10, pady=5, sticky="w", columnspan=2
                        )
                        tk.Label(win, text="贡献内容：").grid(
                            row=1, column=0, padx=10, pady=5, sticky="e"
                        )
                        contrib_entry = tk.Entry(win, width=40)
                        contrib_entry.grid(row=1, column=1, padx=10, pady=5)

                        def do_add_contrib():
                            contrib = contrib_entry.get().strip()
                            if not contrib:
                                messagebox.showwarning("输入为空", "请输入贡献内容")
                                return
                            try:
                                req = {
                                    "type": "change_contribution",
                                    "project_name": project_name,
                                    "contribution": contrib,
                                }
                                self.sock.send(json.dumps(req).encode())
                                resp = self.sock.recv(BUFLEN).decode()
                                resp_data = json.loads(resp)
                                if resp_data.get("code") == 200:
                                    messagebox.showinfo("添加成功", "贡献已添加")
                                    win.destroy()
                                    detail.destroy()
                                    self.enter_selected_project(project_name)
                                else:
                                    messagebox.showerror(
                                        "添加失败",
                                        resp_data.get("message", "添加贡献失败"),
                                    )
                            except Exception as e:
                                messagebox.showerror(
                                    "添加失败", f"与服务器通信失败: {e}"
                                )

                        tk.Button(win, text="添加", command=do_add_contrib).grid(
                            row=2, column=0, columnspan=2, pady=10
                        )

                    # 显示成员最新贡献列表
                    latest_contribs = []
                    if contributions:
                        for line in contributions.split("],"):
                            line = line.strip().rstrip(",")
                            if not line:
                                continue
                            if ":" in line:
                                member, contribs = line.split(":", 1)
                                member = member.strip().strip("'\"")
                                contribs = contribs.strip().lstrip("[")
                                contribs_list = [
                                    c.strip().strip("'\"")
                                    for c in contribs.strip("[]").split(",")
                                    if c.strip()
                                ]
                                latest = contribs_list[-1] if contribs_list else ""
                                latest_contribs.append((member, latest))
                    if latest_contribs:
                        # 右侧：成员最新贡献
                        right_frame = tk.Frame(main_frame)
                        right_frame.pack(
                            side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10
                        )
                        tk.Label(
                            right_frame,
                            text="成员当前贡献：",
                            font=("微软雅黑", 15, "bold"),
                        ).pack(anchor="w")
                        for member, latest in latest_contribs:
                            tk.Label(
                                right_frame,
                                text=f"{member}: {latest}",
                                font=("微软雅黑", 13, "bold"),  # 字体加粗并放大
                                fg="#1a237e",
                            ).pack(anchor="w", pady=2)
                    else:
                        tk.Label(
                            right_frame,
                            text="暂无成员贡献信息",
                            font=("微软雅黑", 13, "bold"),
                        ).pack(anchor="w", padx=10, pady=10)

                    # 接收over消息
                    over_data = self.sock.recv(BUFLEN).decode()
                    if json.loads(over_data).get("type") == "over":
                        self.sock.send(json.dumps({"type": "success"}).encode())
                        # 这里再接收一次success消息并丢弃
                        try:
                            final_msg = self.sock.recv(BUFLEN).decode()
                            if final_msg:
                                final_json = json.loads(final_msg)
                                if final_json.get("type") == "success":
                                    pass
                        except Exception:
                            pass

                    tk.Button(
                        button_frame, text="增加贡献", command=add_contribution
                    ).pack(side=tk.LEFT, padx=10)

                    remark_var = tk.StringVar()
                    remark_var.set("")

                    def load_remark():
                        try:
                            req = {"type": "get_remark", "project_name": project_name}
                            self.sock.send(json.dumps(req).encode())
                            resp = self.sock.recv(BUFLEN).decode()
                            resp_data = json.loads(resp)
                            if resp_data.get("type") == "remark":
                                remark_var.set(resp_data.get("remark", ""))
                            else:
                                remark_var.set("")
                        except Exception:
                            remark_var.set("")

                    def edit_remark():
                        if leader != self.current_user:
                            messagebox.showinfo("无权限", "只有负责人可以编辑备注。")
                            return
                        edit_win = tk.Toplevel(detail)
                        edit_win.title("编辑项目备注")
                        tk.Label(edit_win, text="项目备注：").pack(
                            anchor="w", padx=10, pady=5
                        )
                        text = tk.Text(edit_win, width=40, height=5)
                        text.insert(tk.END, remark_var.get())
                        text.pack(padx=10, pady=5)

                        def save_remark():
                            new_remark = text.get("1.0", tk.END).strip()
                            try:
                                req = {
                                    "type": "set_remark",
                                    "project_name": project_name,
                                    "remark": new_remark,
                                }
                                self.sock.send(json.dumps(req).encode())
                                resp = self.sock.recv(BUFLEN).decode()
                                resp_data = json.loads(resp)
                                if resp_data.get("code") == 200:
                                    remark_var.set(new_remark)
                                    messagebox.showinfo("保存成功", "备注已保存")
                                    edit_win.destroy()
                                else:
                                    messagebox.showerror("保存失败", "备注保存失败")
                            except Exception as e:
                                messagebox.showerror(
                                    "保存失败", f"与服务器通信失败: {e}"
                                )

                        tk.Button(edit_win, text="保存", command=save_remark).pack(
                            pady=10
                        )

                    tk.Label(left_frame, text="项目备注：").pack(
                        anchor="w", pady=(10, 0)
                    )
                    remark_label = tk.Label(
                        left_frame,
                        textvariable=remark_var,
                        wraplength=200,
                        justify="left",
                        fg="#333",
                    )
                    remark_label.pack(anchor="w", pady=(0, 5))
                    tk.Button(left_frame, text="编辑备注", command=edit_remark).pack(
                        anchor="w", pady=(0, 10)
                    )

                    load_remark()

                else:
                    messagebox.showerror(
                        "获取项目详情失败",
                        start_json.get("message", "获取项目详情失败"),
                    )
        except Exception as e:
            messagebox.showerror("获取项目详情失败", f"与服务器通信失败: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()
