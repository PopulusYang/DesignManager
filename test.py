class Person:
    def __init__(self, name):
        self.name = name
        self.password = None  # 密码可以在后续方法中设置
        self.projects = {}  # 参与的项目列表

    def set_password(self, password):
        """设置密码"""
        self.password = password

    def __str__(self):
        return f"Person(name={self.name})"

    def create_project(self, project_name, description):
        """创建新项目"""
        project = Project(project_name, description)
        project.contributions[self] = ["创建项目"]  # 添加创建者的贡献
        project.leader = self  # 设置项目负责人为创建者
        self.projects[project_name] = project



class Project:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.contributions = {}  # person -> list of contributions
        self.leader = None  # 项目负责人

    def add_contribution(self, person, contribution):
        if person not in self.contributions:
            raise ValueError(f"{person.name} 还不是该项目成员，无法添加贡献")
        self.contributions[person].append(contribution)

    def add_member(self, person):
        """添加项目成员"""
        if person not in self.contributions:
            self.contributions[person] = ["加入项目"]
            person.projects[self.name] = self  # 将项目添加到成员的项目列表中

    def set_leader(self, person):
        if person in self.contributions:
            self.leader = person
        else:
            raise ValueError(f"{person.name} 还不是该项目成员，无法设为负责人")

    def is_leader(self, person):
        return person == self.leader

    def __str__(self):
        leader_name = self.leader.name if self.leader else "无"
        return (
            f"Project(name={self.name}, description={self.description}, "
            f"leader={leader_name}, members={[p.name for p in self.contributions]})"
        )


# 创建人物
alice = Person("Alice")
bob = Person("Bob")
projectname = "牛逼项目"
alice.create_project(projectname,"这个项目很牛逼")
project = alice.projects[projectname]
project.add_member(bob)
project.add_contribution(bob,"他有点太牛逼了")
project.set_leader(bob)
print(bob)
print(project)
for person, items in project.contributions.items():
    print(f"{person.name} 的贡献: {items}")
