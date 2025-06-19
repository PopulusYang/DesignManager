# DesignManager

一个基于 Python 的项目/成员管理系统，支持客户端（Tkinter GUI）、命令行客户端和服务器端。

## 目录结构

- `client.py`：图形化客户端，使用 Tkinter 实现。
- `op_client.py`：命令行客户端，支持手动输入命令与服务器交互。
- `server.py`：服务器端，支持多线程处理多个客户端连接。
- `design_manager_data.json`：项目和用户数据存储文件。
- `client_config.json`：客户端配置文件（服务器地址、端口、用户名等）。
- `log.log`：服务器日志文件。
- `test.py`：本地测试用的类和方法。
- `process.md`：流程图和开发文档。

## 快速开始

### 1. 启动服务器

```sh
python server.py
```

### 2. 启动客户端

- 图形界面客户端：

  ```sh
  python client.py
  ```

- 命令行客户端：

  ```sh
  python op_client.py
  ```

### 3. 功能说明

- 用户注册/登录、修改密码
- 创建/删除项目，添加/移除成员
- 设置/更改项目负责人
- 项目备注、成员贡献管理
- 日志记录与数据持久化

## 依赖

- Python 3.x
- Tkinter（标准库自带）

## 其他

- 流程图见 [process.md](process.md)
- 数据文件自动生成，无需手动创建

如有问题请联系管
